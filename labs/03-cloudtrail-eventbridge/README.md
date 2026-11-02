# Lab 03 — CloudTrail + EventBridge: ai đã terminate EC2?

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | D1 Monitoring 22% |
| Thời gian | ~150 phút |
| Cần app stack | Không |
| Chi phí | Thấp |
| Lab ID | `03` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** Học cách trả lời câu hỏi forensics: ai gọi API, lúc nào, từ IP nào. Đây là lab CloudTrail + EventBridge, không phải lab sửa app.
- **Việc đầu tiên:** Ô **Search** → `CloudTrail` → menu trái **Event history**.
- **Xong khi:** `verify 03` PASS: CloudTrail có event TerminateInstances cho canary, actor là `AssumedRole`, có `sourceIPAddress`.
- **Nếu lạc:** `./bin/lab console 03` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

Học cách trả lời câu hỏi forensics: ai gọi API, lúc nào, từ IP nào. Đây là lab CloudTrail + EventBridge, không phải lab sửa app.

## 2. Hiện tại có gì?

Core stack + CloudTrail đủ (không cần app stack). Lab tạo một canary EC2 nhỏ, một EventBridge rule bắt sự kiện EC2 stopped/terminated, và SQS để nhận event.

## 3. Kiến trúc

```text
Lab operator role
  │  AssumeRole → TerminateInstances
  ▼
Canary EC2  ──► CloudTrail (audit API)
  │
  └──► EventBridge rule ──► SQS
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

- Chỉ cần core stack; không cần app stack.

- Đọc `labs/03-*/README.md` (file này) và dòng lab `03` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up 03
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break 03
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint 03
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify 03
   ```

6. Ghi note:

   ```bash
   ./bin/lab note 03
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down 03
   ```

## 5b. Ghi chú / lệnh riêng

EventBridge rule nhận cả `stopped` và `terminated`; canary không cần SSH/SSM.

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
| Management event | Sự kiện gọi API quản trị, ví dụ TerminateInstances. |
| Event history | Danh sách event CloudTrail, chỉ giữ 90 ngày. |
| Event pattern | Bộ điều kiện JSON để EventBridge chọn event. |
| Event bus | Đường ống sự kiện; mặc định là `default`. |
| AssumeRole session | Danh tính tạm thời khi một role gọi API. |

### Khái niệm của lab này

- **CloudTrail** trả lời “ai gọi API gì, từ đâu” và giữ event 90 ngày.
- **EventBridge** là bus sự kiện gần thời gian thực: rule khớp `source`, `detail-type`, `detail` rồi đẩy tới target.
- Hai thứ bổ sung nhau: CloudTrail để điều tra, EventBridge để tự động phản ứng.

### Đường bấm từng bước

1. Ô **Search** → `CloudTrail` → menu trái **Event history**.
2. Bộ lọc **Event name** = `TerminateInstances`; time range **1h** (hoặc **3h**).
3. Bấm event mới nhất → mở **Event record** (JSON).
4. Đọc `userIdentity.type`, `userIdentity.arn`, `userIdentity.sessionContext`, `eventTime`, `sourceIPAddress`, `userAgent`, `requestParameters`.
5. Ô **Search** → `EventBridge` → menu trái **Rules** → bấm `soa-c03-lab03-ec2-state`.
6. Tab **Event pattern**: xem `source`, `detail-type`, `detail.state`.
7. Tab **Targets**: phải có SQS `soa-c03-lab03-events`.
8. Tab **Monitoring**: xem **Invocations** và **Failed invocations** trong 1h.
9. Ô **Search** → `SQS` → `soa-c03-lab03-events` → **Send and receive messages** → **Poll for messages**.
10. Ô **Search** → `EC2` → **Instances** → search `soa-c03-lab03-canary` → xem **Instance state**.

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
| userIdentity.type | `AssumedRole` nghĩa là một role, không phải user gốc. |
| userIdentity.arn | Role nào và session nào đã gọi. |
| sourceIPAddress | Gọi từ IP nào; có thể là IP của AWS service nếu là event do service tạo. |
| requestParameters | Instance ID nào bị terminate. |
| Rule Invocations | 0 nghĩa là event không khớp pattern hoặc rule bị disable. |
| SQS message | Payload thật EventBridge gửi, gồm `detail.instance-id` và `state`. |

### Link nhanh

- [CloudTrail event history](https://console.aws.amazon.com/cloudtrail/home?region=ap-southeast-1#/events)
- [EventBridge rule `soa-c03-lab03-ec2-state`](https://console.aws.amazon.com/events/home?region=ap-southeast-1#/eventbus/default/rules/soa-c03-lab03-ec2-state)
- [SQS queues](https://console.aws.amazon.com/sqs/v3/home?region=ap-southeast-1#/queues)
- [EC2 instances](https://console.aws.amazon.com/ec2/home?region=ap-southeast-1#Instances:)

### Nếu không thấy mục đó

- CloudTrail chưa có event: có thể trễ vài phút; mở rộng time range lên **3h**.
- Event history chỉ có management events; nếu lab dùng data event thì phải xem trail/log khác.
- Rule không invocation: bấm **Event pattern** so khớp chính xác `detail-type` và `detail.state`.
- SQS trống: rule đã gửi nhưng target sai ARN, hoặc policy queue thiếu quyền `events.amazonaws.com`.

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->
## 5d. Brief trước khi phá — đọc trước khi `break`

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** Lab này dạy forensic: khi một EC2 biến mất, làm sao biết ai làm, lúc nào, từ đâu, và automation có bắt được sự kiện không.

### Bạn cần biết 5 khái niệm

- **CloudTrail**: Camera ghi lại ai gọi API gì, lúc nào, từ IP nào. Giữ event 90 ngày.
- **EventBridge**: Bộ lọc sự kiện: EC2 đổi trạng thái → rule khớp → đẩy thông báo tới SQS.
- **Canary**: Một EC2 nhỏ để thử. Không phải app thật, không phục vụ user.
- **SQS**: Hàng đợi nhận thông báo. Dùng để chứng minh event có tới.
- **IAM role**: Thẻ quyền tạm thời. Lab dùng role để terminate canary.

### Hệ thống hiện tại (baseline)

| Thành phần | Tên thật | Trạng thái khoẻ | Xem ở đâu |
|---|---|---|---|
| Canary EC2 | soa-c03-lab03-canary | running | EC2 → Instances → search tên |
| CloudTrail | soa-c03-trail | Logging ON | CloudTrail → Dashboard |
| EventBridge rule | soa-c03-lab03-ec2-state | Enabled; target SQS | EventBridge → Rules |
| SQS | soa-c03-lab03-events | 0 message | SQS → Queues |
| IAM role | soa-c03-lab-operator | tồn tại | IAM → Roles |

### Bản đồ chẩn đoán

| Câu hỏi | Xem ở đâu | Đọc gì |
|---|---|---|
| Ai đã làm? | CloudTrail → Event history | userIdentity.type, arn, sessionName |
| Lúc nào? | Event record | eventTime |
| Từ đâu? | Event record | sourceIPAddress, userAgent |
| Automation có thấy? | EventBridge → rule → Monitoring | Invocations, FailedInvocations |
| Message có tới? | SQS → Send and receive messages | body, detail.state |
| Cái gì bị ảnh hưởng? | EC2 → Instances | Instance state |

### Trước khi phá, bạn phải trả lời 3 câu

1. Canary đang ở trạng thái nào?
2. Nếu canary bị terminate, 3 nơi nào sẽ thay đổi?
3. Bạn sẽ xem gì đầu tiên để trả lời “ai làm”?

> Trả lời được 3 câu này rồi mới chạy `break`. Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline 03 --live` và `./bin/lab teach 03`.

## 6. Hiện tượng bạn sẽ thấy

Canary bị terminate. CloudTrail có thể mất vài phút mới hiện event; EventBridge gần như ngay.

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
| Ai đã terminate? | CloudTrail → Event history → Event name = TerminateInstances |
| Actor là user hay role? | Đọc `userIdentity.type`, `arn`, `sessionName` |
| Gọi từ đâu? | `sourceIPAddress`, `userAgent` |
| EventBridge có bắt không? | SQS `soa-c03-lab03-events` |

## 8. Thành công trông như thế nào?

`verify 03` PASS: CloudTrail có event TerminateInstances cho canary, actor là `AssumedRole`, có `sourceIPAddress`.

Nếu FAIL, đọc:

```bash
cat labs/03-*/evidence/verify-last.txt
```

## 9. Exam takeaway

- Management events vs data events; Event history chỉ 90 ngày.
- CloudTrail (ai gọi API) khác AWS Config (resource thay đổi thế nào).
- Event pattern phải khớp `source`, `detail-type`, `detail.state`.

## 10. Note mẫu

- 1. Ai làm? (userIdentity)
- 2. Làm gì? (eventName + requestParameters)
- 3. Từ đâu? (sourceIPAddress)

## 11. Cleanup

```bash
./bin/lab down 03
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
./bin/lab hint 03
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab 03. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
