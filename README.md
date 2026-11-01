# Glamira Project 05 — Data Source

Pipeline **Data Source** cho Glamira. Repo này không dựng GCS, BigQuery, dbt hay Looker.

## Checkpoint

| # | Deliverable | Trạng thái |
|---|---|---|
| 1 | Null % theo event type | `docs/null_profile.md` — full scan |
| 2 | Data quality report | `docs/data_quality_report.md` — 41,432,473 document |
| 3 | Scope confirmation | `docs/scope_confirmation.md` — đề xuất GO, chờ xác nhận |
| 4–11 | uv, Mongo, IP lookup, crawl | Chưa làm |

## Dữ liệu

Hai file coach giao **không** nằm trong git:

- `glamira_ubl_oct2019_nov2019.tar.gz` — mongodump `dump/countly/summary.bson` (31.23 GB uncompressed). Dữ liệu đo được: 2020-04-01 → 2020-06-04 UTC.
- `IP-COUNTRY-REGION-CITY.BIN` — IP2Location DB3, header 2016-11-29.

```bash
cp .env.example .env   # điền DATA_TAR_PATH
python3 -m unittest discover -s tests
python3 -m src.cli explore quality-report --sample-size 0
```

Phase 0 dùng Python 3.12 stdlib. `uv` và Mongo để sau khi scope được xác nhận. Chi tiết lệnh: `docs/runbook.md`.
