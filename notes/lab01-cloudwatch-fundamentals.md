# 📒 LAB 01 — CloudWatch Fundamentals

```text
LAB: 01 — CloudWatch Fundamentals
SERVICE: EC2 / CloudWatch Metrics
DATE: 2026-10-01
PHASES: Build [x] Break [x] Diagnose [x] Fix [ ] Verify [ ] Cleanup [ ]
```

1. What did I build?
   - EC2 `t3.micro` (Amazon Linux 2023), tag `Name=lab01-cw`.
   - Dashboard `lab01-dashboard` với 4 metric: `CPUUtilization`, `NetworkIn`, `NetworkOut`, `StatusCheckFailed`.
   - Luyện chỉnh Period (1m/5m) và Statistic (Average/Maximum/Sum) trong CloudWatch → Metrics → Graphed metrics.

2. What failed?
   - Cố tình tạo CPU spike bằng `stress --cpu 2 --timeout 300`.
   - `CPUUtilization` tăng vọt so với baseline.

3. How did I detect it?
   - So graph `CPUUtilization` (Average vs Maximum) với baseline.
   - `StatusCheckFailed = 0` → EC2 vẫn khỏe, vấn đề chỉ là tải CPU, không phải lỗi hạ tầng.

4. How did I fix it?
   - Stress tự kết thúc sau timeout 300s, CPU về baseline.
   - (Chưa cleanup theo yêu cầu — giữ sandbox để làm lab tiếp.)

5. What exam trap did I learn?
   - StatusCheckFailed = 0 + CPU cao ⇒ tải thật, không phải lỗi hạ tầng.
   - Period 1m chỉ có khi bật Detailed monitoring; Basic monitoring tối thiểu 5m.
   - CPU dùng Average/Maximum (Maximum bắt được spike ngắn); Network dùng Sum (tổng byte/period).

---
⬅️ [Week 1](../week1-monitoring.md) · [README](../README.md)
