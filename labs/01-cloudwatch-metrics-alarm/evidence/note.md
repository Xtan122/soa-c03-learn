# LAB 01 — CloudWatch metrics, dashboard, alarm, SNS

```text
LAB: 01 — CloudWatch metrics, dashboard, alarm, SNS
SERVICE: CloudWatch (metric/alarm), SNS, SQS, EC2, Auto Scaling
DATE: 2026-10-25 local (2026-10-24Z)
DOMAIN: D1 Monitoring 22%
PHASES: Build [x] Break [x] Diagnose [x] Fix [n/a] Verify [x] Cleanup [ ]
```

1. What did I build?
   - Alarm `soa-c03-lab01-cpu-high`: metric `CPUUtilization`, statistic Average,
     period 60s, EvaluationPeriods 1, threshold 50, dimension = 1 instance.
   - Hai alarm ASG dùng cùng cơn load nhưng cấu hình khác:
     `soa-c03-asg-cpu` (Average, 60s, EvaluationPeriods 2, threshold 70) và
     `TargetTracking-...-AlarmHigh` (Average, 60s, EvaluationPeriods 3,
     threshold 50, do scaling policy tạo).
   - SQS queue `soa-c03-lab01-events`, subscribe vào SNS topic của core stack
     (cùng email). Chuỗi: EC2 → metric → alarm → SNS → {email, SQS}.
   - ASG `soa-c03-asg` tạm suspend scaling (MinSize=1, MaxSize=2) để load không đẻ
     thêm instance.

2. What failed? (symptom, not root cause)
   - Không có lớp nào "hỏng". CPU của 1 instance vọt lên ~99.6% và alarm báo ALARM.
   - Symptom người dùng thấy: nhận email `soa-c03-lab01-cpu-high`, alarm In alarm,
     biểu đồ CPU ~99%. CPU đã 99% từ đầu nhưng ba alarm CPU báo lệch nhau
     1m22 / 3m32 / 3m42 sau khi load bắt đầu.

3. How did I detect it? (metric/log/event/CLI)
   - Email SNS + CloudWatch console (Alarm state + biểu đồ CPU).
   - `aws cloudwatch describe-alarms` → 3 alarm CPU: lab01-cpu-high (instance),
     soa-c03-asg-cpu (ASG), TargetTracking-...-AlarmHigh (ASG).
   - `aws cloudwatch describe-alarm-history` (StateUpdate) — cùng load bắt đầu
     01:00:48, ba alarm chuyển OK → ALARM lệch nhau:
       lab01-cpu-high (Eval 1) : 01:02:10  → trễ 1m22
       soa-c03-asg-cpu (Eval 2): 01:04:20  → trễ 3m32
       TargetTracking  (Eval 3): 01:04:30  → trễ 3m42
   - SQS `receive-message` → 5 message. SNS publish mỗi lần state đổi của alarm đã
     subscribe, nên con số này phải đối chiếu với (AlarmName, NewStateValue,
     Timestamp) trong từng body — chưa đối chiếu đủ từng body trong phiên này.
   - `./bin/lab verify 01` → PASS, CPU max=99.6333, alarm=ALARM (18:29:19Z).

4. Root cause (the actual broken layer)
   - Một process tải CPU được bơm vào instance qua SSM Run Command (không phải
     traffic người dùng) đẩy CPU lên ~99.6% trong 30 phút.
   - Không có "lỗi cấu hình": alarm phản ứng đúng, chỉ chậm vì cần đủ datapoint.
   - Trễ = EvaluationPeriods × Period, cộng thêm phần pha loãng của phút đầu
     (load bắt đầu 01:00:48, datapoint của phút đó chỉ chứa 12 giây load) và độ
     trễ đẩy datapoint. Vì vậy Eval 1 → 1m22, Eval 2 → 3m32, Eval 3 → 3m42
     trên cùng một cơn load.

5. How did I fix it? (exact command or console action)
   - Không sửa gì: load chỉ sống 30 phút rồi tự hết; alarm tự về OK.
   - Đã verify trước khi dọn (đúng thứ tự verify → note → down):
     `./bin/lab verify 01` → PASS.
   - Dọn bằng `./bin/lab down 01` (sẽ resume ASG scaling + xoá alarm/SQS của lab).

6. Prevention / automation
   - Muốn cảnh báo nhanh hơn: giảm EvaluationPeriods/DatapointsToAlarm trước,
     rồi giảm Period. Period 60s cần detailed monitoring trên instance (basic
     monitoring là 5 phút). Đánh đổi: dễ báo giả khi CPU nhô lên ngắn, alarm
     flapping ALARM↔OK, nhiều message; detailed monitoring tốn thêm phí
     (chưa xác minh giá trong phiên này).
   - Khi alarm "không bắn", thứ tự kiểm tra: (1) metric thực tế có vượt ngưỡng
     không (CPU), (2) alarm State + History có đổi không, (3) chỉ khi state đã đổi
     mà không có thông báo mới xét SNS subscription / SQS.
     Kiểm tra "confirm subscription" chỉ đúng khi chưa từng nhận được email nào.

7. Exam trap
   - Alarm không bắn ngay: cần đủ N datapoint liên tiếp; datapoint là average của
     cả period nên period đầu bị pha loãng → trễ thêm gần 1 period.
   - Cùng một cơn load (CPU ~99.6%), ba alarm đo cùng CPU nhưng EvaluationPeriods
     1/2/3 báo lệch nhau 1m22 / 3m32 / 3m42. Câu hỏi thi hay hỏi "vì sao alarm A
     báo mà B chưa" → so EvaluationPeriods và DatapointsToAlarm trước khi nghi
     metric sai.
   - Basic monitoring 5 phút vs detailed monitoring 1 phút: `Period=60` chỉ có
     nghĩa khi đã bật detailed monitoring.
   - `ALARM` không đồng nghĩa hệ thống hỏng (TargetTracking-AlarmLow = ALARM khi
     ASG đã ở MinSize). Ngược lại, alarm `OK` không chứng minh dịch vụ khoẻ.
   - Alarm state đổi ≠ chắc chắn có thông báo tới người nhận.
