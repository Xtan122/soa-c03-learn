# LAB 17 — Boss fight: 3 lỗi mạng cùng lúc

```text
LAB: 17 — Boss fight: 3 lỗi mạng cùng lúc
SERVICE:
DATE: 2026-11-04
DOMAIN: D5 Networking 18%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
ALB -> NACL -> Target Group -> SG -> EC2 app

2. What failed? (symptom, not root cause)
Health check unhealthy

3. How did I detect it? (metric/log/event/CLI)
Check in to out: SG -> NACL -> Health check path

4. Root cause (the actual broken layer)
SG: No inbound rule
NACL: block port 8080
Health check path: wrong path

5. How did I fix it? (exact command or console action)
SG: add inbound rule
NACL: delete 1 rule
Health check path: Modify
6. Prevention / automation
Use IaC and review IaC before apply
Use Config to check the infra

7. Exam trap
Error code not show where is fail 
