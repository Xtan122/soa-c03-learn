# LAB 02 — CloudWatch Logs, Agent, Insights, metric filter

```text
LAB: 02 — CloudWatch Logs, Agent, Insights, metric filter
SERVICE: CloudWatch Logs, CloudWatch Agent, Logs Insights, metric filter, CloudWatch alarm, SNS
DATE: 2026-10-25
DOMAIN: D1 Monitoring 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
SOLUTION_USED: yes
TIME_TO_ROOT_CAUSE: 20 minutes
```

> `SOLUTION_USED: yes` — phần note này được AI viết hộ theo yêu cầu của người học
> (`START-HERE.md` §3). Evidence gốc (`verify-last.txt`, `DONE`) không bị sửa.

## 1. What did I build?

```text
App (JSON log) → /var/log/cloudops/app.log
  → CloudWatch Agent (log stream = instance id)
  → Log group /aws/cloudops/soa-c03/app
      ├── Logs Insights (query)
      └── metric filter { $.level = "ERROR" }
            → metric CloudOpsLab/ErrorCount (value 1, defaultValue 0)
            → alarm soa-c03-lab02-errors (Sum / period 60s / eval 1 / threshold 5 / GTE)
            → SNS topic → email
```

Log line (JSON, 1 dòng = 1 event):

```json
{"timestamp":"2026-10-25T03:41:39+0000","level":"ERROR","logger":"cloudops",
 "message":"simulated application failure","instance_id":"i-01c2a6aa400c07050",
 "event":"simulated_error","path":"/error","status":500}
```

Khoá thật của log: `timestamp, level, logger, message, instance_id, event, path, status`.
Lưu ý: **không có** khoá `errors` — đó chỉ là alias do `stats count() as errors` sinh ra.

## 2. Symptom (không phải root cause)

- Nhận **email alarm** từ SNS.
- CloudWatch → metric `CloudOpsLab/ErrorCount` = **16**.
- Alarm `soa-c03-lab02-errors` ở trạng thái `ALARM`.
- App vẫn `/health` 200, DB 200, target 1/1 → **không phải sự cố hạ tầng**.

## 3. Evidence

```text
# A. Nội dung log (Logs Insights, group /aws/cloudops/soa-c03/app)
filter level = "ERROR" | stats count() as n by bin(1m)
  2026-10-25 03:41Z   n=16
  2026-10-25 04:06Z   n=16      → tổng 32, chia 2 burst
Mỗi burst = 15 × GET /error (HTTP 500) + 1 × GET /log?level=ERROR

# B. Log thô của burst 1
  03:41:39.846Z → 03:41:42.853Z  (16 dòng, ~3 giây)

# C. Metric (CloudWatch, namespace CloudOpsLab, ErrorCount, Sum, period 60)
  10:41 (+07)  Sum = 16
  11:06 (+07)  Sum = 16
  các phút còn lại  Sum = 0   ← do defaultValue: 0

# D. Alarm history (describe-alarm-history, StateUpdate)
  03:42:35Z  OK    → ALARM      (burst 1)
  03:43:35Z  ALARM → OK         ← tự tắt sau 60 giây
  04:07:35Z  OK    → ALARM      (burst 2)
  04:08:35Z  ALARM → OK         ← lại tự tắt sau 60 giây

# E. Verify
  ./bin/lab verify 02 → PASS 2026-10-25T04:16:06Z
  ERROR logs=16  metric=16  alarm=OK (history chứng minh đã ALARM lúc 04:07:35Z)
```

Ba lớp đã chứng minh **chạy đúng** (evidence tích cực, không phải suy đoán):

| Lớp | Evidence chứng minh |
|---|---|
| CloudWatch Agent | log có trên CloudWatch, đủ 8 khoá JSON |
| Log group + metric filter | `Sum = 16` khớp đúng 15 + 1 |
| Alarm + SNS | email đã tới hộp thư, history có `OK → ALARM` |

## 4. Root cause

Hai tầng, phải tách rõ:

1. **Tầng ứng dụng (triệu chứng):** app trả `HTTP 500` trên route `/error` và ghi
   `level=ERROR`. Đây là **traffic lỗi được tạo có chủ đích** (`event=simulated_error`),
   không phải defect ẩn trong code. 16 = 15 lần `/error` + 1 lần `/log?level=ERROR`.
2. **Tầng guardrail (root cause thật của bài monitoring):** alarm **không giữ được**
   trạng thái `ALARM`. Vì `period = 60s` + `evaluation-periods = 1`, và metric filter có
   `defaultValue: 0` nên **mỗi phút** đều có datapoint (0 khi không có lỗi). Chỉ cần
   **1 phút** dưới ngưỡng 5 là alarm đổi về `OK`. Kết quả: cửa sổ quan sát thực tế chỉ
   có **60 giây**.

Điểm dễ hiểu sai: `defaultValue` **không phải** thủ phạm duy nhất. Nếu bỏ `defaultValue`
thì metric không có datapoint, và với `treat-missing-data = notBreaching` alarm **vẫn**
về `OK`. Thủ phạm là **độ dài cửa sổ đánh giá**, không phải giá trị mặc định.

## 5. How did I fix it?

Lab 02 không có lỗi cấu hình app cần sửa — chuỗi log → metric → alarm vốn đã đúng.
Phần "fix" thật của buổi này là **sửa công cụ verify** (6 bug, ghi ở
`docs/audit-report.md`), vì `verify 02` fail 3 lần mà không lần nào do người học:

```text
1. None: unbound variable        → AWS CLI in ra "None" khi query chưa có row; strip về số.
2. count luôn = 0                → JMESPath "errors" là quoted identifier (tên field),
                                   không phải string literal; đổi sang results[0][0].value.
3. metric luôn = 0               → --output text in mọi datapoint trên MỘT dòng;
                                   awk chỉ cộng $1. Sửa: cộng mọi field.
4. window lệch giây              → CloudWatch chia bucket từ đúng --start-time,
                                   datapoint ở mốc :00 bị rơi giữa 2 bucket. Canh :00.
5. alarm check race              → alarm tự về OK sau 1 period; chấp nhận ALARM hiện tại
                                   HOẶC có OK→ALARM trong 30 phút (alarm_fired_within).
6. window 15' < 20' diagnose     → nới lên 30 phút cho lab 02. Ngưỡng giữ nguyên.
```

Không sửa ngưỡng: vẫn `>= 10` ERROR, `>= 5` metric, alarm phải thực sự kêu.

## 6. Prevention

- **Alarm:** đổi `evaluation-periods` từ `1` → **`3`** (giữ `period = 60s`).
  Alarm cần **3 phút liên tiếp** vượt ngưỡng để kêu, và **3 phút liên tiếp** dưới ngưỡng
  để tắt ⇒ giữ `ALARM` khoảng **3 phút** thay vì 60 giây.
  Đánh đổi: phát hiện chậm hơn ~2 phút. Chấp nhận được với lỗi 500 ở mức vài chục
  request/phút, vì đổi lại người trực có thời gian mở dashboard.
  Phương án thay thế: `period = 300` (giữ ALARM 5 phút, nhưng mất granularity 1 phút).
- **Automation:** giữ `defaultValue: 0` để metric liên tục, nhưng **không** dựa vào
  trạng thái alarm tức thời để kết luận; luôn đọc `describe-alarm-history`.
- **Guardrail:** dashboard `soa-c03-ops` phải hiển thị `ErrorCount` + đường threshold,
  để alarm tắt rồi vẫn thấy lịch sử; và mọi báo cáo "hệ thống OK" phải kèm mốc thời gian
  của lần `ALARM → OK` gần nhất.

## 7. Exam trap

> `ALARM` hiện tại `OK` **không** có nghĩa là sự cố chưa từng xảy ra — `period`,
> `evaluation-periods` và `treat-missing-data` quyết định alarm giữ trạng thái bao lâu,
> nên phải đọc **alarm history** chứ không chỉ đọc trạng thái hiện tại.

## 8. Nếu gặp lại lúc 2h sáng

1. `aws cloudwatch describe-alarm-history --history-item-type StateUpdate` → alarm đã
   kêu lúc nào, tắt lúc nào.
2. `filter level = "ERROR" | stats count() by bin(1m)` → lỗi tập trung 1 phút hay rải rác;
   đếm theo `event`, không chỉ đếm tổng.
3. So `Sum` của metric với số dòng log **trong cùng một cửa sổ đã canh phút** → nếu lệch,
   kiểm tra pattern của metric filter trước khi kết luận app hỏng.
