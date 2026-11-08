# Từ thư mục trống đến source hiện tại

File này viết cho người mới chuyển sang Data Engineer, đang làm dự án đầu tiên. Đọc từ trên xuống. Mỗi phần trả lời một câu: coach yêu cầu gì, input là gì, vì sao có từng thư mục, rồi mới tới lệnh chạy.

Bản dịch đầy đủ trang Notion nằm ở `docs/huong_dan_coach.md`. File này không thay trang gốc.

---

## 1. Có làm từng bước như trang Notion không?

Có đọc trang [Glamira Project 5](https://davidnotio101.notion.site/Glamira-Project-5-39e6f7803e7b8012ba5bf0db897d9b72#3c16f7803e7b800887f4e9f514a4c1e8), đúng mục **0.4 Scope Confirmation** trong link đó. Quy tắc coach: hiểu data trước, code sau. Mỗi checkpoint một ý.

Repo này **làm đúng thứ tự ý** của Pha 0 và Pha 2, và **làm Pha 1 trên máy local** thay vì GCP, vì bạn đã nói cloud để sau.

| # | Coach viết | Repo này | Giống / khác |
|---|---|---|---|
| 1 | Đo % trống theo loại event | `src/explore/` → `docs/null_profile.md` | Giống ý. File nguồn là BSON trong tar.gz, không phải JSONL như ví dụ Notion, nên phải viết `src/stream/` trước. |
| 2 | `data_quality_report.md` | `docs/data_quality_report.md` | Giống. Đủ năm kiểm tra: id, ngày, giá, IP, tiền tệ. |
| 3 | `scope_confirmation.md` GO IP và product | `docs/scope_confirmation.md` | Giống. Tick GO sau khi có số, không tick trước. |
| 4 | GCP + GCS | chưa làm | Cố ý. Cloud để sau. |
| 5 | `uv sync` | `pyproject.toml`, `uv.lock` | Giống. Coach để bước này ở Pha 1; repo làm sớm hơn vì không có `uv` thì không chạy script Pha 0. |
| 6 | MongoDB trên VM GCP | Mongo local `data/mongo` | Cùng ý “có Mongo, máy cá nhân nối được”. Khác chỗ: không thuê VM. Dịch vụ user `glamira-mongod`. |
| 7 | Nạp 41 triệu, đếm khớp | `src/ingest/load_mongo.py` | Giống ý. Collection đặt `glamira_raw` chứ không phải `summary`, vì field `collection` trong document đã là tên event. |
| 8 | Tra IP, đo % phủ | `src/enrich/ip_lookup.py`, `docs/ip_coverage.md` | Giống ý. Coach gợi ý LITE-DB5 (có lat/long). File giao là DB3 (country, region, city), nên không có tọa độ. Collection `ip_geo`, không phải `ip_locations`. |
| 9 | Tập `product_id` + URL không trùng | `extract-products` → `data/exports/product_urls.csv` | Giống ý. Bốn event recommendation **không** ghép `viewing_product_id` với URL đang xem, vì mẫu thật không khớp mô tả Notion. |
| 10 | Crawl thử 100, parse HTML | `enrich crawl --limit 100` | Giống ý. HTTP GET bị 403 nên mở Chrome thật, không phải `requests` một dòng. |
| 11 | Crawl hết + dictionary | crawl full chưa chạy | Dictionary bản Pha 0 đã có. Field crawl mới chưa viết hết vào dictionary. |

Năm nhắc cuối trang Notion vẫn giữ: không bỏ Pha 0, file scope là cam kết, crawl chậm, đếm lại số dòng, CSV cạnh Mongo (`product_urls.csv`, TSV IP).

Chưa làm đúng chữ Notion: GCP, VM, commit+push từng checkpoint, crawl đủ 19.093, handoff Project 06.

---

## 2. Input của dự án là gì? Cấu trúc ra sao? Đọc thế nào?

Hãy tưởng tượng bạn nhận một ổ USB, không phải một file Excel. Bên trong có **hai file**. Đó là toàn bộ input.

### Hai file coach giao

| File | Để ở | Việc của nó |
|---|---|---|
| `glamira_ubl_oct2019_nov2019.tar.gz` (~5,5 GB nén) | `data/raw/` | Log hành vi: người xem trang, thêm giỏ, thanh toán. |
| `IP-COUNTRY-REGION-CITY.BIN` (~144 MB) | `data/reference/` | Sổ tra IP → nước, vùng, thành phố. Không phải log. |

Cả hai **không** đưa lên git. Chúng quá lớn và không phải code.

### File log không phải CSV

Tên file `.tar.gz` nghĩa là: nén gzip, bên trong là archive tar (như zip, nhưng là tar).

Mở lớp nén ra, bên trong **không** có `data.csv`. Có hai thành viên:

```text
dump/countly/summary.metadata.json     ← mô tả collection nguồn
dump/countly/summary.bson              ← ~31 GB, hàng chục triệu document dính nhau
```

Đó là bản sao MongoDB (mongodump) của hệ thống Countly. Database nguồn tên `countly`. Collection nguồn tên `summary`.

`.bson` không phải JSON. JSON là chữ. BSON là JSON đóng thành byte để Mongo đọc nhanh. Mỗi document bắt đầu bằng **4 byte** nói “tôi dài bao nhiêu byte”, rồi mới tới các field.

Một document (một event) trông như JSON khi đã decode, ví dụ:

```json
{
  "_id": { "$oid": "..." },
  "collection": "view_product_detail",
  "time_stamp": 1585699201,
  "ip": "85.115.53.202",
  "product_id": "100045",
  "current_url": "https://www.glamira.fi/glamira-riipus-odila.html?stone2=...",
  "store_id": "fi"
}
```

Hai điểm dễ nhầm:

1. Field tên `collection` **không** phải tên bảng Mongo. Đó là **loại hành vi**: xem sản phẩm, thanh toán xong, …
2. Event `checkout_success` **không** có `product_id` ở ngoài. Id và giá nằm trong mảng `cart_products`. Ví dụ Notion vẽ `product_id` trên checkout cho dễ hiểu; file thật khác.

Không giải nén 31 GB ra đĩa. Code mở gzip, tìm đúng member `summary.bson`, rồi đọc lần lượt từng document theo 4 byte độ dài. Đó là việc của `src/stream/`.

### File BIN

File `.BIN` là sổ của IP2Location, không mở bằng Excel. Thư viện `IP2Location` đọc nó. Loại DB3: bốn cột country, region, city. Không có vĩ độ/kinh độ. Ngày sổ: 2016-11-29, cũ hơn log khoảng 3,5 năm, nên **nước** dùng được, **thành phố** chỉ gần đúng.

### Đường đi của dữ liệu sau khi hiểu input

```text
tar.gz + BIN
    → đo (Pha 0), chưa Mongo
    → nạp glamira.glamira_raw          (một event một document)
    → tra BIN → glamira.ip_geo         (một IP một document)
    → rút URL → product_urls.csv
    → mở trang → glamira.products      (một sản phẩm một document)
```

Dashboard sau này join:

- nước của event: `glamira_raw.ip` = `ip_geo._id`
- tên sản phẩm: `product_id` = `products._id`

---

## 3. Vì sao phải tạo từng thư mục, vì sao đặt tên như vậy

Quy tắc đặt tên: **tên nói việc đang làm**, không nói công cụ. Người đọc folder là biết tầng nào của pipeline.

Hãy tưởng tượng nhà bếp. Không để dao, thịt sống, và món chín chung một ngăn. `stream` là rửa và thái (đọc file). `explore` là nếm (đo). `ingest` là cho vào tủ lạnh (Mongo). `enrich` là nêm thêm (IP, tên sản phẩm). `docs` là sổ tay. `tests` là nấu một muỗng để thử công thức, không nấu cả nồi 41 triệu.

| Thư mục / file | Việc | Vì sao tên đó, không tên khác |
|---|---|---|
| `data/` | Mọi thứ nặng, không phải code | Tên ngắn, git bỏ cả nhánh. Không gọi `files/` vì quá chung. |
| `data/raw/` | File coach giao, chưa biến đổi | `raw` = nguyên bản. Không sửa file trong này. |
| `data/reference/` | Sổ tra (BIN), không phải log | `reference` = tra cứu. Không nhét BIN vào `raw` vì đó không phải event. |
| `data/mongo/` | File WiredTiger của `mongod` | Chỉ server Mongo đọc. Không mở bằng VS Code. |
| `data/staging/` | TSV đếm IP, file tạm giữa hai lệnh | `staging` = chưa phải sản phẩm cuối. |
| `data/exports/` | CSV đưa ra ngoài (URL sản phẩm) | `exports` = mang đi được, tạo lại bằng lệnh. |
| `src/` | Code chạy | Quy ước Python: source. |
| `src/stream/` | Đọc tar/BSON theo dòng chảy | `stream` = không nhét cả file vào RAM. Không gọi `parser/` vì parser thường hiểu là HTML/JSON. |
| `src/explore/` | Đo, không ghi Mongo | `explore` = Pha 0. Không gọi `analysis/` để khỏi nhầm pandas/notebook. |
| `src/ingest/` | Nạp event vào Mongo | `ingest` = đưa dữ liệu vào hệ thống. Không gọi `load/` vì dễ trùng với “load vào RAM”. |
| `src/enrich/` | Thêm field log không có | `enrich` = bổ sung. Coach gọi đúng hai việc này là enrichment. |
| `src/cli.py` | Một cửa cho mọi lệnh | `cli` = command line. Không viết 5 file `run_*.py`. |
| `src/config.py` | Đọc `.env` | Một chỗ cho đường dẫn và tên collection. |
| `src/db.py` | Tạo kết nối Mongo | Tách khỏi ingest để crawl cũng dùng được. |
| `tests/` | BSON/HTML giả | Không đụng file 5 GB. |
| `docs/` | Quyết định và số đã đo | Báo cáo markdown, không phải code. |
| `.venv/` | Thư viện `uv` cài | Không commit. Tạo lại bằng `uv sync`. |

### Vì sao từng file Python bên trong

| File | Câu nó trả lời | Vì sao tách riêng |
|---|---|---|
| `stream/tar_bson.py` | Làm sao lấy `summary.bson` ra khỏi tar.gz? | Luật tar (kể cả size > 8 GB) khác luật BSON. |
| `stream/bson_lite.py` | Làm sao đi từng document mà không copy email? | Pha 0 chỉ cần đếm. Decode đủ field là việc của `pymongo` lúc nạp. |
| `explore/sketch.py` | Có bao nhiêu giá trị khác nhau khi không giữ 41 triệu id? | HyperLogLog. Tách để test ước lượng, không phụ thuộc tar. |
| `explore/profile.py` | Null %, loại event, IP, ngày? | Máy đếm. |
| `explore/render.py` | In ra markdown thế nào? | Đếm và trình bày không chung một hàm. |
| `ingest/load_mongo.py` | Ghi `glamira_raw` thế nào để chạy lại không nhân đôi? | Không rút URL ở đây. Một lệnh một việc. |
| `enrich/ip_lookup.py` | IP → nước? | Không cần Chrome, không cần HTML. |
| `enrich/urls.py` | Id và URL chuẩn hóa ra sao? | Luật thuần, test không cần Mongo. |
| `enrich/extract_products.py` | Một URL cho mỗi `product_id` lấy từ đâu? | Quét Mongo, gọi `urls.py`. |
| `enrich/crawl.py` | Mở trang, lấy tên, ghi `products`? | Có mạng, có Chrome. Tách khỏi extract. |

Tên collection Mongo:

| Tên | Vì sao không lấy tên coach |
|---|---|
| `glamira_raw` | Coach gọi `summary`. Field `collection` trong document đã nghĩa “loại event”. Đặt collection vận hành trùng `summary` hoặc trùng tên event thì Compass rất dễ nhầm. |
| `ip_geo` | Coach gọi `ip_locations`. Tên này nói rõ: địa lý của IP, join bằng `_id` = chuỗi IP. |
| `products` | Đúng tên coach ở bước crawl. |

---

## 4. Bảng thuật ngữ

Đọc bảng này khi gặp từ lạ trong file này hoặc trong code.

| Thuật ngữ | Nghĩa thường | Nghĩa trong dự án này |
|---|---|---|
| Data Engineer | Người xây đường ống dữ liệu | Ở đây: nhận file, đo, nạp Mongo, bổ sung IP và tên sản phẩm. Không vẽ dashboard. |
| Data Source | Nguồn dữ liệu | Phần việc của Project 05. GCS/BigQuery/dbt là project sau. |
| Pipeline | Chuỗi bước xử lý | explore → ingest → enrich ip → extract URL → crawl. |
| Checkpoint | Cột mốc coach chấm | 11 mốc. Xong một ý rồi mới sang ý sau. |
| GO / NO-GO | Được làm tiếp / dừng | Sau khi đo: có GO tra IP và GO crawl. |
| Schema-on-read | Đọc rồi mới hiểu form | Không ép mọi event cùng cột. `view_product_detail` có `product_id`; `checkout_success` thì id nằm trong `cart_products`. |
| Nullish | “Không có giá trị dùng được” | Thiếu field, hoặc null, hoặc `""`. Số `0` và `false` **không** tính trống. |
| Coverage | Tỷ lệ phủ | Ví dụ 99,16% đơn `checkout_success` tra được nước. |
| Event | Một hành vi đã ghi | Một document trong log. Loại event nằm ở field `collection`. |
| Field `collection` | (dễ nhầm với bảng Mongo) | **Loại event**, ví dụ `view_product_detail`. |
| Collection (Mongo) | Bảng lỏng | `glamira_raw`, `ip_geo`, `products`. |
| Document | Một dòng dạng JSON | Một event, hoặc một IP, hoặc một sản phẩm. |
| `_id` | Khóa của document | Event: ObjectId gốc. IP: chuỗi IP. Sản phẩm: `product_id` dạng chữ. |
| ObjectId | Id 12 byte của Mongo | Lấy nguyên từ file dump để nạp lại không trùng. |
| BSON | JSON dạng nhị phân | File `summary.bson`. Đọc theo 4 byte độ dài. |
| mongodump | Bản sao một database Mongo | Đúng format file `.tar.gz` coach giao. |
| tar.gz | Archive + nén | Lớp ngoài. Bên trong mới là BSON. |
| gzip | Thuật toán nén | Magic byte `1f 8b` ở đầu file. |
| ustar | Kiểu tar cũ | File thật là ustar. Python mặc định hay ghi PAX, test phải ghi ustar. |
| GNU base-256 | Cách ghi số lớn trong tar | Member BSON > 8 GB. Byte đầu `0x80`. Sai chỗ này thì đọc lệch hết document. |
| Stream | Đọc lần lượt | Không `read()` cả 31 GB. |
| Batch / chunk | Một nắm rồi xử lý | Nạp Mongo 10.000 document một lần. |
| Idempotent | Chạy lại không hỏng | Nạp lại: bản trùng bị bỏ. Crawl lại: id đã có tên thì bỏ qua. |
| Upsert | Có thì sửa, chưa có thì thêm | Crawl ghi `products` theo `_id` = `product_id`. |
| Index | Mục lục tìm nhanh | Tạo **sau** khi nạp xong. |
| Join | Ghép hai bảng theo khóa | `glamira_raw.ip` = `ip_geo._id`. Mongo không tự join như SQL. |
| Dimension table | Bảng tra, không phải bảng sự kiện | `ip_geo` và `products` là bảng tra. `glamira_raw` là sự kiện. |
| BIN | File sổ IP | `IP-COUNTRY-REGION-CITY.BIN`, DB3. |
| IPv4 public | Địa chỉ internet thông thường | Mới đưa vào BIN. Private/IPv6 không tra. |
| HyperLogLog (HLL) | Ước lượng số giá trị khác nhau | Dùng lúc Pha 0 vì không giữ 41 triệu id. Sai số khoảng ±1%. |
| Canonical URL | Một URL đại diện | Một `product_id` một URL, ưu tiên trang `.co.uk` **có thật trong log**. |
| Seed | Danh sách đầu vào crawl | `data/exports/product_urls.csv`. |
| Rate limit | Giới hạn tốc độ gọi | Nghỉ 1,5–4,2 giây giữa hai trang, không DDoS site. |
| JSON-LD | JSON mô tả sản phẩm trong HTML | Glamira để Product trong `ItemPage.mainEntity`. |
| User-Agent | Chuỗi trình duyệt tự xưng | HTTP GET của script bị 403. Chrome thật thì vào được. |
| 403 / 404 | Cấm / không có trang | 403: bot bị chặn. 404: path không tồn tại. |
| Playwright | Thư viện cầm trình duyệt | Mở `/usr/bin/google-chrome`. |
| `uv` | Công cụ cài Python | Coach bắt dùng, không dùng Poetry. `uv sync` tạo `.venv`. |
| `.env` | File cấu hình máy bạn | Đường dẫn tar, URI Mongo. Không commit. |
| `mongod` | Chương trình server Mongo | File trên đĩa chỉ được đọc khi `mongod` đang chạy. Compass không tự đọc `data/mongo`. |
| Compass | App xem Mongo | Nối `mongodb://127.0.0.1:27017`. |
| WiredTiger | Engine lưu file của Mongo | Các file `*.wt` trong `data/mongo`. |
| PII | Thông tin nhận dạng người | Email, IP thô trong extract. Không commit vào docs. |
| FX | Quy đổi tiền | Project này không quy đổi. Giá giữ nguyên theo `currency`. |
| Schema | Bộ field | Ở đây khác nhau theo loại event. |
| CLI | Giao diện dòng lệnh | `python -m src.cli ...` |
| Enrichment | Bổ sung field thiếu | Hai việc: IP → nước, `product_id` → tên/category. |

---

## 5. Cách đọc code như Data Engineer

Đừng mở `src/cli.py` trước. CLI chỉ là nút. Đọc theo dữ liệu đi qua:

1. `docs/scope_confirmation.md` — GO gì, cấm gì.
2. `docs/architecture.md` — một trang đường ống.
3. `src/stream/` — đọc file.
4. `src/explore/` — đo.
5. `src/config.py`, `src/db.py`.
6. `src/ingest/load_mongo.py`.
7. `src/enrich/ip_lookup.py`.
8. `src/enrich/urls.py`, `extract_products.py`.
9. `src/enrich/crawl.py`.
10. `src/cli.py` — lệnh nào gọi hàm nào.
11. `tests/` — ví dụ nhỏ.

Mỗi file Python trả lời **một** câu. Nếu một file vừa đọc tar, vừa tra IP, vừa crawl, thì thiết kế đã sai.

---

## 6. Thứ tự xuất hiện từng folder (khi làm)

### Bước 0 — Chỉ có `project05`

Chưa có `src/`. Hai file coach đặt vào `data/raw/` và `data/reference/`.

Câu hỏi phải đo, không đoán từ tên file:

- Có phải JSONL không? (không, là mongodump BSON)
- Ngày trên tên file có đúng không? (không: log là 2020-04-01 → 2020-06-04 UTC)
- `product_id` đơn hàng nằm ở đâu? (`cart_products`)
- IP có đủ tra nước không? (có, 99,98% IPv4 public)

Quyết định: chưa nạp Mongo, chưa crawl. Trước hết viết reader và máy đếm.

### Bước 1 — Khung repo

Thêm `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `docs/`, `src/__init__.py`, `src/config.py`, `src/cli.py` (chỉ nhóm `explore`).

Vì sao `src/` ngay, không viết một notebook 2000 dòng: notebook khó test, khó chạy lại 41 triệu dòng, khó tách “đo” khỏi “nạp”.

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/loclt/workspace/unigap_course/projects/project05
uv sync
```

### Bước 2 — `src/stream/`

`tar_bson.py` + `bson_lite.py` + `tests/test_phase0.py`.

Kiến thức: gzip, tar 512 byte/header, GNU base-256, BSON int32 length prefix. Không pandas: pandas sẽ kéo cả member vào RAM.

### Bước 3 — `src/explore/` rồi `docs/` đo được

`sketch.py` (HyperLogLog), `profile.py`, `render.py`. Lệnh ghi `null_profile.md`, `data_quality_report.md`, `data_dictionary.md`. Người đọc số rồi tick `scope_confirmation.md`.

```bash
uv run python -m src.cli explore quality-report --sample-size 0
```

`--sample-size 0` = đọc hết. Khoảng 43 phút. 41.432.473 document, leftover 0.

### Bước 4 — Mongo rồi `src/ingest/`

Binary `~/.local/mongodb/bin/mongod` (không phải file hệ thống). Dữ liệu `data/mongo`. Dịch vụ user `glamira-mongod`. Thêm `src/db.py`, `load_mongo.py`, thư viện `pymongo`.

`_id` = ObjectId gốc. `insert_many` unordered. Trùng thì bỏ. Index sau khi nạp. Cùng pass ghi TSV IP. Không rút URL sản phẩm lúc nạp.

```bash
systemctl --user status glamira-mongod
uv run python -m src.cli ingest load-mongo
```

### Bước 5 — `src/enrich/ip_lookup.py`

Một IP một document. Không nhét country vào 41 triệu event. Coverage `checkout_success` 99,16%.

```bash
uv run python -m src.cli enrich ip
```

### Bước 6 — `urls.py` + `extract_products.py`

Một URL thật cho mỗi id. Ưu tiên `.co.uk` **đã có trong log**. Không dán path Phần Lan lên host Anh.

Event recommendation không ghép: `viewing_product_id` là id gợi ý, không phải id của trang đang mở.

```bash
uv run python -m src.cli enrich extract-products
```

19.093 sản phẩm. 17.849 URL là `www.glamira.co.uk`.

### Bước 7 — `crawl.py`

Chrome tuần tự, nghỉ 1,5–4,2 giây. 404 thì thử `https://www.glamira.com/catalog/product/view/id/<product_id>`. Ghi `glamira.products`. `--limit 100` = 100 dòng đầu CSV, không phải cả file.

```bash
uv run python -m src.cli enrich crawl --seed data/exports/product_urls.csv --limit 100
```

---

## 7. Cây source khi đã xong (bỏ data và .venv)

```text
project05/
  pyproject.toml
  uv.lock
  .env.example
  README.md
  src/
    cli.py  config.py  db.py
    stream/     tar_bson.py  bson_lite.py
    explore/    sketch.py  profile.py  render.py
    ingest/     load_mongo.py
    enrich/     ip_lookup.py  urls.py  extract_products.py  crawl.py
  tests/
    test_phase0.py  test_enrich.py
  docs/
    scope_confirmation.md  architecture.md
    null_profile.md  data_quality_report.md  data_dictionary.md
    ip_coverage.md  runbook.md  huong_dan_coach.md
    mongodb.md  qua_trinh.md
```

---

## 8. Lệnh đúng thứ tự trên máy này

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/loclt/workspace/unigap_course/projects/project05
uv sync
systemctl --user status glamira-mongod

uv run python -m unittest discover -s tests
uv run python -m src.cli explore quality-report --sample-size 0
uv run python -m src.cli ingest load-mongo
uv run python -m src.cli enrich ip
uv run python -m src.cli enrich extract-products
uv run python -m src.cli enrich crawl --seed data/exports/product_urls.csv --limit 100
```

Nạp lại không nhân đôi. Extract ghi đè CSV. Crawl bỏ qua sản phẩm đã có tên.

Xem dữ liệu: `docs/mongodb.md`. Compass không đọc file trên đĩa một mình. `mongod` phải đang chạy. URI `mongodb://127.0.0.1:27017`, database `glamira`.

---

## 9. Chưa làm

- Crawl đủ 19.093 URL trên seed đã sửa, có catalog khi 404.
- `docs/handoff_to_project06.md`.
- GCP / GCS / VM.
- Dictionary chưa ghi hết field crawl mới (`currency`, `material`, …).
- Commit + push từng checkpoint như Notion. Không commit khi chưa được yêu cầu.
