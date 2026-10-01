# WEEK 4 — Security + Networking Operations

> **Mục tiêu tuần:** debug IAM/STS/KMS/S3 và trace toàn bộ đường mạng VPC.
> **Domains:** Domain 4 – Security and Compliance (16%); Domain 5 – Networking and Content Delivery (18%).

- [ ] LAB 22 — IAM Troubleshooting
- [ ] LAB 23 — STS AssumeRole
- [ ] LAB 24 — KMS Troubleshooting
- [ ] LAB 25 — S3 Security Incident
- [ ] LAB 26 — VPC Troubleshooting
- [ ] LAB 27 — VPC Endpoint
- [ ] LAB 28 — Networking Boss Fight

---

## LAB 22 — IAM Troubleshooting

⏱ 1.5h · Tuần 4 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
User/Role
 ↓
S3
```

### Phase B — Break
Cố tình deny:
```text
s3:GetObject
```

### Phase C — Diagnose
Debug:
```text
IAM Policy
Identity Policy
Resource Policy
Explicit Deny
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Lab: Troubleshooting IAM Access Issues**
- 🧪 Workshop: https://builder.aws.com/content/3Isby75bGyrVOGEdohsT1LMPi64/why-your-iam-deny-isnt-always-winning-a-practical-guide-to-aws-policy-evaluation-logic
- 📘 AWS Docs: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html
- 🧭 Domain: Domain 4 – Security and Compliance (16%)

---

## LAB 23 — STS AssumeRole

⏱ 1.5h · Tuần 4 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
Role A
   ↓ AssumeRole
Role B
   ↓
S3
```

### Phase C — Diagnose
Debug trust policy. Đặc biệt:
```text
Trust Policy
vs
Permissions Policy
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Deep Dive with Security: AWS Identity and Access Management (IAM)**
- 🧪 Workshop: https://builder.aws.com/content/2yIbFNFWiq3Ay8JL5DfZmf8X4q3/cross-account-access-in-aws-using-iam-roles-without-iam-users
- 📘 AWS Docs: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html
- 🧭 Domain: Domain 4 – Security and Compliance (16%)

---

## LAB 24 — KMS Troubleshooting

⏱ 1.5h · Tuần 4 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
Tạo encrypted:
```text
S3 object
```

### Phase B — Break
Cố tình:
```text
IAM allows S3
BUT
KMS denies
```

### Phase C — Diagnose
Tìm nguyên nhân. Đây là dạng rất đáng luyện.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Introduction to AWS Key Management Service**
- 🧪 Workshop: https://builder.aws.com/content/3JwQkP4yZ3AosoGmp68NTmu4Lpm/aws-iam-access-denied-why-your-application-has-permission-but-still-cant-access-a-resource
- 📘 AWS Docs: https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html
- 🧭 Domain: Domain 4 – Security and Compliance (16%)

---

## LAB 25 — S3 Security Incident

⏱ 1.5h · Tuần 4 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
S3 bucket.

### Phase C — Diagnose
Kiểm tra:
- Block Public Access
- Bucket Policy
- ACL
- encryption
- versioning
- lifecycle

### Phase B/D — Break & Fix
Cố tình tạo public access rồi tìm cách đóng lại.

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Amazon Simple Storage Service (Amazon S3) Block Public Access**
- 🧪 Workshop: https://builder.aws.com/content/3JqjPi90AFcof5AP3PGSVKRrehZ/an-s-checklist-public-access-versioning-and-recovery
- 📘 AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
- 🧭 Domain: Domain 4 – Security and Compliance (16%)

---

## LAB 26 — VPC Troubleshooting

⏱ 1.5h · Tuần 4 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
Public Subnet
Private Subnet
```

### Phase B — Break
**Incident:** EC2 private không ra Internet.

### Phase C — Diagnose
Debug:
```text
Route Table
IGW
NAT
SG
NACL
```

Không nhìn solution. Tự trace:
```text
EC2
 ↓
ENI
 ↓
Route Table
 ↓
NAT
 ↓
Route
 ↓
IGW
 ↓
Internet
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **AWS SimuLearn: Resolve VPC Routing Conflicts** — https://skillbuilder.aws/learn/E3UGAAPXTQ/aws-simulearn-resolve-vpc-routing-conflicts/DMERQQJJH4
- 🧪 Workshop: https://catalog.workshops.aws/networking/en-US
- 📘 AWS Docs: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html
- 🧭 Domain: Domain 5 – Networking and Content Delivery (18%)

---

## LAB 27 — VPC Endpoint

⏱ 1.5h · Tuần 4 · Độ khó ★★☆
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Dựng
```text
Private EC2
    ↓
VPC Endpoint
    ↓
S3
```

### Phase A — Build
Không cần Internet Gateway/NAT cho S3 access.

### Phase C — Diagnose
Phân biệt:
```text
Gateway Endpoint
Interface Endpoint
```

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Networking Essentials for Cloud Applications on AWS** — https://skillbuilder.aws/learn/6BRHDAUYTF/networking-essentials-for-cloud-applications-on-aws/UTMRCECAY7
- 🧪 Workshop: https://builder.aws.com/content/2b5hpna7zvZdEgaUOeE0xLN95OT/vpc-endpoints-an-alternative-to-nat-gateway
- 📘 AWS Docs: https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html
- 🧭 Domain: Domain 5 – Networking and Content Delivery (18%)

---

## LAB 28 — Networking Boss Fight

⏱ 1.5h · Tuần 4 · Độ khó ★★★
`[ ] Build  [ ] Break  [ ] Diagnose  [ ] Fix  [ ] Verify  [ ] Cleanup`

### Cho một architecture
```text
Internet
   ↓
ALB
   ↓
Private EC2
   ↓
RDS
```

### Phase B — Break
Cố tình phá **3 thứ**:
```text
SG
Route Table
Target Health
```

### Phase C — Diagnose
Bạn phải troubleshoot toàn bộ.

### Phase D — Fix
```text
Verify → Document → Cleanup
```

### 📚 Nguồn tham chiếu
- 🎓 SBTS (search trong account): **Troubleshooting Website Reachability behind a Load Balancer**
- 🧪 Workshop: https://builder.aws.com/content/2me33ZfxzWPiwmF6BbOmbawEeah/dmz-like-setup-in-aws-for-a-three-tier-application
- 📘 AWS Docs: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html
- 🧭 Domain: Domain 5 – Networking and Content Delivery (18%)

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

⬅️ [Week 3](week3-automation.md) · [README](README.md) · ➡️ [Week 5](week5-incident-response.md)
