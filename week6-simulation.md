# WEEK 6 — FULL CLOUDOPS SIMULATION

> Đây mới là **Hủy Diệt**. Không còn lab hướng dẫn từng bước.
> Mỗi incident xử lý như một CloudOps engineer:
> **1. Detect  2. Collect evidence  3. Identify root cause  4. Remediate  5. Verify  6. Prevent recurrence  7. Automate if possible**

- [ ] LAB 35 — Production Architecture Build
- [ ] LAB 36 — Production Monitoring
- [ ] LAB 37 — Production Incident #1
- [ ] LAB 38 — Production Incident #2
- [ ] LAB 39 — Production Incident #3
- [ ] LAB 40 — THE FINAL BOSS

---

## LAB 35 — Production Architecture Build

⏱ 1.5h · Tuần 6 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
             Internet
                │
             Route53
                │
             ALB
                │
          ┌─────┴─────┐
          │           │
        EC2         EC2
          │           │
          └─────┬─────┘
                │
               RDS
```

### Phase A — Build
Thêm:
```text
CloudWatch
CloudTrail
SSM
SNS
IAM
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Deploying a Highly Available Multi-AZ Architecture** — https://skillbuilder.aws/search?searchText=high%20availability&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/6b77e05c-929d-4b54-9516-3454e46a5c8e
- 📘 AWS Docs: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

---

## LAB 36 — Production Monitoring

⏱ 1.5h · Tuần 6 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Thêm
```text
ALB
 ├── RequestCount
 ├── TargetResponseTime
 ├── HTTPCode
 └── HealthyHostCount

EC2
 ├── CPU
 ├── Network
 └── StatusCheck

RDS
 ├── CPU
 ├── Connections
 ├── FreeStorage
 └── FreeableMemory
```

### Phase A — Build
Tạo dashboard.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Building Amazon CloudWatch Dashboards** — https://skillbuilder.aws/search?searchText=CloudWatch%20dashboard&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/31676d37-bbe9-4992-9cd1-ceae13c5116c
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 37 — Production Incident #1

⏱ 1.5h · Tuần 6 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Verify  [ ] Prevent`

### Scenario
> Website trả 5xx tăng đột biến.

### Bạn không được xem hint
Phải đi theo:
```text
CloudWatch
   ↓
ALB
   ↓
Target
   ↓
EC2
   ↓
Application logs
```
Sau đó fix.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Remediating Application 5xx Errors with Amazon CloudWatch** — https://skillbuilder.aws/search?searchText=troubleshooting&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/6b7b81cc-01fc-4ef8-8427-a03096dc5a81
- 📘 AWS Docs: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 38 — Production Incident #2

⏱ 1.5h · Tuần 6 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Verify  [ ] Prevent`

### Scenario
> EC2 không thể truy cập S3.

Có thể do:
```text
IAM
SG
NACL
Route
Endpoint
Bucket Policy
KMS
```
Bạn phải tìm root cause.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Enabling Private Amazon EC2 Access to Amazon S3** — https://skillbuilder.aws/search?searchText=S3%20access&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/093c6055-093f-4928-ba16-83a79874e2fe
- 📘 AWS Docs: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html
- 🧭 Domain: Domain 5 – Networking and Content Delivery (18%)

---

## LAB 39 — Production Incident #3

⏱ 1.5h · Tuần 6 · Độ khó ★★★
`[ ] Detect  [ ] Evidence  [ ] Root cause  [ ] Remediate  [ ] Verify  [ ] Prevent`

### Scenario
> RDS connection tăng mạnh và application bắt đầu timeout.

### Điều tra
```text
CloudWatch
RDS metrics
Application logs
Connections
CPU
Memory
```
Sau đó đề xuất remediation.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Diagnosing Amazon RDS Connection and Performance Issues** — https://skillbuilder.aws/search?searchText=RDS%20performance&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/3207e1b6-848b-465b-9e6d-b40925bcccdc
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 40 — THE FINAL BOSS

⏱ 1.5h+ · Tuần 6 · Độ khó ★★★★
`[ ] A  [ ] B  [ ] C  [ ] D  [ ] E`

🔥 **Không có hướng dẫn.**

Bạn được cung cấp:
```text
ALB
ASG
EC2
RDS
S3
CloudWatch
CloudTrail
EventBridge
IAM
SSM
VPC
```

### Incident A
```text
ALB → 503
```
### Incident B
```text
EC2 → cannot access S3
```
### Incident C
```text
RDS → connection timeout
```
### Incident D
```text
CPU → 95%
```
### Incident E
```text
IAM → AccessDenied
```

Xử lý từng case như một CloudOps engineer:
```text
1. Detect
2. Collect evidence
3. Identify root cause
4. Remediate
5. Verify
6. Prevent recurrence
7. Automate if possible
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Builder Labs — Multi-Service Incident Response and Remediation** — https://skillbuilder.aws/search?searchText=incident%20response&typeId=aws_builder_lab&page=1
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/workshops/c6043c98-6f3c-4900-beb9-34f85118dc66
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)
- 🔁 Ôn lại cheatsheet: `cheatsheets/incident-triage.md`

---

## 📄 Note cuối tuần & sau cùng
```text
LAB:
SERVICE:

1. What did I build? / Scenario?
2. What failed?
3. How did I detect it?
4. How did I fix it?
5. What exam trap did I learn?
```

⬅️ [Week 5](week5-incident-response.md) · [README](README.md)
