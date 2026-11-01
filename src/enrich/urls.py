"""Product id and canonical URL rules. No network, no Mongo."""

from __future__ import annotations

from urllib.parse import urlsplit


def normalize_product_id(value: object) -> str:
    """Cart ids are ints. Detail pages store the same id as a string."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def canonical_product_url(url: str, base_url: str) -> str | None:
    """Keep the product path and force the agreed host, dropping query strings."""
    if not url or ".html" not in url:
        return None
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if "glamira." not in host:
        return None
    path = parts.path
    html_at = path.lower().find(".html")
    if html_at < 0:
        return None
    path = path[: html_at + len(".html")]
    if not path.startswith("/"):
        path = "/" + path
    base = base_url.rstrip("/")
    return f"{base}{path}"


def prefer_url(current: str | None, candidate: str) -> str:
    """Prefer an already-canonical .co.uk URL over a translated storefront."""
    if current is None:
        return candidate
    if "glamira.co.uk" in candidate and "glamira.co.uk" not in current:
        return candidate
    return current
