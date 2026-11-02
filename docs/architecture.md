# Architecture

## Hai stack, hai vòng đời

```text
core stack (persistent, ~USD 1-2/month)
  VPC 10.42.0.0/16
    public  subnets 10.42.0.0/24, 10.42.1.0/24  -> IGW
    private subnets 10.42.10.0/24, 10.42.11.0/24 -> no egress by default
  S3 data bucket (versioned, SSE-KMS, BPA on)
  KMS key + alias
  CloudTrail (multi-region, log validation)
  SNS alerts topic
  IAM: app instance role, Lambda remediation role, lab operator role
  SSM parameters: /soa-c03/app/port, /soa-c03/app/health-path

app stack (on demand, deploy/delete per session)
  Internet -> ALB :80 -> target group :8080 -> ASG (t4g.micro) -> app
                                                   |
                                                   +-> RDS PostgreSQL (private)
  CloudWatch alarms -> SNS
  EventBridge EC2 state change -> SNS
```

Vì sao tách:

- **Cost:** core chạy 24/7 chỉ tốn vài cent/ngày. App stack (ALB + RDS + EC2) là phần tốn tiền, bật đúng lúc lab và xoá cuối buổi.
- **Lifecycle:** xoá app stack không mất CloudTrail, bucket, KMS, IAM, SSM.
- **Exam:** bạn luyện `Fn::ImportValue`, cross-stack reference, stack update/delete, drift — những thứ SOA-C03 hỏi.
- **Blast radius:** phá app stack không ảnh hưởng core.

## Vì sao không có NAT mặc định

NAT Gateway ~USD 0.059/giờ (~42/tháng ở ap-southeast-1). Với lab:

- Public subnet dùng IGW (miễn phí).
- Private subnet dùng **Gateway VPC Endpoint cho S3** (miễn phí) và **Interface Endpoint cho SSM** (~0.01/giờ/AZ) khi cần.
- Chỉ bật NAT trong một lab ngắn nếu thực sự muốn so sánh.

`EnableNat=true` trong `platform/core.yaml` tạo NAT + route; nhớ set lại `false` ngay sau lab.

## Luồng dữ liệu của app

```text
GET /            -> identity JSON
GET /health      -> 200, dùng cho ALB health check
GET /ready       -> DB check
GET /db          -> PostgreSQL SELECT 1 qua Secrets Manager
GET /error       -> 500 + ERROR log (metric filter / alarm)
GET /log         -> log level tùy chọn
GET /load        -> spawn CPU workers (CPU alarm / ASG)
GET /stop        -> kill CPU workers
GET /slow        -> sleep (latency alarm)
GET /config      -> cấu hình không bí mật
```

Log là JSON lines trong `/var/log/cloudops/app.log`; CloudWatch Agent gửi lên log group
`/aws/cloudops/soa-c03/app`. Metric filter mẫu:

```text
{ $.level = "ERROR" }
```

## Tag strategy

Mọi resource có:

```text
Project=soa-c03
Lab=soa-c03
ExpiryDate=2026-12-01
```

`scripts/inventory.sh` và `scripts/cleanup-all.sh` dựa vào tag này. Nếu bạn tạo resource
bằng tay, hãy tag ngay — nếu không cleanup sẽ bỏ sót.

## Đây không phải production

- ALB mở 80 cho toàn Internet.
- App SG egress all (để SSM/S3/CloudWatch hoạt động đơn giản).
- RDS dùng managed password nhưng `DeletionProtection=false`.
- Không có WAF, Shield Advanced, multi-account landing zone.

Mục tiêu là **học phản xạ vận hành**, không phải dựng landing zone production. Khi đã quen,
bạn siết SG, thêm endpoint, bật WAF/GuardDuty như bài nâng cao.
