# WEEK 3 — Deployment & Automation

> **Mục tiêu tuần:** truy cập không cần SSH, quản lý config/secret, IaC, và remediation tự động. Đây là tuần cực quan trọng với SOA.
> **Domains:** Domain 3 – Deployment, Provisioning & Automation (22%); LAB 18 thiên về Domain 4 (16%).

- [ ] LAB 15 — Systems Manager Session Manager
- [ ] LAB 16 — Systems Manager Run Command
- [ ] LAB 17 — Parameter Store
- [ ] LAB 18 — Secrets Manager
- [ ] LAB 19 — CloudFormation
- [ ] LAB 20 — StackSets
- [ ] LAB 21 — Event-Driven Remediation

---

## LAB 15 — Systems Manager Session Manager

⏱ 1.5h · Tuần 3 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
EC2:
```text
No SSH
No public IP
```

### Phase A — Build
Truy cập:
```text
SSM Session Manager
```

### Phase C — Diagnose
Hiểu:
```text
EC2
 ↓
SSM Agent
 ↓
IAM Role
 ↓
SSM
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Getting Started with AWS Systems Manager** — https://skillbuilder.aws/learn/1AG8ZGZN4Z/getting-started-with-aws-systems-manager/PKCXBQX7M5
- 🧪 Workshop: https://builder.aws.com/content/3JhCiFr46V3a4gQVN5EKwISL7OE/aws-systems-manager-deep-dive-session-manager-fleet-manager-run-command-and-memory-metrics
- 📘 AWS Docs: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

---

## LAB 16 — Systems Manager Run Command

⏱ 1.5h · Tuần 3 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Phase A — Build
Dùng Run Command để:
```bash
systemctl status nginx
```
hoặc:
```bash
df -h
```
trên EC2. **Không SSH.**

### Phase C — Diagnose
Hiểu cách Run Command nhận document + target + output.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Using the AWS Systems Manager Run Command for Automation**
- 🧪 Workshop: https://builder.aws.com/content/2dtXf9nEc2TMhEHBKq8PdXAwsnm/run-commands-on-an-ec2-instance-with-aws-systems-manager
- 📘 AWS Docs: https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

---

## LAB 17 — Parameter Store

⏱ 1.5h · Tuần 3 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
Tạo:
```text
/app/dev/db-host
/app/dev/db-port
/app/dev/api-url
```

### Phase A — Build
Application đọc Parameter Store.

### Phase B — Break
Đổi parameter.

### Phase C — Diagnose
Quan sát behavior.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Getting Started with AWS Systems Manager** (Parameter Store modules) — https://skillbuilder.aws/learn/1AG8ZGZN4Z/getting-started-with-aws-systems-manager/PKCXBQX7M5
- 🧪 Workshop: https://builder.aws.com/content/3GYQoH2ezwSD7pQFVvb6mFsaeJM/stop-hardcoding-use-aws-parameter-store-instead-hands-on
- 📘 AWS Docs: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

---

## LAB 18 — Secrets Manager

⏱ 1.5h · Tuần 3 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Phase A — Build
Tạo secret. Application lấy secret thông qua IAM Role.

### Phase C — Diagnose
So sánh:
```text
Parameter Store
vs
Secrets Manager
```
Phải biết **khi nào dùng cái nào**.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Using AWS Secrets Manager**
- 🧪 Workshop: https://catalog.us-east-1.prod.workshops.aws/v2/workshops/8e3a5338-cfc0-4d53-9b97-e8f96c59950a/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
- 🧭 Domain: Domain 4 – Security and Compliance (16%)

---

## LAB 19 — CloudFormation

⏱ 1.5h · Tuần 3 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng stack
```text
VPC
Subnet
SG
EC2
```

### Phase A — Build
Create stack.

### Phase B — Break
Cố tình tạo lỗi để xem:
```text
ROLLBACK_IN_PROGRESS
ROLLBACK_COMPLETE
```

### Phase C — Diagnose
```text
Update Stack
Rollback
Delete
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Using AWS CloudFormation for Automation**
- 🧪 Workshop: https://catalog.workshops.aws/cfn101/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

---

## LAB 20 — StackSets

⏱ 1.5h · Tuần 3 · Độ khó ★★☆ (conceptual nếu không có multi-account)
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng (nếu tài khoản cho phép)
```text
Management account
        ↓
StackSet
   ├── Account A
   ├── Account B
   └── Account C
```

> Nếu không có Organizations/multi-account environment:
> đọc + thực hành conceptual flow, **không cần cố tạo multi-account**.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Using AWS CloudFormation StackSets**
- 🧪 Workshop: https://builder.aws.com/content/2tkt6EW3hI7gATUCbAIc6t4Dr8B/what-s-the-deal-with-aws-cloudformation-stacksets
- 📘 AWS Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

---

## LAB 21 — Event-Driven Remediation

⏱ 1.5h · Tuần 3 · Độ khó ★★★ — **boss lab**
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
EC2 stopped
     ↓
EventBridge
     ↓
Lambda
     ↓
Start EC2
```

### Phase A — Build
Sau đó nâng cấp:
```text
CloudTrail
    ↓
EventBridge
    ↓
Lambda
    ↓
Remediation
    ↓
SNS
```

### Phase C — Diagnose
Bạn phải giải thích được:
> EventBridge Rule khác EventBridge Scheduler/Pipes ở đâu?

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Event Driven Architecture with Amazon API Gateway, Amazon EventBridge and AWS Lambda**
- 🧪 Workshop: https://builder.aws.com/content/2aF37cWDiG7IysTb8ZDVurVOAFd/how-to-get-custom-email-notification-for-ec2-state-changes-using-eventbridge-lambda
- 📘 AWS Docs: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html
- 🧭 Domain: Domain 3 – Deployment, Provisioning & Automation (22%)

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

⬅️ [Week 2](week2-reliability.md) · [README](README.md) · ➡️ [Week 4](week4-security-networking.md)
