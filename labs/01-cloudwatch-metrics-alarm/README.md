# Lab 01 — CloudWatch metrics, dashboard, alarm, SNS

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D1 Monitoring 22% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `01` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học cách biết một EC2 đang quá tải: xem metric nào, period/statistic nào, và tại sao chuông báo (alarm) có thể chậm hơn CPU thực tế.
- **Việc đầu tiên:** Ô **Search** → `CloudWatch` → menu trái **Metrics** → **All metrics**.
- **Xong khi:** `verify 01` PASS: CPU max ≥ 50% **và** alarm đang `ALARM`. Đừng stop load trước khi verify; `./bin/lab down 01` sẽ stop.
- **Nếu lạc:** `./bin/lab console 01` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học cách biết một EC2 đang quá tải: xem metric nào, period/statistic nào, và tại sao chuông báo (alarm) có thể chậm hơn CPU thực tế.

## 2. Hiện tại có gì?

App stack đang chạy. Lab tạo một alarm theo dõi CPU của **một** instance cụ thể và một SQS queue để nhận thông báo.

## 3. Kiến trúc

```text
EC2 (1 instance)
  │  CPUUtilization (1 phút)
  ▼
CloudWatch Metric
  │  threshold > 50%
  ▼
Alarm ──► SNS topic ──► SQS queue
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/01-*/README.md` (file này) và dòng lab `01` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 01
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 01
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 01
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 01
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 01
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 01
   ```

## 5b. Ghi chú / lệnh riêng

Lab 01 tạm suspend ASG scaling để CPU load không tạo thêm instance. `down 01` sẽ resume.

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
| Metric | Đồng hồ đo, ví dụ CPUUtilization. |
| Namespace | Ngăn tủ chứa metric, ví dụ `AWS/EC2`. |
| Dimension | Nhãn để chỉ đúng đối tượng, ví dụ `InstanceId=i-...`. |
| Period | Mỗi bao lâu lấy một điểm, ví dụ 60 giây. |
| Statistic | Cách gộp các điểm trong period: Average, Maximum, Sum... |
| Evaluation periods | Cần bao nhiêu period liên tiếp vượt ngưỡng mới đổi trạng thái. |
| INSUFFICIENT_DATA | Chưa đủ dữ liệu để kết luận, không phải lỗi. |

### Khái niệm của lab này

- CloudWatch lưu **metric** (con số theo thời gian).
- Mỗi metric có namespace, tên, dimension (ví dụ `InstanceId`) và được gộp theo **period**.
- **Alarm** chỉ là một quy tắc đọc metric đó: lấy statistic nào, trong bao nhiêu period, vượt ngưỡng bao nhiêu lần thì đổi trạng thái.

### Đường bấm từng bước

1. Ô **Search** → `CloudWatch` → menu trái **Metrics** → **All metrics**.
2. Chọn namespace **EC2** → **Per-Instance Metrics**.
3. Ở ô search của bảng metric, dán instance ID. Lấy ID bằng `./bin/lab status` (dòng `ec2  : i-...`).
4. Tick metric **CPUUtilization**.
5. Phía trên biểu đồ: chọn **Average** và **Maximum**; time range **1h**; nếu có, period **1 minute**.
6. Menu trái → **Alarms** → **All alarms** → bấm `soa-c03-lab01-cpu-high`.
7. Tab **Details**: đọc **State**, **Threshold**, **Period**, **Evaluation periods**, **Statistic**.
8. Tab **History**: tìm dòng `OK -> ALARM` và giờ chuyển.
9. Ô **Search** → `SQS` → **Queues** → `soa-c03-lab01-events` → **Send and receive messages** → **Poll for messages**.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| CPUUtilization Average vs Maximum | Average thấp mà Maximum cao nghĩa là chỉ một lúc bị đẩy lên; alarm dùng Average sẽ chậm hơn. |
| Alarm State | `OK`, `ALARM`, hoặc `INSUFFICIENT_DATA`. |
| Threshold + comparison | Ví dụ `> 50` nghĩa là vượt 50% mới tính. |
| Period × Evaluation periods | Thời gian tối thiểu trước khi alarm có thể đổi trạng thái. |
| History | Bằng chứng alarm đã từng kêu, kể cả khi giờ đã về `OK`. |
| SQS message body | Thông báo thật đã đi qua SNS tới queue hay chưa. |

### Link nhanh

- [CloudWatch metrics](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#metricsV2:)
- [Alarm `soa-c03-lab01-cpu-high`](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#alarmsV2:alarm/soa-c03-lab01-cpu-high)
- [All alarms](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#alarmsV2:alarms)
- [SQS queues](https://console.aws.amazon.com/sqs/v3/home?region=ap-southeast-1#/queues)
- [SNS topics](https://console.aws.amazon.com/sns/v3/home?region=ap-southeast-1#/topics)

### Nếu không thấy mục đó

- Không thấy metric EC2: instance mới tạo có thể chưa có datapoint; đợi 2–5 phút, hoặc kiểm tra detailed monitoring.
- Không thấy alarm: `./bin/lab up 01` chưa chạy hoặc đã `down`.
- Queue trống: alarm chưa từng vào `ALARM`, hoặc subscription SNS→SQS sai; xem tab **History** trước.
- Đừng kết luận “alarm hỏng” chỉ vì state đang `OK`; alarm có thể đã kêu rồi tự về `OK`.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học cách đọc metric CPU, hiểu alarm period/evaluation, và thấy thông báo đi qua SNS tới SQS.

### Bạn cần biết 4 khái niệm

- **Metric**: Đồng hồ đo theo thời gian, ví dụ CPUUtilization.
- **Period**: Mỗi bao lâu lấy một điểm, ví dụ 60 giây.
- **Statistic**: Cách gộp điểm: Average, Maximum, Sum.
- **Evaluation periods**: Cần bao nhiêu period vượt ngưỡng mới đổi trạng thái.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| App stack | soa-c03-app | CREATE_COMPLETE | ./bin/lab status |
| ALB | soa-c03-alb | target healthy 1/1 | EC2 → Load balancers |
| EC2 app | instance trong ASG | running, SSM Online | EC2 → Instances |
| Alarm | soa-c03-lab01-cpu-high | OK trước break | CloudWatch → Alarms |
| SQS | soa-c03-lab01-events | 0 message | SQS → Queues |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| CPU thực tế? | CloudWatch → Metrics → EC2 | CPUUtilization Average/Maximum |
| Alarm trạng thái? | CloudWatch → Alarms → History | OK → ALARM, thời điểm |
| Process ăn CPU? | Systems Manager → Run Command | top, ps aux |
| Thông báo có tới? | SQS → Poll for messages | body |

### Trước khi phá, bạn phải trả lời 3 câu

1. CPU bình thường của instance là bao nhiêu?
2. Nếu CPU tăng, metric nào đổi và alarm nào có thể kêu?
3. Bạn sẽ xem Average hay Maximum trước? Vì sao?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 01 --live` và `./bin/lab teach 01`.

## 6. Hiện tượng bạn sẽ thấy

CPU tăng cao. Alarm có thể vẫn `OK` một lúc vì cần đủ period/evaluation. Đây là điểm dễ gây hoang mang cho người mới.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| CPU thực tế bao nhiêu? | CloudWatch → Metrics → EC2 → CPUUtilization; xem Average và Maximum |
| Alarm đang ở trạng thái nào? | CloudWatch → Alarms → soa-c03-lab01-cpu-high; hoặc `aws cloudwatch describe-alarms` |
| Process nào ăn CPU? | SSM Run Command: `top -b -n1`, `ps aux --sort=-%cpu` |
| Alarm có gửi thông báo không? | SQS queue `soa-c03-lab01-events`; hoặc SNS topic |

## 8. Thành công trông như thế nào?

`verify 01` PASS: CPU max ≥ 50% **và** alarm đang `ALARM`. Đừng stop load trước khi verify; `./bin/lab down 01` sẽ stop.

Nếu FAIL, đọc:

```bash
cat labs/01-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Period, statistic, evaluation periods, `INSUFFICIENT_DATA`.
- Basic monitoring 5 phút vs detailed monitoring 1 phút.
- Alarm chỉ chuyển trạng thái sau đủ số datapoint, không tức thì.

## 10. Note mẫu

- 1. Metric nào chứng minh EC2 quá tải?
- 2. Vì sao chọn Average hay Maximum?
- 3. Alarm mất bao lâu để chuyển ALARM?

## 11. Cleanup

```bash
./bin/lab down 01
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
./bin/lab hint 01
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 01. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
