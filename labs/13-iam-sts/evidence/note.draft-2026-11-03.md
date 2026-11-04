# LAB 13 — IAM + STS AssumeRole: trust policy vs permissions

```text
LAB: 13 — IAM + STS AssumeRole: trust policy vs permissions
SERVICE:
DATE: 2026-11-03
DOMAIN: D4 Security 16%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
Role -> AssomeRole -> S3 Bucket

2. What failed? (symptom, not root cause)
Access deny when call sts identify

3. How did I detect it? (metric/log/event/CLI)
Check the trust policy of Role
4. Root cause (the actual broken layer)
Condition MFA enable = true

5. How did I fix it? (exact command or console action)
Delete the condition

6. Prevention / automation
Use Alarm on CloudTrail
IAM Access Analyzer


7. Exam trap
Role được assume không có nghĩa là truy cập được tài nguyên, phải đảm bảo 3 thứ: có quyền Assume, được assume, và được truy cập