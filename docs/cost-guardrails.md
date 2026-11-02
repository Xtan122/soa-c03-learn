# Cost guardrails

## Deadline

| Mốc | Ngày |
|---|---|
| Bắt đầu track 30 ngày | 2026-10-24 |
| Thi (mục tiêu) | ~2026-11-21 |
| **Phải xoá toàn bộ tài nguyên** | **2026-12-01** |
| Credit hết hạn | 2026-12-03 |

Đặt `EXPIRY_DATE=2026-12-01` trong `.env`. Mọi stack/resource được tag bằng ngày này.

## Giá tham khảo (ap-southeast-1, on-demand, 2026-10-24)

> Giá dưới đây lấy từ **AWS Price List API** cho `ap-southeast-1` ngày 2026-10-24,
> không phải giá us-east-1. Giá có thể đổi; trước khi chạy dài, kiểm tra lại bằng
> [AWS Pricing Calculator](https://calculator.aws/).

| Resource | Giá ap-southeast-1 | 3 giờ lab | Bỏ quên 30 ngày |
|---|---:|---:|---:|
| t4g.micro | **$0.0106/h** | $0.032 | $7.63 |
| EBS gp3 8 GiB | **$0.096/GiB-month** | ~$0.003 | $0.77 |
| Public IPv4 | $0.005/h | $0.015 | $3.60 mỗi địa chỉ |
| ALB | **$0.0252/h** + $0.008/LCU-h | ~$0.10 | ~$18.14 + LCU |
| NAT Gateway | **$0.059/h** + $0.059/GB | $0.177 | **$42.48** + data |
| RDS db.t4g.micro PostgreSQL single-AZ | **$0.025/h** + storage | ~$0.087 | ~$20.76 |
| RDS Multi-AZ | compute x2, storage $0.276/GB-mo | ~$0.17 | ~$41.50 |
| EKS control plane | ~$0.10/h | $0.30 | **~$72** |
| KMS key | $1/key-month + $0.03/10k requests | ~$0.004 | $1 |
| Secrets Manager | $0.40/secret-month + $0.05/10k requests | ~$0.002 | $0.40 |
| CloudWatch Logs ingest | $0.50/GB (first 10 TB) | cents | tùy log |
| CloudWatch alarm | $0.10/alarm-month | ~$0 | $0.10/alarm |
| S3 Standard | $0.025/GB-month (first 50 TB) | cents | tùy dung lượng |
| EBS snapshot | $0.05/GB-month | cents | tùy dung lượng |
| Lambda / SNS / SQS / SSM / IAM / CloudTrail mgmt | free/cent | ~$0 | ~$0 |

**Một buổi app stack 3 giờ** (ALB + 1–2 EC2 + RDS + IPv4 + logs) ≈ **$0.30–0.45**.
**24 lab** ≈ **$10–25** nếu dọn đúng. **Bỏ quên app stack 24/7**:
~**$70–75/tháng** nếu không NAT; ~**$115/tháng** nếu bật NAT.

### Vì sao NAT là bẫy lớn nhất

`$0.059/giờ` nghe nhỏ, nhưng 24/7 là **$42.48/tháng** chỉ cho một NAT Gateway,
chưa tính data processing. Đừng bật NAT trừ khi lab yêu cầu rõ ràng.
Dùng public subnet hoặc VPC Gateway Endpoint cho S3 (miễn phí).

## 7 luật

1. **Một region, một AZ** trừ lab Multi-AZ. Region mặc định: `ap-southeast-1`.
2. **Không bật NAT 24/7.** Dùng public subnet hoặc VPC endpoint.
3. **App stack chỉ sống trong buổi lab.** `make app-down` trước khi đóng laptop.
4. **Không EKS control plane.** Dùng ECS Fargate hoặc lab free trên Skill Builder.
5. **Log retention 7 ngày**, xoá log group của lab sau khi xong.
6. **Tag mọi thứ**; chạy `make inventory` cuối tuần.
7. **Budget $10/$25/$50** + `make cost` mỗi ngày.

## Routine mỗi buổi

```bash
make doctor          # trước khi bắt đầu
./bin/lab up 05
# ... lab ...
./bin/lab verify 05
./bin/lab down 05
make app-down        # nếu không làm lab tiếp trong ngày
make cost
```

## Cleanup ngày 01/12

```bash
DRY_RUN=yes make cleanup     # xem trước
CONFIRM_DESTROY=yes make cleanup
make inventory
make cost
```

`cleanup-all.sh` xoá: CloudFormation stacks, EC2, RDS, ALB/NLB, target groups, NAT, EIP,
VPC endpoints, Lambda, SQS, SNS, log groups, alarms, dashboards, secrets, SSM parameters,
Backup plans/vaults, Config, ECR, S3 buckets (versioned), IAM roles/policies, CloudTrail,
KMS (schedule deletion), budget.

**Không tự động xoá:** GuardDuty detector, Security Hub, KMS pending deletion (7 ngày).
Kiểm tra tay trong console.

## Dấu hiệu bạn đang đốt tiền

- `make cost` thấy EC2/RDS/ALB/NAT > 0 ngoài giờ lab.
- `make inventory` có resource không có tag `ExpiryDate`.
- CloudWatch Logs tăng nhanh (log debug còn bật).
- Có `eks` trong danh sách cluster.
- RDS Multi-AZ còn bật sau lab 08.
