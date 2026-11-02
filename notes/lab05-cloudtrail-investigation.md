# 📒 LAB 05 — CloudTrail Investigation

```text
LAB: 05 — CloudTrail Investigation
SERVICE: CloudTrail / IAM / S3 / EC2
DATE: 2026-10-23
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [x]
```

1. What did I build?
   - Trail `lab05-trail`: multi-region, ghi management events vào bucket `lab05-cloudtrail-<account-id>`.
   - "Nghi phạm": IAM user `lab05-suspect` (AmazonEC2FullAccess) — thao tác qua `<incognito / switch role>`.
   - 3 loại thay đổi: IAM (create user + attach policy), S3 (upload/delete `secret.txt`), EC2 (run → terminate `t3.micro`).

2. What failed?
   - <điền: vd bật Data events muộn / quên multi-region / filter sai time range / user không có quyền>

3. How did I detect it?
   - `CloudTrail → Event history` → filter `Event name = TerminateInstances`, time range last 1h.
   - Đọc JSON: `userIdentity.type = <IAMUser / AssumedRole>`, `userName/arn = <...>`,
     `accessKeyId = <AKIA...>`, `eventTime = <...Z>`, `sourceIPAddress = <...>`,
     `eventSource = ec2.amazonaws.com`, `requestParameters.instancesSet = <i-...>`.
   - S3 `DeleteObject` **không** thấy trong Event history → xác nhận data events mặc định tắt.

4. How did I fix it?
   - <điền: cách xác minh trail ghi log / có bật data events không / thời gian log tới S3>
   - Cleanup: xoá access key + user `lab05-suspect`, role (nếu có), stop + delete trail,
     empty + xoá 2 bucket.

5. What exam trap did I learn?
   - Event history chỉ giữ **90 ngày** và chỉ có **management events**.
   - **Data events** (S3 object-level, Lambda Invoke) mặc định **tắt** → phải bật trên trail.
   - Trail ghi S3 **không real-time**; Event history gần như ngay.
   - `userIdentity.type`: `Root` / `IAMUser` / `AssumedRole` / `AWSService` — role session cho manh mối qua session name.
   - CloudTrail (ai gọi API gì) ≠ **AWS Config** (resource thay đổi thế nào).
   - `eventTime` là **UTC**.
   - Multi-region trail **không** tự gồm global services → cần include global service events.
   - Bảo vệ log: **log file validation** (digest) + S3 Object Lock nếu cần immutable.

---
⬅️ [README](../README.md) · [Exam map](../docs/exam-map.md)
