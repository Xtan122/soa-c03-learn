# Lab audit — 24 labs

Ngày rà static: 2026-10-25, cập nhật brief 24 lab: 2026-10-26. Phạm vi: khởi tạo, verify, cleanup, README beginner,
console guidance, idempotency.

> **Đọc thêm:** [`docs/lab-readiness.md`](lab-readiness.md) — ma trận rủi ro từng
> lab, lỗi đã sửa, và cách chạy `./bin/lab preflight <id> [--live]`.
> Bảng dưới đây là kết quả static; **chưa** phải bằng chứng 24/24 lab đã chạy thật.

| Lab | Build | Verify | Cleanup | README | Console | Ghi chú |
|---|---|---|---|---|---|---|
| 00 Bootstrap | ✅ | ✅ | ✅ (no-op) | ✅ | ✅ | Core only, không fault |
| 01 CloudWatch metrics | ✅ | ✅ | ✅ | ✅ | ✅ | 30' CPU load; tạm suspend ASG scaling |
| 02 CloudWatch Logs | ✅ | ✅ | ✅ | ✅ | ✅ | Log/metric trễ 30–90s |
| 03 CloudTrail + EventBridge | ✅ | ✅ | ✅ | ✅ | ✅ | Không cần app; canary được rebuild |
| 04 Monitoring capstone | ✅ | ✅ | ✅ | ✅ | ✅ | Chuỗi 4 mắt xích |
| 05 ALB 503 | ✅ | ✅ | ✅ | ✅ | ✅ | Health check path/port |
| 06 ASG failure | ✅ | ✅ | ✅ | ✅ | ✅ | Giữ launch template version gốc |
| 07 RDS backup/restore | ✅ | ✅ | ✅ | ✅ | ✅ | Snapshot cũ được thay |
| 08 RDS Multi-AZ | ✅ | ✅ | ✅ | ✅ | ✅ | Multi-AZ tốn x2, nhớ revert |
| 09 SSM operations | ✅ | ✅ | ✅ | ✅ | ✅ | Không SSH |
| 10 Secrets + KMS | ✅ | ✅ | ✅ | ✅ | ✅ | Key policy gốc được giữ |
| 11 CloudFormation/CDK | ✅ | ✅ | ✅ | ✅ | ✅ | Không cần app stack |
| 12 Event remediation | ✅ | ✅ | ✅ | ✅ | ✅ | Lambda permission được reset |
| 13 IAM + STS | ✅ | ✅ | ✅ | ✅ | ✅ | Không cần app stack |
| 14 S3 public exposure | ✅ | ✅ | ✅ | ✅ | ✅ | Không cần app stack |
| 15 VPC troubleshooting | ✅ | ✅ | ✅ | ✅ | ✅ | Flow log/path được thay |
| 16 VPC endpoint | ✅ | ✅ | ✅ | ✅ | ✅ | Không cần app; endpoint được dọn trước |
| 17 Networking boss | ✅ | ✅ | ✅ | ✅ | ✅ | 3 faults |
| 18 ECS Fargate | ✅ | ✅ | ✅ | ✅ | ✅ | Fargate + public image |
| 19 Backup/Config/Cost | ✅ | ✅ | ✅ | ✅ | ✅ | Backup/Config chậm, CE trễ 24h |
| 20 Incident compute/network | ✅ | ✅ | ✅ | ✅ | ✅ | CPU + 5xx + latency |
| 21 Incident data/identity | ✅ | ✅ | ✅ | ✅ | ✅ | DB SG + IAM deny |
| 22 Production capstone | ✅ | ✅ | ✅ | ✅ | ✅ | Tự tạo dashboard + 4 alarm |
| 23 Final boss | ✅ | ✅ | ✅ | ✅ | ✅ | 5 faults |

## Kết luận

- 24/24 lab có `build`, `break`, `verify`, `cleanup` (hoặc `reset`) trong
  `scripts/lib/labs.sh`.
- 24/24 README có mục **0. Đọc nhanh (60 giây)**, **5c. Console — bấm ở đâu,
  thấy gì** và **5d. Brief trước khi phá** với inventory, baseline, bản đồ chẩn
  đoán, 3 câu dự đoán, I do/We do/You do.
- `docs/learner-quickstart.md` (người học), `docs/ai-mentor-runbook.md` (AI dạy
  từng màn hình/từng nút), `docs/glossary.md` (114 thuật ngữ, sinh tự động).
- 24/24 lab ID khớp thư mục; manifest khớp `NEEDS_APP` với code.
- `tools/check_labs.py` là static gate mới: fail nếu thiếu function, thiếu mục
  console, dùng `us-east-1`, còn placeholder, hoặc tên tài nguyên không tồn tại
  trong `labs.sh`/`platform`.
- **Chưa runtime-test toàn bộ 24 lab.** Đã kiểm tra static + core/app bootstrap +
  lab 00/01/02. Trước mỗi lab, chạy `./bin/lab preflight <id> --live`.
- App stack hiện tại (2026-10-25) healthy 1/1 nhưng launch template vẫn là bản
  trước khi sửa venv. Cần `make app-up` (hoặc `make app-down && make app-up`) để
  instance tương lai dùng user-data mới.

## Rủi ro cần theo dõi

| Lab | Rủi ro | Cách xử lý |
|---|---|---|
| 07 | Restore DB sai subnet/SG | Dùng `DbSubnetGroupName`, `DbSecurityGroupId` từ stack output |
| 08 | Quên revert Multi-AZ | `./bin/lab down 08` |
| 10, 13 | User thiếu `sts:AssumeRole` | Cấp quyền cho user lab |
| 16 | Interface endpoint phí theo giờ | `./bin/lab down 16` ngay sau lab |
| 18 | Fargate public image pull | Xem ECS stopped reason |
| 19 | Backup/Config lâu, CE trễ | Verify lại sau vài phút; không fail vì CE |
| 20, 23 | CPU load có thể scale ASG | Verify sẽ stop load; theo dõi cost |
| 22 | ASG thay instance tới 10 phút | Kiểm tra Activity, không reboot tay |
