# LAB 09 — SSM Session Manager, Run Command, Parameter Store

```text
LAB: 09 — SSM Session Manager, Run Command, Parameter Store
SERVICE: EC2 (i-00bb7ca67e31cf673) + cloudops-app + ALB target group soa-c03-tg
DATE: 2026-11-02
DOMAIN: D3 Automation 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] (tự hồi do ASG, không sửa tay) Verify [x] Cleanup [ ]
SOLUTION_USED: yes (user nói "viết hộ tôi"; người học tự đọc console + tự decode base64)
EVIDENCE_SOURCE: console Systems Manager / EC2 / ASG Activity; verify 2026-11-02T07:38:51Z
```

1. What did I build?

Lab 09 tạo parameter `/soa-c03/lab09/message = hello-from-parameter-store` trên app stack có sẵn
(ALB + ASG + 1 EC2 + RDS). Mục tiêu là vận hành EC2 **không SSH, không public IP**: vào máy bằng
Session Manager, chạy lệnh bằng Run Command, đọc config bằng Parameter Store.

2. What failed? (symptom, not root cause)

`cloudops-app` trên EC2 dừng lại. ALB health check `/health` fail → target group `soa-c03-tg` báo
**Unhealthy** → ASG terminate máy cũ và launch máy mới. Người dùng thấy khoảng ~2 phút gián đoạn
(5xx) rồi tự hết, nên nếu chỉ nhìn dashboard thì không thấy gì bất thường.

3. How did I detect it? (metric/log/event/CLI)

- **EC2 → Target Groups → `soa-c03-tg` → Targets**: instance ID đổi từ `i-00bb7ca67e31cf673`
  (lúc baseline) sang `i-02423875c0fd46212`, `Health status = Healthy` → chứng tỏ máy đã bị thay.
- **EC2 → Auto Scaling Groups → `soa-c03-asg` → Activity**:
  - `2026-11-02T07:19:48Z` — Terminating EC2 instance `i-00bb7ca67e31cf673`, cause
    *"an instance was taken out of service in response to an ELB system health check failure"*.
  - `2026-11-02T07:19:48Z` — Launching a new EC2 instance `i-02423875c0fd46212`, cause
    *"an instance was launched in response to an unhealthy instance needing to be replaced"*.
- **Systems Manager → Run Command → Command history**: command `f5c5da3a-2bb0-4ec6-9bcd-4e00f658f482`,
  document `AWS-RunShellScript`, status `Success`, **Start 07:17:36Z → Finish 07:17:46Z**,
  1 target `i-00bb7ca67e31cf673`, `Response code 0`.
- **Command parameters**: `commands = "echo c3lzdGVtY3RsIHN0b3AgY2xvdWRvcHMtYXBw | base64 -d | bash"`;
  `base64 -d` cho ra `systemctl stop cloudops-app`.

4. Root cause (the actual broken layer)

Lớp bị tác động là **application service trên EC2**, không phải SSM agent và không phải ALB:
một lệnh **SSM Run Command** (`AWS-RunShellScript`, tham số bị base64 hoá) đã chạy
`systemctl stop cloudops-app` lúc **07:17:36–07:17:46Z**. Service chết → ALB health check fail →
target Unhealthy → ASG coi instance là hỏng và **thay bằng máy mới**, user-data khởi động lại app
nên hệ thống tự về trạng thái khoẻ.

Timeline:

```text
07:17:36  Run Command bắt đầu (document AWS-RunShellScript)
07:17:46  lệnh xong, cloudops-app đã dừng
07:19:48  ALB báo unhealthy → ASG terminate i-00bb7ca67e31cf673 + launch i-02423875c0fd46212
07:19:50  máy mới running, app khởi động lại → healthy
07:38:51  verify 09 PASS
```

5. How did I fix it? (exact command or console action)

**Không sửa tay.** Đây là ca **self-healing**: ASG đã thay instance và user-data khởi động lại
service. Việc còn lại là chứng minh trạng thái bằng:
`./bin/lab verify 09` → `service=active health=200 parameter=hello-from-parameter-store` (PASS).

Bài học: symptom hết **không** có nghĩa là sự kiện không xảy ra. Nếu chỉ nhìn trạng thái hiện tại
(target Healthy) thì đã bỏ mất root cause; phải đọc **Activity history** + **Command history**.

6. Prevention / automation

- **Prevent**: IAM deny `ssm:SendCommand` cho mọi principal trừ role vận hành, giới hạn bằng
  `ResourceTag` (chỉ instance tag `Project=soa-c03`); bật approval (Change Manager) cho lệnh
  tác động service.
- **Detect**: CloudTrail ghi `SendCommand` kèm identity + tham số → EventBridge rule → SNS/email;
  bật **SSM Command output → CloudWatch Logs/S3** để giữ output lâu dài.
- **Detect lớp app**: CloudWatch agent đẩy log app + alarm trên `UnHealthyHostCount` để biết sớm
  hơn thay vì chờ 2 phút.
- **Đừng tin base64**: base64 không phải mã hoá; Run Command lưu nguyên văn tham số nên
  obfuscation không che được audit.

7. Exam trap

- **Run Command vs Session Manager**: cả hai đều qua SSM agent, **không cần SSH/port 22**.
  Run Command = chạy script hàng loạt, có Command history; Session Manager = shell tương tác.
  Cả hai cần IAM role + outbound 443 tới `ssm`/`ssmmessages`/`ec2messages` (private subnet không
  NAT thì phải có interface endpoint).
- **`Ping status = ConnectionLost`** là lỗi **lớp kết nối** (agent / IAM role / mạng), không phải
  lỗi của lệnh gửi đi, và **không** liên quan tới ALB.
- **Self-healing che root cause**: khi ASG thay instance, mọi check hiện tại đều xanh; phải đọc
  Activity history (`Cause`) + Command history để tìm sự kiện.
- **Health check math**: interval 15s × unhealthy threshold 3 = **45s lý thuyết**, nhưng thực đo
  từ lúc lệnh xong (07:17:46Z) tới lúc ASG phản ứng (07:19:48Z) là **122s**.
  Chênh lệch **chưa giải thích được** — ghi lại làm câu hỏi mở, không suy đoán.

## Câu hỏi mở (chưa có evidence)

- Vì sao 45s lý thuyết thành 122s thực tế? Ứng viên cần kiểm: thời điểm service thực sự chết
  (systemd stop time), độ trễ ASG đọc ELB health, và health check grace period 600s của ASG.
- Chưa truy **identity** của người gọi `SendCommand` trong CloudTrail (lab không yêu cầu);
  nếu làm tiếp: CloudTrail → Event name `SendCommand` → đọc `userIdentity` + `sourceIPAddress`.
