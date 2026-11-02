# Lab 20 — Incident: CPU 95% + 5xx + ALB

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D1/D2/D5 |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `20` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Đây là incident tổng hợp: CPU cao, app trả 500, ALB có thể 503. Bạn phải tách symptom khỏi root cause.
- **Việc đầu tiên:** Ô **Search** → `CloudWatch` → **Metrics** → **EC2** → tick `CPUUtilization` của instance; time range **1h**, xem Average/Maximum.
- **Xong khi:** `verify 20` PASS: CPU giảm, `/health` và `/db` = 200, target healthy.
- **Nếu lạc:** `./bin/lab console 20` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Đây là incident tổng hợp: CPU cao, app trả 500, ALB có thể 503. Bạn phải tách symptom khỏi root cause.

## 2. Hiện tại có gì?

App stack chạy. `break 20` tạo CPU load, 20 lỗi 500 và vài request chậm.

## 3. Kiến trúc

```text
Client → ALB → EC2 app
                    ├── CPU 95%
                    ├── HTTP 500
                    └── latency cao
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/20-*/README.md` (file này) và dòng lab `20` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 20
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 20
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 20
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 20
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 20
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 20
   ```


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
| Symptom | Cái người dùng thấy: chậm, 500, 503. |
| Root cause | Lớp thật sự hỏng. |
| 5xx | Lỗi server/ALB. |
| Latency | Thời gian phản hồi. |
| Triage | Ưu tiên kiểm tra theo thứ tự user-facing trước. |

### Khái niệm của lab này

- Incident có nhiều **symptom** cùng lúc: CPU cao, 5xx, chậm.
- Symptom không phải root cause.
- Đi từ user-facing path (`/health`, ALB) xuống target, instance, process, log, DB.
- Scale out có thể che symptom nhưng không chứng minh đã sửa gốc.

### Đường bấm từng bước

1. Ô **Search** → `CloudWatch` → **Metrics** → **EC2** → tick `CPUUtilization` của instance; time range **1h**, xem Average/Maximum.
2. **Alarms** → **All alarms** → filter prefix `soa-c03`: xem state và history.
3. Ô **Search** → `EC2` → **Target groups** → `soa-c03-tg` → **Targets**: healthy/unhealthy.
4. **CloudWatch** → **Logs Insights** → log group app → query:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | sort @timestamp desc
   | limit 50
   ```
5. **CloudWatch** → **Metrics** → **RDS** → CPU/connections của `soa-c03-db`.
6. Terminal: `curl -i http://<alb>/health`, `/db`, `/slow?ms=1000`.
7. Nếu cần process: **Systems Manager** → **Run Command** → `top -b -n1` và `ps aux --sort=-%cpu`.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| CPU timeline | CPU tăng đúng lúc symptom bắt đầu hay từ trước? |
| Alarm history | Alarm nào kêu trước, alarm nào kêu sau. |
| Target health | Nếu unhealthy, lỗi ở network/app; nếu healthy, lỗi có thể ở app/DB. |
| Log ERROR | Thông điệp lỗi thật và timestamp. |
| RDS metrics | CPU/connections có tăng bất thường không. |
| HTTP code từng endpoint | Tách `/health` (app sống) khỏi `/db` (đường DB). |

### Link nhanh

- [CloudWatch metrics](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#metricsV2:)
- [CloudWatch alarms](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#alarmsV2:alarms)
- [Target groups](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#TargetGroups:)
- [Logs Insights](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:logs-insights)
- [RDS databases](https://console.aws.amazon.com/rds/home?region=ap-southeast-1#databases:)

### Nếu không thấy mục đó

- CPU đã giảm nhưng vẫn 5xx: CPU có thể là hậu quả, không phải nguyên nhân; đọc log.
- Target healthy nhưng `/db` lỗi: đi tiếp xuống DB/SG/secret.
- ASG vừa scale: instance mới có thể chưa có metric/log; chờ vài phút.
- Đừng stop load trước khi verify nếu verify cần metric.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Incident tổng hợp: CPU cao, 5xx, request chậm. Tách symptom khỏi root cause.

### Bạn cần biết 4 khái niệm

- **Symptom**: Cái người dùng thấy: chậm, 500, 503.
- **Root cause**: Lớp thật sự hỏng.
- **Latency**: Thời gian phản hồi.
- **Triage**: Ưu tiên kiểm tra user-facing trước.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| App | soa-c03-app | /health 200, /db 200 | ./bin/lab status |
| EC2 | instance trong ASG | CPU thấp trước break | CloudWatch → Metrics |
| Target group | soa-c03-tg | 1 healthy | EC2 → Target groups |
| Log group | /aws/cloudops/soa-c03/app | tồn tại | CloudWatch → Log groups |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| CPU? | CloudWatch → Metrics → EC2 | CPUUtilization |
| Target? | Target group → Targets | healthy/unhealthy |
| App lỗi gì? | Logs Insights | ERROR, msg |
| DB? | RDS metrics + curl /db | CPU, connections, status |
| Chậm? | curl /slow | thời gian phản hồi |

### Trước khi phá, bạn phải trả lời 3 câu

1. Symptom nào xuất hiện đầu tiên?
2. CPU cao là nguyên nhân hay hậu quả?
3. Bạn kiểm tra user-facing path trước hay metric trước?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 20 --live` và `./bin/lab teach 20`.

## 6. Hiện tượng bạn sẽ thấy

Người dùng thấy chậm/500; CloudWatch thấy CPU cao; ALB có thể 503 nếu target unhealthy.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| CPU cao do process nào? | CloudWatch + SSM `top`, `ps` |
| App có lỗi gì? | Logs Insights filter level=ERROR |
| ALB thấy gì? | Target health + ALB 5xx metrics |
| DB có liên quan không? | `/db` + RDS metrics |

## 8. Thành công trông như thế nào?

`verify 20` PASS: CPU giảm, `/health` và `/db` = 200, target healthy.

Nếu FAIL, đọc:

```bash
cat labs/20-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Không phải mọi 5xx đều do CPU; đọc log và target health.
- Scale out có thể che symptom nhưng không sửa root cause.
- Luôn kiểm tra user-facing path trước khi sửa sâu.

## 10. Note mẫu

- 1. Symptom nào xuất hiện đầu tiên?
- 2. CPU cao là nguyên nhân hay hậu quả?
- 3. Fix nào an toàn nhất?

## 11. Cleanup

```bash
./bin/lab down 20
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
./bin/lab hint 20
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 20. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
