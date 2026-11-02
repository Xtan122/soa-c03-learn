# Lab 02 — CloudWatch Logs, Agent, Insights, metric filter

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D1 Monitoring 22% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `02` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học cách đưa log từ EC2 lên CloudWatch, query bằng Logs Insights, rồi biến một dòng `ERROR` thành metric và alarm.
- **Việc đầu tiên:** Ô **Search** → `CloudWatch` → menu trái **Log groups**.
- **Xong khi:** `verify 02` PASS: Logs Insights thấy ≥ 10 ERROR, metric `ErrorCount` ≥ 5, alarm `ALARM`.
- **Nếu lạc:** `./bin/lab console 02` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học cách đưa log từ EC2 lên CloudWatch, query bằng Logs Insights, rồi biến một dòng `ERROR` thành metric và alarm.

## 2. Hiện tại có gì?

App stack chạy. App ghi log JSON vào `/var/log/cloudops/app.log`; CloudWatch Agent gửi lên log group. Lab tạo metric filter `ERROR` + alarm.

## 3. Kiến trúc

```text
App (JSON log)
  │  /var/log/cloudops/app.log
  ▼
CloudWatch Agent
  ▼
Log group /aws/cloudops/soa-c03/app
  ├── Logs Insights (query)
  └── Metric filter ERROR → CloudOpsLab/ErrorCount → Alarm
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/02-*/README.md` (file này) và dòng lab `02` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 02
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 02
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 02
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 02
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 02
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 02
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
| Log group | Thư mục log, ví dụ `/aws/cloudops/soa-c03/app`. |
| Log stream | Một dãy log từ một nguồn, thường là một file trên một instance. |
| Metric filter | Bộ lọc biến dòng log khớp pattern thành metric. |
| Logs Insights | Ngôn ngữ query log có `fields`, `filter`, `stats`, `sort`. |
| Retention | Bao lâu thì log tự bị xoá. |
| Ingestion delay | Độ trễ từ lúc app ghi log đến lúc CloudWatch thấy. |

### Khái niệm của lab này

- **Log group** là thư mục, **log stream** là một dãy sự kiện từ một nguồn (ví dụ một file).
- **Metric filter** biến một dòng khớp pattern thành datapoint; nó chỉ chạy trên log đến **sau** khi filter được tạo.
- **Logs Insights** là nơi query nhiều stream cùng lúc, khác với bấm đọc từng dòng.

### Đường bấm từng bước

1. Ô **Search** → `CloudWatch` → menu trái **Log groups**.
2. Bấm log group `/aws/cloudops/soa-c03/app`.
3. Tab **Log streams**: bấm stream mới nhất (tên thường có ngày/instance).
4. Trong stream, bấm một event để mở JSON: đọc `timestamp`, `level`, `msg`.
5. Menu trái → **Logs Insights**. Ở dropdown log group, chọn `/aws/cloudops/soa-c03/app`.
6. Dán query đếm lỗi rồi bấm **Run query**:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | stats count() as errors
   ```
7. Đổi query để xem dòng mới nhất:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | sort @timestamp desc
   | limit 50
   ```
8. Menu trái → **Metrics** → **All metrics** → namespace **CloudOpsLab** → **ErrorCount**.
9. Menu trái → **Alarms** → `soa-c03-lab02-errors` → tab **Details** + **History**.
10. Quay lại log group → tab **Metric filters** → bấm `soa-c03-lab02-errors` để xem pattern.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Event JSON | `level` có đúng `ERROR` không; `msg` nói lỗi gì. |
| Logs Insights result | `errors` là tổng số dòng khớp trong time range đang chọn. |
| Time range | Mặc định có thể là 1h; nếu vừa break xong, chọn **1h** hoặc **3h**. |
| ErrorCount datapoints | Metric filter chỉ tạo datapoint khi có log khớp pattern. |
| Alarm History | Bằng chứng `OK -> ALARM`, kể cả khi state đã về `OK`. |
| Metric filter pattern | Pattern JSON `{ $.level = "ERROR" }` chỉ khớp log JSON có field `level`. |

### Link nhanh

- [Log group `/aws/cloudops/soa-c03/app`](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:log-groups/log-group/%2Faws%2Fcloudops%2Fsoa-c03%2Fapp)
- [Logs Insights](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:logs-insights)
- [Metric `CloudOpsLab/ErrorCount`](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#metricsV2:)
- [Alarm `soa-c03-lab02-errors`](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#alarmsV2:alarm/soa-c03-lab02-errors)

### Nếu không thấy mục đó

- Không thấy log group: CloudWatch Agent chưa chạy hoặc instance mới chưa gửi log; xem `/var/log/amazon/amazon-cloudwatch-agent/amazon-cloudwatch-agent.log` qua SSM.
- Có log nhưng query 0 dòng: time range sai, hoặc field không phải `level`; bấm một event để xem tên field thật.
- Metric có graph nhưng alarm `OK`: kiểm tra threshold, period, và thời điểm filter được tạo (filter không tính log cũ).
- Log lên chậm 30–90 giây là bình thường.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học cách đưa log từ EC2 lên CloudWatch, query bằng Logs Insights, rồi biến dòng ERROR thành metric và alarm.

### Bạn cần biết 4 khái niệm

- **Log group**: Thư mục log, ví dụ /aws/cloudops/soa-c03/app.
- **Log stream**: Một dãy log từ một nguồn.
- **Metric filter**: Biến dòng log khớp pattern thành metric.
- **Logs Insights**: Query log bằng fields, filter, stats.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Log group | /aws/cloudops/soa-c03/app | tồn tại, có stream mới | CloudWatch → Log groups |
| Metric filter | soa-c03-lab02-errors | pattern level ERROR | Log group → Metric filters |
| Metric | CloudOpsLab/ErrorCount | 0 trước break | CloudWatch → Metrics |
| Alarm | soa-c03-lab02-errors | OK trước break | CloudWatch → Alarms |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Log lên CloudWatch? | CloudWatch → Log groups → stream | timestamp, level, msg |
| Bao nhiêu ERROR? | Logs Insights | stats count() as errors |
| Metric có tăng? | CloudWatch → Metrics → CloudOpsLab | ErrorCount datapoints |
| Alarm có kêu? | CloudWatch → Alarms | State và History |

### Trước khi phá, bạn phải trả lời 3 câu

1. Log đi qua những lớp nào từ app tới CloudWatch?
2. Metric filter tạo datapoint khi nào?
3. Nếu log có ERROR mà metric bằng 0, bạn nghi gì?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 02 --live` và `./bin/lab teach 02`.

## 6. Hiện tượng bạn sẽ thấy

App sinh nhiều dòng `ERROR`. Log có thể mất 30–60 giây mới lên CloudWatch; metric filter cũng cần thêm thời gian.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Log đã lên CloudWatch chưa? | CloudWatch → Log groups → /aws/cloudops/soa-c03/app |
| Có bao nhiêu ERROR? | Logs Insights: `filter level = "ERROR" | stats count()` |
| Metric filter có đếm đúng? | CloudWatch → Metrics → CloudOpsLab → ErrorCount |
| Alarm có kêu? | CloudWatch → Alarms → soa-c03-lab02-errors |

## 8. Thành công trông như thế nào?

`verify 02` PASS: Logs Insights thấy ≥ 10 ERROR, metric `ErrorCount` ≥ 5, alarm `ALARM`.

Nếu FAIL, đọc:

```bash
cat labs/02-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- CloudWatch Agent config: file path, log group, retention.
- Metric filter pattern `{ $.level = "ERROR" }`.
- Logs Insights khác `filter-log-events` ở chỗ nào.

## 10. Note mẫu

- 1. Log đi qua những lớp nào?
- 2. Vì sao metric filter chưa có datapoint ngay?
- 3. Nếu log là text thường, pattern phải viết thế nào?

## 11. Cleanup

```bash
./bin/lab down 02
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
./bin/lab hint 02
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 02. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
