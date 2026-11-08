# MongoDB từ zero đến hero, cho project này

Câu trả lời ngắn: **không**. Dữ liệu đã nằm trên đĩa, nhưng mở MongoDB Compass một mình thì chưa xem được.

Có ba thứ khác nhau. Cả ba phải đúng chỗ thì mới thấy document.

| Thứ | Là gì | Ở project này |
|---|---|---|
| File trên đĩa | Dữ liệu đã ghi | Thư mục `data/mongo`. Xóa thư mục này là mất dữ liệu. |
| `mongod` | Chương trình server. Nó mở các file đó và nghe ở một cổng mạng. | `127.0.0.1:27017`. Terminal chạy lệnh này phải còn mở. |
| Compass | App để xem. Nó không đọc file. Nó nói chuyện với `mongod`. | Kết nối `mongodb://127.0.0.1:27017` |

PostgreSQL hoạt động cùng kiểu này. pgAdmin hay DBeaver không mở thư mục data của Postgres. Chúng nối tới tiến trình server `postgres`, thường nghe cổng `5432`. Trên nhiều máy, gói cài đăng ký Postgres thành dịch vụ: bật máy là server tự chạy, nên mở app là thấy dữ liệu. Mongo trên máy này là binary tự giải nén, không đăng ký dịch vụ, nên tắt terminal là server tắt. File trong `data/mongo` vẫn còn. Compass không đọc các file đó.

## 1. Bật server

Mở một terminal, đứng ở thư mục gốc repo:

```bash
cd /home/loclt/workspace/unigap_course/projects/project05
mkdir -p data/mongo
~/.local/mongodb/bin/mongod \
  --dbpath data/mongo \
  --bind_ip 127.0.0.1 \
  --port 27017 \
  --wiredTigerCacheSizeGB 1
```

Ý từng cờ:

| Cờ | Việc nó làm |
|---|---|
| `--dbpath data/mongo` | Bảo server đọc và ghi đúng thư mục đã có dữ liệu. |
| `--bind_ip 127.0.0.1` | Chỉ máy này vào được. Máy khác trong mạng không vào. |
| `--port 27017` | Cổng Compass sẽ gõ. 27017 là cổng mặc định của MongoDB. |
| `--wiredTigerCacheSizeGB 1` | Giới hạn RAM cache khoảng 1 GB để khỏi chiếm hết máy. |

Đợi log có dòng:

```text
"msg":"Waiting for connections","attr":{"port":27017,"ssl":"off"}
```

Đó là lúc xem được. Dòng chữ `error` xuất hiện lúc khởi động thường là cấu hình nội bộ của engine WiredTiger, không phải server hỏng. Cứ đợi dòng `Waiting for connections`.

Terminal này phải để mở. Đóng cửa sổ hoặc nhấn Ctrl+C là server tắt. Compass sẽ báo không kết nối được. Dữ liệu không mất.

Máy này không đặt user và mật khẩu. URI không có `user:pass`.

## 2. Mở Compass

1. Mở ứng dụng MongoDB Compass.
2. Ô URI điền `mongodb://127.0.0.1:27017`.
3. Bấm Connect.
4. Cột trái xuất hiện database `glamira`. Bấm vào đó.
5. Ba collection: `glamira_raw`, `ip_geo`, `products`. Bấm một cái để thấy document.

Nếu Connect báo `ECONNREFUSED` hoặc `server selection timeout`, `mongod` đang tắt. Quay lại mục 1. Không cần chạy lại lệnh nạp dữ liệu.

## 3. Tắt server cho sạch

Trong terminal đang chạy `mongod`, nhấn Ctrl+C. Đợi dòng `mongod shutdown complete`. Rồi mới đóng terminal. Đừng `kill -9` nếu còn cách tắt bằng Ctrl+C. Đừng xóa `data/mongo`.

## 4. Từ cần nắm, gắn với dữ liệu thật

### Server và client

`mongod` là server. Compass và Python (`pymongo`) là client. Client gửi câu hỏi, server đọc file và trả document. Code trong `src/db.py` cũng là một client: nó nối `MONGO_URI` trong `.env`.

### Database

Một database là một nhóm collection. Project này chỉ dùng database tên `glamira`. Trên cùng server có thể có database khác. Đừng tìm dữ liệu Glamira ở database `admin` hay `local`. Đó là database hệ thống.

### Collection

Một collection là một tập document cùng một vai trò. Nó gần với một bảng, nhưng các document không bắt buộc có cùng các field.

| Collection | Một document là | `_id` |
|---|---|---|
| `glamira_raw` | Một event hành vi trong file dump | ObjectId gốc của event |
| `ip_geo` | Một địa chỉ IP đã phân loại | Chuỗi IP, ví dụ một IPv4 public |
| `products` | Một sản phẩm đã mở trang | `product_id` dạng chuỗi, ví dụ `"102002"` |

### Document và field

Một document là một bản ghi dạng JSON. Field là một key trong đó.

Ví dụ một document rút gọn trong `products`:

```json
{
  "_id": "102002",
  "product_id": "102002",
  "name": "14K Yellow Gold Round Diamond Ring Loronda",
  "price": "2188.75",
  "currency": "USD",
  "http_status": 200
}
```

`_id` là khóa. Hai document trong cùng một collection không được trùng `_id`. Project này tự đặt `_id`, không để Mongo tự sinh cho event và cho sản phẩm. Nhờ vậy chạy lại lệnh nạp không nhân đôi event: bản trùng bị bỏ qua.

### Field tên `collection` không phải collection của Mongo

Trong `glamira_raw`, mỗi event có field `collection` với giá trị như `view_product_detail` hoặc `checkout_success`. Đó là **loại hành vi** do hệ thống tracking ghi. Tên collection Mongo chứa các event đó là `glamira_raw`.

Tìm event xem chi tiết sản phẩm thì filter field, không đổi sang một collection khác:

```json
{ "collection": "view_product_detail", "product_id": "100045" }
```

### Filter

Ô Filter ở đầu danh sách document nhận một document JSON. Nó nghĩa là "chỉ hiện document khớp các field này".

Bằng đúng một giá trị:

```json
{ "product_id": "100045" }
```

`product_id` trong log là chuỗi. Gõ số không có ngoặc kép, `{ "product_id": 100045 }`, thường ra rỗng vì kiểu không khớp.

Nhiều điều kiện cùng lúc thì ghi cạnh nhau. Mongo hiểu là AND:

```json
{ "collection": "checkout_success" }
```

Đếm nhanh: tab Aggregations, hoặc nhìn dòng `1-20 of N` sau khi Find. Với 41 triệu document, filter trên field chưa có index sẽ lâu. Các index đã tạo trên `glamira_raw` gồm `collection`, `time_stamp`, `ip`, `product_id`, `viewing_product_id`.

### Index

Index là mục lục. Nó không đổi nội dung document. Filter đúng field đã có index thì nhanh. Tạo index xong mới có tác dụng cho các câu tìm sau, không làm thay đổi số document.

### Join ở project này không phải một câu SQL

Mongo không tự nối ba collection thành một bảng. Cách project này thiết kế:

- Nước của một event: lấy `glamira_raw.ip`, tìm `ip_geo` có `_id` bằng chuỗi IP đó.
- Tên sản phẩm: lấy `product_id`, tìm `products` có `_id` bằng chuỗi đó.

Trong Compass, làm bằng hai lần Find. Dashboard sau này sẽ join. Project 05 chỉ chuẩn bị hai bảng tra.

## 5. Bên trong `data/mongo` là gì

Đó là file của engine WiredTiger (`*.wt`, `WiredTiger`, journal). Người không mở các file này bằng editor. Chúng không phải JSON. Compass và `mongod` mới đọc được. Sửa hoặc xóa một file `.wt` có thể làm hỏng cả database.

## 6. Ba collection, field nên biết

### `glamira_raw` — 41.432.473 document

Mỗi document là một event. Field có mặt tùy loại event. Đây là schema-on-read: không ép mọi event có cùng form.

| Field | Cách hiểu |
|---|---|
| `_id` | ObjectId gốc. Khóa để nạp lại không trùng. |
| `collection` | Loại event, không phải tên collection Mongo. |
| `time_stamp` | Giây Unix, UTC. Mốc thời gian đúng. Khoảng đo được: 2020-04-01 đến 2020-06-04. |
| `local_time` | Giờ trên chuỗi, không đáng tin để tính doanh thu. |
| `ip` | Chuỗi IP. Chưa có tên nước. |
| `product_id` | Có ở event xem sản phẩm. Kiểu chuỗi. |
| `current_url` | URL store lúc đó, thường kèm query (`?alloy=...`). |
| `cart_products` | Có ở checkout. `product_id` và `price` nằm trong từng phần tử. |
| `order_id` | Có giá trị ở `checkout_success`. |

Đừng cộng `price` của nhiều loại tiền. Đừng dùng `cat_id` làm category. Đừng lấy `viewing_product_id` làm id sản phẩm đang xem: field đó chủ yếu là id gợi ý.

### `ip_geo` — 3.239.628 document

| Field | Cách hiểu |
|---|---|
| `_id` | Chuỗi IP. |
| `status` | `ok`, `not_found`, `private`, `ipv6`, `invalid`. |
| `country_code`, `country_name`, `region`, `city` | Kết quả file BIN 2016. Chỉ IP public IPv4 được tra. |
| `events` | Số event mang IP đó. |

### `products` — những sản phẩm đã crawl, chưa đủ 19.093

| Field | Cách hiểu |
|---|---|
| `_id`, `product_id` | Id sản phẩm, chuỗi. |
| `source_url` | URL lấy từ log, URL thử đầu tiên. |
| `url` | URL thực sự lấy được tên. Có thể là `source_url`, hoặc đường dẫn dự phòng `https://www.glamira.com/catalog/product/view/id/<product_id>` khi trang đầu 404. |
| `name`, `category`, `description`, `image_url` | Nội dung trang. |
| `price`, `currency` | Giá và mã tiền của đúng trang đó. `USD` và `GBP` không được cộng vào nhau. |
| `brand`, `sku`, `material`, `color` | Hãng, mã biến thể trang đang mở, chất liệu, màu đá. |
| `availability`, `gtin`, `mpn`, `weight` | Còn hàng, mã vạch, mã nhà sản xuất, khối lượng. Trang nào không có thì field trống. |
| `http_status` | `200` mở được. `404` không có trang. `0` Chrome không tải được. |
| `error` | Lỗi kết nối, hoặc ghi nhận đường dẫn dự phòng cũng không ra tên. |
| `crawled_at` | Thời điểm UTC lúc ghi. |

Document `http_status` 404 và `name` trống là sản phẩm crawl chưa lấy được tên. Lần chạy sau sẽ thử lại những id đó.

## 7. Năm câu tự gõ trong Compass

`mongod` phải đang ở trạng thái Waiting for connections.

1. Vào `glamira_raw`, filter `{ "product_id": "100045" }`. Đây là các event của một sản phẩm. Nhìn `current_url`: host là store gốc, có query string.
2. Vào `products`, filter `{ "_id": "102002" }`. Đây là trang đã crawl. So `source_url` với `url`.
3. Vào `ip_geo`, filter `{ "status": "ok" }`. Mở một document, thấy `country_code`.
4. Lấy giá trị `ip` của một event ở bước 1. Sang `ip_geo`, filter `{ "_id": "<dán chuỗi ip>" }`. Đó là cách join bằng tay.
5. Vào `glamira_raw`, filter `{ "collection": "checkout_success" }`. Mở `cart_products` để thấy giá nằm trong line item, không nằm ở field top-level `price`.

## 8. Python nối vào cùng server đó

Code không nhúng dữ liệu trong repo. `src/db.py` đọc `MONGO_URI=mongodb://127.0.0.1:27017/` từ `.env`, rồi `MongoClient` ping server. Nếu `mongod` tắt, lệnh `uv run python -m src.cli ...` báo không chọn được server, dù `data/mongo` vẫn còn file.

Thứ tự đúng khi làm việc:

1. Bật `mongod`, đợi Waiting for connections.
2. Mở Compass nếu muốn xem.
3. Chạy lệnh Python nếu muốn nạp hoặc crawl. Crawl ghi vào `products` khi server đang chạy.
