# Exam map — SOA-C03

## Facts

| Item | Value |
|---|---|
| Questions | 65 (50 scored + 15 unscored) |
| Time | 130 minutes |
| Passing score | 720 / 1000 |
| Fee | USD 150 |
| Domains | D1 22% · D2 22% · D3 22% · D4 16% · D5 18% |

D1 + D2 + D3 = **66%** of the score. Nếu thời gian có hạn, đây là nơi phải chắc.

## 24 lab → domain

| Lab | Domain | Kỹ năng đề thi |
|---|---|---|
| 00 Bootstrap | All | account guardrails, budget, tagging |
| 01 CloudWatch metrics/alarm | D1 | metric math, period, statistic, alarm states, SNS |
| 02 CloudWatch Logs | D1 | agent, log groups, Insights, metric filter |
| 03 CloudTrail + EventBridge | D1 | event history, userIdentity, event pattern |
| 04 Monitoring capstone | D1 | end-to-end detect → alert |
| 05 ALB health/503 | D2 | target group, health check, 502/503/504 |
| 06 ASG scaling failure | D2 | launch template, scaling activity, health check type |
| 07 RDS backup/restore | D2 | snapshot, restore, subnet group, SG |
| 08 RDS Multi-AZ/DR | D2 | failover, endpoint, RTO/RPO, Multi-AZ vs replica |
| 09 SSM operations | D3 | Session Manager, Run Command, Parameter Store |
| 10 Secrets + KMS | D4 | secret retrieval, key policy, explicit deny |
| 11 CloudFormation/CDK | D3 | update, rollback, drift, imports/exports, CDK synth |
| 12 Event remediation | D3 | EventBridge → Lambda, resource policy, idempotency |
| 13 IAM + STS | D4 | trust vs permission, AssumeRole, session |
| 14 S3 security | D4 | BPA, bucket policy, ACL, Access Analyzer |
| 15 VPC troubleshooting | D5 | SG, NACL, route, Flow Logs, Reachability Analyzer |
| 16 VPC endpoint | D5 | Gateway vs Interface, private DNS, route table |
| 17 Networking boss | D5 | multi-layer isolation |
| 18 ECS Fargate | D3 | task vs service, execution role, Container Insights, ECR |
| 19 Backup/Config/Cost | D2/D3 | AWS Backup, Config recorder, Cost Explorer, Budgets |
| 20 Compute/network incident | D1/D2/D5 | triage under multiple symptoms |
| 21 Data/identity incident | D2/D4 | DB path + permission path |
| 22 Production capstone | All | HA, observability, backup, self-healing |
| 23 Final boss | All | 5 simultaneous faults |

## Phải tay làm (Tier 1)

CloudWatch (metrics/logs/alarms/Insights/agent), CloudTrail, EventBridge, SNS, SQS,
SSM, IAM, STS, KMS, Secrets Manager, S3, VPC (SG/NACL/route/endpoint/Flow Logs),
ALB, ASG, RDS (backup/Multi-AZ/Performance Insights), CloudFormation, Lambda,
ECS Fargate, ECR, AWS Backup, Config, Budgets/Cost Explorer.

## Demo 30 phút (Tier 2)

CDK, GuardDuty, Security Hub, Route 53,
CloudFront, DynamoDB, ElastiCache, RDS Proxy, Managed Prometheus/Grafana,
Network Firewall, Transit Gateway, VPC Reachability Analyzer.

## Đọc để nhận diện (Tier 3)

Athena, Firehose, DataSync, FSx, Storage Gateway, Global Accelerator, Shield,
WAF, Macie, Inspector, Service Catalog, RAM, IPAM, Control Tower,
Application Recovery Controller, X-Ray, Bedrock.

## Những điểm SOA-C03 mới hay hỏi

> **Multi-account / landing zone (SCP, Control Tower, IAM Identity Center):** chỉ đọc lý thuyết
> trong exam guide. Không dựng trong account này để tránh ảnh hưởng credit/account.


- **CloudWatch Agent trên EC2/ECS/EKS** (không chỉ EC2).
- **CDK** và CloudFormation (synth, stack, rollback, drift).
- **Multi-account / multi-region**: cross-account role, centralized logging, cross-account dashboard (lý thuyết; không dựng multi-account).
- **Containers**: ECS task vs service, Fargate, ECR, Container Insights.
- **Cost**: Cost Explorer, CUR, Savings Plans, right-sizing.
- **Network**: Network Firewall, Transit Gateway, PrivateLink, Route 53 Resolver DNS Firewall.

## Chiến thuật phòng thi

- 65 câu / 130 phút ≈ 2 phút/câu. Câu dài đọc đáp án trước để tìm keyword.
- Keyword quyết định: *MOST cost-effective*, *LEAST operational overhead*, *MOST secure*,
  *HIGHEST availability*, *real-time*.
- Nếu có giải pháp managed/automation và giải pháp manual, thường chọn managed/automation.
- Loại đáp án vi phạm yêu cầu rõ ràng (public S3 khi cần private, single-AZ khi cần HA).
- Đánh dấu câu khó, quay lại sau; không bỏ trống.
- 15 câu không tính điểm nằm rải rác; đừng hoảng nếu gặp câu lạ.

## Ngưỡng trước khi thi

- ≥ 80% trên bộ đề mới, chưa từng làm, trong 130 phút.
- Giải thích được **tại sao** 3 đáp án sai.
- Không còn domain nào dưới 65%.
- Làm lại được 5 lab incident mà không xem note.
