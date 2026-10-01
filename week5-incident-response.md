# WEEK 5 — Incident Response

> Tuần này **không học service mới nhiều**. Thay vào đó: **Tôi đưa incident → bạn tìm cách giải quyết.**
> Mỗi lab đi theo khung: **Detection → Evidence → Root cause → Remediation → Prevention.**

- [ ] LAB 29 — EC2 CPU Incident
- [ ] LAB 30 — EC2 Unreachable
- [ ] LAB 31 — ALB 503
- [ ] LAB 32 — RDS Connection Failure
- [ ] LAB 33 — IAM AccessDenied
- [ ] LAB 34 — CloudTrail Forensics

> 💡 Bắt đầu mạnh practice exam từ tuần này. Dùng cheatsheet `cheatsheets/incident-triage.md` khi bí.

---

## LAB 29 — EC2 CPU Incident

⏱ 1.5h · Tuần 5 · Độ khó ★★☆
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Prevention`

### Scenario
> CPU 95%.

### Bạn phải xác định
```text
Detection
Evidence
Root cause
Remediation
Prevention
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Monitoring Amazon EC2 with Amazon CloudWatch** — https://skillbuilder.aws/search?searchText=EC2%20monitoring&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.workshops.aws/workshops/20c57d32-162e-4ad5-86a6-dff1f8de4b3c
- 📘 AWS Docs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-cloudwatch.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 30 — EC2 Unreachable

⏱ 1.5h · Tuần 5 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Prevention`

### Scenario
> SSH timeout.

### Bạn phải xác định
**Không được reboot ngay.** Check:
```text
Instance status
SG
NACL
Route
Public IP
Network ACL
OS
SSM
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Troubleshooting Amazon EC2 Connectivity and SSH Access** — https://skillbuilder.aws/search?searchText=EC2%20connectivity&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.workshops.aws/workshops/04e6e6c8-c19b-40f9-8cc7-945669ca86b4
- 📘 AWS Docs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingConnecting.html
- 🧭 Domain: Domain 5 – Networking and Content Delivery (18%)

---

## LAB 31 — ALB 503

⏱ 1.5h · Tuần 5 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Prevention`

### Scenario
```text
Client
 ↓
ALB
 ↓
503
```

### Investigate
```text
Target Group
Health Check
SG
Application
Port
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Troubleshooting Elastic Load Balancing and Backend Health** — https://skillbuilder.aws/search?searchText=Elastic%20Load%20Balancing&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/e4953d7d-f92f-4521-89a5-0002765de750
- 📘 AWS Docs: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 32 — RDS Connection Failure

⏱ 1.5h · Tuần 5 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Prevention`

### Scenario
```text
EC2
 ↓
RDS
 ❌ timeout
```

### Check
```text
SG
Subnet
Route
Port
DNS
RDS status
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Connecting to and Troubleshooting Amazon RDS Databases** — https://skillbuilder.aws/search?searchText=Amazon%20RDS&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/0135d1da-9f07-470c-9845-44ead3c78212
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 33 — IAM AccessDenied

⏱ 1.5h · Tuần 5 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Prevention`

### Scenario
```text
Lambda
 ↓
S3
 ❌ AccessDenied
```

### Debug
```text
Lambda execution role
 ↓
IAM policy
 ↓
Bucket policy
 ↓
KMS
 ↓
SCP
```

Đây là lab rất đáng tiền.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Troubleshooting IAM Access Denied Errors** — https://skillbuilder.aws/search?searchText=IAM%20permissions&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/cf795253-d458-4381-8307-3900f43b3334
- 📘 AWS Docs: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html
- 🧭 Domain: Domain 4 – Security and Compliance (16%)

---

## LAB 34 — CloudTrail Forensics

⏱ 1.5h · Tuần 5 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Prevention`

### Scenario
> Một resource production bị thay đổi ngoài dự kiến.

### Tìm
```text
Who
When
What
API
Source IP
User agent
```
Sau đó đưa ra remediation.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Analyzing Activity with AWS CloudTrail** — https://skillbuilder.aws/search?searchText=CloudTrail&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/7e9f67a3-985a-4e9c-b38b-2d54a70d0da7
- 📘 AWS Docs: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## 📄 Note cuối tuần
```text
LAB:
SERVICE:

1. What did I build? / Scenario?
2. What failed?
3. How did I detect it?
4. How did I fix it?
5. What exam trap did I learn?
```

⬅️ [Week 4](week4-security-networking.md) · [README](README.md) · ➡️ [Week 6](week6-simulation.md)
