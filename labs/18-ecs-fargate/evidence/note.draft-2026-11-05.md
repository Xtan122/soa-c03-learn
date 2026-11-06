# LAB 18 — ECS Fargate + Container Insights + ECR

```text
LAB: 18 — ECS Fargate + Container Insights + ECR
SERVICE:
DATE: 2026-11-05
DOMAIN: D3 Automation 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
ECS -> Cluser -> Service + Task
2. What failed? (symptom, not root cause)
People search IP and recive timeout
3. How did I detect it? (metric/log/event/CLI)
I check who StopTask
4. Root cause (the actual broken layer)
IAM User xtan call an API that stop Task
5. How did I fix it? (exact command or console action)
I dont fix, I only detect the root cause, Service autimaticly lanch new task
6. Prevention / automation
Limit the privilege of user who can call API
use CloudTrail to detect
7. Exam trap
