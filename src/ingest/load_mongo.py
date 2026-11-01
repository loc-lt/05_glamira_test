"""Stream summary.bson into `glamira_raw`.

The source ObjectId is the Mongo `_id`, so a second run does not duplicate rows.
One pass also records IP frequencies and product URLs. Reading the 5 GB gzip
twice would add another ~40 minutes and is unnecessary.
"""

from __future__ import annotations

import shutil
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from bson import decode as decode_bson
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

from src.config import Settings
from src.db import get_client
from src.enrich.urls import canonical_product_url, normalize_product_id, prefer_url
from src.stream.tar_bson import SummaryDump

_MIN_FREE_BYTES = 8 * 1024 * 1024 * 1024


@dataclass
class LoadResult:
    docs_scanned: int
    inserted: int
    duplicates: int
    completed_member: bool
    mongo_count: int
    elapsed_seconds: float
    stopped_for_disk: bool
    ip_count_path: str
    product_seed_path: str
    distinct_ips: int
    detail_products: int


@dataclass
class _Sidecar:
    ip_counts: dict[str, int] = field(default_factory=dict)
    detail_urls: dict[str, str] = field(default_factory=dict)
    cart_ids: set[str] = field(default_factory=set)
    checkout_ips: dict[str, int] = field(default_factory=dict)
    checkout_docs: int = 0
    checkout_lines: int = 0
    checkout_lines_with_price: int = 0


def load_tar(
    path: str,
    settings: Settings,
    *,
    batch_size: int | None = None,
    limit: int = 0,
    progress_every: int = 200_000,
    database: str | None = None,
    collection: str | None = None,
    write_sidecars: bool = True,
    ip_count_path: str = "data/staging/ip_event_counts.tsv",
    product_seed_path: str = "data/exports/product_urls.csv",
) -> LoadResult:
    client = get_client(settings)
    client.admin.command("ping")
    db_name = database or settings.mongo_db
    coll_name = collection or settings.mongo_collection_raw
    coll = client[db_name][coll_name]
    batch_size = batch_size or settings.ingest_batch_size
    started = time.perf_counter()
    sidecar = _Sidecar()
    batch: list[dict] = []
    scanned = 0
    inserted = 0
    duplicates = 0
    stopped_for_disk = False
    dump = SummaryDump(path)

    for raw in dump:
        document = decode_bson(raw)
        _observe(document, sidecar, settings.crawl_base_url)
        batch.append(document)
        scanned += 1
        if len(batch) >= batch_size:
            added, dup = _flush(coll, batch)
            inserted += added
            duplicates += dup
            batch.clear()
            if progress_every and scanned % progress_every == 0:
                _log(scanned, inserted, duplicates, started)
            if _disk_is_low(ip_count_path):
                stopped_for_disk = True
                break
        if limit and scanned >= limit:
            break
    if batch and not stopped_for_disk:
        added, dup = _flush(coll, batch)
        inserted += added
        duplicates += dup

    completed = dump.completed and not stopped_for_disk and limit == 0
    if write_sidecars and completed:
        _write_ip_counts(ip_count_path, sidecar.ip_counts)
        checkout_path = str(Path(ip_count_path).with_name("checkout_success_ips.tsv"))
        _write_ip_counts(checkout_path, sidecar.checkout_ips)
        _write_product_seed(product_seed_path, sidecar, settings.crawl_base_url)
        _ensure_indexes(coll)
    mongo_count = coll.count_documents({}) if (completed or limit or stopped_for_disk) else coll.estimated_document_count()
    return LoadResult(
        docs_scanned=scanned,
        inserted=inserted,
        duplicates=duplicates,
        completed_member=completed,
        mongo_count=mongo_count,
        elapsed_seconds=time.perf_counter() - started,
        stopped_for_disk=stopped_for_disk,
        ip_count_path=ip_count_path if completed else "",
        product_seed_path=product_seed_path if completed else "",
        distinct_ips=len(sidecar.ip_counts),
        detail_products=len(sidecar.detail_urls),
    )


def _observe(document: dict, sidecar: _Sidecar, base_url: str) -> None:
    ip = document.get("ip")
    if isinstance(ip, str) and ip:
        sidecar.ip_counts[ip] = sidecar.ip_counts.get(ip, 0) + 1
    event = document.get("collection")
    if event == "view_product_detail":
        product_id = normalize_product_id(document.get("product_id"))
        url = document.get("current_url")
        if product_id and isinstance(url, str):
            canonical = canonical_product_url(url, base_url)
            if canonical:
                sidecar.detail_urls[product_id] = prefer_url(sidecar.detail_urls.get(product_id), canonical)
    elif event == "checkout_success":
        sidecar.checkout_docs += 1
        if isinstance(ip, str) and ip:
            sidecar.checkout_ips[ip] = sidecar.checkout_ips.get(ip, 0) + 1
        for line in document.get("cart_products") or []:
            if not isinstance(line, dict):
                continue
            sidecar.checkout_lines += 1
            product_id = normalize_product_id(line.get("product_id"))
            if product_id:
                sidecar.cart_ids.add(product_id)
            price = line.get("price")
            if isinstance(price, str) and price.strip():
                sidecar.checkout_lines_with_price += 1


def _flush(collection: Collection, batch: list[dict]) -> tuple[int, int]:
    try:
        result = collection.insert_many(batch, ordered=False)
    except BulkWriteError as exc:
        details = exc.details or {}
        errors = details.get("writeErrors") or []
        other = [item for item in errors if item.get("code") != 11000]
        if other:
            sample = other[0]
            raise RuntimeError(
                f"mongo write failed code={sample.get('code')} message={sample.get('errmsg')}"
            ) from exc
        inserted = int(details.get("nInserted") or 0)
        return inserted, len(errors)
    return len(result.inserted_ids), 0


def _ensure_indexes(collection: Collection) -> None:
    collection.create_index("collection")
    collection.create_index("time_stamp")
    collection.create_index("ip")
    collection.create_index("product_id", sparse=True)
    collection.create_index("viewing_product_id", sparse=True)


def _disk_is_low(anchor: str) -> bool:
    path = Path(anchor).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(path.parent).free
    if free < _MIN_FREE_BYTES:
        print(f"[load] stop: only {free / 1024**3:.1f} GiB free", flush=True)
        return True
    return False


def _write_ip_counts(path: str, counts: dict[str, int]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for ip, count in counts.items():
            handle.write(f"{ip}\t{count}\n")


def _write_product_seed(path: str, sidecar: _Sidecar, base_url: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    missing = sidecar.cart_ids - set(sidecar.detail_urls)
    with destination.open("w", encoding="utf-8") as handle:
        handle.write("product_id,canonical_url,has_detail_url,in_checkout_success\n")
        for product_id, url in sorted(sidecar.detail_urls.items()):
            in_checkout = "1" if product_id in sidecar.cart_ids else "0"
            handle.write(f"{product_id},{url},1,{in_checkout}\n")
        for product_id in sorted(missing):
            handle.write(f"{product_id},,0,1\n")
    note = destination.with_suffix(".md")
    price_pct = (
        100.0 * sidecar.checkout_lines_with_price / sidecar.checkout_lines
        if sidecar.checkout_lines
        else 0.0
    )
    note.write_text(
        "\n".join(
            [
                "# Product seed",
                "",
                f"- Detail products with a `.html` URL: {len(sidecar.detail_urls):,}",
                f"- Product ids seen in `checkout_success` carts: {len(sidecar.cart_ids):,}",
                f"- Checkout ids with no detail URL: {len(missing):,}",
                f"- `checkout_success` documents: {sidecar.checkout_docs:,}",
                f"- Cart lines: {sidecar.checkout_lines:,}",
                f"- Cart lines with a non-empty price: {sidecar.checkout_lines_with_price:,} ({price_pct:.2f}%)",
                f"- Canonical host: {base_url}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _log(scanned: int, inserted: int, duplicates: int, started: float) -> None:
    elapsed = time.perf_counter() - started
    rate = scanned / elapsed if elapsed else 0
    print(
        f"[load] scanned={scanned:,} inserted={inserted:,} dup={duplicates:,} "
        f"rate={rate:,.0f}/s elapsed={elapsed:,.0f}s",
        flush=True,
    )


def iter_decoded(path: str, limit: int = 0) -> Iterable[dict]:
    seen = 0
    for raw in SummaryDump(path):
        yield decode_bson(raw)
        seen += 1
        if limit and seen >= limit:
            break
