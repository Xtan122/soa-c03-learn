# Lab 08 — RDS Multi-AZ + failover + RTO

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D2 Reliability 22% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Trung bình |
| Lab ID | `08` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học Multi-AZ thực sự làm gì khi failover: endpoint có đổi không, app có timeout không, đo RTO.
- **Việc đầu tiên:** Ô **Search** → `RDS` → **Databases** → bấm `soa-c03-db`.
- **Xong khi:** `verify 08` PASS: `MultiAZ=True`, DB `available`, có event failover, `/db` = 200.
- **Nếu lạc:** `./bin/lab console 08` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học Multi-AZ thực sự làm gì khi failover: endpoint có đổi không, app có timeout không, đo RTO.

## 2. Hiện tại có gì?

App stack + RDS chạy. `up 08` chuyển DB sang Multi-AZ; `break 08` yêu cầu failover.

## 3. Kiến trúc

```text
App EC2 → RDS endpoint (không đổi)
                 │
        ┌────────┴────────┐
        ▼                 ▼
     Primary           Standby
     (AZ A)            (AZ B)
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/08-*/README.md` (file này) và dòng lab `08` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 08
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 08
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 08
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 08
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 08
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 08
   ```

## 5b. Ghi chú / lệnh riêng

Multi-AZ tốn gấp đôi compute/storage. `down 08` sẽ đưa về single-AZ.

<!-- console-guide:start -->
## 5c. Console — bấm ở đâu, thấy gì

> **Trước khi bấm:** mở https://console.aws.amazon.com/ và đăng nhập **đúng account lab**
> (không dùng account cá nhân). Kiểm tra region góc trên phải là **Singapore (ap-southeast-1)**.
> Console AWS dùng tiếng Anh; nhãn trong bài là nhãn tiếng Anh.
> **Đường bấm** là nguồn chính; **link nhanh** chỉ là shortcut và có thể đổi khi AWS cập nhật giao diện.
> **Cách AI dạy:** mỗi lượt chỉ một màn hình và một nút. Bạn bấm xong, mô tả bạn thấy gì;
> AI mới đi tiếp. Đừng làm cả danh sách bước một lúc.
> Nhãn tiếng Anh khó hiểu? Tra bảng nút ở [`docs/console-guide.md`](../../docs/console-guide.md) mục 2e.

### Từ vựng nhanh (đọc trước)

| Thuật ngữ | Nghĩa đời thường |
|---|---|
| Multi-AZ | Một primary + một standby đồng bộ ở AZ khác. |
| Failover | Chuyển vai primary sang standby. |
| Endpoint | DNS name giữ nguyên qua failover. |
| RTO | Thời gian downtime thực tế. |
| Read replica | Bản sao chỉ đọc, khác Multi-AZ. |

### Khái niệm của lab này

- **Multi-AZ** tạo một standby đồng bộ ở AZ khác.
- Khi failover, DNS endpoint **không đổi**; RDS chuyển vai primary/standby.
- Vì vậy app phải reconnect, và bạn đo **RTO** bằng thời gian từ lúc reboot đến khi `/db` trả 200.

### Đường bấm từng bước

1. Ô **Search** → `RDS` → **Databases** → bấm `soa-c03-db`.
2. Tab **Configuration**: mục **Availability and durability** → **Multi-AZ** phải là **Yes**; xem **Primary AZ**.
3. Tab **Monitoring**: xem CPU, connections, read/write latency trong 1h.
4. Menu trái **Events** (hoặc tab **Events** của DB): lọc theo DB instance, tìm event failover.
5. Để đo RTO: mở terminal chạy `while true; do curl -s -o /dev/null -w '%{http_code} %{time_total}
' http://<alb>/db; sleep 2; done`.
6. Quay lại DB → **Actions** → **Reboot** → tick **Reboot with failover?** (nếu có) → confirm.
7. Đọc chuỗi status code cho tới khi `200` trở lại.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Multi-AZ | `Yes` nghĩa là có standby. |
| Primary AZ / Secondary AZ | Hai AZ khác nhau chứng minh HA thật. |
| DB status | `rebooting` → `available`. |
| RDS event | Câu chữ chứa `failover` và thời điểm. |
| Chuỗi HTTP code | Các dòng 000/502/503 xen giữa là downtime. |
| Thời gian tới 200 | Đó là RTO bạn đo được, không phải con số lý thuyết. |

### Link nhanh

- [RDS databases](https://console.aws.amazon.com/rds/home?region=ap-southeast-1#databases:)
- [RDS events](https://console.aws.amazon.com/rds/home?region=ap-southeast-1#events:)

### Nếu không thấy mục đó

- Multi-AZ vẫn `No`: `up 08` có thể chưa chạy xong; modification có thể mất 10–12 phút.
- Không thấy event failover: mở rộng time range; event có thể trễ vài phút.
- `/db` vẫn lỗi sau failover: kiểm tra SG/subnet và app có tự reconnect không.
- Nhớ `./bin/lab down 08` để trả về single-AZ, tránh tốn gấp đôi.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học Multi-AZ thực sự làm gì khi failover: endpoint có đổi không, app timeout bao lâu, đo RTO.

### Bạn cần biết 4 khái niệm

- **Multi-AZ**: Một primary và một standby đồng bộ ở AZ khác.
- **Failover**: Chuyển vai primary sang standby.
- **Endpoint**: DNS name giữ nguyên qua failover.
- **RTO**: Thời gian downtime thực tế.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| RDS | soa-c03-db | available | RDS → Databases |
| Multi-AZ | No trước up 08, Yes sau up | Yes khi làm lab | RDS → Configuration |
| App | soa-c03-app | /db 200 | ./bin/lab status |
| RDS events | soa-c03-db | có event failover sau break | RDS → Events |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| MultiAZ bật chưa? | RDS → Configuration | Availability and durability |
| Có failover? | RDS → Events | event chứa failover |
| App reconnect? | curl /db | HTTP status |
| RTO? | đo từ reboot tới 200 | số giây |

### Trước khi phá, bạn phải trả lời 3 câu

1. Multi-AZ khác Read Replica ở đâu?
2. Failover có đổi endpoint không?
3. Bạn đo RTO bằng gì?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 08 --live` và `./bin/lab teach 08`.

## 6. Hiện tượng bạn sẽ thấy

DB failover. App có thể timeout vài chục giây; endpoint DNS vẫn giữ nguyên.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| MultiAZ đã bật chưa? | `aws rds describe-db-instances --db-instance-identifier soa-c03-db` |
| Có event failover không? | `aws rds describe-events --source-identifier soa-c03-db` |
| App có kết nối lại không? | `curl http://<alb>/db` |
| RTO là bao lâu? | Đo từ lúc reboot đến khi `/db` = 200 |

## 8. Thành công trông như thế nào?

`verify 08` PASS: `MultiAZ=True`, DB `available`, có event failover, `/db` = 200.

Nếu FAIL, đọc:

```bash
cat labs/08-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Multi-AZ vs Read Replica: sync/HA vs async/scale đọc.
- Endpoint không đổi khi failover.
- Failover không thay thế backup/DR cross-region.

## 10. Note mẫu

- 1. Failover mất bao lâu?
- 2. App có tự reconnect không?
- 3. Multi-AZ khác Read Replica ở đâu?

## 11. Cleanup

```bash
./bin/lab down 08
make cost
```

Nếu hết buổi:

```bash
make app-down
make inventory
make cost
```

- Lab này có resource riêng; `down` sẽ dọn. Nếu đã dùng `reset`, ghi `SOLUTION_USED: yes` vào note.

## 12. Nếu bí

```bash
./bin/lab hint 08
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 08. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
