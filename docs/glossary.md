# Glossary — thuật ngữ trong 24 lab

> File này được sinh tự động từ `tools/lab_console.py`.
> Đừng sửa tay; sửa nguồn rồi chạy `python3 tools/gen_lab_docs.py`.
>
> Cách dùng: gặp từ lạ trong lab nào, tra ở đây, rồi quay lại mục 5c của lab đó.
> Một số từ có định nghĩa khác nhau theo lab; cột **Lab** cho biết đang đọc định nghĩa nào.
> Bảng 20 từ cốt lõi nằm trong `docs/beginner-mentor.md` mục 2.

## #

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **502 / 504** | Target trả lỗi / target trả lời quá chậm. | 05 |
| **503** | ALB không có target khoẻ để chuyển request. | 05 |
| **5xx** | Nhóm HTTP status 500–599, lỗi phía server/ALB. | 04 |
| **5xx** | Lỗi server/ALB. | 20 |

## A

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Access Analyzer** | Dịch vụ tìm resource cho phép truy cập ngoài. | 14 |
| **AccessDenied** | Lỗi quyền, không phải lỗi mạng. | 21 |
| **ACL** | Quyền kiểu cũ, thường nên tắt. | 14 |
| **Alarm state change** | Sự kiện riêng của CloudWatch khi alarm đổi trạng thái. | 04 |
| **Anonymous access** | Truy cập không có credential, ví dụ curl không ký. | 14 |
| **App role** | Role gắn vào EC2 app qua instance profile. | 21 |
| **AssumeRole** | Mượn danh tính tạm thời của một role. | 10 |
| **AssumeRole** | Đổi sang danh tính tạm thời của role. | 13 |
| **AssumeRole session** | Danh tính tạm thời khi một role gọi API. | 03 |

## B

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Backup plan** | Lịch backup và thời gian giữ. | 19 |
| **Backup vault** | Kho chứa recovery point. | 19 |
| **Block Public Access** | Công tắc khoá cửa bucket S3, chặn truy cập nặc danh. | 00 |
| **Block Public Access** | 4 công tắc chặn public ở mức bucket/account. | 14 |
| **Bucket policy** | JSON policy gắn vào bucket. | 14 |
| **Budget** | Chuông báo chi phí, không phải công tắc chặn chi phí. | 00 |
| **Budget** | Cảnh báo chi phí theo ngưỡng. | 19 |

## C

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Change set** | Bản nháp cho biết update sẽ thay đổi gì. | 11 |
| **CloudTrail** | Camera ghi lại ai đã gọi API nào, lúc nào. | 00 |
| **Config recorder** | Bộ ghi trạng thái tài nguyên. | 19 |
| **Config rule** | Luật compliance, ví dụ EBS phải mã hoá. | 19 |
| **Container Insights** | Metric/log nâng cao cho cluster. | 18 |
| **Cooldown** | Thời gian ASG chờ trước khi scale tiếp. | 06 |
| **Core stack** | Nền nhà dùng chung: VPC, S3, KMS, CloudTrail, SNS, IAM, SSM. | 00 |

## D

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Dashboard** | Một trang gom metric/log quan trọng. | 22 |
| **Data path** | Đường app → DB. | 23 |
| **DB subnet group** | Tập subnet mà RDS được phép đặt DB. | 07 |
| **DB timeout** | Kết nối TCP không thành công hoặc quá chậm. | 21 |
| **Desired capacity** | Số instance ASG muốn có. | 06 |
| **Dimension** | Nhãn để chỉ đúng đối tượng, ví dụ `InstanceId=i-...`. | 01 |
| **DLQ** | Queue nhận message không xử lý được; lab này chưa dùng. | 04 |
| **Drift** | Resource bị sửa ngoài CloudFormation. | 11 |

## E

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Endpoint** | Địa chỉ DNS + port để kết nối DB. | 07 |
| **Endpoint** | DNS name giữ nguyên qua failover. | 08 |
| **ENI** | Card mạng ảo của instance/endpoint. | 16 |
| **Ephemeral port** | Port tạm cho chiều về, thường 1024–65535. | 15 |
| **Evaluation periods** | Cần bao nhiêu period liên tiếp vượt ngưỡng mới đổi trạng thái. | 01 |
| **Event bus** | Đường ống sự kiện; mặc định là `default`. | 03 |
| **Event history** | Danh sách event CloudTrail, chỉ giữ 90 ngày. | 03 |
| **Event pattern** | Bộ điều kiện JSON để EventBridge chọn event. | 03 |
| **Event pattern** | Bộ lọc JSON quyết định event nào khớp rule. | 12 |
| **EventBridge rule** | Bộ lọc bắt sự kiện alarm rồi đẩy tới SQS. | 04 |
| **Execution role** | Role Lambda dùng khi chạy code. | 12 |
| **Execution role** | Role để ECS agent pull image/ghi log. | 18 |
| **Explicit deny** | Câu `Deny` luôn thắng `Allow`. | 10 |
| **Explicit deny** | Câu Deny thắng mọi Allow. | 21 |
| **External ID** | Chuỗi bí mật thêm vào trust để tránh confused deputy. | 13 |

## F

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Failover** | Chuyển vai primary sang standby. | 08 |
| **Fargate** | Chạy container không cần quản lý EC2. | 18 |
| **Fleet Manager** | Màn hình quản lý instance và trạng thái agent. | 09 |
| **Flow Logs** | Nhật ký luồng IP, có ACCEPT/REJECT. | 15 |
| **Flow Logs** | Bằng chứng ACCEPT/REJECT. | 17 |

## G

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Gateway endpoint** | Cửa vào S3/DynamoDB qua route table, miễn phí. | 16 |

## H

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Health check** | Lễ tân gọi vào phòng xem app còn trả lời. | 05 |
| **Health check grace** | Thời gian ASG chờ app khởi động trước khi đánh unhealthy. | 22 |
| **Health check path** | Đường dẫn ALB gọi để kiểm tra app. | 17 |
| **Health check type** | ASG kiểm tra EC2 hay kiểm tra qua ELB. | 06 |
| **Healthy / Unhealthy** | Target có vượt qua health check hay không. | 05 |

## I

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **IAM policy** | Role/user được phép gọi action nào. | 10 |
| **Idempotency** | Chạy lại nhiều lần vẫn cho cùng kết quả. | 12 |
| **Identity path** | Đường app role → S3/secret. | 23 |
| **Ingestion delay** | Độ trễ từ lúc app ghi log đến lúc CloudWatch thấy. | 02 |
| **Instance profile** | Thẻ IAM gắn vào EC2. | 09 |
| **INSUFFICIENT_DATA** | Chưa đủ dữ liệu để kết luận, không phải lỗi. | 01 |
| **Interface endpoint** | ENI riêng trong subnet cho phần lớn service khác, có phí. | 16 |

## K

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Key policy** | Ai được dùng key, gắn trực tiếp vào key. | 10 |
| **KMS alias** | Tên dễ nhớ trỏ tới một khoá mã hoá, ví dụ `alias/soa-c03-lab`. | 00 |

## L

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Latency** | Thời gian phản hồi. | 20 |
| **Launch template** | Bản thiết kế EC2: AMI, instance type, user-data, SG. | 06 |
| **Layered fix** | Sửa một lớp, verify, rồi mới sang lớp tiếp. | 17 |
| **Layered fix** | Sửa từng lớp, verify sau mỗi lần. | 23 |
| **Listener** | Cửa của ALB, ví dụ HTTP:80. | 05 |
| **Log group** | Thư mục log, ví dụ `/aws/cloudops/soa-c03/app`. | 02 |
| **Log stream** | Một dãy log từ một nguồn, thường là một file trên một instance. | 02 |
| **Logs Insights** | Ngôn ngữ query log có `fields`, `filter`, `stats`, `sort`. | 02 |

## M

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Management event** | Sự kiện gọi API quản trị, ví dụ TerminateInstances. | 03 |
| **Metric** | Đồng hồ đo, ví dụ CPUUtilization. | 01 |
| **Metric filter** | Bộ lọc biến dòng log khớp pattern thành metric. | 02 |
| **Metric filter** | Biến dòng log ERROR thành metric `CapstoneErrorCount`. | 04 |
| **Multi-AZ** | Một primary + một standby đồng bộ ở AZ khác. | 08 |

## N

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **NACL** | Tường lửa stateless gắn vào subnet. | 15 |
| **NACL** | Tường lửa stateless ở subnet, có số thứ tự. | 17 |
| **Namespace** | Ngăn tủ chứa metric, ví dụ `AWS/EC2`. | 01 |

## P

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Parameter Store** | Ngăn kéo lưu cấu hình dạng key/value. | 00 |
| **Parameter Store** | Kho key/value cho cấu hình. | 09 |
| **Period** | Mỗi bao lâu lấy một điểm, ví dụ 60 giây. | 01 |
| **Permission policy** | Quyền của role sau khi được assume. | 13 |
| **Private DNS** | Phân giải tên service thành IP nội bộ. | 16 |

## R

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Reachability Analyzer** | Công cụ mô phỏng đường đi và tìm điểm chặn. | 15 |
| **Read replica** | Bản sao chỉ đọc, khác Multi-AZ. | 08 |
| **Recovery point** | Một bản backup cụ thể. | 19 |
| **Recovery point** | Một bản backup. | 22 |
| **Resource-based policy** | Ai được phép gọi Lambda. | 12 |
| **Restore** | Tạo DB mới từ snapshot. | 07 |
| **Retention** | Bao lâu thì log tự bị xoá. | 02 |
| **Root cause** | Lớp thật sự hỏng. | 20 |
| **Route table** | Bảng chỉ đường ra Internet/giữa subnet. | 15 |
| **Route table association** | Gắn endpoint với route table của subnet. | 16 |
| **RPO** | Mất tối đa bao nhiêu dữ liệu tính từ lần backup gần nhất. | 07 |
| **RTO** | Mất bao lâu để dịch vụ chạy lại. | 07 |
| **RTO** | Thời gian downtime thực tế. | 08 |
| **Run Command** | Chạy script trên nhiều instance, có lịch sử output. | 09 |
| **Runbook** | Các bước xử lý khi sự cố. | 22 |

## S

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Scaling activity** | Nhật ký ASG thử thêm/bớt máy và kết quả. | 06 |
| **Secret** | Chuỗi bí mật lưu trong Secrets Manager. | 21 |
| **Security group** | Tường lửa stateful gắn vào ENI. | 15 |
| **Security group** | Tường lửa stateful ở ENI. | 17 |
| **Self-healing** | Hệ thống tự thay thành phần hỏng. | 22 |
| **Service** | Bộ quản lý giữ số task đúng desired count. | 18 |
| **Session** | Phiên assume, có thời hạn. | 13 |
| **Session Manager** | Shell từ xa không cần SSH hay public IP. | 09 |
| **Snapshot** | Ảnh chụp dữ liệu tại một thời điểm. | 07 |
| **SSE-KMS** | S3 mã hoá object bằng một key KMS. | 10 |
| **SSM Agent** | Bot trên EC2 nói chuyện với Systems Manager. | 09 |
| **Stack** | Một nhóm tài nguyên được quản lý chung. | 11 |
| **Stack event** | Nhật ký từng bước tạo/sửa/xoá resource. | 11 |
| **Statistic** | Cách gộp các điểm trong period: Average, Maximum, Sum... | 01 |
| **Symptom** | Cái người dùng thấy: chậm, 500, 503. | 20 |

## T

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Target** | Đích rule gọi tới: Lambda, SQS, SNS... | 12 |
| **Target group** | Danh sách instance/container nhận traffic. | 05 |
| **Task** | Một container đang chạy. | 18 |
| **Task definition** | Bản thiết kế container: image, CPU, memory, log. | 18 |
| **Triage** | Ưu tiên kiểm tra theo thứ tự user-facing trước. | 20 |
| **Triage** | Phân loại và ưu tiên theo mức ảnh hưởng. | 23 |
| **Trust policy** | Danh sách principal được phép assume role. | 13 |

## U

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Update rollback** | Tự quay về trạng thái trước khi update lỗi. | 11 |
| **User-facing path** | Đường người dùng đi: ALB → target → app. | 23 |

## V

| Thuật ngữ | Nghĩa đời thường | Lab |
|---|---|---|
| **Version** | Một bản snapshot của template; `$Latest` là bản mới nhất. | 06 |
