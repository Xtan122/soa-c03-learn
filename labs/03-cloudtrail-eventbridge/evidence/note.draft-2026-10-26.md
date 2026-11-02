# DRAFT (bản gốc của người học, giữ nguyên — không sửa)

Lưu lại trước khi AI viết `note.md` theo yêu cầu rõ ràng của người học.
Thời điểm lưu: 2026-10-26 02:35 (+07).

```text
LAB: 03 — CloudTrail + EventBridge: ai đã terminate EC2?
SERVICE:
DATE: 2026-10-25
DOMAIN: D1 Monitoring 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [x] Cleanup [ ]
```

1. What did I build?
I designed a pipeline that check the API affect to resource

2. What failed? (symptom, not root cause)
An instance is terminated
3. How did I detect it? (metric/log/event/CLI)
I check Cloudtrail event  to detect who, when, which
4. Root cause (the actual broken layer)
A AssumedRole terminated my instance
5. How did I fix it? (exact command or console action)
I did not fix, I only detect the root cause
6. Prevention / automation
I think I will add SNS to get Email
7. Exam trap
I dont know
