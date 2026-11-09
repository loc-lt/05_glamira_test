# Implements — làm 11 checkpoint của coach, có GCP

File này là **sổ thi công**: mỗi checkpoint có mục tiêu, lệnh chạy, cách kiểm tra, lỗi hay gặp và commit để đẩy GitHub.

- Lý do thiết kế và cách đọc code: `docs/qua_trinh.md`.
- Bản dịch trang Notion: `docs/huong_dan_coach.md`.
- Link gốc: [Glamira Project 5](https://davidnotio101.notion.site/Glamira-Project-5-39e6f7803e7b8012ba5bf0db897d9b72#3c16f7803e7b800887f4e9f514a4c1e8).

Quy tắc coach giữ nguyên: **hiểu data trước, dựng máy sau. Mỗi checkpoint một ý. Xong thì commit + push rồi mới sang bước kế.**

---

## 0. Trạng thái hiện tại (đo ngày 2026-11-09)

| # | Pha | Checkpoint | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| 1 | 0 | % trống theo event | ✅ | `docs/null_profile.md`, full scan 41.432.473 doc |
| 2 | 0 | `data_quality_report.md` | ✅ | `docs/data_quality_report.md` |
| 3 | 0 | `scope_confirmation.md` GO | ✅ | GO tra IP, GO crawl |
| 4 | 1 | GCP + bucket + `gsutil cp` | ⏳ **làm theo mục 3.1–3.3** | `infra/gcp/01_project.sh`, `02_bucket.sh` |
| 5 | 1 | `uv sync` | ✅ local · ⏳ trên VM | `pyproject.toml`, `uv.lock` |
| 6 | 1 | Mongo trên VM, máy cá nhân nối được | ⏳ **mục 3.4–3.6** | `infra/gcp/04_vm.sh`, `vm/install_mongo.sh` |
| 7 | 1 | Nạp đủ 41 triệu, đếm khớp | ✅ local (41.432.473) · ⏳ trên VM | `src/ingest/load_mongo.py` |
| 8 | 2 | Tra IP, % phủ | ✅ local · ⏳ trên VM | `docs/ip_coverage.md`: 3.239.628 IP, `checkout_success` 99,16% |
| 9 | 2 | `product_id` + URL không trùng | ✅ | `data/exports/product_urls.csv`: 19.093 id |
| 10 | 2 | Crawl thử 100 | ✅ | `docs/crawl_pilot.md`, `docs/product_sample.md` |
| 11 | 2 | Crawl hết + dictionary | ⏳ 2.104 / 19.093 id có tên | mục 4.4–4.6 |

Số trong Mongo local lúc viết file này:

| Collection | Document |
|---|---:|
| `glamira_raw` | 41.432.473 |
| `ip_geo` | 3.239.628 |
| `products` | 2.161 (2.104 có `name`) |

Lỗi đã sửa cùng lúc viết file này: `enrich crawl --limit 0` trước đây chỉ đọc **1** dòng seed. Giờ `0` nghĩa là đọc cả seed. Lệnh crawl full ở checkpoint 11 cần sửa này.

---

## 1. Kiến trúc khi có GCP

```text
Máy cá nhân (Ubuntu 24.04)                     GCP project
──────────────────────────                     ────────────────────────────────────────
data/raw/*.tar.gz  ──gcloud storage cp──►  GCS gs://glamira-raw-data-<region>-<project>/
data/reference/*.BIN ─────────────────►        raw/  reference/  smoke/  exports/
                                                     │
                                                     │ (VM đọc bằng service account, không key JSON)
                                                     ▼
git push ──► GitHub ──git clone──►         VM glamira-mongo (e2-standard-4, 16 GB, 100 GB)
                                             mongod 8.0, auth bật, cổng 27017
                                             uv run … ingest load-mongo  → glamira_raw
                                             uv run … enrich ip          → ip_geo
                                             uv run … enrich extract-products → CSV
                                                     ▲
mongosh / Compass ──tcp 27017 (chỉ IP của bạn)───────┘
crawl (Chrome có màn hình) ─► Mongo local → mongodump products → mongorestore lên VM
```

Vì sao chia như vậy:

- **Nạp 41 triệu dòng chạy trên VM.** Coach viết: code ở local, push GitHub, kéo về VM rồi chạy full. File tar nằm trong GCS cùng region với VM nên tải về nhanh và không mất phí egress.
- **Crawl chạy ở máy cá nhân.** `crawl.py` mở Chrome **có cửa sổ** (`headless=False`), vì HTTP GET bị 403. VM không có màn hình. Crawl ~17.000 trang mất khoảng 15–20 giờ. Để VM bật suốt thời gian đó là tốn credit. Crawl vào Mongo local, xong đẩy một collection `products` lên VM.
- **Không bỏ Mongo local.** Nó là bản dự phòng, và crawl cần nó.

Tên cố định trong file này:

| Thứ | Tên |
|---|---|
| Region / zone | `asia-southeast1` / `asia-southeast1-b` (Singapore, gần Việt Nam) |
| Bucket | `glamira-raw-data-asia-southeast1-<project-id>` (coach: `glamira-raw-data-[region]`. Thêm project id vì tên bucket phải duy nhất toàn cầu) |
| Service account | `glamira-vm@<project-id>.iam.gserviceaccount.com` |
| VM | `glamira-mongo`, tag `glamira-mongo` |
| Firewall | `glamira-mongo-from-my-ip`: tcp 27017, chỉ `<IP của bạn>/32` |
| Mongo user | `admin` (root), `glamira_app` (readWrite trên `glamira`) |
| Database / collection | `glamira` / `glamira_raw`, `ip_geo`, `products` |

---

## 2. Pha 0 — đã làm (checkpoint 1–3)

Mục này ghi để bạn biết đã làm gì và chạy lại thế nào. Không cần làm lại.

### Checkpoint 1 — % trống theo loại event

| | |
|---|---|
| Mục tiêu | Biết field nào trống ở event nào trước khi nạp Mongo |
| Code | `src/stream/tar_bson.py` (mở tar.gz, kể cả header size base-256 > 8 GB), `src/stream/bson_lite.py` (đi từng document theo 4 byte độ dài), `src/explore/profile.py`, `src/explore/render.py` |
| Lệnh | `uv run python -m src.cli explore null-profile --sample-size 500000` (mẫu nhanh) |
| Output | `docs/null_profile.md` |
| Kiểm tra | `checkout_success` có `order_id`, `cart_products`, không có `product_id` top-level |
| Commit đã có | `d837bdf feat: stream the Glamira mongodump for Phase 0 profiling` |

### Checkpoint 2 — báo cáo chất lượng

```bash
uv run python -m src.cli explore quality-report --sample-size 0
```

Đọc hết 41.432.473 document, khoảng 43 phút. Ghi một lần ba file: `data_quality_report.md`, `null_profile.md`, `data_dictionary.md`. Đủ năm kiểm tra coach yêu cầu: id trùng, ngày tương lai, giá âm, IP trống, danh sách tiền tệ.

Commit đã có: `5db7803 docs: record the full-scan null profile and quality report`.

### Checkpoint 3 — chốt phạm vi

`docs/scope_confirmation.md` trả lời ba câu của coach (mục 0.4):

1. Log có nước chưa? Chưa. → **GO tra IP.**
2. `view_product_detail` có tên sản phẩm chưa? Chưa. → **GO crawl.**
3. Nạp đủ hay mẫu? Đủ 41 triệu. → cần Mongo (Pha 1).

Commit đã có: `901bc21 docs: propose GO for IP lookup and product crawl`.

---

## 3. Pha 1 trên GCP (checkpoint 4–7)

### 3.0 Chuẩn bị một lần trên máy cá nhân

**a) Cài Google Cloud CLI** (máy hiện chưa có `gcloud`):

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install -y google-cloud-cli
gcloud version
```

`gsutil` đi kèm gói này.

**b) Đăng nhập.** Lệnh mở trình duyệt nên bạn tự gõ trong prompt, có dấu `!` ở đầu:

```bash
! gcloud auth login
```

**c) Kiểm tra billing.** Vào Console → Billing → project của bạn phải có billing account. Không có thì `gcloud services enable compute…` sẽ báo lỗi `FAILED_PRECONDITION`.

**d) Đặt budget alert** (khuyên làm): Console → Billing → Budgets & alerts → 20 USD, báo ở 50% / 90%. Bạn quên tắt VM thì có email.

**e) Điền cấu hình:**

```bash
cd /home/loclt/workspace/unigap_course/projects/project05
cp infra/gcp/gcp.env.example infra/gcp/gcp.env
gcloud projects list                 # lấy PROJECT_ID (không phải tên hiển thị)
nano infra/gcp/gcp.env               # sửa GCP_PROJECT_ID và GCS_BUCKET
```

`infra/gcp/gcp.env` đã có trong `.gitignore`. File này không chứa mật khẩu, nhưng mỗi máy một bản.

### 3.1 Checkpoint 4a — project, API, service account

```bash
bash infra/gcp/01_project.sh
```

Script làm bốn việc:

1. `gcloud config set project/region/zone`.
2. Bật API `compute`, `storage`, `bigquery`, `iam`. Coach yêu cầu BigQuery dù P05 chưa dùng. Project 06 sẽ cần.
3. Tạo service account `glamira-vm`. VM sẽ chạy dưới tên này nên đọc được bucket mà **không cần tải key JSON** về máy. Key JSON là thứ hay bị commit nhầm lên GitHub.
4. In danh sách API đã bật.

Kiểm tra: output có `compute.googleapis.com`, `storage.googleapis.com`, `bigquery.googleapis.com`.

Lần đầu bật Compute có thể mất 1–2 phút.

### 3.2 Checkpoint 4b — bucket và upload thử

```bash
bash infra/gcp/02_bucket.sh
```

- Bucket cùng region với VM, `uniform-bucket-level-access`, `public-access-prevention`. Không ai ngoài project đọc được log khách hàng.
- Cấp cho service account quyền `roles/storage.objectAdmin` **trên bucket này**, không phải cả project.
- Upload thử `docs/scope_confirmation.md` bằng `gsutil cp`. Đây đúng là điều kiện qua checkpoint 4 của coach.

Kiểm tra: dòng cuối in `gs://…/smoke/scope_confirmation.md` kèm kích thước.

Lỗi hay gặp:

| Lỗi | Nghĩa | Sửa |
|---|---|---|
| `409 … bucket name is not available` | Tên đã có người dùng | Đổi `GCS_BUCKET` trong `gcp.env` |
| `403 … does not have storage.buckets.create` | Tài khoản không phải Owner/Editor | Console → IAM, cấp `Storage Admin` |

**Ghi bằng chứng** vào `docs/gcp_evidence.md` mục checkpoint 4: dán output `gsutil ls -l`. Bỏ số billing account, bỏ email.

**Commit + push checkpoint 4:**

```bash
git add docs/gcp_evidence.md
git commit -m "docs: record GCP project and bucket smoke upload (checkpoint 4)"
git push origin main
```

### 3.3 Upload hai file coach lên GCS

```bash
bash infra/gcp/03_upload_inputs.sh
```

Khoảng 5,5 GB + 144 MB. Tốc độ phụ thuộc mạng upload nhà bạn: 50 Mbps ≈ 15 phút, 20 Mbps ≈ 40 phút. `gcloud storage cp` tự so CRC32C sau khi lên. Lệnh không lỗi tức là file trên GCS giống hệt file local.

Kiểm tra:

```bash
source infra/gcp/lib.sh
gcloud storage ls -l "gs://$GCS_BUCKET/raw/" "gs://$GCS_BUCKET/reference/"
```

Phải thấy `5495914358` byte cho tar và `143974289` byte cho BIN. Đó là đúng kích thước file local.

Không commit gì ở bước này. File dữ liệu không bao giờ vào git.

### 3.4 Checkpoint 6a — VM và firewall

```bash
bash infra/gcp/04_vm.sh
```

| Lựa chọn | Giá trị | Vì sao |
|---|---|---|
| Máy | `e2-standard-4` (4 vCPU, 16 GB) | Coach yêu cầu 16–32 GB. WiredTiger mặc định dùng ~50% RAM làm cache |
| Đĩa | 100 GB `pd-balanced` | Mongo local đo được 13 GB cho `glamira_raw` + `ip_geo` + index. Tar 5,5 GB. Còn dư cho log và `products` |
| OS | Ubuntu 24.04 LTS | Cùng bản với máy bạn. Lệnh apt giống nhau |
| Service account | `glamira-vm`, scope `cloud-platform` | Quyền thật bị giới hạn bởi IAM ở bucket (mục 3.2) |
| Firewall | tcp 27017 chỉ từ `<IP>/32` | Coach: “chỉ mở firewall cho IP của mình”. Không bao giờ để `0.0.0.0/0` cho Mongo |

Script in IP public của VM ở dòng cuối. Ghi lại, gọi là `VM_IP`.

IP nhà bạn đổi (wifi khác, router khởi động lại) thì chạy lại `04_vm.sh`. Script cập nhật rule, không tạo VM thứ hai.

> MongoDB phiên bản: coach viết MongoDB 6. Bản 6.0 đã hết hỗ trợ (EOL 07/2025) và không có gói cho Ubuntu 24.04. Repo dùng **8.0**, cùng bản `mongod` local (`v8.0.13`). Các lệnh `mongosh`, `countDocuments`, index không khác.

### 3.5 Checkpoint 6b — cài MongoDB, tạo user, bật auth

Đưa script lên VM rồi chạy trên VM:

```bash
source infra/gcp/lib.sh
gcloud compute scp infra/gcp/vm/install_mongo.sh "$VM_NAME":~ --zone="$GCP_ZONE"
gcloud compute ssh "$VM_NAME" --zone="$GCP_ZONE"
# --- từ đây là shell trên VM ---
bash ~/install_mongo.sh
```

Lần đầu `gcloud compute ssh` sẽ tạo SSH key. Bấm Enter cho passphrase trống, hoặc đặt passphrase nếu muốn.

Script làm theo thứ tự này, và thứ tự quan trọng:

1. Cài `mongodb-org` 8.0 từ repo chính thức, cài thêm `git` và `tmux`.
2. Khởi động `mongod` **khi chưa bật auth và chỉ nghe 127.0.0.1**. Lúc này chưa ai ngoài VM vào được.
3. Hỏi hai mật khẩu (không hiện trên màn hình, không lưu vào file), tạo `admin` và `glamira_app`.
4. Sửa `/etc/mongod.conf`: `bindIp: 0.0.0.0` và `security.authorization: enabled`. Bản gốc lưu ở `/etc/mongod.conf.bak`.
5. Restart, in trạng thái.

Nếu mở cổng trước khi bật auth, ai quét được cổng là đọc được dữ liệu. Vì vậy script tạo user và bật auth trước, rồi mới mở mạng.

Lưu hai mật khẩu vào trình quản lý mật khẩu. Không ghi vào file trong repo.

### 3.6 Checkpoint 6c — máy cá nhân nối vào VM

`mongosh` có sẵn trên VM. Máy cá nhân hiện chỉ có `mongod` trong `~/.local/mongodb/bin`. Dùng Python của repo để thử, khỏi cài thêm:

```bash
# trên MÁY CÁ NHÂN
cd /home/loclt/workspace/unigap_course/projects/project05
read -r -s -p "glamira_app password: " P; echo
uv run python -c "
from pymongo import MongoClient
c = MongoClient('mongodb://glamira_app:$P@<VM_IP>:27017/glamira?authSource=admin', serverSelectionTimeoutMS=5000)
print(c.admin.command('ping')); print(c.server_info()['version'])
"
```

Muốn dùng đúng `mongosh` như coach: tải bản `.tgz` ở mongodb.com/try/download/shell, giải nén vào `~/.local/mongosh`, rồi chạy:

```bash
~/.local/mongosh/bin/mongosh "mongodb://glamira_app@<VM_IP>:27017/glamira?authSource=admin"
```

Compass: New connection → URI như trên (có mật khẩu) → Connect.

Qua checkpoint 6 khi in ra `{'ok': 1.0}` và `8.0.x`.

| Lỗi | Nghĩa | Sửa |
|---|---|---|
| `ServerSelectionTimeoutError` | Firewall chặn, hoặc mongod chưa nghe 0.0.0.0 | `curl -4 api.ipify.org` so với rule, chạy lại `04_vm.sh`. Trên VM: `sudo ss -ltnp \| grep 27017` |
| `Authentication failed` | Sai mật khẩu, hoặc thiếu `authSource=admin` | User tạo trong DB `admin`, nên URI phải có `authSource=admin` |
| Mật khẩu có `@ : / ?` | URI hỏng | Mã hóa bằng `urllib.parse.quote_plus` |

**Commit + push checkpoint 6** (dán output ping, che IP VM nếu muốn):

```bash
git add docs/gcp_evidence.md
git commit -m "docs: record Mongo VM reachable from my machine (checkpoint 6)"
git push origin main
```

Hai script hạ tầng `infra/gcp/` đã commit cùng file này.

### 3.7 Checkpoint 5 trên VM — clone và `uv sync`

Coach đặt `uv sync` ở Pha 1. Local đã có. Giờ làm trên VM:

```bash
# trên VM
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
git clone https://github.com/loc-lt/05_glamira.git project05
cd project05
uv sync
uv run python -m unittest discover -s tests
```

Repo private thì `git clone` HTTPS sẽ hỏi đăng nhập. Hai cách:

- `sudo apt-get install -y gh && gh auth login` rồi `gh repo clone loc-lt/05_glamira project05`.
- Hoặc tạo deploy key read-only: `ssh-keygen -t ed25519` trên VM, dán `~/.ssh/id_ed25519.pub` vào GitHub → repo → Settings → Deploy keys.

Kiểm tra: `Ran 24 tests … OK`.

Tạo `.env` trên VM (không commit):

```bash
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

Không có commit nào ở bước này: code đã có, `.env` không commit.

### 3.8 Checkpoint 7 — nạp 41 triệu dòng trên VM

Kéo input từ bucket về VM:

```bash
# trên VM, trong ~/project05
GCS_BUCKET=<tên bucket> bash infra/gcp/vm/fetch_inputs.sh
```

Chạy nạp trong `tmux`. SSH rớt thì job vẫn chạy:

```bash
tmux new -s load
uv run python -m src.cli ingest load-mongo 2>&1 | tee data/staging/load_vm.log
# Ctrl+b rồi d để thoát tmux mà job vẫn chạy. Vào lại: tmux attach -t load
```

Local mất khoảng 45–60 phút. Trên VM tương đương. Mỗi 200.000 document script in một dòng tiến độ.

Script đã làm đúng các ý coach:

| Coach | `src/ingest/load_mongo.py` |
|---|---|
| Đọc batch 10.000 | `INGEST_BATCH_SIZE=10000` |
| `insert_many` | `insert_many(ordered=False)`, bản trùng `_id` bị bỏ |
| In tiến độ | mỗi 200.000 dòng |
| Đếm lại | `count_documents({})` khi hết member |
| Index `collection`, `product_id` | tạo **sau** khi nạp: `collection`, `time_stamp`, `ip`, `product_id`, `viewing_product_id` |
| `_loaded_at`, `_source_file` | **Không thêm.** `_id` là ObjectId gốc. Nạp lại không nhân đôi, và giờ nạp đọc được từ ObjectId. Ghi rõ điểm khác này trong evidence |

Kiểm tra số khớp nguồn:

```bash
mongosh -u glamira_app -p --authenticationDatabase admin glamira --eval '
print("glamira_raw", db.glamira_raw.countDocuments({}));
printjson(db.glamira_raw.getIndexes().map(i => i.name));
'
```

Phải in `glamira_raw 41432473`. Đó là số đo ở Pha 0 (`docs/data_quality_report.md`).

Nếu thiếu số: xem `data/staging/load_vm.log`. Dòng cuối có `stopped_for_disk=True` nghĩa là đĩa gần đầy. Tăng đĩa: `gcloud compute disks resize glamira-mongo --size=150GB --zone=…`, rồi chạy lại lệnh nạp. Bản trùng bị bỏ, nên chạy lại không hỏng.

**Commit + push checkpoint 7:**

```bash
# trên máy cá nhân, sau khi dán output countDocuments vào docs/gcp_evidence.md
git add docs/gcp_evidence.md
git commit -m "docs: record 41,432,473 events loaded on the GCP Mongo VM (checkpoint 7)"
git push origin main
```

---

## 4. Pha 2 (checkpoint 8–11)

### 4.1 Checkpoint 8 — tra IP trên VM

Lệnh nạp đã ghi `data/staging/ip_event_counts.tsv` và `checkout_success_ips.tsv` trên VM. Tra BIN từ các file này:

```bash
# trên VM
uv run python -m src.cli enrich ip
mongosh -u glamira_app -p --authenticationDatabase admin glamira \
  --eval 'print(db.ip_geo.countDocuments({}))'
```

Kỳ vọng: `ip_geo` = **3.239.628**, `checkout_success` resolve **99,16%**. Đó là số local. Ngưỡng coach là 80%.

Lệnh ghi lại `docs/ip_coverage.md`. So với bản đã commit:

```bash
git diff --stat docs/ip_coverage.md
```

Chỉ khác dòng đường dẫn BIN, hoặc không khác gì, nghĩa là VM và local cho cùng kết quả.

Coach muốn có **CSV cạnh Mongo**. Xuất `ip_geo` ra CSV và đưa lên bucket:

```bash
mongoexport -u glamira_app -p --authenticationDatabase admin \
  --db glamira --collection ip_geo --type csv \
  --fields _id,status,country_code,country_name,region,city,events \
  --out data/exports/ip_geo.csv
gcloud storage cp data/exports/ip_geo.csv "gs://<bucket>/exports/"
```

Tên field phải khớp code. Xem nhanh một document trước khi export:

```bash
mongosh … glamira --eval 'printjson(db.ip_geo.findOne({status: "ok"}))'
```

Sai tên field thì cột CSV trống, không có lỗi báo. Sửa `--fields` cho đúng tên.

**Commit + push checkpoint 8** (từ máy cá nhân, sau khi `gcloud compute scp` file `docs/ip_coverage.md` của VM về, hoặc ghi số vào evidence):

```bash
git add docs/ip_coverage.md docs/gcp_evidence.md
git commit -m "feat: resolve IPs on the GCP Mongo VM and record coverage (checkpoint 8)"
git push origin main
```

### 4.2 Checkpoint 9 — tập `product_id` + URL

```bash
# trên VM
uv run python -m src.cli enrich extract-products
wc -l data/exports/product_urls.csv            # 19094 = 1 header + 19093 id
cut -d, -f1 data/exports/product_urls.csv | sort | uniq -d | wc -l   # 0 = không trùng
gcloud storage cp data/exports/product_urls.csv "gs://<bucket>/exports/"
```

Event coach liệt kê đều được quét (`src/enrich/extract_products.py`). Bốn event recommendation **không** ghép `viewing_product_id` với URL đang xem, vì `viewing_product_id` là id được gợi ý, không phải id của trang. Lý do đầy đủ ở `docs/qua_trinh.md` mục 6.

Máy cá nhân lấy CSV từ bucket để crawl:

```bash
gcloud storage cp "gs://<bucket>/exports/product_urls.csv" data/exports/product_urls.csv
```

Commit: chỉ khi số id khác 19.093. Ghi vào evidence rồi `git commit -m "docs: record product url seed from VM (checkpoint 9)"`.

### 4.3 Checkpoint 10 — crawl thử 100 (đã qua)

`docs/crawl_pilot.md`: 96/97 trang có tên trên seed cũ. `docs/product_sample.md`: đủ field `name`, `category`, `price`, `currency`, `image_url`, `description`. Ngưỡng repo đặt ra: 95/100.

Muốn chạy lại cho thấy trên máy (máy cá nhân, Mongo local):

```bash
uv run python -m src.cli enrich crawl --seed data/exports/product_urls.csv --limit 100
```

Crawl bỏ qua id đã có `name`. 100 dòng đầu đã crawl rồi, nên lệnh này kết thúc rất nhanh.

### 4.4 Checkpoint 11a — crawl hết (máy cá nhân)

Còn khoảng **16.989** id chưa có tên (19.093 − 2.104). Nghỉ 1,5–4,2 giây, cộng thời gian tải trang khoảng 2–3 giây, nên cần **15–20 giờ**. Chạy được nhiều đêm: crawl bỏ qua id đã có tên, ghi Mongo mỗi 10 trang, dừng giữa chừng không mất kết quả.

```bash
# máy cá nhân, Mongo local đang chạy
systemctl --user status glamira-mongod
tmux new -s crawl
uv run python -m src.cli enrich crawl \
  --seed data/exports/product_urls.csv \
  --limit 0 \
  --out docs/crawl_full.md 2>&1 | tee data/staging/crawl_full.log
```

- `--limit 0` = cả seed. Cần bản sửa lỗi đã commit cùng file này.
- Chrome mở cửa sổ. Đừng đóng, đừng để máy sleep: `systemd-inhibit --what=sleep:idle uv run …`.
- 404 với URL `.co.uk` thì code thử `https://www.glamira.com/catalog/product/view/id/<id>` (`docs/crawl_fallback_probe.md`).
- Bị chặn liên tục (nhiều 403/captcha) thì dừng, nghỉ vài giờ, chạy lại. Không giảm thời gian nghỉ.

Đếm sau mỗi đợt:

```bash
uv run python -c "
from src.config import Settings; from src.db import get_client
s = Settings.from_env(); p = get_client(s)[s.mongo_db].products
print('products', p.count_documents({}), 'named', p.count_documents({'name': {'\$type': 'string', '\$ne': ''}}))
"
```

Điều kiện coach: số document `products` = số id ở checkpoint 9 (19.093). Id thật sự đã gỡ khỏi site (404 cả hai URL) vẫn có document, kèm `http_status` và `error`. Như vậy đếm vẫn khớp, và `docs/data_dictionary.md` ghi rõ tỉ lệ có tên.

`docs/crawl_full.md` liệt kê **mọi** dòng, có thể dài 19.000 dòng. Commit phần tóm tắt đầu và cuối file là đủ: `head -6` + `tail -5`. Không cần commit cả bảng.

### 4.5 Checkpoint 11b — đẩy `products` lên VM + CSV

Máy cá nhân cần MongoDB Database Tools (`mongodump`, `mongorestore`, `mongoexport`). Tải bản Ubuntu 24.04 x86_64 `.tgz` ở mongodb.com/try/download/database-tools, giải nén, copy `bin/*` vào `~/.local/mongodb/bin/`.

```bash
# máy cá nhân
~/.local/mongodb/bin/mongoexport --uri mongodb://127.0.0.1:27017 --db glamira --collection products \
  --type csv --fields _id,product_id,name,category,price,image_url,url,source_url,http_status,error,crawled_at \
  --out data/exports/products.csv
~/.local/mongodb/bin/mongodump --uri mongodb://127.0.0.1:27017 --db glamira --collection products \
  --gzip --archive=data/exports/products.archive.gz
source infra/gcp/lib.sh
gcloud storage cp data/exports/products.csv data/exports/products.archive.gz "gs://$GCS_BUCKET/exports/"
```

Như ở bước IP, xem một document `products` trước để `--fields` đúng tên.

Trên VM:

```bash
gcloud storage cp "gs://<bucket>/exports/products.archive.gz" data/exports/
mongorestore -u glamira_app -p --authenticationDatabase admin \
  --gzip --archive=data/exports/products.archive.gz --nsInclude 'glamira.products' --drop
mongosh -u glamira_app -p --authenticationDatabase admin glamira \
  --eval 'print(db.products.countDocuments({}))'
```

`--drop` chỉ xóa collection `products` trên VM rồi nạp lại bản local. Không đụng `glamira_raw`.

### 4.6 Checkpoint 11c — data dictionary

Cập nhật `docs/data_dictionary.md`. Hiện là bản Pha 0. Thêm:

- `glamira_raw`: giữ bảng field theo event (đã có), thêm danh sách index.
- `ip_geo`: `_id` (chuỗi IP), `status` (`ok`, `not_found`, `private`, `ipv6`, `invalid`), `country_code`, `country_name`, `region`, `city`, `events` (số event của IP), `lookup_at`. Nguồn DB3 ngày 2016-11-29: nước tin được, thành phố gần đúng, không có lat/long. Coach gợi ý LITE-DB5. File được giao là DB3.
- `products`: `_id` (= `product_id` dạng chữ), `product_id`, `name`, `category`, `price`, `image_url`, `description`, `url` (trang đã mở thật, có thể là URL catalog), `source_url` (URL trong seed), `http_status`, `error`, `crawled_at`. Một số document có thêm `currency`, `material`: liệt kê hết bằng cách gom key trên toàn collection trước khi viết. Tỉ lệ có tên = named / 19.093.
- Cách join: `glamira_raw.ip = ip_geo._id`; `product_id` (hoặc `cart_products[].product_id` với `checkout_success`) `= products._id`.
- Lỗi chất lượng đã biết: link sang `docs/data_quality_report.md`.

**Commit + push checkpoint 11:**

```bash
git add docs/data_dictionary.md docs/crawl_full.md docs/gcp_evidence.md
git commit -m "feat: finish the product crawl and data dictionary (checkpoint 11)"
git push origin main
```

---

## 5. Tắt VM, chi phí, dọn dẹp

Tắt ngay sau mỗi lần làm. Coach nhắc rõ: tắt VM để khỏi cháy credit.

```bash
source infra/gcp/lib.sh
gcloud compute instances stop  "$VM_NAME" --zone="$GCP_ZONE"
gcloud compute instances start "$VM_NAME" --zone="$GCP_ZONE"   # khi cần lại
```

Sau khi `start`, IP public **có thể đổi** (IP ephemeral). Chạy lấy IP mới:

```bash
gcloud compute instances describe "$VM_NAME" --zone="$GCP_ZONE" \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
```

Chi phí ước lượng, giá công bố có thể đổi theo thời điểm, kiểm tra ở Console → Billing:

| Thứ | Khi chạy | Khi VM tắt |
|---|---|---|
| `e2-standard-4` asia-southeast1 | ~0,15 USD/giờ | 0 |
| Đĩa 100 GB pd-balanced | ~10–12 USD/tháng | vẫn tính |
| GCS ~6 GB Standard | ~0,15 USD/tháng | vẫn tính |

Cả Pha 1 + 2 trên VM khoảng 3–5 giờ máy chạy, tức dưới 1 USD tiền compute. Phần đắt nhất là để VM chạy rồi quên tắt.

Sau khi coach chấm xong và chưa cần cho Project 06:

```bash
gcloud compute instances delete "$VM_NAME" --zone="$GCP_ZONE"   # xóa cả đĩa boot
gcloud compute firewall-rules delete glamira-mongo-from-my-ip
# GIỮ bucket nếu Project 06 dùng GCS/BigQuery
```

---

## 6. Git: mỗi checkpoint một commit, push ngay

Quy tắc:

1. Chạy test trước mỗi commit: `uv run python -m unittest discover -s tests`.
2. `git status` trước `git add`. Không bao giờ `git add .` khi có `data/`, `.env`, `infra/gcp/gcp.env` gần đó. `.gitignore` đã chặn, nhưng kiểm tra bằng mắt vẫn tốt hơn.
3. Mỗi commit một ý, message dạng `type: việc đã xong (checkpoint N)`.
4. `git push origin main` ngay sau commit, để coach xem từng mốc.

| Checkpoint | Commit | Trạng thái |
|---|---|---|
| 1 | `d837bdf feat: stream the Glamira mongodump for Phase 0 profiling` | đã push |
| 1–2 | `5db7803 docs: record the full-scan null profile and quality report` | đã push |
| 3 | `901bc21 docs: propose GO for IP lookup and product crawl` | đã push |
| 5, 7, 8 (local) | `1ebe312 feat: load events into local Mongo and resolve IPs` | đã push |
| 9, 10 | `e83b8f0 feat: upload prj` | đã push |
| — | `fix: let crawl --limit 0 read the whole seed` | commit cùng file này |
| 4, 6 (hạ tầng) | `feat: add GCP scripts for bucket, Mongo VM and firewall` | commit cùng file này |
| — | `docs: write the step-by-step GCP implementation guide` | commit cùng file này |
| 4 | `docs: record GCP project and bucket smoke upload (checkpoint 4)` | bạn làm |
| 6 | `docs: record Mongo VM reachable from my machine (checkpoint 6)` | bạn làm |
| 7 | `docs: record 41,432,473 events loaded on the GCP Mongo VM (checkpoint 7)` | bạn làm |
| 8 | `feat: resolve IPs on the GCP Mongo VM and record coverage (checkpoint 8)` | bạn làm |
| 9 | `docs: record product url seed from VM (checkpoint 9)` | bạn làm, nếu số khác |
| 11 | `feat: finish the product crawl and data dictionary (checkpoint 11)` | bạn làm |
| handoff | `docs: hand off sources to Project 06` | sau cùng |

---

## 7. Danh sách nộp (đối chiếu coach)

| Coach yêu cầu | File / nơi |
|---|---|
| Script khám phá Pha 0 | `src/stream/`, `src/explore/` |
| `data_quality_report.md` | `docs/data_quality_report.md` |
| `scope_confirmation.md` | `docs/scope_confirmation.md` |
| GCP + bucket | `infra/gcp/01_project.sh`, `02_bucket.sh`, bằng chứng `docs/gcp_evidence.md` |
| VM MongoDB 41 triệu dòng | `infra/gcp/04_vm.sh`, `vm/install_mongo.sh`, `countDocuments` trong evidence |
| Script nạp có đếm | `src/ingest/load_mongo.py` |
| Script IP + CSV | `src/enrich/ip_lookup.py`, `docs/ip_coverage.md`, `gs://…/exports/ip_geo.csv` |
| Script crawl + CSV | `src/enrich/crawl.py`, `gs://…/exports/products.csv` |
| Data dictionary | `docs/data_dictionary.md` |
| README, `.gitignore` sạch | `README.md`, `.gitignore` (chặn `data/`, `.env`, `gcp.env`, `*.BIN`, `*.tar.gz`) |

---

## 8. Kiểm tra nhanh trước khi báo coach

```bash
git status                                   # sạch
git log --oneline | head -15                 # mỗi checkpoint một dòng
git ls-files | grep -E '\.env$|gcp\.env$|\.BIN$|\.tar\.gz$|^data/' || echo "không có file cấm trong git"
uv run python -m unittest discover -s tests  # OK
```

Trên VM:

```bash
mongosh -u glamira_app -p --authenticationDatabase admin glamira --eval '
["glamira_raw","ip_geo","products"].forEach(c => print(c, db[c].countDocuments({})))'
```

Kỳ vọng: `glamira_raw 41432473`, `ip_geo 3239628`, `products 19093`.

Xong thì **tắt VM**.
