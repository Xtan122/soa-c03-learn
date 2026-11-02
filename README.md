# SOA-C03 CloudOps Lab — 24 labs / 30 ngày

> **Hands-on là mũi nhọn.** Repo này không phải giáo trình đọc. Nó là một lab platform:
> mỗi lab có fault inject, verify tự động, cleanup, cost guardrail và evidence.
> Mục tiêu: ngày thi, tay đã chạm đủ 24 tình huống vận hành thật.

**Phạm vi an toàn:** track này **không** dùng multi-account/landing zone (OU, SCP, Control Tower,
IAM Identity Center). Các dịch vụ đó có thể ảnh hưởng điều kiện credit/account; phần
lý thuyết chỉ đọc trong exam guide. Track gồm **24 lab**.

**Deadline cứng**

| Việc | Ngày |
|---|---|
| Track 30 ngày | **2026-10-24 → 2026-11-22** |
| Buffer luyện đề | 2026-11-23 → 2026-11-30 |
| **Xoá toàn bộ tài nguyên** | **2026-12-01** |
| Credit hết hạn | 2026-12-03 |

---

## Quickstart

> **Mỗi buổi lab:** mở `START-HERE.md` và nói với AI:
> `Đọc START-HERE.md và bắt đầu buổi lab hôm nay.`
> Đây là file entrypoint duy nhất; không cần dán toàn bộ rule vào chat.

```bash
# 0. Cần: AWS CLI v2, jq, curl, python3, quyền vào account lab
make init                 # tạo .env, điền account/region
$EDITOR .env              # ALERT_EMAIL, kiểm tra EXPIRY_DATE=2026-12-01
make doctor               # pre-flight
make bootstrap            # budget + core stack + upload app artifacts (~3')
./bin/lab list            # 24 lab
./bin/lab up 00           # lab đầu tiên: verify baseline
./bin/lab preflight 05    # trước mỗi lab: static (thêm --live để read-only AWS)
./bin/lab brief 03        # trước break: khái niệm + baseline + bản đồ + 3 câu hỏi
./bin/lab console 05      # xem đúng đường bấm console của lab
make app-up               # trước các lab cần app (01,02,04–10,12,15,17–23); ~8-12 phút
```

`./bin/lab up <id>` sẽ báo nếu thiếu app stack. Hết buổi nhớ `make app-down`.

Mỗi lab:

```bash
./bin/lab up 05
ALLOW_BREAK=yes ./bin/lab break 05
# ... tự chẩn đoán, không đọc scripts/lib/labs.sh ...
./bin/lab verify 05
./bin/lab note 05
./bin/lab down 05
make app-down             # hết buổi thì tắt app stack
make cost
```

---

## Vì sao repo này khác

| Thường thấy | Repo này |
|---|---|
| 40 file README, không có gì chạy được | 24 lab có `up/break/verify/down` thật |
| "Hãy tạo EC2 rồi xem metric" | App stack + fault catalog + tiêu chí PASS |
| Không có cleanup | `cleanup-all.sh` xoá theo tag + stack, kiểm tra versioned S3/EIP/NAT/RDS |
| Hướng dẫn console chung chung | Mỗi lab có mục **5c**: service → menu → tab → nút, link nhanh, ô cần đọc |
| Phá xong bắt diagnose khi còn mù | Mỗi lab có **5d. Brief**: inventory, baseline, bản đồ, 3 câu dự đoán trước `break` |
| `up` lần 2 dễ fail | Static preflight + build idempotent cho canary/snapshot/endpoint/backup |
| Học xong không có bằng chứng | `evidence/note.md`, `verify-last.txt`, `DONE` |
| Không kiểm soát chi phí | core/app tách rời, budget, `make cost`, deadline 01/12 |
| Lab nào cũng giống lab nào | 5 incident drills + final boss 5 faults |

### Kiến trúc

```text
core stack (chạy 24/7, ~$1-2/tháng)          app stack (bật theo buổi, ~$0.4/3h)
┌──────────────────────────────┐             ┌──────────────────────────────┐
│ VPC 10.42/16                 │             │ Internet → ALB :80           │
│ public + private subnets     │  exports    │            ↓                 │
│ S3 (versioned, SSE-KMS)      │ ──────────> │      ASG t4g.micro :8080     │
│ KMS, CloudTrail, SNS         │             │            ↓                 │
│ IAM roles, SSM parameters    │             │      RDS PostgreSQL          │
└──────────────────────────────┘             │ alarms + EventBridge         │
                                             └──────────────────────────────┘
```

Chi tiết: [`docs/architecture.md`](docs/architecture.md)

---

## 24 lab

| # | Lab | Domain | Thời gian |
|---:|---|---|---:|
| 00 | [Bootstrap: account, budget, core, guardrails](labs/00-bootstrap/README.md) | Foundation | 90' |
| 01 | [CloudWatch metrics, dashboard, alarm, SNS](labs/01-cloudwatch-metrics-alarm/README.md) | D1 | 150' |
| 02 | [CloudWatch Logs, Agent, Insights, metric filter](labs/02-cloudwatch-logs-insights/README.md) | D1 | 150' |
| 03 | [CloudTrail + EventBridge: ai terminate EC2?](labs/03-cloudtrail-eventbridge/README.md) | D1 | 150' |
| 04 | [Monitoring capstone: 500 → alarm → event](labs/04-monitoring-capstone/README.md) | D1 | 180' |
| 05 | [ALB health check → 503](labs/05-alb-health-503/README.md) | D2 | 120' |
| 06 | [ASG scale-out thất bại](labs/06-asg-scaling-failure/README.md) | D2 | 150' |
| 07 | [RDS snapshot, restore, verify dữ liệu](labs/07-rds-backup-restore/README.md) | D2 | 180' |
| 08 | [RDS Multi-AZ + failover + RTO](labs/08-rds-multiaz-dr/README.md) | D2 | 150' |
| 09 | [SSM Session Manager, Run Command, Parameter Store](labs/09-ssm-operations/README.md) | D3 | 120' |
| 10 | [Secrets Manager + KMS AccessDenied](labs/10-secrets-kms/README.md) | D4 | 150' |
| 11 | [CloudFormation rollback + drift + CDK](labs/11-cloudformation-cdk/README.md) | D3 | 150' |
| 12 | [Event-driven remediation: EC2 stopped → Lambda](labs/12-event-remediation/README.md) | D3 | 150' |
| 13 | [IAM + STS AssumeRole](labs/13-iam-sts/README.md) | D4 | 120' |
| 14 | [S3 public exposure: detect, contain, fix](labs/14-s3-security/README.md) | D4 | 150' |
| 15 | [VPC: SG, NACL, route, Flow Logs, Reachability](labs/15-vpc-troubleshooting/README.md) | D5 | 150' |
| 16 | [Private subnet → S3 endpoint + SSM endpoint](labs/16-vpc-endpoint/README.md) | D5 | 180' |
| 17 | [Networking boss: 3 lỗi cùng lúc](labs/17-networking-boss/README.md) | D5 | 180' |
| 18 | [ECS Fargate + Container Insights + ECR](labs/18-ecs-fargate/README.md) | D3 | 180' |
| 19 | [AWS Backup, Config, Cost Explorer, Budgets](labs/19-backup-config-cost/README.md) | D2/D3 | 180' |
| 20 | [Incident: CPU 95% + 5xx + ALB](labs/20-incident-compute-network/README.md) | D1/D2/D5 | 180' |
| 21 | [Incident: DB timeout + AccessDenied](labs/21-incident-data-identity/README.md) | D2/D4 | 180' |
| 22 | [Production capstone: self-healing + backup](labs/22-production-capstone/README.md) | All | 240' |
| 23 | [Final boss: 5 faults](labs/23-final-boss/README.md) | All | 240' |

Lịch chi tiết: [`PLAN-30-DAYS.md`](PLAN-30-DAYS.md) · Map domain: [`docs/exam-map.md`](docs/exam-map.md)
· CLI theo service: [`cheatsheets/aws-cli-soa-c03.md`](cheatsheets/aws-cli-soa-c03.md)
· Khi lỗi: [`docs/troubleshooting.md`](docs/troubleshooting.md)

---

## Luật chơi

1. **Không đọc `scripts/lib/labs.sh` trước khi thử 3 giả thuyết.** Đó là answer key.
2. **Không xoá stack để "fix".** Fix đúng lớp đang hỏng.
3. **Không bỏ verify.** `./bin/lab verify` là định nghĩa của "xong".
4. **Không để `ALLOW_BREAK=yes`** sau khi xong.
5. **Không để app stack qua đêm.**
6. Mỗi lab phải có `evidence/note.md` với root cause + evidence thật.

Chi tiết: [`docs/lab-contract.md`](docs/lab-contract.md)
· Mentor playbook: [`docs/mentor-playbook.md`](docs/mentor-playbook.md)
· Beginner mentor: [`docs/beginner-mentor.md`](docs/beginner-mentor.md)
· Console guide: [`docs/console-guide.md`](docs/console-guide.md)
· AI mentor runbook: [`docs/ai-mentor-runbook.md`](docs/ai-mentor-runbook.md)
· Learner quickstart: [`docs/learner-quickstart.md`](docs/learner-quickstart.md)
· Glossary: [`docs/glossary.md`](docs/glossary.md)
· Lab readiness: [`docs/lab-readiness.md`](docs/lab-readiness.md)
· AI rules: [`AGENTS.md`](AGENTS.md) + [`docs/ai-rules.md`](docs/ai-rules.md)
· Audit gần nhất: [`docs/audit-report.md`](docs/audit-report.md)
· Audit từng lab: [`docs/lab-audit.md`](docs/lab-audit.md)

---

## Chi phí

- Core stack: ~**$1–2/tháng**.
- App stack 3 giờ: ~**$0.30–0.45**.
- Cả 24 lab nếu dọn đúng: ~**$10–25**.
- Bỏ quên app stack 24/7: ~**$70–75/tháng** (không NAT); ~**$115/tháng** nếu bật NAT.
- **Không dùng EKS control plane** (~$73/tháng); dùng ECS Fargate hoặc lab free.

Chi tiết + bảng giá: [`docs/cost-guardrails.md`](docs/cost-guardrails.md)

---

## Commands

```bash
make init            # tạo .env
make doctor          # kiểm tra credentials, budget, stack, app, expiry
make bootstrap       # budget + core stack + upload artifacts
make app-up          # ALB + ASG + RDS (on demand)
make app-down        # tắt meter
make status          # stack, URL, target health, alarms, SSM
make cost            # spend + resource đang chạy
make inventory       # mọi resource tagged Project=soa-c03
make upload          # upload app artifacts
make dash            # tạo/refresh dashboard
make cleanup         # CONFIRM_DESTROY=yes make cleanup
make test            # bash -n, py_compile, cfn-lint (nếu có)

./bin/lab list
./bin/lab up 05
ALLOW_BREAK=yes ./bin/lab break 05
./bin/lab hint 05
./bin/lab verify 05
./bin/lab reset 05
./bin/lab down 05
./bin/lab note 05
./bin/lab progress
```

---

## Requirements

- AWS CLI v2, `jq`, `curl`, `python3` (3.9+), `zip` (hoặc Python zipfile).
- Quyền: CloudFormation, EC2, VPC, IAM, S3, KMS, RDS, ELBv2, ASG, CloudWatch, Logs,
  CloudTrail, SNS, SQS, Lambda, Events, SSM, Secrets Manager, ECS, ECR, Backup, Config,
  Budgets, Cost Explorer.
- Region mặc định: `ap-southeast-1`.
- Account **paid plan** (bạn đang có), credit hết hạn 2026-12-03.

---

## Trạng thái

- 24 lab đã scaffold + fault/verify/cleanup.
- 24 README lab được viết lại cho người mới: mục tiêu, hiện trạng, kiến trúc, triệu chứng,
  nơi chẩn đoán, tiêu chí đúng, exam takeaway, note, cleanup.
- CloudFormation đã pass `cfn-lint` và `aws cloudformation validate-template` (chưa deploy
  vào account của bạn — lần đầu chạy `make bootstrap` là lần test thật).
- Notes CloudWatch/CloudTrail cũ được giữ trong [`notes/`](notes/) để tham khảo;
  evidence của track mới nằm trong `labs/<id>/evidence/`.

---

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
- [Exam overview](https://aws.amazon.com/certification/certified-cloudops-engineer-associate/)
- [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/)
- [VPC pricing](https://aws.amazon.com/vpc/pricing/) · [ELB pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
