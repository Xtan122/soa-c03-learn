# Troubleshooting the lab platform

## `make init` / credentials

```bash
aws sts get-caller-identity
aws configure list
```

- Sai account: sửa `LAB_ACCOUNT_ID` trong `.env` hoặc đổi profile.
- Region sai: `AWS_REGION` trong `.env`; mặc định `ap-southeast-1`.

## Core stack rollback

| Symptom | Nguyên nhân thường gặp | Fix |
|---|---|---|
| S3 bucket already exists | Bucket name `soa-c03-<account>-<region>-data` đã tồn tại | Xoá bucket cũ hoặc đổi `LAB_PREFIX` |
| KMS key pending deletion | Key cũ chưa xoá xong | Chờ hoặc dùng key mới/đổi prefix |
| CloudTrail bucket policy | Bucket policy thiếu quyền CloudTrail | Xem Stack Events, sửa `core.yaml` |
| `EnableNat`/`EnableFlowLogs` lạ | Condition/param | Đặt cả hai `false` khi bootstrap |

Xem lỗi:

```bash
aws cloudformation describe-stack-events --stack-name soa-c03-core \
  --max-items 20 --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
  --output table
```

## App stack không tạo được

- **AMI**: kiểm tra SSM public parameter:
  `aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`
- **RDS**: `db.t4g.micro` phải có trong region; kiểm tra quota DB instances.
- **ALB name**: `soa-c03-alb` phải unique trong account/region.
- **EIP/quota**: NAT mặc định tắt nên ít gặp; nếu bật NAT, kiểm tra EIP quota.
- **Stack rollback**: đọc Events, không đoán.

## App không healthy

```bash
# Lấy instance và URL
./bin/lab status

# Nếu SSM online
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["tail -100 /var/log/cloudops-bootstrap.log","journalctl -u cloudops-app -n 100 --no-pager"]'
```

Các lỗi hay gặp:

| Log | Nguyên nhân |
|---|---|
| `aws: command not found` | user-data không cài được AWS CLI |
| `Unable to locate credentials` | instance profile thiếu hoặc chưa gắn |
| `pip3 install` timeout | public subnet không có egress / DNS |
| `Permission denied` khi đọc S3 | IAM role hoặc KMS |
| app chạy nhưng ALB 503 | SG 8080, health path, port |

## App stack có target unhealthy / alarm `unhealthy-hosts`

Triệu chứng:

- `curl http://<alb>/health` vẫn 200 vì còn 1 instance khoẻ.
- Target Group có 1 target `unhealthy`.
- Alarm `soa-c03-unhealthy-hosts` ở `ALARM`.

Nguyên nhân đã gặp trong repo này: user-data cũ chạy `pip3 install boto3` vào
**system Python**, làm hỏng AWS CLI v2 của AL2023 (`ModuleNotFoundError: No module named 'dateutil'`).
Instance mới không tải được app từ S3 nên không healthy.

Cách kiểm tra:

```bash
aws elbv2 describe-target-health --target-group-arn <tg>
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["tail -40 /var/log/cloudops-bootstrap.log"]'
```

Nếu thấy lỗi `dateutil` hoặc `aws s3 cp` fail:

1. Code đã được sửa sang virtualenv (`/opt/cloudops/venv`) và service file dùng venv python.
2. Đưa launch template mới vào app stack. Thử update trước (giữ RDS):

```bash
make app-up
```

Nếu target vẫn unhealthy sau 10 phút, tạo lại sạch:

```bash
make app-down
make app-up
```

3. Kiểm tra lại:

```bash
./bin/lab status
make doctor
```

Không chạy lab tiếp theo khi vẫn còn target unhealthy, vì alarm baseline sẽ gây nhiễu.

## SSM không online

1. Instance có public IP hoặc NAT/endpoint để ra 443?
2. Instance profile có `AmazonSSMManagedInstanceCore`?
3. Private subnet: có interface endpoint `ssm`, `ssmmessages`, `ec2messages`?
4. Endpoint SG cho phép 443 từ instance SG?
5. Agent: `systemctl status amazon-ssm-agent`.

## `/db` trả 503

```bash
# Từ app instance
source /etc/cloudops.env
aws secretsmanager get-secret-value --secret-id "$DB_SECRET_ARN" --query SecretString --output text
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c 'select 1'
```

- `AccessDenied` secret → IAM role.
- `KMS` → key policy.
- `timeout` → DB SG 5432, NACL, route, DNS.
- `too many connections` → `DatabaseConnections` metric, RDS Proxy.

## CloudTrail không thấy event

- Trail đang logging? `aws cloudtrail get-trail-status --name soa-c03-trail`.
- Đúng region? Management events được ghi ở region xảy ra.
- Data events mặc định tắt (S3 object-level, Lambda invoke).
- Event history chỉ giữ 90 ngày.
- IAM role vừa assume có thể mất vài giây để event xuất hiện.

## Alarm không chuyển ALARM

- Period × EvaluationPeriods: alarm cần đủ số datapoint.
- `TreatMissingData`: `notBreaching` có thể giữ OK nếu metric không có data.
- Dimension sai (ASG name, ALB full name, DB identifier).
- Detailed monitoring: metric 1 phút cần bật; basic là 5 phút.
- Metric filter: pattern có khớp JSON log? Dùng `Test metric filter` trong console.

## `./bin/lab up` fail hoặc chạy lần 2 fail

Trước tiên chạy read-only:

```bash
./bin/lab preflight <id>
./bin/lab preflight <id> --live
```

- Static fail: đọc dòng `FAIL`, thường là thiếu function, thiếu mục 5c, hoặc tên
  tài nguyên trong README không khớp `labs.sh`.
- `--live` báo account khác: sửa credential, không cố chạy tiếp.
- `--live` báo leftover: dọn bằng `./bin/lab down <id>`, rồi preflight lại.
- Lỗi hay gặp:
  - `InvalidGroup.Duplicate`: canary/SG cũ còn; `down` rồi `up` lại.
  - `DBSnapshotAlreadyExists`: snapshot cũ; `down 07` rồi `up 07`.
  - `ResourceConflictException` (Lambda): permission cũ; `down 12` rồi `up 12`.
  - Interface endpoint trùng: `down 16` (xoá theo tag `Lab=lab16`).
  - Backup plan trùng: `down 19` hoặc `down 22`.
- Không sửa bằng cách xoá stack app; chỉ dọn resource của lab.

## Verify fail dù đã fix

- Đợi thêm 1-2 phút (ALB health check 15s × 3, alarm evaluation).
- Chạy `./bin/lab reset <id>` nếu đã sửa nửa vời.
- Kiểm tra bạn đang ở đúng account/region.
- Đọc `evidence/verify-last.txt` để xem check nào fail.

## Cleanup còn sót

```bash
make inventory
make cost
```

- S3 versioned bucket: phải xoá versions + delete markers (script làm).
- ENI còn gắn: xoá instance/endpoint trước.
- EIP: release sau khi xoá NAT/instance.
- KMS: pending deletion 7 ngày, không tính là còn chạy.
- GuardDuty/Security Hub: tắt detector nếu lab bật.
