# Runbook — {{ALERT_NAME}}

## Alert

- **Alarm:**
- **Metric / threshold:**
- **Symptom user thấy:**
- **Severity mặc định:**

## 5 phút đầu

1. Xác nhận alert còn active: `aws cloudwatch describe-alarms --alarm-names <name>`
2. Kiểm tra user-facing: `curl -s -o /dev/null -w '%{http_code}' https://<endpoint>/health`
3. Xác định blast radius: 1 instance hay cả fleet? 1 AZ hay cả region?
4. Không reboot mù. Không xoá stack.

## Chẩn đoán

```bash
# ALB / target
aws elbv2 describe-target-health --target-group-arn <tg>
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB ...

# EC2 / ASG
aws autoscaling describe-scaling-activities --auto-scaling-group-name <asg>
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["systemctl status cloudops-app","df -h","free -m"]'

# RDS
aws rds describe-db-instances --db-instance-identifier <db>
aws cloudwatch get-metric-statistics --namespace AWS/RDS ...

# Logs
aws logs start-query --log-group-name /aws/cloudops/soa-c03/app \
  --start-time $(date -u -d '15 minutes ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, level, event, message | filter level = "ERROR" | sort @timestamp desc'
```

## Mitigation

| Symptom | Hành động an toàn |
|---|---|
| ALB 503, target unhealthy | Sửa health path/SG/port; không xoá ALB |
| ASG không scale | Sửa launch template/user-data; rollback version |
| DB timeout | Sửa SG/NACL/route; kiểm tra connections; không restart DB ngay |
| CPU 100% | Scale out hoặc kill process; tìm root cause trước khi scale vô hạn |
| AccessDenied | So sánh identity/resource policy/KMS/permission boundary; explicit deny thắng |

## Verify

- `/health` = 200
- `/db` = 200
- target healthy ≥ 1
- alarm về OK
- log không còn ERROR mới
- chi phí không tăng bất thường

## Escalation

- Sau 15 phút chưa khoanh vùng: escalate.
- Sau 30 phút chưa mitigate: cân nhắc rollback thay đổi gần nhất.

## Follow-up

- Postmortem trong 48h.
- Action item phải có owner + deadline.
