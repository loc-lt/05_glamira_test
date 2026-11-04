# Hướng dẫn coach — Glamira Project 5, giải thích bằng tiếng Việt

Nguồn: trang Notion “Glamira Project 5” của coach. Đây là bản dịch và giải thích để đọc, không thay trang gốc.

Project 5 chỉ làm **nguồn dữ liệu**. Dashboard vẽ ở project sau. Việc của project này là hiểu log, nạp MongoDB, rồi bổ sung hai thứ log không có sẵn: **nước/thành phố** và **tên/loại sản phẩm**.

Quy tắc của coach: hiểu dữ liệu trước, dựng máy chủ sau. Mỗi checkpoint là một ý, xong thì commit và đẩy GitHub rồi mới sang bước kế.

## Dashboard cần gì

| Dashboard | Câu hỏi | Thiếu trong log |
|---|---|---|
| Doanh thu theo địa lý | Đức có cao hơn Pháp không? | `country`, `city` |
| Sản phẩm | Nhẫn có bán chạy hơn vòng tay không? | `product_name`, `category` |

Ví dụ coach đưa: event `checkout_success` có `ip` và `product_id`, không có nước và không có loại sản phẩm. Hai việc bổ sung là:

- IP `85.115.53.202` tra thư viện IP2Location ra nước và thành phố.
- `product_id` `96047` mở trang trên `glamira.co.uk` để lấy tên và category.

Ví dụ đó được viết cho dễ hiểu. Trong file thật, id sản phẩm của đơn hàng nằm trong mảng `cart_products`, không nằm ở field top-level `product_id`.

## Mười một checkpoint

| # | Pha | Việc cần xong |
|---|---|---|
| 1 | 0 | Đo % giá trị trống theo từng loại event |
| 2 | 0 | Viết `data_quality_report.md` |
| 3 | 0 | `scope_confirmation.md` có quyết định GO cho IP và sản phẩm |
| 4 | 1 | Tạo project GCP, bật API, tạo bucket GCS, upload thử một file |
| 5 | 1 | Tạo project Python bằng `uv`, `uv sync` chạy được |
| 6 | 1 | Máy ảo MongoDB trên GCP, máy cá nhân kết nối được |
| 7 | 1 | Nạp đủ khoảng 41 triệu dòng, số document trong Mongo khớp file nguồn |
| 8 | 2 | Tra IP xong, đo được % phủ |
| 9 | 2 | Rút ra tập `product_id` và URL, không trùng |
| 10 | 2 | Crawl thử 100 sản phẩm, đọc được HTML |
| 11 | 2 | Crawl hết, viết xong `data_dictionary.md` |

Pha 2 chỉ làm những mục đã GO ở checkpoint 3.

## Pha 0 — xem dữ liệu, chưa tốn tiền cloud

Mục đích: biết file là gì và cần làm gì trước khi thuê máy ảo.

### Bước 0.1 — project Python và mẫu nhỏ

Cài `uv`, clone repo, chạy `uv sync`. `uv` tạo `.venv` và khóa phiên bản thư viện.

Chỉ lấy mẫu khoảng 10.000–100.000 dòng, chưa đụng 41 triệu. Script in ra số dòng, vài dòng đầu, danh sách loại event, số dòng mỗi loại, khoảng ngày, và số IP khác nhau.

Xong khi script chạy và in ra danh sách event.

### Bước 0.2 — schema và giá trị trống

Cùng một collection Mongo vẫn chứa nhiều loại event. Mỗi loại có bộ field riêng. Đây gọi là schema-on-read: không ép mọi document cùng một form ngay từ đầu.

Việc cần làm là đo % trống của `product_id`, `order_id`, IP theo từng event, rồi trả lời vì sao `checkout_success` có `order_id` và `cart_products` còn `view_product_detail` thì không. Đó là thiết kế của log, không phải file bị hỏng.

### Bước 0.3 — chất lượng dữ liệu

Viết `data_quality_report.md` với ít nhất năm kiểm tra trên dữ liệu thật: id trùng, ngày ở tương lai, doanh thu âm, IP trống, và danh sách tiền tệ. Nhiều loại tiền thì project sau phải quy đổi, project này chưa quy đổi.

### Bước 0.4 — chốt phạm vi

Đây là mục trong link bạn gửi. Trả lời ba câu rồi ghi vào `scope_confirmation.md`:

1. Dashboard có cần doanh thu theo nước không? Log đã có sẵn nước chưa? Quyết định làm hay bỏ tra IP.
2. Dashboard có cần tên và category không? `view_product_detail` đã có `product_name` chưa? Nếu chưa thì phải crawl.
3. Cần nạp đủ 41 triệu dòng hay chỉ mẫu? Đủ 41 triệu thì cần máy ảo và MongoDB.

GO nghĩa là được sang Pha 1. Chưa có file này thì coach bảo dừng.

## Pha 1 — hạ tầng và nạp đủ dữ liệu

Chỉ bắt đầu sau khi Pha 0 đã chốt.

### Bước 1.1 — GCP và GCS

Tạo project Google Cloud, bật Compute Engine, Cloud Storage, BigQuery. Tạo bucket `glamira-raw-data-[region]`, tạo service account, upload thử một file mẫu. Checkpoint qua khi `gsutil cp` thành công.

### Bước 1.2 — máy ảo và MongoDB

Tạo VM Ubuntu, khoảng 16–32 GB RAM, đĩa 100 GB. Cài MongoDB 6, tạo user, chỉ mở firewall cho IP của mình. Checkpoint qua khi từ máy cá nhân chạy `mongosh` vào được VM.

### Bước 1.3 — nạp 41 triệu dòng

Coach gợi ý file `load_data_to_mongodb.py`: đọc theo batch 10.000 dòng, thêm `_loaded_at` và `_source_file`, `insert_many`, in tiến độ mỗi 100.000 dòng, rồi đếm lại. Collection coach gọi là `summary`. Index trên `collection` và `product_id`.

Xong khi `countDocuments()` khớp số dòng nguồn. Sau đó tắt VM để khỏi cháy credit GCP. Code thì viết ở máy local, đẩy GitHub, kéo về VM rồi mới chạy full.

## Pha 2 — chỉ làm phần đã GO

### Bước 2.1 — IP

Dùng `ip2location-python` và database LITE-DB5. Lấy IP không trùng từ `summary`, tra ra nước, thành phố, vĩ độ, kinh độ, ghi collection `ip_locations`, xuất CSV, tạo index trên `ip`.

Xong khi phủ ít nhất 80% và collection có dữ liệu.

### Bước 2.2 — sản phẩm, chia ba chặng

**2.2a — rút id và URL.** Không chỉ lấy `view_product_detail`. Coach liệt kê:

- `view_product_detail`
- `select_product_option`, `select_product_option_quality`
- `add_to_cart_action`
- `product_detail_recommendation_visible`, `product_detail_recommendation_noticed`
- `back_to_product_action` và `view_all_recommend`: lấy `product_id` cùng `current_url`
- `product_view_all_recommend_clicked`: event này không có `product_id`, lấy `viewing_product_id` cùng `referrer_url`

Gom thành một tập các cặp `(product_id, url)`, in ra số id không trùng. Đó là checkpoint 9.

**2.2b — thử 100 sản phẩm.** File gợi ý `crawl_products.py`. Mỗi trang là một HTTP GET có User-Agent, parse HTML bằng BeautifulSoup, lấy `name`, `price`, `category`, `description`, `image_url`. Upsert ngay vào collection `products`, kèm `crawled_at` và `source_url`. Nghỉ ngẫu nhiên từ 1,5 đến 4,2 giây, không nghỉ đều một nhịp. Một URL lỗi thì ghi log và đi tiếp.

Nếu bị chặn, coach gợi ý đổi User-Agent, chia batch, và giữ log lỗi. Crawl đủ 100 trang, có tên và category, là qua checkpoint 10.

**2.2c — crawl hết.** Mỗi `product_id` chỉ giữ một bản ghi. Số document trong `products` phải bằng số id ở bước rút. Xuất thêm CSV. Đó là checkpoint 11.

### Bước 2.3 — từ điển dữ liệu

Viết `data_dictionary.md` sau khi đã nạp và bổ sung xong. Gồm collection `summary`, `ip_locations` nếu có, `products` nếu có, và các lỗi chất lượng đã biết.

## Việc phải nộp

- Pha 0: notebook hoặc script khám phá, `data_quality_report.md`, `scope_confirmation.md`.
- Pha 1: GCP, VM MongoDB có đủ 41 triệu dòng, script nạp có kiểm tra số dòng.
- Pha 2: script IP và CSV nếu GO, script crawl và CSV nếu GO, từ điển dữ liệu.
- README, repo GitHub, `.gitignore` không chứa mật khẩu và file lớn.

Năm nhắc nhỏ ở cuối trang: không bỏ Pha 0, coi file scope là cam kết, crawl chậm khoảng 1–2 giây một trang, đếm lại số dòng mỗi bước, và luôn có bản CSV bên cạnh MongoDB.

## Source hiện tại sạch đến đâu

Bố cục giữ một module một việc. Nạp Mongo không còn rút URL sản phẩm. Việc đó chỉ nằm ở `src/enrich/extract_products.py`. Collection sản phẩm là `products`.

Chưa xong, và cố ý chưa làm trong lần dọn này:

- Chưa commit. Bốn commit cũ dừng ở nạp Mongo và tra IP.
- Chưa có GCP, GCS, VM.
- Chưa crawl hết danh sách. HTTP GET vẫn `403`, trang mẫu đọc bằng Chrome.
- Collection Mongo cũ `products_catalog` có thể còn vài document của lần thử trước. Code không ghi vào đó nữa.

## Từng bước của coach nằm ở file nào

| Bước coach | File làm việc đó | Lệnh |
|---|---|---|
| 0.1 Project `uv` | `pyproject.toml`, `uv.lock`, `src/config.py`, `src/cli.py` | `uv sync` |
| 0.1 Đọc file không nhét vào RAM | `src/stream/tar_bson.py`, `src/stream/bson_lite.py` | được gọi từ các lệnh explore |
| 0.2–0.3 Null và chất lượng | `src/explore/profile.py`, `src/explore/sketch.py`, `src/explore/render.py` | `uv run python -m src.cli explore null-profile` và `explore quality-report` |
| 0.2–0.3 Kết quả | `docs/null_profile.md`, `docs/data_quality_report.md` | file markdown do lệnh trên ghi |
| 0.4 Chốt GO | `docs/scope_confirmation.md` | viết tay sau khi đọc hai báo cáo |
| Test pha 0 | `tests/test_phase0.py` | `uv run python -m unittest discover -s tests` |
| 1.3 Nạp Mongo | `src/db.py`, `src/ingest/load_mongo.py` | `uv run python -m src.cli ingest load-mongo` |
| 1.1–1.2 GCP và VM | chưa có file | coach làm trên cloud. Repo này dùng Mongo local, lệnh trong `docs/runbook.md` |
| 2.1 Tra IP | `src/enrich/ip_lookup.py`, `docs/ip_coverage.md` | `uv run python -m src.cli enrich ip` |
| 2.2a Rút id và URL | `src/enrich/urls.py`, `src/enrich/extract_products.py` | `uv run python -m src.cli enrich extract-products` |
| 2.2b–2.2c Crawl | `src/enrich/crawl.py` | `uv run python -m src.cli enrich crawl --limit 100` rồi bỏ `--limit` khi đã ổn |
| Mẫu đã chạy | `docs/product_sample.md` | 5 trang, collection `products` |
| Test URL và parser | `tests/test_enrich.py` | cùng lệnh unittest |
| 2.3 Từ điển | `docs/data_dictionary.md` | bản nháp pha 0, chưa cập nhật hết field enrich |
| Cách chạy lại | `docs/runbook.md`, `README.md` | |

`src/enrich/urls.py` không gọi mạng. Nó chỉ chuẩn hóa id và đổi mọi host Glamira về `https://www.glamira.co.uk`, bỏ query string. `extract_products.py` đọc Mongo và gọi hàm đó.

## Cấu trúc thư mục

```text
src/config.py                 đọc .env
src/cli.py                    một cửa cho mọi lệnh
src/db.py                     kết nối Mongo
src/stream/                   đọc tar.gz và BSON, không biết Mongo
src/explore/                  đo pha 0, không ghi Mongo
src/ingest/load_mongo.py      nạp glamira_raw
src/enrich/urls.py            luật URL
src/enrich/extract_products.py  tập product id
src/enrich/ip_lookup.py       ip_geo
src/enrich/crawl.py           mở trang, ghi products
tests/                        BSON giả và HTML giả, không có email hay IP thật
docs/                         báo cáo đã đo
data/                         tar, BIN, Mongo, CSV. Git bỏ qua
```

Hướng phụ thuộc một chiều: `cli` gọi `explore`, `ingest`, `enrich`. `stream` không import `pymongo`. `explore` không mở Chrome. Nhờ vậy test pha 0 không cần Mongo và không cần mạng.

## Vì sao chọn từng thứ

File coach giao là mongodump gzip, bên trong BSON khoảng 31 GB, không phải CSV. Pandas sẽ cố kéo cả file vào RAM, nên pha 0 chỉ dùng thư viện chuẩn của Python: đọc gzip, đọc tar, đọc BSON theo 4 byte độ dài. HyperLogLog trong `sketch.py` đếm số IP và số sản phẩm xấp xỉ, vì giữ 41 triệu id trong set sẽ hết RAM.

MongoDB là đúng yêu cầu vận hành của coach: mỗi event một document, schema khác nhau. Collection raw đặt tên `glamira_raw` để khỏi nhầm với field `collection` bên trong document. Field đó là loại event.

`uv` thay pip vì coach yêu cầu, khóa phiên bản trong `uv.lock`. Thư viện chỉ thêm khi tới pha đó:

| Thư viện | Dùng khi | Vì sao |
|---|---|---|
| không có thư viện ngoài | pha 0 | đọc BSON tự viết, test nhanh |
| `pymongo` | nạp và enrich | nói chuyện với Mongo |
| `ip2location` | tra BIN | đúng file `.BIN` coach giao. Gói pip tên `ip2location`, import là `IP2Location` |
| `beautifulsoup4` | đọc HTML | lấy JSON-LD, h1, breadcrumb |
| `playwright` | mở trang | HTTP GET bị 403. Chrome thật thì trang trả HTML |

IP không ghi vào từng event. Một IP xuất hiện nhiều lần, nên `ip_geo` có một document cho mỗi IP, `_id` là chuỗi IP. Sau này join `glamira_raw.ip` = `ip_geo._id`.

`_id` của event giữ nguyên ObjectId trong file. Chạy nạp lại thì Mongo bỏ bản trùng, không nhân đôi 41 triệu dòng.

## Làm lại từ đầu, mỗi commit một bước

Làm trên nhánh mới hoặc repo trống. Chạy test trước khi commit. Không commit `.env`, `data/`, tar, BIN.

1. `chore: start the uv project` — `pyproject.toml`, `.gitignore`, `.env.example`, `src/config.py`, `src/cli.py` trống.
2. `feat: stream the mongodump` — `src/stream/`, `tests/test_phase0.py`. Commit khi test đọc được BSON giả.
3. `docs: record the null profile` — `profile.py`, `render.py`, `docs/null_profile.md`.
4. `docs: record the data quality report` — `docs/data_quality_report.md`.
5. `docs: confirm scope` — `docs/scope_confirmation.md` với GO hoặc NO-GO và lý do. Dừng ở đây nếu chưa GO.
6. `feat: load raw events into Mongo` — `src/db.py`, `src/ingest/load_mongo.py`. Commit khi số document khớp 41.432.473. GCP để commit riêng lúc bạn dựng cloud.
7. `feat: resolve IPs and record coverage` — `src/enrich/ip_lookup.py`, `docs/ip_coverage.md`.
8. `feat: extract one url per product` — `urls.py`, `extract_products.py`, test. In ra số id không trùng.
9. `feat: crawl a 100 product sample` — `crawl.py`. Commit khi ít nhất 95 trong 100 trang có tên và category.
10. `feat: finish the product crawl and dictionary` — crawl hết, CSV, `docs/data_dictionary.md`.

Ba commit đầu trong repo này đã đi gần các bước 2, 3, 4 và 6–7. Bước 8–9 đang nằm trong thư mục làm việc, chưa có commit.
