# WEEK 2 — Reliability & Recovery

> **Mục tiêu tuần:** giữ hệ thống sống, phục hồi khi sự cố, hiểu backup/HA/DR.
> **Domains:** Domain 1 & Domain 2 – Reliability and Business Continuity (22%).

- [ ] LAB 08 — EC2 Status Check Incident
- [ ] LAB 09 — ALB Health Check
- [ ] LAB 10 — Auto Scaling
- [ ] LAB 11 — Auto Scaling Failure
- [ ] LAB 12 — RDS Backup & Restore
- [ ] LAB 13 — RDS Multi-AZ
- [ ] LAB 14 — Disaster Recovery Drill

---

## LAB 08 — EC2 Status Check Incident

⏱ 1.5h · Tuần 2 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Phase A — Build
EC2 cơ bản.

### Phase B — Break
Cố tình tạo:
- system status issue
- instance status issue

### Phase C — Diagnose
Phân biệt:
```text
System status check
Instance status check
```

### Phase D — Fix
Tìm remediation.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Introduction to EC2 Application Status Checks** — https://skillbuilder.aws/learn/Q9435JUQZ9/introduction-to-ec2-application-status-checks/7WC7TX9Z9B
- 🧪 Workshop: https://catalog.workshops.aws/observability/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-system-instance-status-check.html
- 🧭 Domain: Domain 1 – Monitoring, Logging, Analysis, Remediation & Performance Optimization (22%)

---

## LAB 09 — ALB Health Check

⏱ 1.5h · Tuần 2 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
Client
 ↓
ALB
 ↓
EC2
```

### Phase B — Break
Phá:
```text
HTTP 80
```
hoặc application.

### Phase C — Diagnose
Debug:
```text
ALB
 ↓
Target Group
 ↓
Health Check
 ↓
EC2
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Elastic Load Balancing (ELB) — Troubleshooting** — https://skillbuilder.aws/learn/5R5Q9TN3H4/elastic-load-balancing-elb--troubleshooting/GZTEH5S7D2
- 🧪 Workshop: https://catalog.workshops.aws/networking/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 10 — Auto Scaling

⏱ 1.5h · Tuần 2 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
ALB
 ↓
ASG
 ├── EC2
 ├── EC2
 └── EC2
```

### Phase A — Build
Thiết lập:
```text
Target CPU = 50%
Min = 1
Desired = 1
Max = 3
```

### Phase B — Break
Stress CPU.

### Phase C — Diagnose
Quan sát:
```text
1 → 2 → 3
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Maintaining High Availability with Auto Scaling (for Linux)** (AWS Builder Lab) — https://skillbuilder.aws/learn/9JD32YBM69/maintaining-high-availability-with-auto-scaling-for-linux/F659ZE7K47
- 🧪 Workshop: none found
- 📘 AWS Docs: https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 11 — Auto Scaling Failure

⏱ 1.5h · Tuần 2 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Phase A — Build
ASG hoạt động bình thường.

### Phase B — Break
Cố tình:
- bad AMI
- wrong SG
- wrong subnet
- broken user-data

ASG không launch instance.

### Phase C — Diagnose
Bạn phải tìm:
> **Tại sao ASG không scale được?**

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Amazon EC2 Observability, Monitoring, and Troubleshooting** — https://skillbuilder.aws/learn/NVQMVRTS5H/amazon-ec2-observability-monitoring-and-troubleshooting/RC947H252R
- 🧪 Workshop: none found
- 📘 AWS Docs: https://docs.aws.amazon.com/autoscaling/ec2/userguide/ts-as-instancelaunchfailure.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 12 — RDS Backup & Restore

⏱ 1.5h · Tuần 2 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
RDS nhỏ.

### Phase A — Build
```text
DB
 ↓
Snapshot
 ↓
Delete
 ↓
Restore
```

### Phase C — Diagnose
Hiểu:
- automated backup
- manual snapshot
- restore
- retention

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Building with Amazon RDS Databases** (AWS Builder Lab) — https://skillbuilder.aws/learn/NE7Q49VGU9/building-with-amazon-rds-databases/5685GJ8T9J
- 🧪 Workshop: none found
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_RestoreFromSnapshot.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 13 — RDS Multi-AZ

⏱ 1.5h · Tuần 2 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

> Không cần giữ lâu để tiết kiệm tiền.

### Dựng
```text
Primary
   ↓
Standby
```

### Phase C — Diagnose
Hiểu:
- Multi-AZ ≠ Read Replica
- failover
- endpoint
- synchronous replication

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Architecting Highly Available Multi-Tier Applications on AWS** (AWS Builder Lab) — https://skillbuilder.aws/learn/V32MV5MZ6W/architecting-highly-available-multitier-applications-on-aws/M88JRR82HR
- 🧪 Workshop: none found
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

---

## LAB 14 — Disaster Recovery Drill

⏱ 1.5h · Tuần 2 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng mini
```text
Application
    ↓
RDS
    ↓
Backup
```

### Phase B — Break
Giả lập:
> "Database bị xóa."

### Phase C — Diagnose
Bạn phải thực hiện:
```text
Detect
 ↓
Restore
 ↓
Reconnect application
 ↓
Verify
```

### Phase D — Fix
Viết lại **RTO/RPO** của solution.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS Elastic Disaster Recovery Getting Started** — https://skillbuilder.aws/learn/7WQ5EEXCJE/aws-elastic-disaster-recovery-getting-started/55ETVSR1E5
- 🧪 Workshop: none found
- 📘 AWS Docs: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html
- 🧭 Domain: Domain 2 – Reliability and Business Continuity (22%)

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

⬅️ [Week 1](week1-monitoring.md) · [README](README.md) · ➡️ [Week 3](week3-automation.md)
