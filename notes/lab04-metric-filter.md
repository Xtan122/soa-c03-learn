# 📒 LAB 04 — Metric Filter

```text
LAB: 04 — Metric Filter
SERVICE: CloudWatch Logs / Metric Filter / CloudWatch Alarm
DATE: 2026-10-05
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
```

1. What did I build?
   - Tái dùng log group `/lab03/app` (EC2 lab03 + CloudWatch Agent) — không tạo nguồn log mới.
   - Sinh log qua **SSM Session Manager**: `echo "ERROR ..." >> /var/log/lab03/app.log`.
   - Metric filter `Lab04-ErrorCount` trên `/lab03/app`, pattern trần `ERROR`, namespace `Lab04`, metric `ErrorCount`, value `1`, default `0`.
   - Alarm `Lab04-error-alarm`: `ErrorCount` Sum, period 1 phút, threshold ≥ 5, 1 evaluation period, SNS email, *Treat missing data as notBreaching*.
   - Đối chiếu bằng Logs Insights `filter @message like /ERROR/ | stats count() by bin(1m)`.

2. What failed?
   - Ban đầu bơm `ERROR` trước khi tạo filter nhưng metric vẫn 0 → hiểu ra metric filter **không hồi tố**, phải bơm log **mới**.
   - Alarm mới tạo ở trạng thái **INSUFFICIENT_DATA** vì chưa có data point.
   - Phase B bơm 10 dòng `ERROR burst` dồn trong 1 phút để vượt ngưỡng 5.

3. How did I detect it?
   - **Metrics → Lab04 → ErrorCount** thấy graph Sum khớp số ERROR bơm sau khi tạo filter.
   - Logs Insights `stats count() by bin(1m)` cho cùng con số ⇒ filter đếm đúng.
   - Alarm chuyển **OK → ALARM** sau ~1–2 phút khi Sum ≥ 5.

4. How did I fix it?
   - Sinh log mới qua Session Manager thay vì trông chờ log cũ.
   - Thêm `defaultValue=0` + *notBreaching* để alarm không nhảy loạn khi thiếu data.
   - Cleanup: xoá alarm `Lab04-error-alarm`, metric filter `Lab04-ErrorCount`, SNS topic — **giữ lại** log group `/lab03/app`.

5. What exam trap did I learn?
   - Metric filter **KHÔNG hồi tố** — chỉ đếm event sinh ra sau khi filter tồn tại.
   - Custom metric **không hiện** đến khi có data đầu tiên ⇒ luôn set **Default value = 0**.
   - Alarm thiếu data ⇒ `INSUFFICIENT_DATA`; dùng *Treat missing data as notBreaching*.
   - Pattern `ERROR` khớp **substring**; muốn chính xác theo field dùng space-delimited `[ts, level, ...]` hoặc JSON `{ $.level = "ERROR" }`.
   - Metric filter ở **standard resolution (1 phút)**; high-res phải dùng **EMF** (`_aws` trong log JSON).
   - Một metric filter áp dụng cho **toàn bộ log group**, không theo từng stream.

---
⬅️ [Week 1](../week1-monitoring.md) · [README](../README.md)
