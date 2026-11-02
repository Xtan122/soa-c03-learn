# Lab 12 — Event-driven remediation: EC2 stopped → Lambda start

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D3 Automation 22% |
| Thời gian | ~150 phút |
| Cần app stack | Có (`make app-up`) |
| Chi phí | Thấp |
| Lab ID | `12` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học tự động sửa lỗi: EC2 bị stop → EventBridge → Lambda → start lại → thông báo. Đây là pattern remediation hay hỏi trong SOA.
- **Việc đầu tiên:** Ô **Search** → `EventBridge` → **Rules** → bấm `soa-c03-lab12-remediate`.
- **Xong khi:** `verify 12` PASS: canary `running`, log Lambda có `started`, SQS có message.
- **Nếu lạc:** `./bin/lab console 12` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học tự động sửa lỗi: EC2 bị stop → EventBridge → Lambda → start lại → thông báo. Đây là pattern remediation hay hỏi trong SOA.

## 2. Hiện tại có gì?

App stack chạy. Lab tạo Lambda `soa-c03-lab12-remediate`, rule EC2 stopped, canary có tag `auto-remediate=true`, và SQS.

## 3. Kiến trúc

```text
EC2 stopped
   │  EventBridge rule (state=stopped)
   ▼
Lambda (kiểm tra tag auto-remediate=true)
   │
   ├── ec2:StartInstances
   └── SQS message
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h).

- Đọc `labs/12-*/README.md` (file này) và dòng lab `12` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 12
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 12
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 12
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 12
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 12
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 12
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
| Event pattern | Bộ lọc JSON quyết định event nào khớp rule. |
| Target | Đích rule gọi tới: Lambda, SQS, SNS... |
| Resource-based policy | Ai được phép gọi Lambda. |
| Execution role | Role Lambda dùng khi chạy code. |
| Idempotency | Chạy lại nhiều lần vẫn cho cùng kết quả. |

### Khái niệm của lab này

- **EventBridge rule** khớp event `EC2 Instance State-change` với `state=stopped` rồi gọi **Lambda**.
- Lambda cần **execution role** để start instance và **resource-based permission** để EventBridge được phép gọi nó.
- Remediation phải idempotent vì một event có thể đến nhiều lần.

### Đường bấm từng bước

1. Ô **Search** → `EventBridge` → **Rules** → bấm `soa-c03-lab12-remediate`.
2. Tab **Event pattern**: đọc JSON, chú ý `source`, `detail-type`, `detail.state`.
3. Tab **Targets**: xem Lambda `soa-c03-lab12-remediate` và SQS `soa-c03-lab12-events`.
4. Tab **Monitoring**: xem **Invocations**, **Failed invocations**, **Throttles** trong 1h.
5. Ô **Search** → `Lambda` → **Functions** → `soa-c03-lab12-remediate`.
6. Tab **Monitor** → **View CloudWatch logs** → mở stream mới nhất → tìm dòng `started` hoặc `skip`.
7. Tab **Configuration** → **Permissions** → xem **Resource-based policy** (principal `events.amazonaws.com`).
8. Ô **Search** → `EC2` → **Instances** → `soa-c03-lab12-canary` → tab **Tags** (`auto-remediate=true`), **Instance state**.
9. Ô **Search** → `SQS` → `soa-c03-lab12-events` → poll message.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| Event pattern | Thiếu `detail.state` hoặc sai `detail-type` là rule không khớp. |
| Rule Invocations | 0 nghĩa là event không tới rule. |
| Lambda log | `started <id>` chứng minh code đã chạy; `skip` nghĩa là tag sai. |
| Resource-based policy | Thiếu statement cho `events.amazonaws.com` thì rule gọi bị từ chối. |
| Execution role | Thiếu `ec2:StartInstances` thì Lambda lỗi. |
| Canary tag | `auto-remediate=true` là điều kiện code kiểm tra. |

### Link nhanh

- [EventBridge rules](https://console.aws.amazon.com/events/home?region=ap-southeast-1#/eventbus/default/rules)
- [Lambda functions](https://console.aws.amazon.com/lambda/home?region=ap-southeast-1#/functions)
- [SQS queues](https://console.aws.amazon.com/sqs/v3/home?region=ap-southeast-1#/queues)
- [EC2 instances](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#Instances:)

### Nếu không thấy mục đó

- Rule invocation 0: kiểm tra rule **Enabled** và event pattern.
- Lambda lỗi: tab **Monitor** → log; lỗi thường là role thiếu quyền.
- Lambda không được gọi: **Permissions** thiếu statement hoặc sai `source-arn`.
- Canary vẫn stopped: có thể tag sai hoặc Lambda chưa chạy; đọc log trước.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Học remediation: EC2 stopped → EventBridge → Lambda start lại → SQS nhận thông báo.

### Bạn cần biết 4 khái niệm

- **Event pattern**: Bộ lọc JSON quyết định event nào khớp rule.
- **Target**: Đích rule gọi tới: Lambda, SQS.
- **Resource-based policy**: Ai được phép gọi Lambda.
- **Idempotency**: Chạy lại nhiều lần vẫn cùng kết quả.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Lambda | soa-c03-lab12-remediate | Active | Lambda → Functions |
| EventBridge rule | soa-c03-lab12-remediate | Enabled | EventBridge → Rules |
| SQS | soa-c03-lab12-events | 0 message | SQS → Queues |
| Canary | soa-c03-lab12-canary | running, tag auto-remediate=true | EC2 → Instances |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Rule có match? | EventBridge → Monitoring | Invocations |
| Lambda chạy? | Lambda → Monitor → Logs | started hoặc skip |
| Permission? | Lambda → Configuration → Permissions | events.amazonaws.com |
| Tag đúng? | EC2 → Tags | auto-remediate=true |
| Message tới? | SQS → Poll | body |

### Trước khi phá, bạn phải trả lời 3 câu

1. EventBridge rule khớp event dựa vào gì?
2. Lambda cần mấy loại quyền?
3. Vì sao remediation phải idempotent?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 12 --live` và `./bin/lab teach 12`.

## 6. Hiện tượng bạn sẽ thấy

Canary bị stop. Trong 1–2 phút, Lambda phải start lại. Nếu không, xem rule/Lambda permission/log.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Rule có match event không? | EventBridge → Rules → soa-c03-lab12-remediate → Monitoring |
| Lambda có được gọi không? | CloudWatch Logs `/aws/lambda/soa-c03-lab12-remediate` |
| Lambda có quyền start không? | IAM role của Lambda |
| Canary có tag đúng không? | EC2 tags `auto-remediate=true` |

## 8. Thành công trông như thế nào?

`verify 12` PASS: canary `running`, log Lambda có `started`, SQS có message.

Nếu FAIL, đọc:

```bash
cat labs/12-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Event pattern + target permission + Lambda resource policy.
- Idempotency: event có thể đến nhiều lần.
- Remediation phải có guardrail để không start instance sai.

## 10. Note mẫu

- 1. Event có tới rule không?
- 2. Rule có gọi Lambda không?
- 3. Lambda có quyền và tag đúng không?

## 11. Cleanup

```bash
./bin/lab down 12
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
./bin/lab hint 12
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 12. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
