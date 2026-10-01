# 🧭 Services Map — dịch vụ → dùng khi nào (SOA-C03)

## Theo Domain

### D1 — Monitoring, Logging, Analysis, Remediation & Performance (22%)
| Service | Dùng khi |
|---|---|
| CloudWatch Metrics | Theo dõi resource health, CPU/network/status |
| CloudWatch Alarms | Ngưỡng → action (SNS, ASG, EC2) |
| CloudWatch Logs + Insights | Tập trung log, truy vấn |
| Metric Filter | Log pattern → custom metric → alarm |
| CloudTrail | Audit API: who/what/when/where |
| EventBridge | Phản ứng event, schedule |
| X-Ray / Container Insights | Trace, microservice (biết là đủ) |
| Cost Explorer / Budgets | Cost optimization |

### D2 — Reliability & Business Continuity (22%)
| Service | Dùng khi |
|---|---|
| EC2 Status Checks | Phân biệt lỗi hạ tầng vs OS |
| ELB/ALB/NLB | Phân phối tải, health check |
| EC2 Auto Scaling | Scale theo demand, self-heal |
| RDS Automated Backup/Snapshot | Restore, PITR |
| RDS Multi-AZ | HA, failover sync |
| Read Replica | Scale đọc, async |
| AWS Backup | Backup tập trung nhiều service |
| Elastic Disaster Recovery | DR cross-region |

### D3 — Deployment, Provisioning & Automation (22%)
| Service | Dùng khi |
|---|---|
| SSM Session Manager | Truy cập EC2 không SSH/public IP |
| SSM Run Command | Chạy lệnh hàng loạt không SSH |
| SSM Patch Manager/Automation | Patch, runbook |
| Parameter Store | Config & secret đơn giản |
| CloudFormation | IaC, stack, rollback |
| StackSets | Triển khai đa account/Region |
| EventBridge + Lambda | Remediation tự động |
| Launch Templates | Chuẩn hóa launch EC2/ASG |

### D4 — Security & Compliance (16%)
| Service | Dùng khi |
|---|---|
| IAM (policy, role, boundary) | Phân quyền, assume role |
| STS | Temporary credentials |
| KMS | Mã hóa, key policy |
| Secrets Manager | Xoay vòng secret, RDS integration |
| S3 Block Public Access / Bucket Policy / ACL | Bảo vệ dữ liệu |
| Config / Security Hub / GuardDuty | Compliance & phát hiện |

### D5 — Networking & Content Delivery (18%)
| Service | Dùng khi |
|---|---|
| VPC (subnet, route table, IGW, NAT) | Thiết kế mạng |
| Security Group / NACL | Kiểm soát traffic (stateful vs stateless) |
| VPC Endpoint (Gateway/Interface) | Truy cập AWS service không qua Internet |
| Route 53 | DNS, routing policy, failover |
| CloudFront | CDN, content delivery |
| PrivateLink | Expose service private |

## Ngoài phạm vi core lab
EKS (container) — **có trong SOA-C03** nhưng không dựng trong 6 tuần vì chi phí/cleanup. Chỉ nắm khái niệm.

---

⬅️ [README](../README.md)
