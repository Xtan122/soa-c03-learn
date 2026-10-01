# WEEK 1 — Monitoring & Logging

> **Mục tiêu tuần:** nhìn metric/log/event → phát hiện vấn đề → tìm nguyên nhân.
> **Domain:** Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%).

- [ ] LAB 01 — CloudWatch Fundamentals
- [ ] LAB 02 — CloudWatch Alarm
- [ ] LAB 03 — CloudWatch Logs
- [ ] LAB 04 — Metric Filter
- [ ] LAB 05 — CloudTrail Investigation
- [ ] LAB 06 — EventBridge
- [ ] LAB 07 — Monitoring Capstone

---

## LAB 01 — CloudWatch Fundamentals

⏱ 1.5h · Tuần 1 · Độ khó ★☆☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
EC2
 │
 ├── CPUUtilization
 ├── NetworkIn
 ├── NetworkOut
 └── StatusCheckFailed
        ↓
   CloudWatch
```

### Phase A — Build
- EC2
- CloudWatch Metrics
- Metric graph
- Period/statistic
- Dashboard

### Phase B — Break
**Incident:** CPU tăng đột biến.

### Phase C — Diagnose
Phải trả lời được:
> Metric nào chứng minh EC2 đang có vấn đề?

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Amazon CloudWatch Getting Started** — https://skillbuilder.aws/learn/HS1HSVQRHK/amazon-cloudwatch-getting-started/9Y34KP2H1T
- 🧪 Workshop: https://catalog.workshops.aws/observability/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 02 — CloudWatch Alarm

⏱ 1.5h · Tuần 1 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
CPU > 60%
    ↓
Alarm
    ↓
SNS
    ↓
Email
```

### Phase A — Build
Tạo alarm + SNS + email.

### Phase B — Break
Cố tình tạo CPU load.

### Phase C — Diagnose
Bonus — hiểu 3 trạng thái:
```text
OK
ALARM
INSUFFICIENT_DATA
```
Phải hiểu **tại sao alarm chuyển trạng thái**.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Turn Your Amazon CloudWatch Alarms into Actionable Signals** — https://skillbuilder.aws/learn/G6QHSA5MWH/turn-your-amazon-cloudwatch-alarms-into-actionable-signals/N4VMDJYSP4
- 🧪 Workshop: https://catalog.workshops.aws/observability/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 03 — CloudWatch Logs

⏱ 1.5h · Tuần 1 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
Application
     ↓
log file
     ↓
CloudWatch Agent
     ↓
CloudWatch Logs
```

### Phase A — Build
- Log group
- Log stream
- retention
- CloudWatch Agent
- Logs Insights

### Phase B — Break
Sinh log lỗi / mất log.

### Phase C — Diagnose
Query:
```sql
fields @timestamp, @message
| sort @timestamp desc
| limit 50
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Collecting and Analyzing Logs with Amazon CloudWatch Logs Insights** (AWS Builder Lab) — https://skillbuilder.aws/learn/UKDQEXHW73/collecting-and-analyzing-logs-with-amazon-cloudwatch-logs-insights/CWM44FRTBU
- 🧪 Workshop: https://catalog.workshops.aws/observability/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 04 — Metric Filter

⏱ 1.5h · Tuần 1 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
Tạo application log:
```text
INFO
INFO
ERROR
INFO
ERROR
```

Tạo:
```text
ERROR
 ↓
Metric Filter
 ↓
Custom Metric
 ↓
Alarm
```

### Phase A — Build
Metric filter + custom metric + alarm.

### Phase B — Break
Bơm thêm `ERROR`.

### Phase C — Diagnose
Đây là pattern rất quan trọng — xác nhận metric filter đếm đúng.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS CloudOps Engineer — Monitoring** — https://skillbuilder.aws/learn/3QENAD9RRZ/aws-cloudops-engineer--monitoring/F4CT9Q7CVY
- 🧪 Workshop: https://catalog.workshops.aws/observability/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 05 — CloudTrail Investigation

⏱ 1.5h · Tuần 1 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Phase A — Build
Thực hiện:
```text
IAM change
S3 change
EC2 API call
```

### Phase B — Break
**Incident:** "Ai đã terminate EC2?"

### Phase C — Diagnose
Dùng CloudTrail để tìm:
- Who?
- What?
- When?
- Source IP?
- API?
- Resource?

Bạn phải điều tra được.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Lab — Enable Traceability through AWS CloudTrail** (AWS Builder Lab) — https://skillbuilder.aws/learn/2EXUEAUWEK/lab--enable-traceability-through-awscloudtrail/SXX4T33UJ2
- 🧪 Workshop: https://catalog.workshops.aws/security/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 06 — EventBridge

⏱ 1.5h · Tuần 1 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
EC2 state change
       ↓
EventBridge Rule
       ↓
SNS
```

Sau đó:
```text
EC2 stopped
    ↓
EventBridge
    ↓
notification
```

### Phase A — Build
Event rule + SNS.

### Phase B — Break
Stop / start EC2.

### Phase C — Diagnose
Hiểu rõ:
**Event pattern vs schedule-based rule.**

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Debugging Event-Driven Applications Using Amazon EventBridge** (AWS Builder Lab) — https://skillbuilder.aws/learn/9W7JBBV5KR/debugging-eventdriven-applications-using-amazon-eventbridge/K367BXFRSV
- 🧪 Workshop: none found
- 📘 AWS Docs: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-ec2-state-change-notification.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 07 — Monitoring Capstone

⏱ 1.5h · Tuần 1 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
EC2
 ├── CloudWatch Metrics
 ├── CloudWatch Logs
 ├── Metric Filter
 ├── Alarm
 ├── CloudTrail
 └── EventBridge
```

### Phase B — Break
**Incident:** Application trả HTTP 500 ngẫu nhiên.

### Phase C — Diagnose
Bạn phải:
1. Detect
2. Find logs
3. Create metric
4. Alarm
5. Trigger EventBridge
6. Notify

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Lab — Implement Logging and Monitoring using AWS CloudTrail and Amazon CloudWatch** (AWS Builder Lab) — https://skillbuilder.aws/learn/BUYXVAX98Y/lab--implement-logging-and-monitoring-using-awscloudtrail-and-amazon-cloudwatch/PY5QN1QXM2
- 🧪 Workshop: https://catalog.workshops.aws/observability/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## 📄 Note cuối tuần
```text
LAB:
SERVICE:

1. What did I build?
2. What failed?
3. How did I detect it?
4. How did I fix it?
5. What exam trap did I learn?
```

⬅️ [README](README.md) · ➡️ [Week 2](week2-reliability.md)
