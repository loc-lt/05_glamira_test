# Data dictionary — draft Phase 0

Schema-on-read. Bản này chỉ mô tả **raw event** nhìn thấy trong `summary.bson`. Field enrich (`geo_*`, catalog) sẽ được thêm sau checkpoint 8–11.

Scan: **full member**. Yêu cầu: entire member. Documents: **41,432,473**. Thời điểm: 2026-11-01T14:30:17Z.

## File

| Path | Vai trò |
|---|---|
| `glamira_ubl_oct2019_nov2019.tar.gz` | gzip ustar, mongodump Countly |
| `dump/countly/summary.metadata.json` | options + indexes của collection nguồn |
| `dump/countly/summary.bson` | BSON documents, nối tiếp nhau |
| `data/reference/IP-COUNTRY-REGION-CITY.BIN` | IP2Location DB3. Tra IP → country, region, city |

## Collection trên Mongo local

| Tên | Trạng thái | Ghi chú |
|---|---|---|
| `glamira.glamira_raw` | 41,432,473 document | Một event. `_id` là ObjectId gốc. Index: `collection`, `time_stamp`, `ip`, `product_id`, `viewing_product_id` |
| `glamira.ip_geo` | 3,239,628 document | Một IP. `_id` là chuỗi IP. Join `glamira_raw.ip` = `ip_geo._id`. Field: `country_code`, `country_name`, `region`, `city`, `status`, `events` |
| `glamira.products_catalog` | pilot bị 403 | `product_id`, `url`, `name`, `category`, `http_status`, `crawled_at` |

Đừng map field `collection` thành tên collection Mongo.

## Field raw đã gặp

Presence = số document có key, kể cả giá trị rỗng/null. Nullish nằm ở `docs/null_profile.md`.

| Field | Docs có key | % | Ghi chú Phase 0 |
|---|---:|---:|---|
| `_id` | 41,432,473 | 100.00% | ObjectId nguồn. Dùng làm khóa tự nhiên khi load. |
| `time_stamp` | 41,432,473 | 100.00% | Epoch giây (int). Mốc canonical; khớp ObjectId trong scan này. |
| `ip` | 41,432,473 | 100.00% | Public IPv4 41,422,559; IPv6 4,009. Không có country/city. |
| `user_agent` | 41,432,473 | 100.00% |  |
| `resolution` | 41,432,473 | 100.00% |  |
| `user_id_db` | 41,432,473 | 100.00% | Rỗng với khách chưa đăng nhập. |
| `device_id` | 41,432,473 | 100.00% | UUID thiết bị. |
| `api_version` | 41,432,473 | 100.00% |  |
| `store_id` | 41,432,473 | 100.00% | Mã cửa hàng, string. 86 giá trị trong scan này. |
| `local_time` | 41,432,473 | 100.00% | Wall clock string, không zero-pad. Không dùng làm mốc doanh thu. |
| `show_recommendation` | 41,432,473 | 100.00% |  |
| `current_url` | 41,432,473 | 100.00% | URL cửa hàng theo TLD. Trang sản phẩm thường chứa `.html`. |
| `referrer_url` | 41,432,473 | 100.00% |  |
| `email_address` | 41,432,473 | 100.00% | PII. Không đưa vào report hay git. |
| `collection` | 41,432,473 | 100.00% | Event type (view_product_detail, checkout, …). |
| `option` | 34,300,549 | 82.79% | Khi thì array, khi thì document. |
| `product_id` | 22,242,720 | 53.68% | Top-level là string khi có. Trong cart_products (sample checkout_success) là int. Không có name/category. |
| `cat_id` | 12,043,106 | 29.07% | Giá trị dùng được: 258. Không dùng làm category. |
| `collect_id` | 12,043,106 | 29.07% |  |
| `recommendation` | 10,944,427 | 26.42% |  |
| `utm_source` | 10,944,427 | 26.42% |  |
| `utm_medium` | 10,944,427 | 26.42% |  |
| `viewing_product_id` | 1,989,052 | 4.80% | Chủ yếu event recommendation, không phải trang detail. |
| `cart_products` | 457,696 | 1.10% | Array line item của checkout. `product_id` nằm ở phần tử con. |
| `recommendation_product_id` | 243,296 | 0.59% | Id phụ trên event recommendation. Không thay `product_id`. |
| `key_search` | 238,308 | 0.58% |  |
| `recommendation_clicked_position` | 204,773 | 0.49% |  |
| `price` | 187,901 | 0.45% | Số document bằng đúng `add_to_cart_action`. Không có ở top-level của `checkout_success`. |
| `currency` | 187,901 | 0.45% | Đi cùng top-level `price` trên add-to-cart. |
| `is_paypal` | 187,901 | 0.45% |  |
| `order_id` | 114,619 | 0.28% | Giá trị non-empty: 26,079, khớp số `checkout_success`. Key còn xuất hiện dạng rỗng trên `checkout`. |
| `recommendation_product_position` | 38,523 | 0.09% |  |

## Quy tắc làm sạch đã chốt cho các bước sau

- Nullish: missing + BSON null + `""`.
- `product_id` chuẩn hóa về string khi extract catalog.
- IP private / empty / invalid không lookup BIN.
- Join catalog dự kiến trên `product_id` string.
