# LAB 08 — RDS Multi-AZ + failover + RTO

```text
LAB: 08 — RDS Multi-AZ + failover + RTO
SERVICE:
DATE: 2026-10-31
DOMAIN: D2 Reliability 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
ALB -> EC2 -> RDS multi AZ
2. What failed? (symptom, not root cause)
user recỉeve 503 error

3. How did I detect it? (metric/log/event/CLI)
I curl the DB and recieve errror code

4. Root cause (the actual broken layer)
because I change DB from standby -> primary (failover)

5. How did I fix it? (exact command or console action)
not fix any thing

6. Prevention / automation


7. Exam trap
