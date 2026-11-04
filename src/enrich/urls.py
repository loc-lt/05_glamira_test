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


def product_page_url(url: str) -> str | None:
    """Drop the query and keep the store that actually served the page."""
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
    return f"https://{host}{path}"


def canonical_product_url(url: str, base_url: str) -> str | None:
    """Drop the query and keep the store host that served the page.

    `base_url` is the host preferred when several stores have the same product.
    This function does not move a foreign path onto that host: `glamira-riipus-odila`
    on `.fi` is not a `.co.uk` URL.
    """
    if not base_url:
        return None
    return product_page_url(url)


def prefer_url(current: str | None, candidate: str) -> str:
    """Prefer a page whose host is already `www.glamira.co.uk`."""
    if current is None or page_rank(candidate) > page_rank(current):
        return candidate
    return current


def page_rank(url: str) -> tuple[int]:
    """A real `.co.uk` page ranks above the same product on another store."""
    host = (urlsplit(url).hostname or "").lower()
    return (int(host == "www.glamira.co.uk"),)
