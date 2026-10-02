# SOA-C03 Lab Hủy Diệt — 6 tuần / 40 labs

> **CloudOps Engineer thực chiến.** Mục tiêu sau 6 tuần: nhìn một incident AWS và đi theo chuỗi
> **Detect → Diagnose → Fix → Automate → Prevent**.

**Nhịp:** 6 ngày/tuần × ~1.5h/ngày = ~54 giờ · Ngày thứ 7: nghỉ hoặc catch-up.
**Tỷ lệ:** 70% Console/CLI hands-on · 20% Skill Builder/SBTS · 10% notes.
Practice exam chỉ bắt đầu mạnh từ **tuần 5–6**.

---

## 🎛️ Dashboard tiến độ (tick khi xong từng lab)

> Đếm số `[x]` để biết tiến độ. Mỗi lab có checklist phase riêng trong file tuần.

### Week 1 — Monitoring & Logging → `week1-monitoring.md`
- [x] LAB 01 — CloudWatch Fundamentals
- [x] LAB 02 — CloudWatch Alarm
- [x] LAB 03 — CloudWatch Logs
- [ ] LAB 04 — Metric Filter
- [ ] LAB 05 — CloudTrail Investigation
- [ ] LAB 06 — EventBridge
- [ ] LAB 07 — Monitoring Capstone

### Week 2 — Reliability & Recovery → `week2-reliability.md`
- [ ] LAB 08 — EC2 Status Check Incident
- [ ] LAB 09 — ALB Health Check
- [ ] LAB 10 — Auto Scaling
- [ ] LAB 11 — Auto Scaling Failure
- [ ] LAB 12 — RDS Backup & Restore
- [ ] LAB 13 — RDS Multi-AZ
- [ ] LAB 14 — Disaster Recovery Drill

### Week 3 — Deployment & Automation → `week3-automation.md`
- [ ] LAB 15 — Systems Manager Session Manager
- [ ] LAB 16 — Systems Manager Run Command
- [ ] LAB 17 — Parameter Store
- [ ] LAB 18 — Secrets Manager
- [ ] LAB 19 — CloudFormation
- [ ] LAB 20 — StackSets
- [ ] LAB 21 — Event-Driven Remediation

### Week 4 — Security & Networking Operations → `week4-security-networking.md`
- [ ] LAB 22 — IAM Troubleshooting
- [ ] LAB 23 — STS AssumeRole
- [ ] LAB 24 — KMS Troubleshooting
- [ ] LAB 25 — S3 Security Incident
- [ ] LAB 26 — VPC Troubleshooting
- [ ] LAB 27 — VPC Endpoint
- [ ] LAB 28 — Networking Boss Fight

### Week 5 — Troubleshooting / Incident Response → `week5-incident-response.md`
- [ ] LAB 29 — EC2 CPU Incident
- [ ] LAB 30 — EC2 Unreachable
- [ ] LAB 31 — ALB 503
- [ ] LAB 32 — RDS Connection Failure
- [ ] LAB 33 — IAM AccessDenied
- [ ] LAB 34 — CloudTrail Forensics

### Week 6 — Full CloudOps Simulation → `week6-simulation.md`
- [ ] LAB 35 — Production Architecture Build
- [ ] LAB 36 — Production Monitoring
- [ ] LAB 37 — Production Incident #1
- [ ] LAB 38 — Production Incident #2
- [ ] LAB 39 — Production Incident #3
- [ ] LAB 40 — THE FINAL BOSS

---

## 🗺️ Tổng quan

| Tuần | Chủ đề | Labs |
|---|---|---:|
| Week 1 | Monitoring & Logging | 7 |
| Week 2 | Reliability & Recovery | 7 |
| Week 3 | Deployment & Automation | 7 |
| Week 4 | Security & Networking Operations | 7 |
| Week 5 | Troubleshooting / Incident Response | 6 |
| Week 6 | Full CloudOps Simulation | 6 |
| **Tổng** | | **40** |

---

## 📅 Lịch 6 tuần

| Ngày | Lab | ✔ |
|---|---|---|
| **W1-D1** | 01 CloudWatch | [ ] |
| W1-D2 | 02 Alarm | [ ] |
| W1-D3 | 03 Logs | [x] |
| W1-D4 | 04 Metric Filter | [ ] |
| W1-D5 | 05 CloudTrail | [ ] |
| W1-D6 | 06 EventBridge | [ ] |
| W1-D7 | nghỉ |  |
| **W2-D1** | 08 EC2 Status | [ ] |
| W2-D2 | 09 ALB | [ ] |
| W2-D3 | 10 ASG | [ ] |
| W2-D4 | 11 ASG Failure | [ ] |
| W2-D5 | 12 RDS Backup | [ ] |
| W2-D6 | 13 RDS Multi-AZ + 14 DR | [ ] |
| W2-D7 | nghỉ |  |
| **W3-D1** | 15 SSM | [ ] |
| W3-D2 | 16 Run Command | [ ] |
| W3-D3 | 17 Parameter Store | [ ] |
| W3-D4 | 18 Secrets Manager | [ ] |
| W3-D5 | 19 CloudFormation | [ ] |
| W3-D6 | 20 StackSets + 21 Event Remediation | [ ] |
| W3-D7 | nghỉ |  |
| **W4-D1** | 22 IAM | [ ] |
| W4-D2 | 23 STS | [ ] |
| W4-D3 | 24 KMS | [ ] |
| W4-D4 | 25 S3 Security | [ ] |
| W4-D5 | 26 VPC | [ ] |
| W4-D6 | 27 Endpoint + 28 Networking Boss | [ ] |
| W4-D7 | nghỉ |  |
| **W5-D1** | 29 CPU Incident | [ ] |
| W5-D2 | 30 EC2 unreachable | [ ] |
| W5-D3 | 31 ALB 503 | [ ] |
| W5-D4 | 32 RDS failure | [ ] |
| W5-D5 | 33 IAM AccessDenied | [ ] |
| W5-D6 | 34 CloudTrail Forensics | [ ] |
| W5-D7 | nghỉ |  |
| **W6-D1** | 35 Architecture | [ ] |
| W6-D2 | 36 Monitoring | [ ] |
| W6-D3 | 37 Incident #1 | [ ] |
| W6-D4 | 38 Incident #2 | [ ] |
| W6-D5 | 39 Incident #3 | [ ] |
| W6-D6 | **40 Final Boss** | [ ] |
| W6-D7 | Practice exam | [ ] |

---

## ⏱️ Template 1.5h/ngày

```text
10 min | Skill Builder / đọc concept
50 min | Build lab
20 min | Break + troubleshoot
10 min | Note
```

**Đừng dành 60–90 phút xem video.**

---

## 🔥 Luật của Lab Hủy Diệt

Không làm lab theo kiểu copy tutorial. Mỗi lab phải có 4 phases:

### Phase A — Build
```text
Dựng infrastructure
```
### Phase B — Break
```text
Cố tình phá
```
### Phase C — Diagnose
Không xem solution. Chỉ dùng:
```text
CloudWatch
CloudTrail
AWS Console
AWS CLI
SSM
Logs
```
### Phase D — Fix
```text
Verify → Document → Cleanup
```

---

## 📒 Note sau mỗi lab (5 dòng)

Xem `templates/lab-note.md`.

```text
LAB:
SERVICE:

1. What did I build?
2. What failed?
3. How did I detect it?
4. How did I fix it?
5. What exam trap did I learn?
```

Ví dụ:
```text
LAB: VPC Troubleshooting

1. Private EC2 → NAT → Internet
2. Route table missing 0.0.0.0/0
3. Checked route table + connectivity
4. Added route to NAT
5. SG allows traffic ≠ route exists
```

---

## 💰 Cost control

### Có thể dùng thường xuyên
EC2 nhỏ · S3 · Lambda · CloudWatch · CloudTrail · EventBridge · IAM · SSM · DynamoDB · SNS · SQS

### Chỉ bật trong lúc lab rồi xóa
RDS · ALB · ASG · NAT Gateway · CloudFront · Route 53 · VPC Endpoint có phí · KMS usage nếu không cần

### Không đưa vào core lab
**EKS.** SOA không yêu cầu dựng EKS để chứng minh CloudOps skill, chi phí và cleanup không đáng với mục tiêu 6 tuần.

---

## 🎯 Dùng Skill Builder thế nào?

Không học từ A → Z. Mỗi tuần:
```text
AWS Skill Builder → Domain tương ứng → Learning content → Builder Lab
      → Tự rebuild lại → Break it → Troubleshoot
```
Tận dụng **Builder Labs/SBTS** đã có. Nguồn tham chiếu đã gắn ở từng lab và tổng hợp tại `sources/source-index.md`.

---

## 🧨 Một thay đổi đặc biệt khuyên dùng

**Đừng học 40 lab này như 40 bài độc lập.** Xây một **AWS Operations Sandbox** từ Week 1 rồi liên tục nâng cấp:

```text
                  ┌──────── CloudTrail
                  │
Internet → ALB → ASG → EC2
             │      │
             │      ├── CloudWatch
             │      └── SSM
             │
             └────→ RDS

S3 ←──── IAM / KMS
 │
 └──── EventBridge → Lambda → SNS
```

Đến Week 6, toàn bộ hệ thống này trở thành **production-like playground** để cố tình phá.

Đó là cách học SOA-C03: **không học thuộc "dịch vụ X dùng để làm gì", mà luyện phản xạ "hệ thống X đang chết, tôi phải nhìn đâu trước?"**

---

## 📂 Cấu trúc repo

```text
soa-c03/
├── README.md                    # file này
├── week1-monitoring.md          # LAB 01–07
├── week2-reliability.md         # LAB 08–14
├── week3-automation.md          # LAB 15–21
├── week4-security-networking.md # LAB 22–28
├── week5-incident-response.md   # LAB 29–34
├── week6-simulation.md          # LAB 35–40
├── cheatsheets/
│   ├── incident-triage.md
│   └── services-map.md
├── templates/lab-note.md
└── sources/source-index.md
```

> **Ghi chú nguồn:** Nguồn SBTS là tên khóa/lab + link catalog public để bạn search trong tài khoản.
> Nội dung sau đăng nhập (Builder Lab/SimuLearn gated) không deep-link được. Nguồn `docs.aws.amazon.com` ổn định nhất.
