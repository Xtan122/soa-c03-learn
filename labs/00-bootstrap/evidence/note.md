# LAB 00 — Bootstrap: account, budget, core stack, guardrails

```text
LAB: 00 — Bootstrap: account, budget, core stack, guardrails
SERVICE:
DATE: 2026-10-24
DOMAIN: Foundation
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?

2. What failed? (symptom, not root cause)

3. How did I detect it? (metric/log/event/CLI)

4. Root cause (the actual broken layer)

5. How did I fix it? (exact command or console action)

6. Prevention / automation

7. Exam trap

1. Built: core stack, budget, S3, KMS, CloudTrail, IAM, SSM
2. Failed: none (baseline)
3. Detected: make doctor + lab verify 00
4. Root cause: n/a
5. Fix: n/a
6. Prevention: budget, tag ExpiryDate, cleanup 01/12
7. Exam trap: CloudTrail management events ≠ data events