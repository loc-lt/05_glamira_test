# Runbook

Chạy mọi lệnh từ root repo. Phase 0 dùng thư viện chuẩn của Python 3.12, chưa cần `uv` hay Mongo.

## Dữ liệu local

Archive và BIN không nằm trong git. Trỏ tới file coach đã giao:

```bash
cp .env.example .env
# sửa DATA_TAR_PATH và IP_BIN_PATH thành đường dẫn thật
```

Hoặc truyền `--path` mỗi lần chạy.

## Phase 0

Smoke 500k document:

```bash
python3 -m src.cli explore null-profile \
  --path /path/to/glamira_ubl_oct2019_nov2019.tar.gz \
  --sample-size 500000 \
  --out docs/null_profile.md
```

Quét cả member (báo cáo đã sinh ngày 2026-11-01: **41,432,473** document, khoảng 43 phút, ~15.9k docs/s). Một lần chạy ghi null profile, quality report, dictionary draft và JSON local (gitignored):

```bash
python3 -m src.cli explore quality-report \
  --path /path/to/glamira_ubl_oct2019_nov2019.tar.gz \
  --sample-size 0 \
  --out docs/data_quality_report.md \
  --null-out docs/null_profile.md \
  --dictionary-out docs/data_dictionary.md \
  --stats-out data/staging/profile_stats.json
```

Test:

```bash
python3 -m unittest discover -s tests
```

## Mongo local (không cloud)

Binary người dùng, không cần sudo. Dữ liệu nằm trong `data/mongo` (gitignored).

```bash
mkdir -p data/mongo
~/.local/mongodb/bin/mongod \
  --dbpath data/mongo \
  --bind_ip 127.0.0.1 \
  --port 27017 \
  --wiredTigerCacheSizeGB 1
```

`.env` trỏ `MONGO_URI=mongodb://127.0.0.1:27017/`.

```bash
uv sync
uv run python -m src.cli ingest load-mongo
uv run python -m src.cli enrich ip
uv run python -m src.cli enrich extract-products
uv run python -m src.cli enrich crawl --limit 100
```

Lệnh crawl mở Google Chrome đã cài trên máy và nghỉ ngẫu nhiên khoảng 1,5–4,2 giây giữa hai trang.

`load-mongo` chỉ ghi `glamira_raw` và tần suất IP. URL sản phẩm là lệnh `extract-products`, chạy sau khi nạp xong. `_id` là ObjectId gốc nên chạy lại không nhân bản.
