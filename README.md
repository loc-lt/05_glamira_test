# Glamira Project 05 — Data Source

Pipeline **Data Source** cho Glamira. Repo này không dựng GCS, BigQuery, dbt hay Looker.

## Checkpoint

| # | Deliverable | Trạng thái |
|---|---|---|
| 1 | Null % theo event type | `docs/null_profile.md` — full scan |
| 2 | Data quality report | `docs/data_quality_report.md` — 41,432,473 document |
| 3 | Scope confirmation | `docs/scope_confirmation.md` — đã tick GO |
| 4–5 | `uv sync` | `.venv`, `uv.lock` |
| 6–7 | Mongo local + load raw | `glamira_raw` = 41,432,473, khớp nguồn |
| 8 | IP geolocation | `docs/ip_coverage.md` — checkout_success resolve 99.16% |
| 9 | Product URL seed | 19,093 URL canonical, file local `data/exports/product_urls.csv` |
| 10 | Crawl pilot | Site trả 403. Dừng, chưa đủ 95% |
| 11 | Crawl full | Chưa chạy, vì pilot bị chặn |

## Dữ liệu

Hai file coach giao **không** nằm trong git:

- `data/raw/glamira_ubl_oct2019_nov2019.tar.gz` — mongodump. Đo được: 2020-04-01 → 2020-06-04 UTC.
- `data/reference/IP-COUNTRY-REGION-CITY.BIN` — IP2Location DB3, header 2016-11-29.

```bash
uv sync
uv run python -m unittest discover -s tests
uv run python -m src.cli ingest load-mongo
uv run python -m src.cli enrich ip
```

Cloud chưa làm. Chi tiết lệnh: `docs/runbook.md`.
