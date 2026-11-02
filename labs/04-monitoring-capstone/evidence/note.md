# LAB 04 — Capstone: 500 errors → metric → alarm → event

```text
LAB: 04 — Capstone: 500 errors → metric → alarm → event
SERVICE: CloudWatch Logs/Alarms, EventBridge, SQS, ALB/EC2
DATE: 2026-10-26
DOMAIN: D1 Monitoring 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
```x

1. What did I build?
chuỗi 5 mắt xích: log → metric filter → metric → alarm → EventBridge → SQS
2. What failed? (symptom, not root cause)
verify FAIL metric=0, alarm đang OK dù 30 phút trước vừa có 12 lỗi
3. How did I detect it? (metric/log/event/CLI)
Logs Insights 14 ERROR; metric đỉnh 12; SQS body state.value=ALARM 18:01:23
4. Root cause (the actual broken layer)
lỗi nhất thời + cửa sổ bằng chứng 15 phút
5. How did I fix it? (exact command or console action)
bắn 1 request /error mỗi 10s trong 5 phút, chạy nền song song verify
6. Prevention / automation
3 datapoints trong 5 phút; + SQS/EventBridge giữ event làm bằng chứng
7. Exam trap
EventBridge không đánh giá threshold; state change ≠ state hiện tại; alarm đã ALARM sẵn thì không có event mới