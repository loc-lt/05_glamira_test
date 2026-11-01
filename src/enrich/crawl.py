"""Fetch a small number of canonical product pages and store name plus category.

One request per second. The pilot stops at `--limit` (100 for the acceptance run).
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from pymongo import UpdateOne

from src.config import Settings
from src.db import get_client


@dataclass
class CrawlResult:
    attempted: int
    http_200: int
    parsed: int
    elapsed_seconds: float

    @property
    def parse_rate(self) -> float:
        if self.attempted == 0:
            return 0.0
        return 100.0 * self.parsed / self.attempted


def parse_product_html(html: str) -> tuple[str | None, str | None]:
    """Return `(name, category)` from JSON-LD, then h1 and breadcrumbs."""
    soup = BeautifulSoup(html, "html.parser")
    name, category = _from_json_ld(soup)
    if not name:
        heading = soup.select_one("h1")
        if heading is not None:
            name = heading.get_text(" ", strip=True) or None
    if not category:
        crumbs = [
            node.get_text(" ", strip=True)
            for node in soup.select(".breadcrumbs a, nav[aria-label='Breadcrumb'] a, .breadcrumb a")
        ]
        crumbs = [item for item in crumbs if item and item.lower() not in {"home", "glamira"}]
        category = crumbs[-1] if crumbs else None
    return name, category


def crawl_seed(
    settings: Settings,
    *,
    seed_path: str = "data/exports/product_urls.csv",
    limit: int = 100,
    out_md: str = "docs/crawl_pilot.md",
) -> CrawlResult:
    rows = _read_seed(seed_path, limit)
    client = get_client(settings)
    catalog = client[settings.mongo_db][settings.mongo_collection_products]
    delay = 1.0 / settings.crawl_rate_limit_per_sec if settings.crawl_rate_limit_per_sec else 0.0
    started = time.perf_counter()
    http_200 = 0
    parsed = 0
    lines = [
        "# Crawl pilot",
        "",
        f"Limit: {limit}. Rate: {settings.crawl_rate_limit_per_sec} request/s.",
        "",
        "| product_id | status | parsed | url |",
        "|---|---:|---|---|",
    ]
    ops: list[UpdateOne] = []
    with httpx.Client(
        headers={
            "User-Agent": settings.crawl_user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
        },
        follow_redirects=True,
        timeout=30.0,
    ) as http:
        for index, (product_id, url) in enumerate(rows):
            if index:
                time.sleep(delay)
            status, name, category, error = _fetch_one(http, url)
            if status == 200:
                http_200 += 1
            ok = bool(name)
            if ok:
                parsed += 1
            lines.append(f"| `{product_id}` | {status} | {ok} | `{url}` |")
            ops.append(
                UpdateOne(
                    {"_id": product_id},
                    {
                        "$set": {
                            "product_id": product_id,
                            "url": url,
                            "name": name,
                            "category": category,
                            "http_status": status,
                            "error": error,
                            "crawled_at": datetime.now(timezone.utc),
                        }
                    },
                    upsert=True,
                )
            )
    if ops:
        catalog.bulk_write(ops, ordered=False)
    elapsed = time.perf_counter() - started
    result = CrawlResult(attempted=len(rows), http_200=http_200, parsed=parsed, elapsed_seconds=elapsed)
    lines.extend(
        [
            "",
            f"Attempted {result.attempted}. HTTP 200: {result.http_200}. "
            f"Name parsed: {result.parsed} ({result.parse_rate:.2f}%).",
            "",
        ]
    )
    Path(out_md).write_text("\n".join(lines), encoding="utf-8")
    return result


def _fetch_one(http: httpx.Client, url: str) -> tuple[int, str | None, str | None, str | None]:
    try:
        response = http.get(url)
    except httpx.HTTPError as exc:
        return 0, None, None, type(exc).__name__
    name, category = (None, None)
    if response.status_code == 200 and "html" in response.headers.get("content-type", ""):
        name, category = parse_product_html(response.text)
    return response.status_code, name, category, None


def _from_json_ld(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    for node in soup.select("script[type='application/ld+json']"):
        try:
            payload = json.loads(node.get_text())
        except json.JSONDecodeError:
            continue
        for item in _walk_ld(payload):
            kind = item.get("@type")
            types = kind if isinstance(kind, list) else [kind]
            if "Product" not in types:
                continue
            name = item.get("name")
            category = item.get("category")
            if isinstance(category, list):
                category = category[-1] if category else None
            if isinstance(category, dict):
                category = category.get("name")
            return _text(name), _text(category)
    return None, None


def _walk_ld(payload: object) -> list[dict]:
    if isinstance(payload, list):
        found: list[dict] = []
        for item in payload:
            found.extend(_walk_ld(item))
        return found
    if isinstance(payload, dict):
        nested = payload.get("@graph")
        if isinstance(nested, list):
            return _walk_ld(nested)
        return [payload]
    return []


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _read_seed(path: str, limit: int) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            url = (record.get("canonical_url") or "").strip()
            product_id = (record.get("product_id") or "").strip()
            if not url or not product_id:
                continue
            rows.append((product_id, url))
            if len(rows) >= limit:
                break
    return rows
