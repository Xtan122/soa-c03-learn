# 30-day hands-on plan

**Mục tiêu:** hoàn thành 24 lab tay + 4 checkpoint trong 30 ngày, trước khi credit hết hạn.
**Nhịp:** 2.5–3.5 giờ/ngày, 6 ngày/tuần. Ngày còn lại để catch-up hoặc nghỉ.

**Mốc cứng**

| Việc | Ngày |
|---|---|
| Bắt đầu | 2026-10-24 |
| Xong 24 lab | 2026-11-21 |
| Buffer luyện đề | 2026-11-22 → 2026-11-30 |
| **Xoá toàn bộ tài nguyên** | **2026-12-01** |
| Credit hết hạn | 2026-12-03 |

> **Không bật multi-account/landing zone (SCP, Control Tower, IAM Identity Center).**
> Các dịch vụ đó có thể ảnh hưởng điều kiện credit/account. Chỉ học lý thuyết trong exam guide,
> không gọi API.

> Bạn đã làm CloudWatch/CloudTrail cơ bản trước đây. Lab 01–03 của track này là bản
> "có verify + fault + cleanup"; có thể chạy nhanh hơn, nhưng **vẫn phải verify**.

## Lịch

| Ngày | Date | Lab | Nội dung | Chi phí |
|---:|---|---|---|---|
| 1 | 10-24 | `00` | Bootstrap: budget, core stack, S3/KMS/CloudTrail, guardrails | low |
| 2 | 10-25 | `01` | CloudWatch metric, dashboard, alarm, SNS | low |
| 3 | 10-26 | `02` | CloudWatch Agent, Logs Insights, metric filter | low |
| 4 | 10-27 | `03` | CloudTrail + EventBridge: ai terminate EC2? | low |
| 5 | 10-28 | `04` | Capstone monitoring: 500 → metric → alarm → event | low |
| 6 | 10-29 | — | Official 20-question set + review từng câu sai | $0 |
| 7 | 10-30 | — | Catch-up / nghỉ / đọc exam guide | $0 |
| 8 | 10-31 | `05` | ALB health check → 503 | low |
| 9 | 11-01 | `06` | ASG scale-out thất bại | low |
| 10 | 11-02 | `07` | RDS snapshot, restore, verify rows | medium |
| 11 | 11-03 | `08` | RDS Multi-AZ, failover, đo RTO | medium |
| 12 | 11-04 | `09` | SSM Session Manager, Run Command, Parameter Store | low |
| 13 | 11-05 | `10` | Secrets Manager + KMS AccessDenied | low |
| 14 | 11-06 | — | Mock #1 (D1–D2, 30–40 câu) + review | $0 |
| 15 | 11-07 | `11` | CloudFormation rollback, drift, CDK synth | low |
| 16 | 11-08 | `12` | EventBridge → Lambda remediation | low |
| 17 | 11-09 | `13` | IAM + STS AssumeRole | low |
| 18 | 11-10 | `14` | S3 public exposure: detect, contain, fix | low |
| 19 | 11-11 | `15` | VPC SG/NACL/route + Flow Logs + Reachability | medium |
| 20 | 11-12 | `16` | Private subnet → S3 endpoint + SSM endpoint | medium |
| 21 | 11-13 | — | Mock #2 (D3–D4, 30–40 câu) + review | $0 |
| 22 | 11-14 | `17` | Networking boss: 3 lỗi cùng lúc | medium |
| 23 | 11-15 | `18` | ECS Fargate + Container Insights + ECR | medium |
| 24 | 11-16 | `19` | AWS Backup, Config, Cost Explorer, Budgets | low |
| 25 | 11-17 | `20` | Incident: CPU + 5xx + ALB | low |
| 26 | 11-18 | `21` | Incident: DB timeout + AccessDenied | low |
| 27 | 11-19 | — | Mock #3 (full 65 câu/130 phút) + review | $0 |
| 28 | 11-20 | `22` | Production capstone: self-healing + backup | medium |
| 29 | 11-21 | `23` | Final boss: 5 faults | medium |
| 30 | 11-22 | — | Review evidence, cheat sheet, nghỉ sớm | $0 |

### Buffer 23–30/11

- Mua bộ đề (Tutorials Dojo/official practice exam) và làm **2–3 đề full**.
- Mỗi đề: 130 phút, không mở tài liệu; review 60–90 phút.
- Domain nào < 65%: làm lại 1 lab tương ứng + đọc AWS docs 30 phút.
- 30/11: nghỉ hoàn toàn. **01/12: cleanup.**
- 02–03/12: chỉ xem cheat sheet, không học mới.

## Daily loop

```text
10'  Đọc đúng task statement trong exam guide
10'  Vẽ luồng: user → ALB → app → DB → log/metric
5'   Dự đoán 3 cách hệ thống có thể hỏng
90'  ./bin/lab up <id> → break → diagnose mù (timer 20') → fix
20'  ./bin/lab verify <id>; lưu evidence
10'  ./bin/lab note <id>
10'  ./bin/lab down <id>; make cost
```

## Gate (không được bỏ qua)

| Gate | Điều kiện |
|---|---|
| Sau ngày 6 | Official 20q ≥ 50% |
| Sau ngày 14 | Mock #1 ≥ 60% |
| Sau ngày 21 | Mock #2 ≥ 65% |
| Sau ngày 27 | Mock #3 ≥ 75% |
| Trước khi thi | Mock mới ≥ 80%, không domain < 65% |

Nếu fail gate: **không học lab mới**, làm lại 2 lab yếu + 30 phút docs. Chậm 1 ngày tốt hơn
đi tiếp với lỗ hổng.

## Nếu tụt tiến độ

Cắt theo thứ tự:

1. `19` Backup/Config/Cost → chỉ làm AWS Backup + Budgets, bỏ Config recorder.
2. `18` ECS Fargate → dùng lab free Skill Builder.
3. `16` VPC endpoint → chỉ đọc luồng, không dựng interface endpoint.

**Không cắt:** `05`–`17`, `20`–`23`. Đây là xương sống của D1/D2/D3/D5.

## Checklist mỗi cuối tuần

```bash
make doctor
make inventory
make cost
./bin/lab progress
```

- Không có resource ngoài giờ lab.
- Không có resource thiếu tag `ExpiryDate`.
- `app stack` đã xuống.
- Ít nhất 5 note mới có root cause + evidence.
