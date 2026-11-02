# LAB 05 — ALB health check → 503

```text
LAB: 05 — ALB health check → 503
SERVICE: ALB / target group / ASG
DATE: 2026-10-28
DOMAIN: D2 Reliability 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
```

1. What did I build?
ALB + target group + ASG + EC2 app, health check /health (path đúng lúc build). Lúc break, path bị đổi thành /does-not-exist — đó là fault, không phải cấu hình build.
2. What failed? (symptom, not root cause)
UnHealthyHostCount=1, instance bị ASG thay 2 lần, client lúc 200 lúc 502, vì chỉ có 1 target nên ALB fail-open
3. How did I detect it? (metric/log/event/CLI)
UnHealthyHostCount = 1 lúc 13:53; alarm soa-c03-unhealthy-hosts OK→ALARM 13:56:29; ASG Activity 13:54:57 "an instance was taken out of service in response to an ELB system health check failure".
4. Root cause (the actual broken layer)
path /does-not-exist vs app chỉ có /health
5. How did I fix it? (exact command or console action)
Target group → Health checks → Edit → Path
6. Prevention / automation
khoá cấu hình bằng IaC — chỉ pipeline được sửa target group (IAM), và pipeline chạy check CI trước khi apply; kèm drift detection (AWS Config) để bắt thay đổi tay. Lớp (b) chỉ để giảm thời gian phát hiện. Đó là lý do không có 1 đáp án đơn — guardrail thật là nhiều lớp. 
7. Exam trap
502 = ALB đã chuyển request tới target nhưng target trả response không dùng được / đóng kết nối giữa chừng. 503 = ALB không có target khoẻ để chuyển. 504 = target nhận request nhưng trả lời quá timeout. Lab này KHÔNG ra 503 vì target group chỉ có 1 target: khi mọi target unhealthy, ALB chuyển sang fail-open và vẫn đẩy traffic vào target — nên client thấy 200 (target còn phục vụ) hoặc 502 (target đang bị ASG terminate). Nếu có >=2 target thì mới thấy 503.