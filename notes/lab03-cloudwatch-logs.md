# 📒 LAB 03 — CloudWatch Logs

```text
LAB: 03 — CloudWatch Logs
SERVICE: CloudWatch Logs / CloudWatch Agent / SSM
DATE: 2026-10-02
PHASES: Build [x] Break [x] Diagnose [x] Fix [x] Verify [x] Cleanup [ ]
```

1. What did I build?
   - IAM role `CloudWatch_SSM` cho EC2 (instance profile) với `AmazonSSMManagedInstanceCore` + `CloudWatchAgentServerPolicy`.
   - Cài CloudWatch Agent qua SSM Run Command (`AWS-ConfigureAWSPackage`, Name `AmazonCloudWatchAgent`, Version `latest`).
   - Config agent lưu ở SSM Parameter Store `/lab03/cloudwatch-agent-config`, áp dụng qua `AmazonCloudWatch-ManageAgent` (Action `configure`, Source `ssm`, Restart `yes`).
   - Log group `/lab03/app`, log stream `{instance_id}`, retention 7 ngày.
   - Truy vấn bằng CloudWatch Logs Insights.

2. What failed?
   - Đầu tiên instance không hiện trong Run Command: agent báo `no EC2 instance role found` do credential fetch lúc chưa thấy instance profile rồi ngủ backoff 27 phút ⇒ xóa `/var/lib/amazon/ssm/registration` + restart agent.
   - Phase B: bơm 20 dòng `ERROR simulated failure` và `mv /var/log/lab03/app.log → app.log.bak`.
   - Typo `lastest` khi cài package ⇒ `InvalidDocument`.

3. How did I detect it?
   - Logs Insights: `filter @message like /ERROR/ | stats count() by bin(1m)` thấy 20 error dồn vào 1 phút (burst nhân tạo).
   - So `@timestamp` (ingest) với timestamp trong message thấy lệch (10:10 trong text vs 08:31 nhận) ⇒ không tin timestamp trong nội dung.
   - Sau `mv`, log stream ngừng nhận bản ghi mới.

4. How did I fix it?
   - `mv app.log.bak app.log` trả tên về; agent tự bám lại inode (hoặc `systemctl restart amazon-cloudwatch-agent`).
   - Sửa typo `latest`, xóa registration cũ để agent đăng ký lại.

5. What exam trap did I learn?
   - CloudWatch Agent theo dõi log theo **inode**, không theo path ⇒ `mv`/rotate làm mất log nếu không cấu hình đúng.
   - `@timestamp` = ingest time, KHÁC timestamp ghi trong message; muốn chính xác phải `parse`.
   - Retention mặc định là **Never expire** (tốn tiền) — config `retention_in_days`.
   - Gắn/sửa IAM role cho EC2 đang chạy phải **restart SSM agent**, role không tự propagate.
   - Logs Insights tính tiền theo **GB scanned**, lọc time range để tiết kiệm.
   - Log group **tự sinh** theo `log_group_name` trong config, không cần tạo trước.

---

⬅️ [Week 1](../week1-monitoring.md) · [README](../README.md)
