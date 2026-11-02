# LAB 03 — CloudTrail + EventBridge: ai đã terminate EC2?

```text
LAB: 03 — CloudTrail + EventBridge: ai đã terminate EC2?
SERVICE: CloudTrail, EventBridge, SQS, EC2, STS (IAM role)
DATE: 2026-10-25
DOMAIN: D1 Monitoring 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: yes  (AI viết note này theo yêu cầu rõ ràng của người học; bản gốc giữ ở note.draft-2026-10-26.md)
```

1. What did I build?

Một pipeline 2 nửa trên core stack:

- **Canary EC2** `i-0d3e0cd7e44b346d0` (t4g.nano) — mục tiêu để bị tác động.
- **EventBridge rule** `soa-c03-lab03-ec2-state`, event pattern khớp 3 tầng:
  `source = aws.ec2`, `detail-type = EC2 Instance State-change Notification`,
  `detail.state = terminated | stopped`.
- **SQS queue** `soa-c03-lab03-events` làm target của rule (qua resource policy
  cho `events.amazonaws.com`).
- **IAM role** `soa-c03-lab-operator` — role dùng để assume trước khi gọi API.

Mục đích: CloudTrail để **điều tra sau** (ai gọi API gì, lúc nào, từ đâu);
EventBridge → SQS để **phản ứng gần thời gian thực**.

2. What failed? (symptom, not root cause)

Canary `i-0d3e0cd7e44b346d0` chuyển `running → shutting-down → terminated` lúc
`2026-10-25T18:39:56Z`. Không có lỗi ứng dụng, không có 5xx, không có metric bất
thường: đây là một **API call phá huỷ** (terminate), không phải service bị hỏng.

3. How did I detect it? (metric/log/event/CLI)

- **CloudTrail → Event history**, lọc `Event name = TerminateInstances`.
  Đọc được: `userIdentity.type = AssumedRole`,
  `userIdentity.arn = arn:aws:sts::074478993842:assumed-role/soa-c03-lab-operator/lab03-break`,
  `eventTime = 2026-10-25T18:39:56Z`, `sourceIPAddress = 183.80.57.52`,
  `requestParameters...instanceId = i-0d3e0cd7e44b346d0`,
  `responseElements.currentState = shutting-down`.
- **Truy danh tính gốc:** event `AssumeRole` lúc `18:39:54Z` (2 giây trước) có
  `userIdentity.type = IAMUser`, `arn = …:user/xtan`, `roleSessionName = lab03-break`,
  `responseElements.assumedRoleUser.arn` = đúng ARN assumed-role ở trên.
  ⇒ Chuỗi: IAM user `xtan` → assume role (session `lab03-break`) → TerminateInstances.
- **SQS** `soa-c03-lab03-events`: poll được **1 message**,
  `source = aws.ec2`, `detail-type = EC2 Instance State-change Notification`,
  `detail.state = terminated`, `time = 18:40:14Z` (18 giây sau API call).

4. Root cause (the actual broken layer)

Lớp **identity / permission**, không phải lớp app:

- Role `soa-c03-lab-operator` mang quyền `ec2:TerminateInstances` và có thể được
  assume mà không có condition (tag, MFA, thời gian, principal cụ thể).
- `roleSessionName` (`lab03-break`) do **người gọi tự đặt**, nên bản thân event
  terminate **không chứng minh được con người** — phải correlate với event `AssumeRole`.
- Không có cảnh báo thời gian thực cho hành động phá huỷ: chỉ biết sau khi đọc log.

5. How did I fix it? (exact command or console action)

Không cần fix: đây là lab forensics, việc terminate là **có chủ đích** (fault của lab).
Việc mình làm là xác lập chuỗi bằng chứng và loại trừ actor khác:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=TerminateInstances
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole
./bin/lab verify 03     # PASS
```

6. Prevention / automation

- **Phát hiện:** EventBridge rule trên `TerminateInstances` (hoặc trên
  `EC2 Instance State-change`) → SNS → email/chat; thêm CloudWatch alarm trên
  metric filter đếm `TerminateInstances` để có ngưỡng thay vì đọc log thủ công.
- **Ngăn:** thu hẹp trust policy của role (chỉ đúng principal được assume);
  deny `ec2:TerminateInstances` trừ khi có condition (tag `Protected=true`, MFA,
  thời gian); bật termination protection cho máy quan trọng.
- **Truy vết:** alert riêng khi có `AssumeRole` vào các role nhạy cảm, và luôn
  join session name ↔ event `AssumeRole` để ra principal gốc.

7. Exam trap

- **`AssumedRole` không phải con người.** Session name do caller tự đặt. Muốn biết
  "ai", phải tìm event **`AssumeRole`** rồi đọc `userIdentity` (principal gọi) và
  `responseElements.assumedRoleUser.arn` (phiên được cấp) của chính event đó.
- **CloudTrail ≠ AWS Config.** CloudTrail trả lời *ai gọi API gì, lúc nào, từ IP nào*;
  Config trả lời *resource đã thay đổi thế nào*. Câu hỏi "resource thay đổi gì" không
  giải bằng CloudTrail.
- **Event history chỉ 90 ngày**, mặc định chỉ **management events**; data events
  (S3 object-level, Lambda invoke) phải bật trail riêng.
- **EventBridge pattern phải khớp cả 3 tầng** (`source`, `detail-type`, `detail`);
  sai/thiếu một tầng ⇒ `Invocations = 0` dù event có xảy ra.
- **`eventTime` (CloudTrail) ≠ `time` (EventBridge).** Cái đầu là lúc API được gọi,
  cái sau là lúc trạng thái resource đổi — luôn trễ hơn vài giây.
