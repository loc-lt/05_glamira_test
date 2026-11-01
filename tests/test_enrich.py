from __future__ import annotations

import unittest

from src.enrich.crawl import parse_product_html
from src.enrich.urls import canonical_product_url, normalize_product_id, prefer_url


class UrlRuleTest(unittest.TestCase):
    def test_canonical_replaces_host_and_drops_query(self) -> None:
        raw = "https://www.glamira.de/glamira-ring-griseus.html?alloy=yellow-585&gclid=abc"
        self.assertEqual(
            canonical_product_url(raw, "https://www.glamira.co.uk"),
            "https://www.glamira.co.uk/glamira-ring-griseus.html",
        )

    def test_listing_url_is_not_a_product(self) -> None:
        self.assertIsNone(
            canonical_product_url("https://www.glamira.de/diamant-verlobungsringe/", "https://www.glamira.co.uk")
        )

    def test_cart_int_and_detail_string_match(self) -> None:
        self.assertEqual(normalize_product_id(95519), "95519")
        self.assertEqual(normalize_product_id("95519"), "95519")
        self.assertEqual(normalize_product_id(95519.0), "95519")

    def test_prefer_uk_host(self) -> None:
        de = "https://www.glamira.de/ring.html"
        uk = "https://www.glamira.co.uk/ring.html"
        self.assertEqual(prefer_url(de, uk), uk)
        self.assertEqual(prefer_url(uk, de), uk)


class HtmlParserTest(unittest.TestCase):
    def test_json_ld_name_and_category(self) -> None:
        html = """
        <html><head>
          <script type="application/ld+json">
            {"@type": "Product", "name": "Griseus", "category": "Rings"}
          </script>
        </head>
        <body><h1>ignored</h1></body></html>
        """
        self.assertEqual(parse_product_html(html), ("Griseus", "Rings"))

    def test_breadcrumb_fallback(self) -> None:
        html = """
        <html><body>
          <nav class="breadcrumbs"><a>Home</a><a>Rings</a><a>Griseus</a></nav>
          <h1>Griseus Ring</h1>
        </body></html>
        """
        self.assertEqual(parse_product_html(html), ("Griseus Ring", "Griseus"))


if __name__ == "__main__":
    unittest.main()
