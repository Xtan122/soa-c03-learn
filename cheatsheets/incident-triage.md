# 🚑 Incident Triage — "X chết → nhìn đâu trước?"

> Dùng khi làm Phase C (Diagnose). Đọc từ trên xuống, dừng ở tầng đầu tiên sai.

---

## Nguyên tắc vàng
```text
Detect → Evidence → Root cause → Remediate → Verify → Prevent → Automate
```
- Không reboot mù.
- Luôn hỏi: **"Lớp nào trong chuỗi này đang chặn?"**
- SG allows ≠ NACL allows ≠ Route exists. Kiểm tra độc lập.

---

## ALB 503 (hoặc 5xx tăng)
```text
ALB 503?
 └─ Target Group → có target không?
     └─ Health Check → target Healthy không?
         ├─ Không → Check Health Check path/port/protocol
         ├─ SG của target cho phép ALB SG trên port không?
         ├─ App trên EC2 có listen đúng port không?
         └─ NACL subnet cho ephemeral ports không?
     └─ Access logs / target response time / HTTPCode_ELB_5XX
```

## EC2 unreachable (SSH timeout)
```text
EC2 unreachable?
 ├─ Instance status check (system vs instance)
 ├─ Có Public IP / Elastic IP không?
 ├─ SG inbound 22 từ IP của bạn?
 ├─ NACL inbound + outbound (ephemeral)?
 ├─ Route table → IGW (public) / NAT (private)?
 ├─ Subnet có auto-assign public IP?
 ├─ OS: sshd chạy? disk full? resource?
 └─ Fallback: SSM Session Manager, EC2 Serial Console
```

## EC2 → S3 bị từ chối
```text
EC2 → S3 denied?
 ├─ IAM Role attached? Policy cho phép s3:GetObject?
 ├─ S3 Bucket Policy có explicit Deny?
 ├─ Block Public Access / ACL?
 ├─ Object dùng SSE-KMS → KMS key policy + role có kms:Decrypt?
 ├─ Private subnet: cần VPC Endpoint (Gateway cho S3)?
 └─ NACL cho endpoint traffic?
```

## AccessDenied (Lambda/Role → resource)
```text
AccessDenied?
 ├─ Identity policy (IAM) cho phép action + resource?
 ├─ Resource policy (bucket/key/queue) cho phép principal?
 ├─ KMS key policy (nếu encrypted)?
 ├─ SCP (Organizations) chặn?
 ├─ Permission boundary chặn?
 └─ Explicit Deny ở đâu đó luôn thắng Allow.
```

## RDS connection failure / timeout
```text
EC2 → RDS timeout?
 ├─ RDS status = available? (không phải đang failover/reboot)
 ├─ RDS SG inbound từ EC2 SG trên port DB?
 ├─ NACL subnet của RDS + của EC2?
 ├─ Route table (cùng VPC mặc định OK; cross-VPC cần peering/TGW)
 ├─ DNS endpoint resolve đúng?
 ├─ Subnet group có private subnet không?
 └─ max_connections đầy? (xem Connections metric)
```

## CPU 95%
```text
CPU cao?
 ├─ Là 1 instance hay cả fleet? → nếu cả fleet: load thật → scale out
 ├─ CloudWatch: CPUUtilization theo thời gian (đột biến hay tăng dần?)
 ├─ App logs: process nào ăn CPU?
 ├─ SSM: top / ps aux
 └─ Prevention: ASG target tracking theo CPU
```

## VPC: private EC2 không ra Internet
```text
Private EC2 → Internet?
 EC2 → ENI → Route Table → NAT → Route → IGW → Internet
 ├─ Subnet route 0.0.0.0/0 trỏ NAT Gateway?
 ├─ NAT Gateway nằm ở public subnet? có Elastic IP?
 ├─ Public subnet route 0.0.0.0/0 trỏ IGW?
 ├─ SG outbound OK? NACL cho phép?
 └─ DNS resolution (enableDnsSupport) cho NAT?
```

## VPC Routing Conflicts
```text
Route không tới nơi?
 ├─ Longest prefix match (route cụ thể thắng route /0)
 ├─ Route table gắn đúng subnet association?
 ├─ Target (IGW/NAT/peering/TGW/ENI) đúng loại?
 ├─ Edge association / propagation conflict?
 └─ SimuLearn Ref: "Resolve VPC Routing Conflicts"
```

## Event-driven không trigger
```text
EventBridge không fire?
 ├─ Event pattern khớp event thật không? (dùng TestEventPattern)
 ├─ Rule ở đúng event bus?
 ├─ Target permission (Lambda resource policy / SNS / SQS policy)?
 ├─ Event detail-type / source đúng?
 └─ Dead-letter queue có message không?
```

---

## Phân biệt nhanh hay gặp trong đề
| Câu hỏi | Phân biệt |
|---|---|
| System vs Instance status check | System = AWS infra (stop/start); Instance = OS bên trong (reboot) |
| Multi-AZ vs Read Replica | Multi-AZ = HA, sync, cùng endpoint; Replica = scale read, async |
| SG vs NACL | SG = stateful, allow-only, gắn ENI; NACL = stateless, allow+deny, gắn subnet |
| Trust Policy vs Permissions Policy | Trust = ai được assume; Permissions = được làm gì |
| Parameter Store vs Secrets Manager | SSM = config/value rẻ; Secrets = xoay vòng secret, RDS integration |
| Gateway vs Interface Endpoint | Gateway = S3/DynamoDB, route table, miễn phí; Interface = ENI + SG, phần lớn service khác |
| EventBridge Rule vs Scheduler vs Pipes | Rule = react event; Scheduler = cron/rate; Pipes = point-to-point có filtering/enrichment |

---

⬅️ [README](../README.md)
