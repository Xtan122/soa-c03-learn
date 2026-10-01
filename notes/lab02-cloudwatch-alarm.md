# 📒 LAB 02 — CloudWatch Alarm

```text
LAB: 02 — CloudWatch Alarm
SERVICE: CloudWatch Alarm / SNS
DATE: 2026-10-01
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
```

1. What did I build?
   - SNS topic `lab02-cpu-alerts` + email subscription (đã Confirm).
   - Alarm `lab02-cpu-high`: `CPUUtilization Average > 60%`, period 5m, `2 out of 2` datapoints.
   - alarm-actions / ok-actions / insufficient-data-actions đều trỏ về SNS.

2. What failed?
   - Cố tình chạy `stress --cpu 2` đẩy CPU vượt 60%.

3. How did I detect it?
   - Theo dõi `StateValue`: `INSUFFICIENT_DATA → OK → ALARM`; nhận mail ALARM từ SNS.

4. How did I fix it?
   - Stress hết timeout, CPU về baseline → alarm tự về `OK` (nhận mail OK).

5. What exam trap did I learn?
   - `datapoints-to-alarm` (M) ≤ `evaluation-periods` (N); M=N nghiêm ngặt, M<N nhạy/dễ báo.
   - SNS subscription chưa Confirm → alarm kêu nhưng KHÔNG gửi mail.
   - EC2 Basic monitoring chỉ 5m → alarm Period phải ≥ 300s (hoặc bật Detailed monitoring để dùng 60s).
   - Cửa sổ đánh giá = Period × evaluation-periods (`2 out of 2` với period 5m = "2 datapoints within 10 minutes").

---
⬅️ [Week 1](../week1-monitoring.md) · [README](../README.md)
