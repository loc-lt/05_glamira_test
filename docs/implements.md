# Implements — tạo file gì, code gì, commit gì, theo từng checkpoint

File này viết cho người mới, giống `docs/qua_trinh.md`. Khác ở chỗ:

- `qua_trinh.md` trả lời **vì sao**: vì sao có thư mục này, vì sao đặt tên như vậy.
- `implements.md` trả lời **làm gì, theo thứ tự nào**: mỗi bước tạo file nào, file đó đang chứa code gì, chạy lệnh gì, thấy số nào là qua, rồi `git add` file nào và commit message ra sao.

Nguồn yêu cầu: trang Notion [Glamira Project 5](https://davidnotio101.notion.site/Glamira-Project-5-39e6f7803e7b8012ba5bf0db897d9b72#3c16f7803e7b800887f4e9f514a4c1e8), bản dịch ở `docs/huong_dan_coach.md`. Mỗi bước dưới đây ghi rõ **bước coach** (0.1, 1.3, 2.2a, …) và **checkpoint** (1–11).

Đọc từ trên xuống. Mục 1 là kết luận: source hiện tại đã đủ chưa. Mục 3 là thi công từng bước.

---

## 1. Source hiện tại đã đáp ứng coach chưa?

Kết luận ngắn: **phần code Python đã đủ cho cả 11 checkpoint, sau ba bổ sung nhỏ vừa thêm.** Phần còn thiếu không nằm ở code. Đó là **chạy trên GCP** (checkpoint 4, 6, 7 trên cloud) và **chạy crawl đến hết** (checkpoint 11).

Ký hiệu: ✅ tái dùng nguyên · 🔧 tái dùng, vừa bổ sung · 🆕 file mới · ⏳ code có, chưa chạy xong · ↔ khác coach có lý do.

| Bước coach | Coach yêu cầu | File trong repo | Kết luận |
|---|---|---|---|
| 0.1 | `uv`, `uv sync` | `pyproject.toml`, `uv.lock` | ✅ |
| 0.1 | Script mẫu 10k–100k dòng, in event, ngày, IP | `src/explore/profile.py` qua `explore null-profile --sample-size 100000` | ✅ ↔ file là BSON nên đọc bằng `src/stream/`, không đọc JSONL |
| 0.2 | % trống theo event | `src/explore/profile.py`, `render.py` → `docs/null_profile.md` | ✅ checkpoint 1 |
| 0.3 | 5 kiểm tra chất lượng | `render_quality_report` → `docs/data_quality_report.md` | ✅ checkpoint 2 |
| 0.4 | `scope_confirmation.md` | `docs/scope_confirmation.md` | ✅ checkpoint 3 |
| 1.1 | Project GCP, API, bucket, service account, `gsutil cp` | `infra/gcp/01_project.sh`, `02_bucket.sh`, `03_upload_inputs.sh` | 🆕 ⏳ bạn chạy, checkpoint 4 |
| 1.2 | VM 16–32 GB, 100 GB, Mongo, user, firewall 1 IP | `infra/gcp/04_vm.sh`, `vm/install_mongo.sh` | 🆕 ⏳ checkpoint 6. ↔ MongoDB 8.0 thay 6.0 (6.0 đã EOL, không có gói Ubuntu 24.04) |
| 1.3 | `load_data_to_mongodb.py`: batch 10k, `insert_many`, tiến độ mỗi 100k, `_loaded_at`, `_source_file`, đếm lại, index | `src/ingest/load_mongo.py` | 🔧 vừa thêm `_loaded_at`, `_source_file`, in mỗi 100k, dòng `count check … MATCH`. ↔ tên file và collection `glamira_raw` thay `summary` |
| 2.1 | Tra IP, ≥ 80% phủ, collection, **CSV**, index `ip` | `src/enrich/ip_lookup.py` + `src/enrich/export_csv.py` | ✅ tra IP. 🔧 CSV là lệnh mới `enrich export-csv ip_geo`. ↔ `ip_geo` thay `ip_locations`, `_id` = IP nên đã có index. BIN là DB3, không có lat/long |
| 2.2a | Rút `(product_id, url)` từ danh sách event coach | `src/enrich/urls.py`, `extract_products.py` | ✅ checkpoint 9. ↔ 4 event recommendation không ghép URL (lý do ở bước 11) |
| 2.2b | `crawl_products.py`: User-Agent, BeautifulSoup, name/price/category/description/image_url, upsert, `crawled_at`, `source_url`, nghỉ 1,5–4,2 s, lỗi thì log và đi tiếp | `src/enrich/crawl.py` | ✅ checkpoint 10. ↔ Chrome qua Playwright vì HTTP GET bị 403 |
| 2.2c | Crawl hết, số `products` = số id, CSV | `crawl.py` + `export_csv.py` | 🔧 vừa sửa `--limit 0` = cả seed, thêm `enrich product-status` và `enrich export-csv products`. ⏳ mới 2.104 / 19.093 có tên |
| 2.3 | `data_dictionary.md` đủ 3 collection | `docs/data_dictionary.md` | ⏳ bản Pha 0 + bảng collection. Viết nốt ở checkpoint 11 |
| Nộp | README, `.gitignore` sạch | `README.md`, `.gitignore` | ✅ chặn `data/`, `.env`, `gcp.env`, `*.BIN`, `*.tar.gz`, `*.bson` |
| Sau cùng | Handoff Project 06 | `docs/handoff_to_project06.md` | ⏳ viết khi xong checkpoint 11 |

Ba bổ sung vừa làm (commit `feat: stamp loaded events, export CSVs, check crawl completeness`):

| File | Thêm gì | Vì coach viết |
|---|---|---|
| `src/ingest/load_mongo.py` | Hàm `stamp()` thêm `_loaded_at`, `_source_file`. Property `count_matches`. Mặc định in tiến độ mỗi 100.000 | Bước 1.3 |
| `src/cli.py` | `ingest load-mongo` in `count check: source=… mongo=… MATCH`, sai thì exit 3. Lệnh mới `enrich export-csv`, `enrich product-status` | Bước 1.3, 2.1, 2.2c |
| 🆕 `src/enrich/export_csv.py` | `export_collection()` ghi CSV. `product_status()` so `products` với seed | “Luôn có CSV cạnh Mongo”, “số `products` = số id” |
| 🆕 `tests/test_export.py` | 6 test: stamp, count check, CSV, seed | Test không cần Mongo |
| `src/db.py` | Docstring nói rõ URI có user khi dùng VM | Bước 1.2 |

41.432.473 event đang nằm trong Mongo **local** được nạp trước khi có bổ sung này, nên chưa có `_loaded_at`. Lần nạp trên **VM** (bước 9) sẽ có hai field đó. Không cần nạp lại local.

---

## 2. Quy ước trước khi bắt đầu

### Tên của coach ↔ tên trong repo

| Coach | Repo | Vì sao |
|---|---|---|
| `load_data_to_mongodb.py` | `src/ingest/load_mongo.py` | Một tầng một thư mục (`qua_trinh.md` mục 3) |
| `crawl_products.py` | `src/enrich/crawl.py` | Cùng lý do |
| collection `summary` | `glamira_raw` | Field `collection` trong event đã là tên event |
| collection `ip_locations` | `ip_geo` | `_id` = chuỗi IP |
| collection `products` | `products` | Giữ nguyên |
| Chạy `python file.py` | `uv run python -m src.cli <nhóm> <lệnh>` | Một cửa cho mọi lệnh |

### Quy tắc commit

1. Mỗi checkpoint ít nhất một commit. Message: `type: việc đã xong (checkpoint N)`. `type` là `chore` (khung), `feat` (code mới), `fix` (sửa lỗi), `docs` (báo cáo, số đo).
2. Test trước khi commit: `uv run python -m unittest discover -s tests`.
3. `git add` **từng file**, không `git add .`.
4. `git status` trước khi commit. Không bao giờ có `data/`, `.env`, `infra/gcp/gcp.env`.
5. `git push origin main` ngay sau commit.

### Lịch sử commit hiện có so với thứ tự coach

Repo đã push 9 commit. Vài commit gộp nhiều checkpoint, vì lúc đó chưa có yêu cầu commit từng mốc:

| Commit đã có | Checkpoint chứa trong đó |
|---|---|
| `d837bdf feat: stream the Glamira mongodump for Phase 0 profiling` | bước 1–3 dưới đây (khung, stream, explore) |
| `5db7803 docs: record the full-scan null profile and quality report` | checkpoint 1, 2 |
| `901bc21 docs: propose GO for IP lookup and product crawl` | checkpoint 3 |
| `1ebe312 feat: load events into local Mongo and resolve IPs` | checkpoint 7 (local), 8 |
| `e83b8f0 feat: upload prj` | checkpoint 9, 10 |
| `bb645f2 chore: update documents` | checkpoint 10 (fallback catalog), docs |
| `030414b fix: let crawl --limit 0 read the whole seed` | chuẩn bị checkpoint 11 |
| `de05cae feat: add GCP scripts for bucket, Mongo VM and firewall` | checkpoint 4, 6 (script) |
| `f534c1a docs: write the step-by-step GCP implementation guide` | file này, bản đầu |

**Không viết lại lịch sử `main`.** Đã push rồi, `rebase`/`force push` dễ mất việc. Để coach thấy rõ từng mốc, gắn **tag** vào đúng commit, và từ checkpoint 4 trở đi commit đúng một mốc một lần:

```bash
git tag -a cp-01-02 5db7803 -m "checkpoint 1-2: null profile + quality report"
git tag -a cp-03    901bc21 -m "checkpoint 3: scope GO"
git tag -a cp-08    1ebe312 -m "checkpoint 8 (local): IP coverage"
git tag -a cp-09-10 bb645f2 -m "checkpoint 9-10: product seed + crawl pilot"
git push origin --tags
```

Sau mỗi checkpoint mới ở mục 3, tạo tag tương ứng (`cp-04`, `cp-06`, …).

---

## 3. Thi công từng bước

Mỗi bước có cùng sáu mục: **Coach yêu cầu → File → Code hiện tại làm gì → Chạy → Kiểm tra → Commit.**

### Bước 1 — Khung project `uv` (bước coach 0.1, checkpoint 5 phần local)

**Coach yêu cầu.** Cài `uv`, `uv sync` chạy được.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `pyproject.toml` | `name = "glamira-datasource"`, Python ≥ 3.12. Bốn thư viện: `pymongo`, `ip2location`, `beautifulsoup4`, `playwright`. `[tool.uv] package = false`: đây là app, không phải thư viện để publish |
| `uv.lock` | `uv` tự sinh. Khóa đúng phiên bản. Không sửa tay |
| `.gitignore` | Chặn `.env`, `.venv/`, `data/`, `*.tar.gz`, `*.bson`, `*.BIN`, `infra/gcp/gcp.env` |
| `.env.example` | Mẫu biến: `DATA_TAR_PATH`, `IP_BIN_PATH`, `MONGO_URI`, `MONGO_DB`, `MONGO_COLLECTION_RAW`, `MONGO_COLLECTION_PRODUCTS`, `INGEST_BATCH_SIZE`, `CRAWL_*` |
| `src/__init__.py` | Một docstring. Có file này thì `python -m src.cli` chạy được |
| `src/config.py` | `load_dotenv()` tự viết (không cần `python-dotenv`): đọc `KEY=VALUE`, không ghi đè biến đã có. `Settings.from_env()` trả dataclass đóng băng, có default `glamira`, `glamira_raw`, `products`, batch 10.000 |
| `src/cli.py` | `argparse` với ba nhóm `explore`, `ingest`, `enrich`. Lúc bước 1 chỉ cần nhóm `explore` |
| `README.md` | Bảng checkpoint, cách chạy |

Code cốt lõi, `src/config.py`:

```python
@classmethod
def from_env(cls, dotenv: Path | None = None) -> Settings:
    load_dotenv(dotenv)
    return cls(
        data_tar_path=_env("DATA_TAR_PATH"),
        mongo_uri=_env("MONGO_URI"),
        mongo_db=_env("MONGO_DB", "glamira") or "glamira",
        mongo_collection_raw=_env("MONGO_COLLECTION_RAW", "glamira_raw") or "glamira_raw",
        ingest_batch_size=int(_env("INGEST_BATCH_SIZE", "10000") or "10000"),
        ...
    )
```

Mọi module lấy đường dẫn và tên collection từ đây. Không file nào viết cứng `127.0.0.1`.

**Chạy.**

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/loclt/workspace/unigap_course/projects/project05
cp .env.example .env        # rồi sửa MONGO_URI=mongodb://127.0.0.1:27017/
uv sync
```

**Kiểm tra.** Có `.venv/`. `uv run python -c "import pymongo, bs4, IP2Location, playwright"` không lỗi.

**Commit** (đã có trong `d837bdf`; làm lại từ đầu thì):

```bash
git add pyproject.toml uv.lock .gitignore .env.example README.md src/__init__.py src/config.py src/cli.py
git commit -m "chore: start the uv project (checkpoint 5)"
git push origin main
```

---

### Bước 2 — Đọc tar.gz/BSON không nhét vào RAM (bước coach 0.1)

**Coach yêu cầu.** Đọc mẫu dữ liệu. Ví dụ Notion là JSONL. File thật là mongodump BSON trong tar.gz, ~31 GB sau giải nén, nên phải tự viết reader.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/stream/__init__.py` | Docstring |
| `src/stream/tar_bson.py` | `parse_tar_size()`: đọc ô size 12 byte, cả octal lẫn GNU base-256 (byte đầu `0x80`). `parse_tar_header()`: header 512 byte → tên, size, typeflag. `SummaryDump`: mở gzip, nhảy qua member khác, gặp `…summary.bson` thì `yield` từng document. Ghi `completed`, `leftover_bytes` để biết đọc có hết không |
| `src/stream/bson_lite.py` | `iter_fields()`: đi từng field top-level của một document. Chỉ copy byte của field trong `MATERIAL_KEYS` (`collection`, `ip`, `product_id`, `current_url`, …). Email, user agent: chỉ đo rỗng/không rỗng, không copy |
| `tests/test_phase0.py` | Tự tạo BSON giả bằng `bdoc()`, tar ustar giả. Test base-256, ObjectId/int64 không làm lệch con trỏ, email không bị đọc ra |

Code cốt lõi, `SummaryDump._iter_member`:

```python
length = int.from_bytes(buffer[:4], "little", signed=True)   # 4 byte đầu = độ dài document
if length < 5 or length > _MAX_DOC:                           # BSON tối đa 16 MB
    raise ValueError(f"invalid BSON document length {length}")
while len(buffer) < length:
    buffer += limited.read(max(length - len(buffer), _CHUNK))  # đọc thêm từng 8 MB
document = bytes(buffer[:length]); del buffer[:length]
yield document
```

RAM chỉ giữ khoảng 8 MB, không phải 31 GB.

**Chạy / Kiểm tra.**

```bash
uv run python -m unittest tests.test_phase0 -v
```

Phải có `test_octal_and_gnu_base256 … ok` và `test_roundtrip_tiny_dump … ok`.

**Commit** (đã có trong `d837bdf`):

```bash
git add src/stream/__init__.py src/stream/tar_bson.py src/stream/bson_lite.py tests/test_phase0.py
git commit -m "feat: stream the mongodump without unpacking it"
```

---

### Bước 3 — % trống theo loại event (bước coach 0.2, **checkpoint 1**)

**Coach yêu cầu.** Đo % trống của `product_id`, `order_id`, `ip`… theo từng `collection`. Giải thích vì sao `checkout_success` có `cart_products` còn `view_product_detail` thì không.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/explore/__init__.py` | Docstring |
| `src/explore/sketch.py` | `HyperLogLog(precision=14)`: đếm số giá trị khác nhau, sai số ~0,8%, RAM 16 KB. Hash bằng hai lần `zlib.crc32` |
| `src/explore/profile.py` | `profile_tar()` → `profile_documents()` → `_accumulate()` mỗi document. Đếm key, nullish theo event, IP (`classify_ip`: public/private/ipv6/invalid), khoảng `time_stamp`, `local_time`, host URL, store, tiền tệ, `_id` trùng trong 500k đầu. Kết quả là dataclass `Profile`, có `to_dict()` |
| `src/explore/render.py` | `render_null_profile()`, `render_quality_report()`, `render_data_dictionary()`: `Profile` → markdown. Không đếm gì |
| `docs/null_profile.md` | Output |

Định nghĩa trống, ở đầu `profile.py`: thiếu field, BSON null, hoặc `""`. `0` và `false` là có giá trị.

**Chạy.**

```bash
# mẫu nhanh, đúng ý coach 0.1 (10k–100k dòng)
uv run python -m src.cli explore null-profile --sample-size 100000
# full, khoảng 43 phút
uv run python -m src.cli explore null-profile --sample-size 0
```

**Kiểm tra.** `docs/null_profile.md` có bảng theo event. Dòng `checkout_success`: `product_id` trống 100%, `cart_products` có 100%.

**Commit** (đã có `5db7803`):

```bash
git add src/explore/__init__.py src/explore/sketch.py src/explore/profile.py src/explore/render.py docs/null_profile.md
git commit -m "docs: record the null profile by event type (checkpoint 1)"
```

---

### Bước 4 — Báo cáo chất lượng (bước coach 0.3, **checkpoint 2**)

**Coach yêu cầu.** Ít nhất 5 kiểm tra trên dữ liệu thật: id trùng, ngày tương lai, doanh thu âm, IP trống, danh sách tiền tệ.

**File.** Không có code mới. `explore quality-report` dùng cùng `profile.py`, rồi gọi thêm `render_quality_report` và `render_data_dictionary`.

| Output | Nội dung |
|---|---|
| `docs/data_quality_report.md` | 41.432.473 document, 0 lỗi parse. Khoảng ngày thật 2020-04-01 → 2020-06-04 (tên file ghi Oct–Nov 2019). IP public 99,98%. Tiền tệ theo store |
| `docs/data_dictionary.md` | Bản nháp Pha 0: field raw, % có mặt |
| `data/staging/profile_stats.json` | Số thô, không commit (nằm trong `data/`) |

**Chạy.**

```bash
uv run python -m src.cli explore quality-report --sample-size 0
```

Một lần quét ghi ba file, vì quét 43 phút hai lần là phí.

**Kiểm tra.** Đầu report có `41,432,473` và `leftover 0`.

**Commit** (đã có `5db7803`):

```bash
git add docs/data_quality_report.md docs/data_dictionary.md
git commit -m "docs: record the data quality report (checkpoint 2)"
```

---

### Bước 5 — Chốt phạm vi (bước coach 0.4, **checkpoint 3**)

**Coach yêu cầu.** Trả lời ba câu: có cần nước không, có cần tên/category không, nạp đủ hay mẫu. Ghi GO/NO-GO.

**File.** Viết tay, không có code.

| File | Nội dung hiện tại |
|---|---|
| `docs/scope_confirmation.md` | GO tra IP (99,98% IPv4 public, ngưỡng dừng < 95% trên `checkout_success`). GO crawl (17k id, không có tên trong log). Chấp nhận khoảng ngày đo được. Doanh thu tách theo `currency`, không quy đổi |
| `docs/architecture.md` | Một trang đường ống, quyết định đọc archive |

**Kiểm tra.** Bốn ô `[x]` cuối file đều đã tick **sau khi** có số ở bước 3–4.

**Commit** (đã có `901bc21`):

```bash
git add docs/scope_confirmation.md docs/architecture.md
git commit -m "docs: confirm scope with GO for IP lookup and product crawl (checkpoint 3)"
git tag -a cp-03 -m "checkpoint 3" && git push origin main --tags
```

**Dừng ở đây nếu chưa GO.** Coach viết rõ.

---

### Bước 6 — GCP project, API, bucket (bước coach 1.1, **checkpoint 4**)

**Coach yêu cầu.** Tạo project, bật Compute Engine, Cloud Storage, BigQuery. Bucket `glamira-raw-data-[region]`. Service account. Upload thử một file, `gsutil cp` thành công.

**File (🆕, đã commit trong `de05cae`).**

| File | Nội dung hiện tại |
|---|---|
| `infra/gcp/gcp.env.example` | `GCP_PROJECT_ID`, `GCP_REGION=asia-southeast1`, `GCP_ZONE=asia-southeast1-b`, `GCS_BUCKET`, `GCP_SA_NAME=glamira-vm`, `VM_NAME=glamira-mongo`, `VM_MACHINE_TYPE=e2-standard-4`, `VM_DISK_SIZE=100GB`, `VM_TAG` |
| `infra/gcp/lib.sh` | Mọi script `source` file này. Đọc `gcp.env`, dừng nếu còn `your-project-id`, tính `SA_EMAIL` |
| `infra/gcp/01_project.sh` | `gcloud config set project/region/zone`. `services enable compute storage bigquery iam`. Tạo service account nếu chưa có |
| `infra/gcp/02_bucket.sh` | Tạo bucket private (`--uniform-bucket-level-access --public-access-prevention`). Cấp `roles/storage.objectAdmin` cho service account **trên bucket**. `gsutil cp docs/scope_confirmation.md gs://…/smoke/` |
| `infra/gcp/03_upload_inputs.sh` | `gcloud storage cp` tar + BIN lên `raw/` và `reference/`. Tự so CRC32C |
| `docs/gcp_evidence.md` | Template. Bạn dán output thật vào |

Script nào cũng có `describe … || create`, nên chạy lại không tạo trùng.

**Chuẩn bị một lần (máy chưa có `gcloud`).**

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install -y google-cloud-cli
```

Đăng nhập mở trình duyệt, nên bạn tự gõ trong prompt của Claude Code: `! gcloud auth login`.

Console → Billing: project phải có billing account. Nên đặt Budget alert 20 USD.

```bash
cp infra/gcp/gcp.env.example infra/gcp/gcp.env
gcloud projects list            # lấy PROJECT_ID, không phải tên hiển thị
nano infra/gcp/gcp.env          # sửa GCP_PROJECT_ID và GCS_BUCKET
```

**Chạy.**

```bash
bash infra/gcp/01_project.sh
bash infra/gcp/02_bucket.sh
bash infra/gcp/03_upload_inputs.sh     # 5,5 GB, 15–40 phút tùy mạng
```

**Kiểm tra.**

- `01`: in ra `compute.googleapis.com`, `storage.googleapis.com`, `bigquery.googleapis.com`.
- `02`: dòng cuối có `gs://…/smoke/scope_confirmation.md`.
- `03`: `5495914358` byte cho tar, `143974289` byte cho BIN.

| Lỗi | Sửa |
|---|---|
| `FAILED_PRECONDITION` khi enable | Chưa gắn billing |
| `409 bucket name is not available` | Đổi `GCS_BUCKET` |
| `403 storage.buckets.create` | IAM: cấp `Storage Admin` cho tài khoản của bạn |

**Commit:** dán ba output vào `docs/gcp_evidence.md` mục checkpoint 4. Bỏ email và số billing.

```bash
git add docs/gcp_evidence.md
git commit -m "docs: record GCP project and bucket smoke upload (checkpoint 4)"
git tag -a cp-04 -m "checkpoint 4" && git push origin main --tags
```

---

### Bước 7 — VM MongoDB, máy cá nhân nối được (bước coach 1.2, **checkpoint 6**)

**Coach yêu cầu.** VM Ubuntu 16–32 GB RAM, đĩa 100 GB. Cài MongoDB, tạo user, firewall chỉ IP của mình. Máy cá nhân `mongosh` vào được.

**File (🆕, đã commit trong `de05cae`).**

| File | Nội dung hiện tại |
|---|---|
| `infra/gcp/04_vm.sh` | `gcloud compute instances create`: `e2-standard-4` (16 GB), `ubuntu-2404-lts-amd64`, 100 GB `pd-balanced`, chạy dưới service account, tag `glamira-mongo`. Lấy IP của bạn bằng `curl -4 api.ipify.org`, tạo/cập nhật rule `glamira-mongo-from-my-ip` chỉ mở `tcp:27017` cho `<IP>/32`. In IP VM |
| `infra/gcp/vm/install_mongo.sh` | Chạy **trên VM**. Cài `mongodb-org` 8.0 + `git` + `tmux`. Khi Mongo còn nghe 127.0.0.1 và chưa bật auth: hỏi hai mật khẩu, tạo `admin` (root) và `glamira_app` (readWrite `glamira`). Sau đó mới sửa `/etc/mongod.conf`: `bindIp: 0.0.0.0`, `authorization: enabled`. Restart |
| `src/db.py` | `get_client(settings)`: `MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)`. Dùng được cả local không auth lẫn VM có user. 🔧 docstring cập nhật |

Thứ tự trong `install_mongo.sh` quan trọng: tạo user, bật auth, rồi mới mở mạng. Làm ngược lại thì có lúc ai quét cổng cũng vào được.

**Chạy.**

```bash
bash infra/gcp/04_vm.sh                         # ghi lại IP cuối = VM_IP
source infra/gcp/lib.sh
gcloud compute scp infra/gcp/vm/install_mongo.sh "$VM_NAME":~ --zone="$GCP_ZONE"
gcloud compute ssh "$VM_NAME" --zone="$GCP_ZONE"
bash ~/install_mongo.sh                          # trên VM. Lưu hai mật khẩu vào password manager
exit
```

Thử từ máy cá nhân bằng Python của repo (khỏi cài `mongosh`):

```bash
read -r -s -p "glamira_app password: " P; echo
uv run python -c "
from pymongo import MongoClient
c = MongoClient('mongodb://glamira_app:$P@<VM_IP>:27017/glamira?authSource=admin', serverSelectionTimeoutMS=5000)
print(c.admin.command('ping'), c.server_info()['version'])"
```

**Kiểm tra.** In `{'ok': 1.0} 8.0.x`.

| Lỗi | Sửa |
|---|---|
| `ServerSelectionTimeoutError` | IP nhà đổi → chạy lại `04_vm.sh`. Trên VM: `sudo ss -ltnp \| grep 27017` phải là `0.0.0.0:27017` |
| `Authentication failed` | Thiếu `authSource=admin` |
| Mật khẩu có `@ : / ?` | Bọc bằng `urllib.parse.quote_plus` |

**Commit:**

```bash
git add docs/gcp_evidence.md
git commit -m "docs: record Mongo VM reachable from my machine (checkpoint 6)"
git tag -a cp-06 -m "checkpoint 6" && git push origin main --tags
```

---

### Bước 8 — `uv sync` trên VM (bước coach 1.3 đoạn đầu, **checkpoint 5** phần cloud)

**Coach yêu cầu.** Code viết ở local, push GitHub, kéo về VM.

**File.** Không có file mới. Dùng lại bước 1. Thêm `.env` trên VM, không commit.

**Chạy (trên VM).**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env
git clone https://github.com/loc-lt/05_glamira.git project05 && cd project05
uv sync
uv run python -m unittest discover -s tests
read -r -s -p "glamira_app password: " P; echo
cat > .env <<EOF
DATA_TAR_PATH=./data/raw/glamira_ubl_oct2019_nov2019.tar.gz
IP_BIN_PATH=./data/reference/IP-COUNTRY-REGION-CITY.BIN
MONGO_URI=mongodb://glamira_app:$P@127.0.0.1:27017/glamira?authSource=admin
MONGO_DB=glamira
MONGO_COLLECTION_RAW=glamira_raw
MONGO_COLLECTION_PRODUCTS=products
INGEST_BATCH_SIZE=10000
EOF
chmod 600 .env
```

Repo private: `sudo apt-get install -y gh && gh auth login`, rồi `gh repo clone loc-lt/05_glamira project05`.

**Kiểm tra.** `Ran 30 tests … OK`.

**Commit:** không có. Code không đổi, `.env` không commit.

---

### Bước 9 — Nạp 41 triệu dòng trên VM (bước coach 1.3, **checkpoint 7**)

**Coach yêu cầu.** Batch 10.000, `insert_many`, thêm `_loaded_at` và `_source_file`, in tiến độ mỗi 100.000, đếm lại khớp nguồn, index `collection` + `product_id`. Xong thì tắt VM.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/ingest/__init__.py` | Docstring |
| `src/ingest/load_mongo.py` 🔧 | `load_tar()`: `SummaryDump` → `bson.decode` → `stamp()` → gom batch → `_flush()`. `_flush()` gọi `insert_many(ordered=False)`; lỗi trùng `_id` (code 11000) thì đếm `duplicates`, lỗi khác thì dừng. Mỗi batch kiểm tra đĩa: dưới 8 GB trống thì dừng có báo. Cùng lượt đếm tần suất IP → `data/staging/ip_event_counts.tsv` và `checkout_success_ips.tsv` cho bước 10. Đọc hết member mới tạo index `collection`, `time_stamp`, `ip`, `product_id` (sparse), `viewing_product_id` (sparse). `LoadResult.count_matches` = đọc hết **và** `count_documents` = số document đã quét |
| `src/cli.py` 🔧 | `ingest load-mongo`: in `scanned=… inserted=… duplicates=… mongo_count=…`, rồi `count check: source=… mongo=… MATCH`. `MISMATCH` thì exit 3 |
| `infra/gcp/vm/fetch_inputs.sh` | Kéo tar + BIN từ bucket về `data/` của VM |
| `tests/test_export.py` 🆕 | `LoadStampTest`: stamp không ghi đè field gốc, `count_matches` đúng 3 trường hợp |

Code cốt lõi vừa thêm:

```python
def stamp(document: dict, loaded_at: datetime, source_file: str) -> dict:
    """Add the two load-audit fields. Source fields are never overwritten."""
    document.setdefault("_loaded_at", loaded_at)
    document.setdefault("_source_file", source_file)
    return document
```

`_loaded_at` là một mốc cho cả lượt nạp, không phải giờ từng batch. Tìm “mọi event của lượt nạp này” bằng một giá trị duy nhất.

Khác coach một chỗ: coach không nói `_id`. Repo giữ **ObjectId gốc** làm `_id`, nên chạy lại lệnh nạp thì bản trùng bị bỏ, không nhân đôi 41 triệu dòng.

**Chạy (trên VM).**

```bash
GCS_BUCKET=<bucket> bash infra/gcp/vm/fetch_inputs.sh
tmux new -s load                                  # SSH rớt thì job vẫn chạy
uv run python -m src.cli ingest load-mongo 2>&1 | tee data/staging/load_vm.log
# Ctrl+b rồi d để rời. Vào lại: tmux attach -t load
```

**Kiểm tra.** Dòng cuối log:

```text
count check: source=41,432,473 mongo=41,432,473 MATCH
```

Kiểm thêm bằng `mongosh` trên VM:

```bash
mongosh -u glamira_app -p --authenticationDatabase admin glamira --eval '
print(db.glamira_raw.countDocuments({}));
printjson(db.glamira_raw.findOne({}, {_loaded_at: 1, _source_file: 1, collection: 1}));
printjson(db.glamira_raw.getIndexes().map(i => i.name));'
```

`disk_stop=True` thì tăng đĩa bằng `gcloud compute disks resize glamira-mongo --size=150GB --zone=…` rồi chạy lại. Bản trùng bị bỏ, nên chạy lại không hỏng.

**Commit.** Code đã commit trước khi lên VM. Ở đây chỉ commit bằng chứng:

```bash
# máy cá nhân: dán dòng count check + output mongosh vào docs/gcp_evidence.md
git add docs/gcp_evidence.md
git commit -m "docs: record 41,432,473 events loaded on the GCP Mongo VM (checkpoint 7)"
git tag -a cp-07 -m "checkpoint 7" && git push origin main --tags
```

---

### Bước 10 — Tra IP + CSV (bước coach 2.1, **checkpoint 8**)

**Coach yêu cầu.** Lấy IP không trùng, tra nước/thành phố, ghi collection, xuất CSV, index `ip`, phủ ≥ 80%.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/enrich/__init__.py` | Docstring |
| `src/enrich/ip_lookup.py` | `load_ip_geo()`: đọc TSV tần suất IP mà lệnh nạp đã ghi, nên không quét lại 41 triệu event. `classify_ip()` (dùng lại từ `explore/profile.py`) bỏ private/IPv6/invalid. IP public → `IP2Location.get_all()`. Ghi `UpdateOne({"_id": ip}, {"$set": …}, upsert=True)`, 5.000 lệnh một lần. Field: `status` (`ok`/`not_found`/`private`/`ipv6`/`invalid`), `country_code`, `country_name`, `region`, `city`, `events`, `lookup_at`. Ghi `docs/ip_coverage.md` |
| `src/enrich/export_csv.py` 🆕 | `export_collection(settings, "ip_geo", out)` → `data/exports/ip_geo.csv`, cột cố định trong `COLUMNS["ip_geo"]` |
| `docs/ip_coverage.md` | Output |

Vì sao một IP một document, không ghi nước vào từng event: 3,2 triệu lần ghi thay vì 41 triệu. Join sau bằng `glamira_raw.ip = ip_geo._id`. `_id` là IP, nên đã có index unique. Đó là “index trên `ip`” coach yêu cầu.

**Chạy (trên VM).**

```bash
uv run python -m src.cli enrich ip
uv run python -m src.cli enrich export-csv ip_geo
gcloud storage cp data/exports/ip_geo.csv "gs://<bucket>/exports/"
```

**Kiểm tra.** In `public resolve 98.90% checkout_success 99.16%`. `ip_geo` = 3.239.628. `ip_geo.csv` = 3.239.629 dòng (có header). Ngưỡng coach 80%, ngưỡng scope 95%: qua cả hai.

**Commit.**

```bash
# gcloud compute scp "$VM_NAME":~/project05/docs/ip_coverage.md docs/ --zone="$GCP_ZONE"
git add docs/ip_coverage.md docs/gcp_evidence.md
git commit -m "feat: resolve IPs on the GCP Mongo VM and record coverage (checkpoint 8)"
git tag -a cp-08 -m "checkpoint 8" && git push origin main --tags
```

---

### Bước 11 — Tập `product_id` + URL không trùng (bước coach 2.2a, **checkpoint 9**)

**Coach yêu cầu.** Quét danh sách event coach liệt kê, gom `(product_id, url)`, in số id không trùng.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/enrich/urls.py` | Luật thuần, không mạng, không Mongo. `normalize_product_id()`: `96047`, `96047.0`, `"96047"` đều → `"96047"` (cart lưu int, trang detail lưu string). `product_page_url()`: chỉ nhận URL `glamira.*` có `.html`, bỏ query string, **giữ host thật**. `page_rank()`: `www.glamira.co.uk` xếp trên. `catalog_product_url()`: `https://www.glamira.com/catalog/product/view/id/<id>` dùng khi 404 |
| `src/enrich/extract_products.py` | Chia event coach làm ba nhóm. `_PAGE_EVENTS` (`view_product_detail`, `select_product_option`, `select_product_option_quality`, `add_to_cart_action`): lấy `current_url`. `_REFERRER_EVENTS` (`back_to_product_action`): lấy `referrer_url`. `_UNPAIRED_EVENTS` (4 event recommendation): quét để đếm nhưng **không ghép**. Mỗi id chọn một URL: ưu tiên `.co.uk`, hòa thì chọn URL xuất hiện nhiều nhất. Ghi CSV `product_id,canonical_url,source_event`, sắp theo id |
| `tests/test_enrich.py` | Test URL: giữ host, bỏ listing, int = string, ưu tiên UK, không dán slug Phần Lan lên host Anh, recommendation không ghép |

Khác coach: Notion bảo ghép `viewing_product_id` với `referrer_url` cho `product_view_all_recommend_clicked`. Mẫu thật cho thấy `viewing_product_id` là id **được gợi ý**, còn URL là trang người dùng **đang xem**. Hai thứ khác sản phẩm. Ghép vào thì crawl ra sai tên. Các id đó vẫn có URL riêng từ các event nhóm trang.

**Chạy (trên VM, hoặc local, vì cùng dữ liệu).**

```bash
uv run python -m src.cli enrich extract-products
wc -l data/exports/product_urls.csv                                   # 19094
cut -d, -f1 data/exports/product_urls.csv | sort | uniq -d | wc -l    # 0
gcloud storage cp data/exports/product_urls.csv "gs://<bucket>/exports/"
```

**Kiểm tra.** `products=19,093`. 0 id trùng. 17.849 URL là `www.glamira.co.uk`.

**Commit** (code đã có ở `e83b8f0`. Chạy lại trên VM thì chỉ ghi số):

```bash
git add docs/gcp_evidence.md
git commit -m "docs: record 19,093 unique product urls (checkpoint 9)"
git tag -a cp-09 -m "checkpoint 9" && git push origin main --tags
```

---

### Bước 12 — Crawl thử 100 (bước coach 2.2b, **checkpoint 10**)

**Coach yêu cầu.** HTTP GET có User-Agent, BeautifulSoup lấy `name`, `price`, `category`, `description`, `image_url`. Upsert ngay vào `products` kèm `crawled_at`, `source_url`. Nghỉ ngẫu nhiên 1,5–4,2 s. URL lỗi thì log và đi tiếp.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/enrich/crawl.py` | `crawl_seed()`: đọc seed, **bỏ id đã có `name`** (`_named_ids`), thử HTTP GET một lần để ghi lại 403. Mở Chrome thật qua Playwright (`headless=False`), từng trang một, `time.sleep(random.uniform(1.5, 4.2))`. 404/không có tên thì thử URL catalog. Lỗi mạng thì mở tab mới, thử lại một lần. `_catalog_op()`: `UpdateOne({"_id": product_id}, upsert=True)` với `name`, `category`, `price`, `currency`, `description`, `image_url`, `brand`, `sku`, `material`, `color`, `availability`, `url`, `source_url`, `http_status`, `error`, `crawled_at`. Ghi Mongo mỗi 10 trang, Ctrl+C vẫn lưu phần đã lấy |
| `parse_product_html()` cùng file | BeautifulSoup: JSON-LD `Product` trước (kể cả nằm trong `ItemPage.mainEntity`), thiếu tên thì `h1`, thiếu category thì breadcrumb |
| `tests/test_enrich.py` | Test parser trên HTML giả: JSON-LD, `ItemPage.mainEntity`, breadcrumb, field biến thể, URL catalog |
| `docs/crawl_pilot.md`, `docs/product_sample.md`, `docs/crawl_fallback_probe.md` | Kết quả |

Khác coach: HTTP GET có User-Agent bị **403** (dòng `HTTP GET probe: 403` đầu mỗi báo cáo crawl). Chrome thật thì trang trả HTML. Vì vậy crawl cần máy có màn hình, và chạy ở máy cá nhân.

**Chạy (máy cá nhân).**

```bash
uv run python -m src.cli enrich crawl --seed data/exports/product_urls.csv --limit 100
```

**Kiểm tra.** Cuối `docs/crawl_pilot.md`: `Name parsed: ≥ 95%`. Lần chạy đã có: 96/97.

**Commit** (đã có `e83b8f0`, `bb645f2`):

```bash
git add src/enrich/crawl.py tests/test_enrich.py docs/crawl_pilot.md docs/product_sample.md
git commit -m "feat: crawl a 100 product sample (checkpoint 10)"
git tag -a cp-10 -m "checkpoint 10" && git push origin main --tags
```

---

### Bước 13 — Crawl hết, CSV, đếm khớp (bước coach 2.2c, **checkpoint 11** phần 1)

**Coach yêu cầu.** Mỗi `product_id` một bản ghi. Số `products` = số id ở bước 11. Xuất CSV.

**File.**

| File | Nội dung hiện tại |
|---|---|
| `src/enrich/crawl.py` 🔧 | `_read_seed()`: `if limit and len(rows) >= limit`. Trước đây `--limit 0` chỉ đọc 1 dòng. Đã sửa ở `030414b` |
| `src/enrich/export_csv.py` 🆕 | `product_status()`: đếm id seed, id có trong `products`, id có tên, id còn thiếu. `export_collection(…, "products", …)` ghi `data/exports/products.csv` |
| `src/cli.py` 🔧 | `enrich product-status` (exit 4 khi còn thiếu), `enrich export-csv products` |

Trạng thái đo ngày 2026-11-09:

```text
seed=19,093 products=2,161 named=2,104 (11.02%) missing_from_mongo=16,932
```

**Chạy (máy cá nhân, Mongo local).** Khoảng 17.000 trang × 4–6 s ≈ 15–20 giờ. Chạy nhiều đợt được, vì id đã có tên sẽ bị bỏ qua.

```bash
systemctl --user status glamira-mongod
tmux new -s crawl
systemd-inhibit --what=sleep:idle \
  uv run python -m src.cli enrich crawl --seed data/exports/product_urls.csv --limit 0 \
  --out docs/crawl_full.md 2>&1 | tee data/staging/crawl_full.log
```

Sau mỗi đợt:

```bash
uv run python -m src.cli enrich product-status
```

Bị chặn liên tục (403/captcha) thì dừng vài giờ rồi chạy tiếp. Không giảm thời gian nghỉ.

Xong thì xuất CSV, rồi đẩy `products` lên VM. Cần MongoDB Database Tools: tải `.tgz` Ubuntu 24.04 x86_64, chép `bin/*` vào `~/.local/mongodb/bin/`.

```bash
uv run python -m src.cli enrich export-csv products
~/.local/mongodb/bin/mongodump --uri mongodb://127.0.0.1:27017 --db glamira --collection products \
  --gzip --archive=data/exports/products.archive.gz
source infra/gcp/lib.sh
gcloud storage cp data/exports/products.csv data/exports/products.archive.gz "gs://$GCS_BUCKET/exports/"
# trên VM:
gcloud storage cp "gs://<bucket>/exports/products.archive.gz" data/exports/
mongorestore -u glamira_app -p --authenticationDatabase admin \
  --gzip --archive=data/exports/products.archive.gz --nsInclude 'glamira.products' --drop
```

`--drop` chỉ thay collection `products` trên VM.

**Kiểm tra.** `product-status` in `missing_from_mongo=0` và exit 0. `products` trên VM = 19.093 (sản phẩm đã gỡ khỏi site vẫn có document, kèm `http_status` và `error`).

`docs/crawl_full.md` có một dòng cho mỗi id, khoảng 19.000 dòng. Chỉ commit bản tóm tắt: `head -6` + `tail -5` ghi vào `docs/crawl_full.md`.

**Commit:**

```bash
git add docs/crawl_full.md docs/gcp_evidence.md
git commit -m "docs: record the full product crawl and products csv (checkpoint 11)"
```

---

### Bước 14 — Data dictionary (bước coach 2.3, **checkpoint 11** phần 2)

**Coach yêu cầu.** Từ điển gồm collection raw, collection IP, collection products, và lỗi chất lượng đã biết.

**File.** `docs/data_dictionary.md`. Phần field raw do `render_data_dictionary` sinh ở bước 4. Thêm tay ba phần sau, dưới mục “Collection”:

- **`glamira_raw`**: thêm `_loaded_at`, `_source_file` (chỉ có ở bản VM) và 5 index.
- **`ip_geo`**: `_id` (IP), `status` (5 giá trị), `country_code`, `country_name`, `region`, `city`, `events`, `lookup_at`. Nguồn DB3 ngày 2016-11-29: nước tin được, thành phố gần đúng, không có lat/long.
- **`products`**: `_id` = `product_id` chữ, `name`, `category`, `price`, `currency`, `description`, `image_url`, `brand`, `sku`, `material`, `color`, `availability`, `url` (trang đã mở thật, có thể là URL catalog), `source_url` (URL trong seed), `http_status`, `error`, `crawled_at`. Ghi tỉ lệ có tên = named / 19.093.
- **Join**: `glamira_raw.ip = ip_geo._id`. `glamira_raw.product_id` hoặc `cart_products[].product_id` (int, đổi thành chữ) `= products._id`.
- **Lỗi đã biết**: link tới `docs/data_quality_report.md`. Ngày thật khác tên file. Giá là chuỗi theo `currency`, không quy đổi.

Lưu ý: chạy lại `explore quality-report` sẽ **ghi đè** `data_dictionary.md`. Sau bước này đừng chạy lại lệnh đó với `--dictionary-out` mặc định. Dùng `--dictionary-out /tmp/…` nếu cần.

**Commit:**

```bash
git add docs/data_dictionary.md
git commit -m "docs: finish the data dictionary for raw, ip_geo and products (checkpoint 11)"
git tag -a cp-11 -m "checkpoint 11" && git push origin main --tags
```

---

### Bước 15 — Handoff Project 06, tắt VM

**File 🆕** `docs/handoff_to_project06.md`. Một trang: ba collection và số document, đường dẫn GCS (`raw/`, `reference/`, `exports/ip_geo.csv`, `exports/products.csv`, `exports/product_urls.csv`), cách join, giới hạn (DB3 2016, giá chưa quy đổi, % sản phẩm có tên), lệnh chạy lại.

```bash
git add docs/handoff_to_project06.md README.md
git commit -m "docs: hand off the data source to Project 06"
git push origin main
```

Tắt VM ngay sau mỗi lần làm:

```bash
source infra/gcp/lib.sh
gcloud compute instances stop "$VM_NAME" --zone="$GCP_ZONE"
```

`start` lại thì IP VM có thể đổi (IP ephemeral). Lấy IP mới bằng `gcloud compute instances describe … --format="value(networkInterfaces[0].accessConfigs[0].natIP)"`.

Ước lượng chi phí (kiểm lại ở Billing, giá có thể đổi): `e2-standard-4` khoảng 0,15 USD/giờ khi chạy. Đĩa 100 GB khoảng 10–12 USD/tháng, **vẫn tính khi VM tắt**. GCS 6 GB dưới 0,2 USD/tháng. Coach chấm xong mà Project 06 chưa cần VM thì `gcloud compute instances delete`. Giữ bucket.

---

## 4. Cây source sau khi xong

```text
project05/
  pyproject.toml  uv.lock  .env.example  .gitignore  README.md
  infra/gcp/                                  ← bước 6, 7 (🆕)
    gcp.env.example  lib.sh
    01_project.sh  02_bucket.sh  03_upload_inputs.sh  04_vm.sh
    vm/install_mongo.sh  vm/fetch_inputs.sh
  src/
    cli.py  config.py  db.py                  ← bước 1, 7
    stream/   tar_bson.py  bson_lite.py       ← bước 2
    explore/  sketch.py  profile.py  render.py← bước 3, 4
    ingest/   load_mongo.py                   ← bước 9 (🔧)
    enrich/   ip_lookup.py                    ← bước 10
              export_csv.py                   ← bước 10, 13 (🆕)
              urls.py  extract_products.py    ← bước 11
              crawl.py                        ← bước 12, 13
  tests/
    test_phase0.py                            ← bước 2, 3
    test_enrich.py                            ← bước 11, 12
    test_export.py                            ← bước 9, 10, 13 (🆕)
  docs/
    null_profile.md  data_quality_report.md   ← checkpoint 1, 2
    scope_confirmation.md  architecture.md    ← checkpoint 3
    gcp_evidence.md                           ← checkpoint 4, 6, 7, 8, 9, 11
    ip_coverage.md                            ← checkpoint 8
    crawl_pilot.md  product_sample.md         ← checkpoint 10
    crawl_full.md  data_dictionary.md         ← checkpoint 11
    handoff_to_project06.md                   ← sau cùng
    qua_trinh.md  implements.md  huong_dan_coach.md  runbook.md  mongodb.md
```

## 5. Kiểm tra cuối trước khi báo coach

```bash
git status                                                         # sạch
git tag -l 'cp-*'                                                  # cp-03 … cp-11
git ls-files | grep -E '(^|/)\.env$|gcp\.env$|\.BIN$|\.tar\.gz$|^data/' || echo "không có file cấm"
uv run python -m unittest discover -s tests                        # 30 test OK
uv run python -m src.cli enrich product-status                     # missing_from_mongo=0
```

Trên VM:

```bash
mongosh -u glamira_app -p --authenticationDatabase admin glamira --eval '
["glamira_raw","ip_geo","products"].forEach(c => print(c, db[c].countDocuments({})))'
```

Kỳ vọng: `glamira_raw 41432473`, `ip_geo 3239628`, `products 19093`. Xong thì **tắt VM**.
