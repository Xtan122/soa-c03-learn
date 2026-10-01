# 📚 Source Index — toàn bộ nguồn tham chiếu 40 lab

## Cách đọc
- 🎓 **SBTS** — tên khóa/lab để **search trong tài khoản Skill Builder**. Một số link trỏ trang public; link gated ghi `search in account`.
- 🧪 **Workshop** — AWS Workshops / AWS Builder Center (public).
- 📘 **Docs** — tài liệu chính thức `docs.aws.amazon.com` (ổn định nhất).
- 🧭 **Domain** — domain thi SOA-C03 tương ứng.

> ⚠️ **Giới hạn:** nội dung SBTS/Builder Lab/SimuLearn sau đăng nhập **không deep-link được**. Với các lab đó, hãy dùng tên ở cột 🎓 và search trong tài khoản.
> Nguồn neo chung: **Exam Prep Plan SOA-C03** — https://skillbuilder.aws/category/exam-prep/cloudops-engineer-associate-SOA-C03
> Exam guide: https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html

---

## Week 1 — Monitoring & Logging

| Lab | 🎓 SBTS (search in account) | 📘 AWS Docs | 🧪 Workshop |
|---|---|---|---|
| 01 CloudWatch Fundamentals | [Amazon CloudWatch Getting Started](https://skillbuilder.aws/learn/HS1HSVQRHK/amazon-cloudwatch-getting-started/9Y34KP2H1T) | [Working with metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html) | [Observability](https://catalog.workshops.aws/observability/en-US) |
| 02 CloudWatch Alarm | [Turn Alarms into Actionable Signals](https://skillbuilder.aws/learn/G6QHSA5MWH/turn-your-amazon-cloudwatch-alarms-into-actionable-signals/N4VMDJYSP4) | [Alarm that sends email](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) | [Observability](https://catalog.workshops.aws/observability/en-US) |
| 03 CloudWatch Logs | [Collecting/Analyzing Logs with Logs Insights](https://skillbuilder.aws/learn/UKDQEXHW73/collecting-and-analyzing-logs-with-amazon-cloudwatch-logs-insights/CWM44FRTBU) | [Install CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html) | [Observability](https://catalog.workshops.aws/observability/en-US) |
| 04 Metric Filter | [CloudOps Engineer – Monitoring](https://skillbuilder.aws/learn/3QENAD9RRZ/aws-cloudops-engineer--monitoring/F4CT9Q7CVY) | [Monitoring log data](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html) | [Observability](https://catalog.workshops.aws/observability/en-US) |
| 05 CloudTrail Investigation | [Enable Traceability through CloudTrail](https://skillbuilder.aws/learn/2EXUEAUWEK/lab--enable-traceability-through-awscloudtrail/SXX4T33UJ2) | [View CloudTrail events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html) | [Security](https://catalog.workshops.aws/security/en-US) |
| 06 EventBridge | [Debugging Event-Driven Apps with EventBridge](https://skillbuilder.aws/learn/9W7JBBV5KR/debugging-eventdriven-applications-using-amazon-eventbridge/K367BXFRSV) | [EC2 state change notification](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-ec2-state-change-notification.html) | none found |
| 07 Monitoring Capstone | [Logging & Monitoring with CloudTrail + CloudWatch](https://skillbuilder.aws/learn/BUYXVAX98Y/lab--implement-logging-and-monitoring-using-awscloudtrail-and-amazon-cloudwatch/PY5QN1QXM2) | [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html) | [Observability](https://catalog.workshops.aws/observability/en-US) |

## Week 2 — Reliability & Recovery

| Lab | 🎓 SBTS (search in account) | 📘 AWS Docs | 🧪 Workshop |
|---|---|---|---|
| 08 EC2 Status Check | [Introduction to EC2 Application Status Checks](https://skillbuilder.aws/learn/Q9435JUQZ9/introduction-to-ec2-application-status-checks/7WC7TX9Z9B) | [System vs instance status](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-system-instance-status-check.html) | [Observability](https://catalog.workshops.aws/observability/en-US) |
| 09 ALB Health Check | [ELB – Troubleshooting](https://skillbuilder.aws/learn/5R5Q9TN3H4/elastic-load-balancing-elb--troubleshooting/GZTEH5S7D2) | [Target group health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html) | [Networking](https://catalog.workshops.aws/networking/en-US) |
| 10 Auto Scaling | [Maintaining HA with Auto Scaling (Linux)](https://skillbuilder.aws/learn/9JD32YBM69/maintaining-high-availability-with-auto-scaling-for-linux/F659ZE7K47) | [Target tracking scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html) | none found |
| 11 Auto Scaling Failure | [EC2 Observability, Monitoring, Troubleshooting](https://skillbuilder.aws/learn/NVQMVRTS5H/amazon-ec2-observability-monitoring-and-troubleshooting/RC947H252R) | [Instance launch failure](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ts-as-instancelaunchfailure.html) | none found |
| 12 RDS Backup & Restore | [Building with Amazon RDS Databases](https://skillbuilder.aws/learn/NE7Q49VGU9/building-with-amazon-rds-databases/5685GJ8T9J) | [Restore from snapshot](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_RestoreFromSnapshot.html) | none found |
| 13 RDS Multi-AZ | [Architecting HA Multi-Tier Apps on AWS](https://skillbuilder.aws/learn/V32MV5MZ6W/architecting-highly-available-multitier-applications-on-aws/M88JRR82HR) | [Multi-AZ deployments](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html) | none found |
| 14 DR Drill | [AWS Elastic Disaster Recovery Getting Started](https://skillbuilder.aws/learn/7WQ5EEXCJE/aws-elastic-disaster-recovery-getting-started/55ETVSR1E5) | [DR options in the cloud](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) | none found |

## Week 3 — Deployment & Automation

| Lab | 🎓 SBTS (search in account) | 📘 AWS Docs | 🧪 Workshop |
|---|---|---|---|
| 15 SSM Session Manager | [Getting Started with AWS Systems Manager](https://skillbuilder.aws/learn/1AG8ZGZN4Z/getting-started-with-aws-systems-manager/PKCXBQX7M5) | [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) | [SSM deep dive (Builder Center)](https://builder.aws.com/content/3JhCiFr46V3a4gQVN5EKwISL7OE/aws-systems-manager-deep-dive-session-manager-fleet-manager-run-command-and-memory-metrics) |
| 16 SSM Run Command | Using the AWS Systems Manager Run Command for Automation *(search in account)* | [Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html) | [Run commands on EC2 (Builder Center)](https://builder.aws.com/content/2dtXf9nEc2TMhEHBKq8PdXAwsnm/run-commands-on-an-ec2-instance-with-aws-systems-manager) |
| 17 Parameter Store | [Getting Started with AWS Systems Manager](https://skillbuilder.aws/learn/1AG8ZGZN4Z/getting-started-with-aws-systems-manager/PKCXBQX7M5) | [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) | [Stop hardcoding – Parameter Store](https://builder.aws.com/content/3GYQoH2ezwSD7pQFVvb6mFsaeJM/stop-hardcoding-use-aws-parameter-store-instead-hands-on) |
| 18 Secrets Manager | Using AWS Secrets Manager *(search in account)* | [Secrets Manager intro](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) | [Secrets Manager workshop](https://catalog.us-east-1.prod.workshops.aws/v2/workshops/8e3a5338-cfc0-4d53-9b97-e8f96c59950a/en-US) |
| 19 CloudFormation | Using AWS CloudFormation for Automation *(search in account)* | [Update stacks / rollback](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html) | [CFN 101](https://catalog.workshops.aws/cfn101/en-US) |
| 20 StackSets | Using AWS CloudFormation StackSets *(search in account)* | [What is StackSets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html) | [What's the deal with StackSets](https://builder.aws.com/content/2tkt6EW3hI7gATUCbAIc6t4Dr8B/what-s-the-deal-with-aws-cloudformation-stacksets) |
| 21 Event-Driven Remediation | Event Driven Architecture with API Gateway, EventBridge, Lambda *(search in account)* | [EventBridge rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html) | [Email notify EC2 state changes](https://builder.aws.com/content/2aF37cWDiG7IysTb8ZDVurVOAFd/how-to-get-custom-email-notification-for-ec2-state-changes-using-eventbridge-lambda) |

## Week 4 — Security & Networking Operations

| Lab | 🎓 SBTS (search in account) | 📘 AWS Docs | 🧪 Workshop |
|---|---|---|---|
| 22 IAM Troubleshooting | Lab: Troubleshooting IAM Access Issues *(search in account)* | [Policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) | [Why IAM Deny wins](https://builder.aws.com/content/3Isby75bGyrVOGEdohsT1LMPi64/why-your-iam-deny-isnt-always-winning-a-practical-guide-to-aws-policy-evaluation-logic) |
| 23 STS AssumeRole | Deep Dive with Security: IAM *(search in account)* | [Create role for user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html) | [Cross-account access via roles](https://builder.aws.com/content/2yIbFNFWiq3Ay8JL5DfZmf8X4q3/cross-account-access-in-aws-using-iam-roles-without-iam-users) |
| 24 KMS Troubleshooting | Introduction to AWS Key Management Service *(search in account)* | [Key policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html) | [IAM AccessDenied: permission but still can't access](https://builder.aws.com/content/3JwQkP4yZ3AosoGmp68NTmu4Lpm/aws-iam-access-denied-why-your-application-has-permission-but-still-cant-access-a-resource) |
| 25 S3 Security Incident | Amazon S3 Block Public Access *(search in account)* | [Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html) | [S3 checklist: public access, versioning, recovery](https://builder.aws.com/content/3JqjPi90AFcof5AP3PGSVKRrehZ/an-s-checklist-public-access-versioning-and-recovery) |
| 26 VPC Troubleshooting | [AWS SimuLearn: Resolve VPC Routing Conflicts](https://skillbuilder.aws/learn/E3UGAAPXTQ/aws-simulearn-resolve-vpc-routing-conflicts/DMERQQJJH4) | [VPC route tables](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html) | [Networking](https://catalog.workshops.aws/networking/en-US) |
| 27 VPC Endpoint | [Networking Essentials for Cloud Apps](https://skillbuilder.aws/learn/6BRHDAUYTF/networking-essentials-for-cloud-applications-on-aws/UTMRCECAY7) | [Gateway endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) | [VPC endpoints vs NAT](https://builder.aws.com/content/2b5hpna7zvZdEgaUOeE0xLN95OT/vpc-endpoints-an-alternative-to-nat-gateway) |
| 28 Networking Boss Fight | Troubleshooting Website Reachability behind a Load Balancer *(search in account)* | [ALB troubleshooting](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html) | [DMZ-like 3-tier setup](https://builder.aws.com/content/2me33ZfxzWPiwmF6BbOmbawEeah/dmz-like-setup-in-aws-for-a-three-tier-application) |

## Week 5 — Incident Response

| Lab | 🎓 SBTS (Builder Labs search) | 📘 AWS Docs | 🧪 Workshop |
|---|---|---|---|
| 29 EC2 CPU Incident | [EC2 monitoring labs](https://skillbuilder.aws/search?searchText=EC2%20monitoring&typeId=aws_builder_lab&page=1) | [EC2 CloudWatch metrics](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-cloudwatch.html) | [Workshop](https://catalog.workshops.aws/workshops/20c57d32-162e-4ad5-86a6-dff1f8de4b3c) |
| 30 EC2 Unreachable | [EC2 connectivity labs](https://skillbuilder.aws/search?searchText=EC2%20connectivity&typeId=aws_builder_lab&page=1) | [Troubleshooting connecting](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingConnecting.html) | [Workshop](https://catalog.workshops.aws/workshops/04e6e6c8-c19b-40f9-8cc7-945669ca86b4) |
| 31 ALB 503 | [ELB labs](https://skillbuilder.aws/search?searchText=Elastic%20Load%20Balancing&typeId=aws_builder_lab&page=1) | [ALB troubleshooting](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/e4953d7d-f92f-4521-89a5-0002765de750) |
| 32 RDS Connection Failure | [RDS labs](https://skillbuilder.aws/search?searchText=Amazon%20RDS&typeId=aws_builder_lab&page=1) | [RDS troubleshooting](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/0135d1da-9f07-470c-9845-44ead3c78212) |
| 33 IAM AccessDenied | [IAM permissions labs](https://skillbuilder.aws/search?searchText=IAM%20permissions&typeId=aws_builder_lab&page=1) | [Troubleshoot access denied](https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/cf795253-d458-4381-8307-3900f43b3334) |
| 34 CloudTrail Forensics | [CloudTrail labs](https://skillbuilder.aws/search?searchText=CloudTrail&typeId=aws_builder_lab&page=1) | [CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/7e9f67a3-985a-4e9c-b38b-2d54a70d0da7) |

## Week 6 — Full CloudOps Simulation

| Lab | 🎓 SBTS (Builder Labs search) | 📘 AWS Docs | 🧪 Workshop |
|---|---|---|---|
| 35 Architecture Build | [High availability labs](https://skillbuilder.aws/search?searchText=high%20availability&typeId=aws_builder_lab&page=1) | [Route 53 routing policies](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/6b77e05c-929d-4b54-9516-3454e46a5c8e) |
| 36 Production Monitoring | [CloudWatch dashboard labs](https://skillbuilder.aws/search?searchText=CloudWatch%20dashboard&typeId=aws_builder_lab&page=1) | [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/31676d37-bbe9-4992-9cd1-ceae13c5116c) |
| 37 Incident #1 (5xx) | [Troubleshooting labs](https://skillbuilder.aws/search?searchText=troubleshooting&typeId=aws_builder_lab&page=1) | [ALB access logs](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/6b7b81cc-01fc-4ef8-8427-a03096dc5a81) |
| 38 Incident #2 (EC2→S3) | [S3 access labs](https://skillbuilder.aws/search?searchText=S3%20access&typeId=aws_builder_lab&page=1) | [S3 VPC endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/093c6055-093f-4928-ba16-83a79874e2fe) |
| 39 Incident #3 (RDS) | [RDS performance labs](https://skillbuilder.aws/search?searchText=RDS%20performance&typeId=aws_builder_lab&page=1) | [Performance Insights](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/3207e1b6-848b-465b-9e6d-b40925bcccdc) |
| 40 Final Boss | [Incident response labs](https://skillbuilder.aws/search?searchText=incident%20response&typeId=aws_builder_lab&page=1) | [Alarm that sends email](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) | [Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/c6043c98-6f3c-4900-beb9-34f85118dc66) |

---

## Trạng thái xác minh
- ✅ **AWS Docs** links: dạng `docs.aws.amazon.com` canonical — ổn định cao.
- ✅ **Skill Builder** links trong Week 1–4: dạng chi tiết khóa học public, đã được kiểm tra trả về hợp lệ.
- 🔎 **Week 5–6** Skill Builder: link dạng **search query** (an toàn, luôn hoạt động) vì các Builder Lab này phần lớn gated; luôn kèm tên lab để search.
- ⚠️ Vài **Workshop link** trỏ `catalog.us-east-1.prod.workshops.aws` — nếu đổi Region/không tìm thấy, dùng landing chung: https://catalog.workshops.aws/
- 🎓 Các mục `search in account`: nội dung chỉ hiển thị khi đăng nhập SBTS; search đúng tên sẽ ra.

⬅️ [README](../README.md)
