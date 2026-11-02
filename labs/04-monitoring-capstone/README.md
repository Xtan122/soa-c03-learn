# Lab 04 — Capstone monitoring: 500 → metric → alarm → event

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D1 Monitoring 22% |
| Thời gian | ~180 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `04` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Ghép toàn bộ mắt xích monitoring: app trả 500 → log ERROR → metric filter → alarm → EventBridge → SQS. Đây là bài tổng hợp của D1.
- **Việc đầu tiên:** Terminal: `curl -i http://<alb-dns>/error` (lấy DNS bằng `./bin/lab status`). Đọc dòng status.
- **Xong khi:** `verify 04` PASS: metric ≥ 4, alarm `ALARM`, SQS có message.
- **Nếu lạc:** `./bin/lab console 04` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Ghép toàn bộ mắt xích monitoring: app trả 500 → log ERROR → metric filter → alarm → EventBridge → SQS. Đây là bài tổng hợp của D1.

## 2. Hiện tại có gì?

App stack chạy. Lab tạo metric filter, alarm, EventBridge rule bắt alarm state change, và SQS.

## 3. Kiến trúc

```text
Client → ALB → App
                     │  HTTP 500 + log ERROR
                     ▼
              CloudWatch Logs → Metric Filter
                     ▼
                   Alarm (ALARM)
                     ▼
              EventBridge → SQS
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/04-*/README.md` (file này) và dòng lab `04` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 04
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 04
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 04
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 04
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 04
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 04
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
| 5xx | Nhóm HTTP status 500–599, lỗi phía server/ALB. |
| Metric filter | Biến dòng log ERROR thành metric `CapstoneErrorCount`. |
| Alarm state change | Sự kiện riêng của CloudWatch khi alarm đổi trạng thái. |
| EventBridge rule | Bộ lọc bắt sự kiện alarm rồi đẩy tới SQS. |
| DLQ | Queue nhận message không xử lý được; lab này chưa dùng. |

### Khái niệm của lab này

- Đây là một **chuỗi**: app trả 500 → log ghi ERROR → metric filter đếm → alarm đổi trạng thái → EventBridge bắt **alarm state change** → SQS nhận message.
- Mỗi mắt xích có thể đúng riêng lẻ nhưng chuỗi vẫn đứt.

### Đường bấm từng bước

1. Terminal: `curl -i http://<alb-dns>/error` (lấy DNS bằng `./bin/lab status`). Đọc dòng status.
2. CloudWatch → **Log groups** → `/aws/cloudops/soa-c03/app` → **Logs Insights**.
3. Query:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | stats count() as errors
   ```
4. CloudWatch → **Metrics** → **All metrics** → **CloudOpsLab** → `CapstoneErrorCount`.
5. **Alarms** → `soa-c03-lab04-errors` → **Details** + **History**.
6. **EventBridge** → **Rules** → `soa-c03-lab04-alarm` → **Event pattern**, **Targets**, **Monitoring**.
7. **SQS** → `soa-c03-lab04-events` → **Send and receive messages** → **Poll for messages**.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| HTTP status từ `/error` | Phải là 500 để có log ERROR. |
| Số ERROR trong Insights | Nếu 0, chuỗi đứt ngay từ log. |
| Metric `CapstoneErrorCount` | Nếu log có mà metric 0, filter/pattern sai. |
| Alarm History | Nếu metric có mà alarm không đổi, threshold/period sai. |
| Rule Monitoring | Nếu alarm đổi mà invocation 0, event pattern sai. |
| SQS message | Nếu invocation có mà queue trống, target/policy sai. |

### Link nhanh

- [CloudWatch alarms](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#alarmsV2:alarms)
- [Logs Insights](https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:logs-insights)
- [EventBridge rules](https://console.aws.amazon.com/events/home?region=ap-southeast-1#/eventbus/default/rules)
- [SQS queues](https://console.aws.amazon.com/sqs/v3/home?region=ap-southeast-1#/queues)

### Nếu không thấy mục đó

- Alarm đã ở `ALARM` trước khi rule được tạo thì không có **state change** mới; đợi nó về `OK` rồi lên `ALARM` lại, hoặc xem History.
- Rule chỉ bắt `state.value = ALARM`; đổi sang `OK` không khớp.
- Nếu SQS trống, thử **Poll for messages** lần nữa với thời gian chờ dài hơn.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Ghép chuỗi monitoring: app trả 500 → log ERROR → metric filter → alarm → EventBridge → SQS.

### Bạn cần biết 4 khái niệm

- **5xx**: Nhóm HTTP 500–599, lỗi phía server hoặc ALB.
- **Metric filter**: Đếm dòng log khớp pattern.
- **Alarm state change**: Sự kiện riêng khi alarm đổi trạng thái.
- **EventBridge rule**: Bắt sự kiện alarm rồi đẩy tới SQS.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| App | soa-c03-app | /health 200, target healthy | ./bin/lab status |
| Metric filter | soa-c03-lab04-errors | pattern ERROR | Log group → Metric filters |
| Metric | CloudOpsLab/CapstoneErrorCount | 0 trước break | CloudWatch → Metrics |
| Alarm | soa-c03-lab04-errors | OK trước break | CloudWatch → Alarms |
| EventBridge rule | soa-c03-lab04-alarm | Enabled, target SQS | EventBridge → Rules |
| SQS | soa-c03-lab04-events | 0 message | SQS → Queues |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| App có trả 500? | curl /error | HTTP status |
| Log có ERROR? | Logs Insights | count và msg |
| Metric có tăng? | CloudWatch → Metrics | CapstoneErrorCount |
| Alarm có đổi? | CloudWatch → Alarms → History | OK → ALARM |
| Event có tới SQS? | EventBridge Monitoring / SQS | Invocations, body |

### Trước khi phá, bạn phải trả lời 3 câu

1. Chuỗi monitoring gồm những mắt xích nào?
2. Nếu log có ERROR mà metric 0, mắt xích nào đứt?
3. Alarm đã ở ALARM từ trước, vì sao EventBridge có thể không có event mới?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 04 --live` và `./bin/lab teach 04`.

## 6. Hiện tượng bạn sẽ thấy

Website trả nhiều 500. Bạn phải kiểm tra từng mắt xích, vì một mắt xích đúng chưa chắc cả chuỗi đúng.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| App có thật sự trả 500? | `curl -i http://<alb>/error` |
| Log có ERROR? | Logs Insights filter level=ERROR |
| Metric có tăng? | CloudWatch Metrics → CloudOpsLab/CapstoneErrorCount |
| EventBridge có gửi message? | SQS `soa-c03-lab04-events` |

## 8. Thành công trông như thế nào?

`verify 04` PASS: metric ≥ 4, alarm `ALARM`, SQS có message.

Nếu FAIL, đọc:

```bash
cat labs/04-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Alarm state change là một event riêng, cần EventBridge rule.
- SQS policy phải cho phép `events.amazonaws.com` gửi message.
- Debug chuỗi theo thứ tự, đừng nhảy lớp.

## 10. Note mẫu

- 1. Mắt xích nào đứt đầu tiên?
- 2. Evidence nào chứng minh?
- 3. Nếu chỉ có log mà không có metric, thiếu gì?

## 11. Cleanup

```bash
./bin/lab down 04
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
./bin/lab hint 04
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 04. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
