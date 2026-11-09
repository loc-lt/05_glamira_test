# GCP evidence

Dán output thật của từng lệnh vào đây sau mỗi checkpoint. Cách chạy: `docs/implements.md`.
Không dán mật khẩu, số billing account, email, hay URI có mật khẩu.

## Checkpoint 4 — project, API, bucket

- Project id:
- Region / zone: `asia-southeast1` / `asia-southeast1-b`
- Bucket:

```text
# output: gcloud services list --enabled (3 dòng compute/storage/bigquery)

# output: gsutil ls -l gs://<bucket>/smoke/
```

## Input trên GCS

```text
# output: gcloud storage ls -l gs://<bucket>/raw/ gs://<bucket>/reference/
# kỳ vọng: 5495914358 byte tar, 143974289 byte BIN
```

## Checkpoint 6 — VM Mongo, máy cá nhân nối được

- VM: `glamira-mongo`, `e2-standard-4`, 100 GB, Ubuntu 24.04, MongoDB 8.0
- Firewall: `glamira-mongo-from-my-ip`, tcp:27017 từ một IP `/32`

```text
# output ping từ máy cá nhân: {'ok': 1.0} và version 8.0.x
```

## Checkpoint 7 — nạp 41 triệu dòng

```text
# dòng cuối data/staging/load_vm.log
# output countDocuments: kỳ vọng glamira_raw 41432473
# danh sách index
```

Khác coach: không thêm `_loaded_at` / `_source_file`. `_id` là ObjectId gốc, nên nạp lại không nhân đôi.

## Checkpoint 8 — IP

```text
# ip_geo countDocuments: kỳ vọng 3239628
# checkout_success resolve rate: kỳ vọng 99.16%
# gcloud storage ls gs://<bucket>/exports/ip_geo.csv
```

## Checkpoint 9 — product URL seed

```text
# wc -l data/exports/product_urls.csv: kỳ vọng 19094 (header + 19093)
# số id trùng: kỳ vọng 0
```

## Checkpoint 11 — products

```text
# products countDocuments trên VM: kỳ vọng 19093
# số có name:
# gcloud storage ls gs://<bucket>/exports/products.csv
```
