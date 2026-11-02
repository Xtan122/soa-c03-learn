# LAB 08 — RDS Multi-AZ + failover + RTO

```text
LAB: 08 — RDS Multi-AZ + failover + RTO
SERVICE: RDS (Multi-AZ), ALB, EC2 app, CloudWatch
DATE: 2026-10-31
DOMAIN: D2 Reliability 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
SOLUTION_USED: yes (user yêu cầu rõ "check và viết lại hộ tôi"; bản gốc giữ ở note.draft-2026-11-01.md)
HINTS_USED: 0
```

## 1. What did I build?

App stack + RDS `soa-c03-db` chuyển từ single-AZ sang **Multi-AZ**.

```text
User → ALB → EC2 app → soa-c03-db.ch8q4oyqg4cb.ap-southeast-1.rds.amazonaws.com
                                 │
                        Primary (ap-southeast-1a)
                                 │ sync
                        Standby (AZ khác)
```

`./bin/lab up 08` đưa DB về Multi-AZ: `Status=available`, `MultiAZ=true`, primary `ap-southeast-1a`.
Chuyển đổi mất ~8 phút (17:41:19Z bắt đầu apply → 17:47:21Z MultiAZ=true → 17:49:24Z available).

## 2. What failed? (symptom, not root cause)

Trong **12 giây**, mọi request `GET /db` trả **503**: 4 khách bị từ chối
(17:59:16Z, 17:59:22Z, 17:59:24Z, 17:59:26Z). Trước và sau đó là `200` (~0.33s).

- `/health` vẫn `200` suốt thời gian này — **chỉ đường có truy vấn DB mới hỏng**.
- Endpoint **không đổi** tên trong suốt sự cố.
- Người dùng thấy lỗi, không thấy cảnh báo nào (không alarm nào kêu).

## 3. How did I detect it? (metric/log/event/CLI)

Bằng **dòng thời gian tự đo**, không bằng cảm giác:

```bash
# vòng lặp 2 giây/lần, chạy trước khi break, log lại giờ + mã HTTP
while true; do printf "%s %s\n" "$(date -u +%H:%M:%SZ)" \
  "$(curl -s -o /dev/null -m 5 -w '%{http_code} %{time_total}s' http://<alb>/db)"; sleep 2; done
```

Lưu tại `evidence/rto-probe-2026-10-31.log` (485 dòng).

Đối chiếu 3 nguồn độc lập:

| Nguồn | Dữ liệu |
|---|---|
| Log curl (phía khách) | 4 × `503` trong 12s, rồi `200` trở lại |
| RDS Events (phía AWS) | `failover started` 17:59:16 → `restarted` 17:59:28 → `failover completed` 17:59:44 |
| CloudWatch (ALB) | `HTTPCode_ELB_5XX_Count = 0` · `HTTPCode_Target_5XX_Count = 4` @17:59Z |
| describe-db-instances | AZ đổi `ap-southeast-1a` → `ap-southeast-1b` |

`curl` gọi **ALB**, không gọi trực tiếp DB. Chuỗi là `curl → ALB → app → DB`; lỗi ở lớp sau cùng nhưng mã lỗi do lớp giữa sinh ra.

## 4. Root cause (the actual broken layer)

**Lớp availability của DB.** Failover được yêu cầu lúc 17:59:10Z: RDS hạ primary ở
`ap-southeast-1a` và nâng standby ở `ap-southeast-1b` thành primary mới.

Trong lúc chuyển vai, các connection TCP đang mở tới DB cũ bị đứt. App
(`platform/app/app.py:251`) không query được DB nên trả **503** cho khách; ALB vẫn
khoẻ, vẫn có target healthy, nên **không** tự sinh lỗi — bằng chứng là
`ELB_5XX = 0` trong khi `Target_5XX = 4`.

Phân biệt 2 câu hỏi:
- **Ai sinh mã 503** → app (lớp ứng dụng).
- **Ai gây ra** → DB (lớp availability).

## 5. How did I fix it? (exact command or console action)

**Không phải sửa gì** — Multi-AZ tự phục hồi, đây là thiết kế đúng:

```text
17:59:16Z  failover started
17:59:28Z  app trả 200 trở lại  (RTO người dùng = 12 giây)
17:59:44Z  RDS báo "failover completed" (28.7 giây)
```

App sống lại **trước khi** RDS tuyên bố failover xong, vì standby đã sẵn sàng nhận
connection trước khi tiến trình failover đóng sổ.

Kiểm chứng: `./bin/lab verify 08` → **PASS** lúc 2026-10-31T18:14:14Z
(`MultiAZ=True status=available failoverEvent=yes app/db=200`).

## 6. Prevention / automation

Alarm hiện có **không bắt được** sự cố này — 3 lỗ hổng thật, kiểm bằng lệnh:

```bash
aws cloudwatch describe-alarms --query 'MetricAlarms[].[AlarmName,MetricName,Threshold]'
aws rds describe-event-subscriptions
```

| # | Lỗ hổng | Sửa |
|---|---|---|
| 1 | `soa-c03-alb-5xx` đo `HTTPCode_ELB_5XX_Count`, mà metric này = **0** trong sự cố | Đổi sang `HTTPCode_Target_5XX_Count` (hoặc cả hai) — lỗi do app sinh ra |
| 2 | Ngưỡng `5` lỗi/phút, thực tế chỉ có **4** | Hạ ngưỡng về `1`; hoặc alarm trên **tỷ lệ 5XX / RequestCount** thay vì số tuyệt đối |
| 3 | **Không có RDS event subscription** | Tạo subscription → SNS `soa-c03-alerts` cho category `failover`, `failure`, `availability` để có bản ghi mỗi lần failover |

Bổ sung ngoài alarm:
- App nên **retry + reconnect** với backoff khi mất connection (giảm 12s xuống vài giây).
- Dashboard có panel **RTO đo được** (synthetic canary gọi `/db` mỗi 30s) thay vì tin vào "failover completed".
- Diễn tập failover định kỳ (game day) để biết RTO thật của hệ thống mình, không tin con số lý thuyết của tài liệu AWS.

## 7. Exam trap

- **Multi-AZ ≠ Read Replica.** Multi-AZ: standby **đồng bộ**, không phục vụ read, tự failover, mục đích **HA**. Read Replica: **bất đồng bộ**, có phục vụ read, **không** tự thăng cấp primary, mục đích **scale đọc**.
- **Failover không đổi endpoint.** Tên DNS giữ nguyên; cái đổi là bản ghi DNS trỏ sang máy mới, và các connection đang mở bị đứt.
- **`503` ở đây không phải ALB hỏng.** Đọc `ELB_5XX` vs `Target_5XX` để biết ai sinh lỗi.
- **Đừng nhầm RTO với thời gian "failover completed".** Người dùng hết lỗi sau **12s**, RDS báo xong sau **28.7s**.
- **Standby chết không làm sập dịch vụ**, nhưng mất lưới an toàn: nếu primary chết lúc đó, downtime là hàng chục phút chứ không phải 12 giây.
- Multi-AZ **không thay thế** backup và DR cross-region — nó chỉ chống hỏng 1 AZ.
