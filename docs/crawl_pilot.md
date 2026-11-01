# Crawl pilot

Limit: 3. Rate: 1.0 request/s.

| product_id | status | parsed | url |
|---|---:|---|---|
| `100000` | 403 | False | `https://www.glamira.co.uk/glamira-ring-lucetta.html` |
| `100001` | 403 | False | `https://www.glamira.co.uk/glamira-ring-orva.html` |
| `100002` | 403 | False | `https://www.glamira.co.uk/glamira-ring-palmier.html` |

Attempted 3. HTTP 200: 0. Name parsed: 0 (0.00%).

Dừng ở 3 request. Cả ba đều `403 Forbidden` từ nginx/Akamai, kể cả khi gọi bằng curl và httpx. Scope nói dừng nếu site từ chối, nên không gửi tiếp 97 request. Parser đã có test trên HTML giả lập. Chạy lại `enrich crawl --limit 100` từ mạng mà site cho vào.
