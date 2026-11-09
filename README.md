# Glamira Project 05 — Data Source

Pipeline **Data Source** cho Glamira. Repo này không dựng GCS, BigQuery, dbt hay Looker.

## Checkpoint

| # | Deliverable | Trạng thái |
|---|---|---|
| 1 | Null % theo event type | `docs/null_profile.md` — full scan |
| 2 | Data quality report | `docs/data_quality_report.md` — 41,432,473 document |
| 3 | Scope confirmation | `docs/scope_confirmation.md` — đã tick GO |
| 4 | GCP + bucket | `infra/gcp/01_project.sh`, `02_bucket.sh` — xem `docs/implements.md` |
| 5 | `uv sync` | `.venv`, `uv.lock` |
| 6–7 | Mongo local + load raw | `glamira_raw` = 41,432,473, khớp nguồn |
| 8 | IP geolocation | `docs/ip_coverage.md` — checkout_success resolve 99.16% |
| 9 | Product URL seed | `enrich extract-products`. Không rút URL trong lúc nạp |
| 10 | Crawl pilot | `docs/crawl_pilot.md` — 96/97 trang có tên trên seed cũ. Mẫu field đủ: `docs/product_sample.md` |
| 11 | Crawl full | Chưa chạy |

## Dữ liệu

Hai file coach giao **không** nằm trong git:

- `data/raw/glamira_ubl_oct2019_nov2019.tar.gz` — mongodump. Đo được: 2020-04-01 → 2020-06-04 UTC.
- `data/reference/IP-COUNTRY-REGION-CITY.BIN` — IP2Location DB3, header 2016-11-29.

```bash
uv sync
uv run python -m unittest discover -s tests
uv run python -m src.cli ingest load-mongo
uv run python -m src.cli enrich ip
uv run python -m src.cli enrich extract-products
uv run python -m src.cli enrich crawl --limit 100      # --limit 0 = cả seed
uv run python -m src.cli enrich product-status        # products so với seed
uv run python -m src.cli enrich export-csv ip_geo     # CSV cạnh Mongo
uv run python -m src.cli enrich export-csv products
```

GCP (bucket, VM Mongo, nạp trên cloud): làm theo `docs/implements.md`, script trong `infra/gcp/`. Lệnh local: `docs/runbook.md`.

Đọc theo thứ tự: `docs/qua_trinh.md` là cách repo được dựng và cách đọc code. `docs/mongodb.md` là cách xem dữ liệu. Mở Compass chưa đủ: `mongod` phải đang chạy thì app mới đọc được file trong `data/mongo`.
