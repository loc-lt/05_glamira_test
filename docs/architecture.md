# Architecture — Project 05 data source

Project 05 dừng ở **Data Source**. GCS, Cloud Function, BigQuery, dbt và Looker thuộc Project 06/07 và không có trong repo này.

```text
tar.gz (mongodump BSON) + IP2Location BIN
        │
        ▼
Phase 0  stream scan → null profile, quality report, scope
        │
        ▼
Phase 1  MongoDB glamira.glamira_raw          (sau khi scope GO)
        │
        ▼
Phase 2  geo fields + products_catalog
        │
        ▼
handoff  docs/handoff_to_project06.md         (chưa viết)
```

## Quyết định đã chốt từ việc mở archive

| Việc | Quyết định |
|---|---|
| Format | gzip + ustar. Bên trong là `dump/countly/summary.bson`, không phải JSONL |
| Cách đọc | Stream BSON theo length-prefix. Không giải nén 31 GB ra đĩa |
| Schema | Schema-on-read. Field phụ thuộc event (`collection`) |
| Tên `collection` | Event type. Mongo collection vận hành sẽ là `glamira_raw` |
| RAM | Chỉ giữ counter / HLL. Không load archive vào bộ nhớ |
| Cloud | Không dựng GCS trong P05 |
| Database khác | Không dùng PostgreSQL hay data Project 03–04 |
| PII | Email và user-agent không được ghi vào docs hay git |

Member `summary.bson` lớn hơn 8 GB nên header tar dùng GNU base-256. Reader xử lý cả octal lẫn base-256.

Index trong `summary.metadata.json`: `_id`, `time_stamp` (-1), `device_id`.

## Ranh giới enrich

Dashboard cần `country`/`city` và `product_name`/`category`. Raw event không có các field đó.

- IP → BIN (checkpoint 8), chỉ IP public.
- Product → `product_id` (và id trong `cart_products`) + URL `.html` trên `current_url` (checkpoint 9–11).

Canonical crawl host dự kiến `https://www.glamira.co.uk`, nhưng event thật đi nhiều TLD. Giả định và quyết định GO nằm trong `docs/scope_confirmation.md`.

## Đã đo (full scan)

- 41,432,473 BSON document, 0 lỗi parse, member `summary.bson` 31.23 GB, leftover 0.
- `time_stamp`: 2020-04-01 → 2020-06-04 UTC. Không dùng khoảng Oct–Nov 2019 trên tên file.
- IP public IPv4: 99.98%. BIN là DB3 IPv4 ngày 2016-11-29, chưa lookup.
