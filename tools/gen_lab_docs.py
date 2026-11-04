#!/usr/bin/env python3
"""Generate beginner-friendly READMEs for the 24 labs.

The lab code lives in scripts/lib/labs.sh. This file is the source of truth
for the *student-facing* explanation. It intentionally describes symptoms and
where to look, not the root cause (hints are in lab.env).
"""
from __future__ import annotations

import pathlib
import sys

from lab_console import first_step, glossary_markdown, render_console
from lab_brief import BRIEFS, render_brief

ROOT = pathlib.Path(__file__).resolve().parents[1]
LABS = ROOT / "labs"
DOCS = ROOT / "docs"


def env_value(key: str, default: str) -> str:
    """Read one non-secret value from .env (or .env.example) for doc rendering."""
    for name in (".env", ".env.example"):
        path = ROOT / name
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


PREFIX = env_value("LAB_PREFIX", "soa-c03")
REGION = env_value("AWS_REGION", "ap-southeast-1")

# id: (title, domain, minutes, needs_app, purpose, state, arch, symptom,
#      observe, success, exam, note, special)
L = {
"00": (
 "Bootstrap: account, budget, core stack, guardrails", "Foundation", 90, "no",
 "Đây không phải lab phá hệ thống. Đây là bước lắp \"nền nhà\": account, budget, VPC, S3, KMS, CloudTrail, IAM, SSM. Nếu bước này sai, mọi lab sau đều sai theo.",
 "Core stack đã được tạo bởi `make bootstrap`. App stack có thể đang tắt. Chưa có fault nào.",
 """Internet
   │
   ▼
Core stack: VPC, S3 bucket, KMS, CloudTrail, SNS, IAM, SSM
   │
   └── App stack (bật sau, khi làm lab 01+)""",
 "Không có sự cố. Bạn chỉ kiểm tra baseline: CloudTrail có ghi log, S3 có chặn public, KMS/SSM có tồn tại, budget có cảnh báo.",
 [
  ("CloudTrail có đang ghi log?", "`aws cloudtrail get-trail-status --name soa-c03-trail`"),
  ("S3 có chặn public hoàn toàn?", "`aws s3api get-public-access-block --bucket <bucket>`"),
  ("Budget có tồn tại?", "`aws budgets describe-budget --account-id <account> --budget-name soa-c03-monthly`"),
  ("SSM parameter cho app có chưa?", "`aws ssm get-parameter --name /soa-c03/app/port`"),
 ],
 "`./bin/lab verify 00` PASS: core stack healthy, Trail logging, S3 BPA on, SSM/KMS/budget tồn tại.",
 [
  "Ops baseline: account guardrails, budget, tagging, expiry date.",
  "CloudTrail management events vs data events.",
  "Vì sao phải có budget trước khi làm lab tốn tiền.",
 ],
 [
  "1. Tôi đã tạo gì? (core stack, budget, trail)",
  "2. Không có fault; verify baseline thay vì đi tìm lỗi.",
  "3. Bằng chứng: output của `make doctor` và `verify 00`.",
 ],
 "",
),
"01": (
 "CloudWatch metrics, dashboard, alarm, SNS", "D1 Monitoring 22%", 150, "yes",
 "Học cách biết một EC2 đang quá tải: xem metric nào, period/statistic nào, và tại sao chuông báo (alarm) có thể chậm hơn CPU thực tế.",
 "App stack đang chạy. Lab tạo một alarm theo dõi CPU của **một** instance cụ thể và một SQS queue để nhận thông báo.",
 """EC2 (1 instance)
  │  CPUUtilization (1 phút)
  ▼
CloudWatch Metric
  │  threshold > 50%
  ▼
Alarm ──► SNS topic ──► SQS queue""",
 "CPU tăng cao. Alarm có thể vẫn `OK` một lúc vì cần đủ period/evaluation. Đây là điểm dễ gây hoang mang cho người mới.",
 [
  ("CPU thực tế bao nhiêu?", "CloudWatch → Metrics → EC2 → CPUUtilization; xem Average và Maximum"),
  ("Alarm đang ở trạng thái nào?", "CloudWatch → Alarms → soa-c03-lab01-cpu-high; hoặc `aws cloudwatch describe-alarms`"),
  ("Process nào ăn CPU?", "SSM Run Command: `top -b -n1`, `ps aux --sort=-%cpu`"),
  ("Alarm có gửi thông báo không?", "SQS queue `soa-c03-lab01-events`; hoặc SNS topic"),
 ],
 "`verify 01` PASS: CPU max ≥ 50% **và** alarm đang `ALARM`. Đừng stop load trước khi verify; `./bin/lab down 01` sẽ stop.",
 [
  "Period, statistic, evaluation periods, `INSUFFICIENT_DATA`.",
  "Basic monitoring 5 phút vs detailed monitoring 1 phút.",
  "Alarm chỉ chuyển trạng thái sau đủ số datapoint, không tức thì.",
 ],
 [
  "1. Metric nào chứng minh EC2 quá tải?",
  "2. Vì sao chọn Average hay Maximum?",
  "3. Alarm mất bao lâu để chuyển ALARM?",
 ],
 "Lab 01 tạm suspend ASG scaling để CPU load không tạo thêm instance. `down 01` sẽ resume.",
),
"02": (
 "CloudWatch Logs, Agent, Insights, metric filter", "D1 Monitoring 22%", 150, "yes",
 "Học cách đưa log từ EC2 lên CloudWatch, query bằng Logs Insights, rồi biến một dòng `ERROR` thành metric và alarm.",
 "App stack chạy. App ghi log JSON vào `/var/log/cloudops/app.log`; CloudWatch Agent gửi lên log group. Lab tạo metric filter `ERROR` + alarm.",
 """App (JSON log)
  │  /var/log/cloudops/app.log
  ▼
CloudWatch Agent
  ▼
Log group /aws/cloudops/soa-c03/app
  ├── Logs Insights (query)
  └── Metric filter ERROR → CloudOpsLab/ErrorCount → Alarm""",
 "App sinh nhiều dòng `ERROR`. Log có thể mất 30–60 giây mới lên CloudWatch; metric filter cũng cần thêm thời gian.",
 [
  ("Log đã lên CloudWatch chưa?", "CloudWatch → Log groups → /aws/cloudops/soa-c03/app"),
  ("Có bao nhiêu ERROR?", "Logs Insights: `filter level = \"ERROR\" | stats count()`"),
  ("Metric filter có đếm đúng?", "CloudWatch → Metrics → CloudOpsLab → ErrorCount"),
  ("Alarm có kêu?", "CloudWatch → Alarms → soa-c03-lab02-errors"),
 ],
 "`verify 02` PASS: Logs Insights thấy ≥ 10 ERROR, metric `ErrorCount` ≥ 5, alarm `ALARM`.",
 [
  "CloudWatch Agent config: file path, log group, retention.",
  "Metric filter pattern `{ $.level = \"ERROR\" }`.",
  "Logs Insights khác `filter-log-events` ở chỗ nào.",
 ],
 [
  "1. Log đi qua những lớp nào?",
  "2. Vì sao metric filter chưa có datapoint ngay?",
  "3. Nếu log là text thường, pattern phải viết thế nào?",
 ],
 "",
),
"03": (
 "CloudTrail + EventBridge: ai đã terminate EC2?", "D1 Monitoring 22%", 150, "no",
 "Học cách trả lời câu hỏi forensics: ai gọi API, lúc nào, từ IP nào. Đây là lab CloudTrail + EventBridge, không phải lab sửa app.",
 "Core stack + CloudTrail đủ (không cần app stack). Lab tạo một canary EC2 nhỏ, một EventBridge rule bắt sự kiện EC2 stopped/terminated, và SQS để nhận event.",
 """Lab operator role
  │  AssumeRole → TerminateInstances
  ▼
Canary EC2  ──► CloudTrail (audit API)
  │
  └──► EventBridge rule ──► SQS""",
 "Canary bị terminate. CloudTrail có thể mất vài phút mới hiện event; EventBridge gần như ngay.",
 [
  ("Ai đã terminate?", "CloudTrail → Event history → Event name = TerminateInstances"),
  ("Actor là user hay role?", "Đọc `userIdentity.type`, `arn`, `sessionName`"),
  ("Gọi từ đâu?", "`sourceIPAddress`, `userAgent`"),
  ("EventBridge có bắt không?", "SQS `soa-c03-lab03-events`"),
 ],
 "`verify 03` PASS: CloudTrail có event TerminateInstances cho canary, actor là `AssumedRole`, có `sourceIPAddress`.",
 [
  "Management events vs data events; Event history chỉ 90 ngày.",
  "CloudTrail (ai gọi API) khác AWS Config (resource thay đổi thế nào).",
  "Event pattern phải khớp `source`, `detail-type`, `detail.state`.",
 ],
 [
  "1. Ai làm? (userIdentity)",
  "2. Làm gì? (eventName + requestParameters)",
  "3. Từ đâu? (sourceIPAddress)",
 ],
 "EventBridge rule nhận cả `stopped` và `terminated`; canary không cần SSH/SSM.",
),
"04": (
 "Capstone monitoring: 500 → metric → alarm → event", "D1 Monitoring 22%", 180, "yes",
 "Ghép toàn bộ mắt xích monitoring: app trả 500 → log ERROR → metric filter → alarm → EventBridge → SQS. Đây là bài tổng hợp của D1.",
 "App stack chạy. Lab tạo metric filter, alarm, EventBridge rule bắt alarm state change, và SQS.",
 """Client → ALB → App
                     │  HTTP 500 + log ERROR
                     ▼
              CloudWatch Logs → Metric Filter
                     ▼
                   Alarm (ALARM)
                     ▼
              EventBridge → SQS""",
 "Website trả nhiều 500. Bạn phải kiểm tra từng mắt xích, vì một mắt xích đúng chưa chắc cả chuỗi đúng.",
 [
  ("App có thật sự trả 500?", "`curl -i http://<alb>/error`"),
  ("Log có ERROR?", "Logs Insights filter level=ERROR"),
  ("Metric có tăng?", "CloudWatch Metrics → CloudOpsLab/CapstoneErrorCount"),
  ("EventBridge có gửi message?", "SQS `soa-c03-lab04-events`"),
 ],
 "`verify 04` PASS: metric ≥ 4, alarm `ALARM`, SQS có message.",
 [
  "Alarm state change là một event riêng, cần EventBridge rule.",
  "SQS policy phải cho phép `events.amazonaws.com` gửi message.",
  "Debug chuỗi theo thứ tự, đừng nhảy lớp.",
 ],
 [
  "1. Mắt xích nào đứt đầu tiên?",
  "2. Evidence nào chứng minh?",
  "3. Nếu chỉ có log mà không có metric, thiếu gì?",
 ],
 "",
),
"05": (
 "ALB health check → 503", "D2 Reliability 22%", 120, "yes",
 "Học vì sao ALB trả 503. 503 thường không phải app chết, mà là ALB không có target khoẻ.",
 "App stack chạy, ALB đang healthy, health check path là `/health`. Lab sẽ làm health check trỏ sai.",
 """Client → ALB :80 → Target Group
                         │ health check /health :8080
                         ▼
                       EC2 app""",
 "Trình duyệt/curl nhận 503. Target có thể vẫn `running` nhưng `unhealthy`.",
 [
  ("Target có healthy không?", "`aws elbv2 describe-target-health`"),
  ("Lý do unhealthy?", "Target health reason: `Target.FailedHealthChecks`, timeout, port..."),
  ("Health check path/port?", "Target Group → Health checks"),
  ("App có nghe đúng port?", "SSM: `ss -lntp | grep 8080`"),
 ],
 "`verify 05` PASS: health check path `/health`, target healthy, `curl /health` = 200.",
 [
  "503 do ALB không có healthy target; 502 do target trả lỗi; 504 do timeout.",
  "Health check interval × unhealthy threshold quyết định thời gian chuyển unhealthy.",
  "SG của target phải cho phép ALB SG trên đúng port.",
 ],
 [
  "1. 503 hay 502/504?",
  "2. Target health reason là gì?",
  "3. Health check dùng path/port nào?",
 ],
 "",
),
"06": (
 "ASG scale-out thất bại", "D2 Reliability 22%", 150, "yes",
 "Học vì sao ASG không scale được: launch template, user-data, security group, subnet, health check. Đây là lỗi rất hay gặp khi vận hành.",
 "App stack chạy với 1 instance. Lab tạo một launch template version có user-data lỗi, đưa ASG dùng version đó, rồi tăng desired capacity lên 2.",
 """ALB → Target Group → ASG (desired 1)
                         │ scale out
                         ▼
                 Launch Template (bad user-data)
                         ▼
                 Instance mới không healthy""",
 "ASG nhận desired 2 nhưng instance mới không vào được target; Scaling Activity có thể báo `Failed`.",
 [
  ("ASG đang dùng launch template version nào?", "ASG → Launch template"),
  ("Scaling activity nói gì?", "`aws autoscaling describe-scaling-activities`"),
  ("Instance mới có health check không?", "EC2 status + target health"),
  ("User-data có lỗi không?", "SSM: `/var/log/cloudops-bootstrap.log`"),
 ],
 "`verify 06` PASS: desired 2, 2 target healthy, launch template về version gốc, có ít nhất 1 bằng chứng scale-out thất bại (scaling activity `Failed`, hoặc instance bị thay vì không qua ELB health check).",
 [
  "Health check type `ELB` vs `EC2`.",
  "Launch template version và `$Latest`.",
  "Cooldown, warmup, termination policy.",
 ],
 [
  "1. ASG có launch được instance không?",
  "2. Instance có healthy không?",
  "3. Lỗi nằm ở template, user-data, SG hay subnet?",
 ],
 "Sau khi sửa, nhớ đưa ASG về launch template version gốc và desired 1 nếu không làm tiếp lab scale.\n\nTrong lúc làm bài, lab tạm `suspend-processes AlarmNotification` của ASG để policy CPU TargetTracking không kéo desired về 1 sau ~9 phút. Đây là **chủ ý của lab**, không phải lỗi; `./bin/lab down 06` sẽ `resume-processes` lại.",
),
"07": (
 "RDS snapshot, restore, verify dữ liệu", "D2 Reliability 22%", 180, "yes",
 "Học backup/restore thật: tạo snapshot, xoá dữ liệu, restore ra DB mới, rồi chứng minh dữ liệu đã quay lại.",
 "App stack + RDS PostgreSQL chạy. Lab tạo bảng `lab07` 5 dòng và một snapshot thủ công.",
 """App EC2 → RDS PostgreSQL
                 │
                 ├── table lab07 (5 rows)
                 └── manual snapshot
                         │
                         ▼
                 restored DB (bạn tạo)""",
 "Dữ liệu trong bảng `lab07` bị xoá. Bạn phải restore snapshot ra một DB mới tên `soa-c03-lab07-restored`.",
 [
  ("Snapshot có tồn tại?", "`aws rds describe-db-snapshots --db-snapshot-identifier soa-c03-lab07-snapshot`"),
  ("Restore ra DB nào?", "RDS → Snapshots → Restore snapshot"),
  ("DB restored có cùng subnet/SG?", "Phải cùng private subnet group và DB SG"),
  ("Dữ liệu đã về chưa?", "`SELECT count(*) FROM lab07;` trên DB restored"),
 ],
 "`verify 07` PASS: DB `soa-c03-lab07-restored` available và bảng `lab07` có ≥ 5 dòng.",
 [
  "Automated backup vs manual snapshot vs restore.",
  "Restore tạo endpoint mới; app phải đổi DNS/parameter nếu muốn dùng.",
  "RTO/RPO: đo thời gian restore và mất bao nhiêu dữ liệu.",
 ],
 [
  "1. Snapshot tạo lúc nào?",
  "2. Restore mất bao lâu?",
  "3. Vì sao DB restored phải cùng subnet/SG?",
 ],
 """### Lệnh restore gợi ý

```bash
# Lấy subnet group và SG của DB gốc
aws cloudformation describe-stacks --stack-name soa-c03-app \
  --query "Stacks[0].Outputs[?OutputKey=='DbSubnetGroupName'].OutputValue" --output text
aws cloudformation describe-stacks --stack-name soa-c03-app \
  --query "Stacks[0].Outputs[?OutputKey=='DbSecurityGroupId'].OutputValue" --output text

aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier soa-c03-lab07-restored \
  --db-snapshot-identifier soa-c03-lab07-snapshot \
  --db-instance-class db.t4g.micro \
  --db-subnet-group-name <DbSubnetGroupName> \
  --vpc-security-group-ids <DbSecurityGroupId> \
  --no-publicly-accessible

aws rds wait db-instance-available \
  --db-instance-identifier soa-c03-lab07-restored
```

Đây là lab duy nhất bạn phải tạo DB mới bằng tay.""",
),
"08": (
 "RDS Multi-AZ + failover + RTO", "D2 Reliability 22%", 150, "yes",
 "Học Multi-AZ thực sự làm gì khi failover: endpoint có đổi không, app có timeout không, đo RTO.",
 "App stack + RDS chạy. `up 08` chuyển DB sang Multi-AZ; `break 08` yêu cầu failover.",
 """App EC2 → RDS endpoint (không đổi)
                 │
        ┌────────┴────────┐
        ▼                 ▼
     Primary           Standby
     (AZ A)            (AZ B)""",
 "DB failover. App có thể timeout vài chục giây; endpoint DNS vẫn giữ nguyên.",
 [
  ("MultiAZ đã bật chưa?", "`aws rds describe-db-instances --db-instance-identifier soa-c03-db`"),
  ("Có event failover không?", "`aws rds describe-events --source-identifier soa-c03-db`"),
  ("App có kết nối lại không?", "`curl http://<alb>/db`"),
  ("RTO là bao lâu?", "Đo từ lúc reboot đến khi `/db` = 200"),
 ],
 "`verify 08` PASS: `MultiAZ=True`, DB `available`, có event failover, `/db` = 200.",
 [
  "Multi-AZ vs Read Replica: sync/HA vs async/scale đọc.",
  "Endpoint không đổi khi failover.",
  "Failover không thay thế backup/DR cross-region.",
 ],
 [
  "1. Failover mất bao lâu?",
  "2. App có tự reconnect không?",
  "3. Multi-AZ khác Read Replica ở đâu?",
 ],
 "Multi-AZ tốn gấp đôi compute/storage. `down 08` sẽ đưa về single-AZ.",
),
"09": (
 "SSM Session Manager, Run Command, Parameter Store", "D3 Automation 22%", 120, "yes",
 "Học vận hành EC2 không cần SSH, không public IP: vào máy bằng Session Manager, chạy lệnh bằng Run Command, đọc config bằng Parameter Store.",
 "App stack chạy, SSM agent online. Lab tạo một parameter `/soa-c03/lab09/message`; `break 09` stop app service từ xa.",
 """Bạn → SSM
        ├── Session Manager → shell trên EC2
        ├── Run Command → chạy lệnh hàng loạt
        └── Parameter Store → config
EC2 → SSM agent → IAM role → SSM endpoint""",
 "App service bị stop từ xa. Bạn không SSH; mọi thứ đi qua SSM.",
 [
  ("Agent có online không?", "`aws ssm describe-instance-information`"),
  ("Service có chạy không?", "Run Command: `systemctl is-active cloudops-app`"),
  ("Parameter có đúng không?", "`aws ssm get-parameter --name /soa-c03/lab09/message`"),
  ("App có health không?", "`curl http://<alb>/health`"),
 ],
 "`verify 09` PASS: service `active`, `/health` 200, parameter đúng giá trị.",
 [
  "Session Manager vs Run Command vs Automation.",
  "SSM cần IAM role + outbound 443; private subnet cần interface endpoint.",
  "Parameter Store vs Secrets Manager.",
 ],
 [
  "1. Không SSH thì vào máy bằng gì?",
  "2. Agent thiếu quyền sẽ thế nào?",
  "3. Parameter Store lưu secret có an toàn không?",
 ],
 "",
),
"10": (
 "Secrets Manager + KMS: có quyền S3 vẫn AccessDenied", "D4 Security 16%", 150, "yes",
 "Học lỗi \"có quyền S3 nhưng vẫn AccessDenied\" vì object mã hoá KMS. Đây là bẫy rất hay gặp trong đề và thực tế.",
 "App stack + core KMS. Lab tạo secret, một object S3 mã hoá KMS, và role `soa-c03-lab10-reader` có quyền S3/Secret nhưng chưa có KMS.",
 """Reader role
   ├── s3:GetObject ──► S3 object (SSE-KMS)
   ├── secretsmanager:GetSecretValue ──► Secret
   └── kms:Decrypt?  ← thiếu hoặc bị deny
                         │
                         ▼
                     KMS key policy""",
 "Role đọc S3 bị `AccessDenied` dù policy S3 đúng; secret cũng có thể bị chặn.",
 [
  ("Role có quyền S3 không?", "IAM role policy"),
  ("Object dùng KMS key nào?", "S3 object → Properties → Encryption"),
  ("Key policy cho role chưa?", "KMS → Key policy"),
  ("Có explicit deny không?", "Key policy + IAM policy"),
 ],
 "`verify 10` PASS: role `soa-c03-lab10-reader` đọc được object và secret.",
 [
  "IAM cho S3 không đủ nếu object SSE-KMS.",
  "Key policy + IAM policy + resource policy; explicit deny thắng.",
  "Secrets Manager secret cũng có resource policy/KMS.",
 ],
 [
  "1. AccessDenied ở API nào?",
  "2. Thiếu `kms:Decrypt` hay bị deny?",
  "3. Sửa IAM hay key policy?",
 ],
 "Lab này cần quyền `sts:AssumeRole` cho user của bạn. Nếu AssumeRole fail, đó là lab 13.",
),
"11": (
 "CloudFormation update rollback + drift + CDK", "D3 Automation 22%", 150, "no",
 "Học IaC thật: update stack bị lỗi thì CloudFormation rollback thế nào, đọc Stack Events ra sao, drift là gì, CDK synth làm gì.",
 "Core stack đủ; không cần app. Lab tạo stack `soa-c03-lab11` gồm SQS, S3 bucket, SSM parameter.",
 """template.yaml
   ├── SQS
   ├── S3 bucket
   └── SSM parameter
        │
        ▼
CloudFormation stack soa-c03-lab11""",
 "Bạn update stack bằng một template lỗi. Update bắt đầu, fail, rồi rollback. Stack có thể ở `UPDATE_ROLLBACK_COMPLETE`.",
 [
  ("Resource nào fail đầu tiên?", "`aws cloudformation describe-stack-events` — đọc event `*_FAILED` đầu tiên"),
  ("Stack đang ở trạng thái nào?", "`aws cloudformation describe-stacks`"),
  ("Có drift không?", "`detect-stack-drift` + `describe-stack-resource-drifts`"),
  ("CDK có synth ra template không?", "`cd labs/11-cloudformation-cdk/cdk && cdk synth`"),
 ],
 "`verify 11` PASS: stack `CREATE_COMPLETE`/`UPDATE_COMPLETE` sau khi bạn sửa template.",
 [
  "`ROLLBACK_COMPLETE` vs `UPDATE_ROLLBACK_COMPLETE`.",
  "Stack Events: đọc từ dưới lên, tìm lỗi đầu tiên.",
  "CDK synth tạo CloudFormation template; CDK không phải dịch vụ runtime.",
 ],
 [
  "1. Lỗi đầu tiên là gì?",
  "2. Rollback đã trả resource về trạng thái cũ chưa?",
  "3. Drift khác update lỗi ở đâu?",
 ],
 "`./bin/lab reset 11` sẽ update lại template gốc. Chỉ dùng sau khi đã đọc Stack Events.",
),
"12": (
 "Event-driven remediation: EC2 stopped → Lambda start", "D3 Automation 22%", 150, "yes",
 "Học tự động sửa lỗi: EC2 bị stop → EventBridge → Lambda → start lại → thông báo. Đây là pattern remediation hay hỏi trong SOA.",
 "App stack chạy. Lab tạo Lambda `soa-c03-lab12-remediate`, rule EC2 stopped, canary có tag `auto-remediate=true`, và SQS.",
 """EC2 stopped
   │  EventBridge rule (state=stopped)
   ▼
Lambda (kiểm tra tag auto-remediate=true)
   │
   ├── ec2:StartInstances
   └── SQS message""",
 "Canary bị stop. Trong 1–2 phút, Lambda phải start lại. Nếu không, xem rule/Lambda permission/log.",
 [
  ("Rule có match event không?", "EventBridge → Rules → soa-c03-lab12-remediate → Monitoring"),
  ("Lambda có được gọi không?", "CloudWatch Logs `/aws/lambda/soa-c03-lab12-remediate`"),
  ("Lambda có quyền start không?", "IAM role của Lambda"),
  ("Canary có tag đúng không?", "EC2 tags `auto-remediate=true`"),
 ],
 "`verify 12` PASS: canary `running`, log Lambda có `started`, SQS có message.",
 [
  "Event pattern + target permission + Lambda resource policy.",
  "Idempotency: event có thể đến nhiều lần.",
  "Remediation phải có guardrail để không start instance sai.",
 ],
 [
  "1. Event có tới rule không?",
  "2. Rule có gọi Lambda không?",
  "3. Lambda có quyền và tag đúng không?",
 ],
 "",
),
"13": (
 "IAM + STS AssumeRole: trust policy vs permissions", "D4 Security 16%", 120, "no",
 "Học lỗi AssumeRole: trust policy quyết định ai được assume; permission policy quyết định làm được gì. Đây là cặp bài trùng rất hay nhầm.",
 "Core stack đủ. Lab tạo role `soa-c03-lab13-target` tin cậy account của bạn và có quyền đọc S3.",
 """Bạn (IAM user)
   │ sts:AssumeRole
   ▼
Role soa-c03-lab13-target
   ├── Trust policy: ai được assume?
   └── Permission policy: được làm gì? (S3)""",
 "AssumeRole fail dù role có policy S3 đúng. Lỗi nằm ở trust policy, không phải permission.",
 [
  ("Trust policy đang tin ai?", "IAM → Roles → Trust relationships"),
  ("Permission policy có gì?", "IAM → Permissions"),
  ("Lỗi STS nói gì?", "`aws sts assume-role ...`"),
  ("Sau khi assume, là ai?", "`aws sts get-caller-identity`"),
 ],
 "`verify 13` PASS: AssumeRole thành công, identity là role, `aws s3 ls` được.",
 [
  "Trust policy vs permission policy.",
  "Role session, temporary credentials, expiry.",
  "Cross-account cần trust ở account đích + quyền sts:AssumeRole ở nguồn.",
 ],
 [
  "1. Ai được assume?",
  "2. Assume xong làm được gì?",
  "3. Lỗi nằm ở trust hay permission?",
 ],
 "Nếu user của bạn không có `sts:AssumeRole`, lab này sẽ fail ở bước assume; đó là lỗi quyền của user, không phải lab.",
),
"14": (
 "S3 public exposure: detect, contain, fix", "D4 Security 16%", 150, "no",
 "Học cách phát hiện và đóng bucket S3 bị public: Block Public Access, bucket policy, ACL, Access Analyzer.",
 "Core stack đủ. Lab tạo bucket `soa-c03-lab14-<account>`, object `secret.txt`, BPA bật, Access Analyzer.",
 """Internet
   │
   ▼
S3 bucket (BPA + bucket policy)
   ├── object secret.txt
   └── Access Analyzer finding""",
 "Bucket bị mở public. Bạn phải chứng minh nó public, rồi đóng lại mà vẫn giữ object.",
 [
  ("BPA có bật đủ 4 cờ?", "`aws s3api get-public-access-block`"),
  ("Bucket policy có public không?", "`get-bucket-policy-status`"),
  ("ACL có public không?", "`get-bucket-acl`"),
  ("Anonymous truy cập được không?", "`curl -I https://<bucket>.s3.<region>.amazonaws.com/secret.txt`"),
 ],
 "`verify 14` PASS: BPA on, policy không public, anonymous nhận 403.",
 [
  "BPA vs bucket policy vs ACL: ba lớp khác nhau.",
  "Access Analyzer tìm public/cross-account access.",
  "Public object có thể bị cache; đóng bucket trước, kiểm tra lại.",
 ],
 [
  "1. Public qua đường nào?",
  "2. BPA có che được bucket policy không?",
  "3. Anonymous 200 hay 403 chứng minh gì?",
 ],
 "",
),
"15": (
 "VPC: SG, NACL, route, Flow Logs, Reachability", "D5 Networking 18%", 150, "yes",
 "Học debug mạng theo lớp: SG → NACL → route → target. Không đoán; dùng Flow Logs và Reachability Analyzer để có bằng chứng.",
 "App stack chạy. Lab bật Flow Logs và tạo một Reachability Analyzer path từ ALB ENI đến app ENI.",
 """Client → ALB → SG → NACL → Route → EC2 app
                              │
                              └── Flow Logs ghi ACCEPT/REJECT
Reachability Analyzer kiểm tra path""",
 "App không truy cập được từ ALB; target unhealthy hoặc 503. Bạn phải tìm lớp nào chặn.",
 [
  ("Target health nói gì?", "Target Group → Targets"),
  ("SG app có cho ALB SG vào 8080?", "EC2 → Security Groups → Inbound"),
  ("NACL có deny không?", "VPC → Network ACLs → Inbound/Outbound"),
  ("Route có đúng không?", "VPC → Route tables"),
  ("Flow Logs nói ACCEPT hay REJECT?", "CloudWatch Logs `/aws/vpc/soa-c03/flow`"),
 ],
 "`verify 15` PASS: SG rule 8080 có, `/health` 200, Reachability Analyzer `reachable`.",
 [
  "SG stateful, NACL stateless; NACL cần ephemeral ports.",
  "Đọc Flow Logs: srcaddr/dstaddr/port/action.",
  "Reachability Analyzer chỉ ra lớp chặn.",
 ],
 [
  "1. Lớp nào chặn?",
  "2. Flow Logs chứng minh gì?",
  "3. NACL khác SG ở đâu?",
 ],
 "",
),
"16": (
 "Private subnet → S3 endpoint + SSM endpoint", "D5 Networking 18%", 180, "no",
 "Học private subnet không NAT: dùng Gateway Endpoint cho S3 (miễn phí) và Interface Endpoint cho SSM. Đây là kiến trúc tiết kiệm chi phí.",
 "Core VPC có private subnet. Lab tạo EC2 private (không public IP), interface endpoints cho SSM/SSM Messages/EC2 Messages, gateway endpoint cho S3.",
 """Private EC2 (no public IP)
   ├── SSM interface endpoint ──► SSM
   ├── SSM Messages endpoint
   ├── EC2 Messages endpoint
   └── S3 gateway endpoint ──► S3
   (không có NAT)""",
 "Private EC2 không truy cập được S3. SSM vẫn có thể online nếu endpoint SSM đúng.",
 [
  ("Instance có public IP không?", "EC2 → Networking (phải không có)"),
  ("SSM có online không?", "`aws ssm describe-instance-information`"),
  ("S3 endpoint có route chưa?", "VPC → Endpoints → Route tables"),
  ("Từ private instance, `aws s3 ls` có được không?", "SSM Session Manager"),
 ],
 "`verify 16` PASS: S3 gateway endpoint tồn tại và private instance `aws s3 ls` thành công.",
 [
  "Gateway endpoint (S3/DynamoDB) vs Interface endpoint (phần lớn service khác).",
  "Private DNS cần `enableDnsSupport`/`enableDnsHostnames`.",
  "Endpoint phải được associate với đúng route table.",
 ],
 [
  "1. SSM online nhờ đâu?",
  "2. S3 đi đường nào?",
  "3. Nếu thiếu route table association thì sao?",
 ],
 "Interface endpoint tốn **$0.013/giờ/AZ** (Price List `ap-southeast-1`, 2026-11-01) — lab tạo 3 cái ⇒ ~$0.039/giờ. `down 16` dọn hết. Không bật NAT cho lab này.",
),
"17": (
 "Boss fight: 3 lỗi mạng cùng lúc", "D5 Networking 18%", 180, "yes",
 "Đây là bài tổng hợp D5: 3 lỗi cùng lúc ở target health, SG và NACL. Bạn phải tách lớp, không sửa mù.",
 "App stack chạy. Lab bật Flow Logs và inject 3 lỗi: health check path sai, SG chặn 8080, NACL deny 8080.",
 """Client → ALB → Target Group (sai path)
                    │
                    ├── SG chặn 8080
                    └── NACL deny 8080
                         ▼
                       EC2 app""",
 "ALB 503, target unhealthy, app có thể vẫn chạy. Một lỗi có thể che lỗi khác.",
 [
  ("Target healthy không?", "Target Group → Targets"),
  ("Health check path đúng chưa?", "Target Group → Health checks"),
  ("SG có cho 8080 không?", "EC2 → Security Groups"),
  ("NACL có deny 8080 không?", "VPC → Network ACLs"),
 ],
 "`verify 17` PASS: path `/health`, SG allow, NACL không deny 8080, target healthy, `/health` 200.",
 [
  "Sửa từng lớp, verify sau mỗi lần.",
  "NACL là stateless; deny inbound 8080 đủ làm app chết.",
  "Một fix có thể che symptom nhưng chưa hết root cause.",
 ],
 [
  "1. Lỗi nào lộ ra trước?",
  "2. Lỗi nào bị che?",
  "3. Bạn chứng minh từng lớp bằng gì?",
 ],
 "",
),
"18": (
 "ECS Fargate + Container Insights + ECR", "D3 Automation 22%", 180, "yes",
 "Học container cơ bản: task vs service, Fargate, execution role, logs, ECR, Container Insights. Đây là phần mới của SOA-C03.",
 "App stack chạy. Lab tạo ECS cluster, service Fargate chạy nginx public image, ECR repo, log group, Container Insights.",
 """Internet → Fargate task (nginx :80)
                 │
                 ├── awslogs → CloudWatch
                 └── Container Insights → ECS metrics
ECR repo (image registry)""",
 "Task bị stop. ECS service phải tự tạo task mới; bạn kiểm tra service events và task stopped reason.",
 [
  ("Service running count?", "`aws ecs describe-services`"),
  ("Task stop reason?", "`aws ecs describe-tasks`"),
  ("Container log nói gì?", "`aws logs tail /aws/ecs/soa-c03/lab18`"),
  ("Task có public IP và HTTP 200?", "`curl http://<task-public-ip>`"),
 ],
 "`verify 18` PASS: service running 1, task HTTP 200.",
 [
  "Task definition vs service vs task.",
  "Fargate cần execution role để pull image/ghi log.",
  "Container Insights cần bật ở cluster; metric có thể trễ.",
 ],
 [
  "1. Task có chạy không?",
  "2. Nếu stop, lý do là gì?",
  "3. Service khác task ở đâu?",
 ],
 "Image dùng `public.ecr.aws/nginx/nginx:latest`; nếu public registry bị chặn, push image lên ECR.",
),
"19": (
 "AWS Backup, Config, Cost Explorer, Budgets", "D2/D3", 180, "yes",
 "Học vận hành backup/compliance/cost: backup plan, recovery point, Config recorder, budget, Cost Explorer. Không phải lab sửa app.",
 "App stack + RDS chạy. Lab tạo backup vault/plan/job, Config recorder/rule, budget riêng.",
 """AWS Backup
   ├── vault
   ├── plan (daily)
   └── on-demand job → recovery point

AWS Config
   ├── recorder → S3
   └── rule encrypted-volumes

Budgets + Cost Explorer""",
 "Config recorder bị stop; dữ liệu compliance trở nên cũ. Bạn kiểm tra backup job, recovery point, Config status, budget.",
 [
  ("Backup job xong chưa?", "`aws backup describe-backup-job --backup-job-id <id>`"),
  ("Có recovery point không?", "`aws backup list-recovery-points-by-backup-vault`"),
  ("Config có recording không?", "`aws configservice describe-configuration-recorder-status`"),
  ("Budget có tồn tại không?", "`aws budgets describe-budget`"),
  ("Cost Explorer có dữ liệu không?", "`aws ce get-cost-and-usage` (có thể trễ 24h)"),
 ],
 "`verify 19` PASS: backup `COMPLETED`, có recovery point, Config `recording=True`, budget tồn tại.",
 [
  "AWS Backup vs RDS snapshot; recovery point.",
  "Config (resource state/compliance) vs CloudTrail (API audit).",
  "Budget alert không chặn chi phí; chỉ thông báo.",
 ],
 [
  "1. Backup job mất bao lâu?",
  "2. Recovery point nằm ở đâu?",
  "3. Config khác CloudTrail thế nào?",
 ],
 "Backup RDS có thể mất vài phút. Cost Explorer có thể chưa có dữ liệu trong ngày; verify chỉ cảnh báo, không fail.",
),
"20": (
 "Incident: CPU 95% + 5xx + ALB", "D1/D2/D5", 180, "yes",
 "Đây là incident tổng hợp: CPU cao, app trả 500, ALB có thể 503. Bạn phải tách symptom khỏi root cause.",
 "App stack chạy. `break 20` tạo CPU load, 20 lỗi 500 và vài request chậm.",
 """Client → ALB → EC2 app
                    ├── CPU 95%
                    ├── HTTP 500
                    └── latency cao""",
 "Người dùng thấy chậm/500; CloudWatch thấy CPU cao; ALB có thể 503 nếu target unhealthy.",
 [
  ("CPU cao do process nào?", "CloudWatch + SSM `top`, `ps`"),
  ("App có lỗi gì?", "Logs Insights filter level=ERROR"),
  ("ALB thấy gì?", "Target health + ALB 5xx metrics"),
  ("DB có liên quan không?", "`/db` + RDS metrics"),
 ],
 "`verify 20` PASS: CPU giảm, `/health` và `/db` = 200, target healthy.",
 [
  "Không phải mọi 5xx đều do CPU; đọc log và target health.",
  "Scale out có thể che symptom nhưng không sửa root cause.",
  "Luôn kiểm tra user-facing path trước khi sửa sâu.",
 ],
 [
  "1. Symptom nào xuất hiện đầu tiên?",
  "2. CPU cao là nguyên nhân hay hậu quả?",
  "3. Fix nào an toàn nhất?",
 ],
 "",
),
"21": (
 "Incident: DB timeout + AccessDenied", "D2/D4", 180, "yes",
 "Incident kết hợp data path và identity path: app không vào được DB, đồng thời role bị deny secret. Bạn phải sửa cả hai lớp.",
 "App stack chạy. `break 21` chặn DB SG 5432 và gắn explicit deny `secretsmanager:GetSecretValue` cho app role.",
 """App → DB SG (5432 bị chặn) → RDS
  │
  └── Secrets Manager (bị deny)""",
 "`/db` trả 503/timeout; log app báo không lấy được secret hoặc không kết nối DB.",
 [
  ("DB SG có cho app SG vào 5432?", "EC2 → Security Groups → DB SG"),
  ("Secret có đọc được không?", "`aws secretsmanager get-secret-value`"),
  ("Role có explicit deny không?", "IAM → Role → Permissions"),
  ("App log nói gì?", "Logs Insights `db_check_failed`"),
 ],
 "`verify 21` PASS: DB SG allow 5432, không còn deny policy, `/db` 200, secret đọc được.",
 [
  "DB timeout: SG, NACL, route, DNS, max connections.",
  "AccessDenied: identity/resource/KMS/SCP/boundary.",
  "Hai triệu chứng có thể cùng root cause hoặc hai lỗi độc lập.",
 ],
 [
  "1. DB timeout hay auth error?",
  "2. Secret bị chặn ở đâu?",
  "3. Sửa mạng hay sửa quyền trước?",
 ],
 "",
),
"22": (
 "Production capstone: self-healing + backup", "All domains", 240, "yes",
 "Bài tổng hợp production-like: chứng minh ASG tự thay instance khi app chết, backup plan tồn tại, dashboard/alarm đủ, app vẫn phục vụ.",
 "App stack chạy, dashboard và alarm đã có. `up 22` tạo backup plan/vault cho RDS. `break 22` stop app service để ASG tự thay instance.",
 """ALB → ASG → EC2 app
          │  app service stopped
          ▼
     target unhealthy → ASG thay instance
RDS ← backup plan/vault""",
 "App service bị stop. Bạn phải thấy instance mới được tạo, target healthy trở lại, app 200.",
 [
  ("ASG có thay instance không?", "`describe-scaling-activities`, instance ID trước/sau"),
  ("Target healthy chưa?", "`describe-target-health`"),
  ("App và DB ổn chưa?", "`/health`, `/db`"),
  ("Backup plan/dashboard/alarm có đủ?", "`aws backup list-backup-plans`, `list-dashboards`, `describe-alarms`"),
 ],
 "`verify 22` PASS: instance mới, `/health`/`/db` 200, target healthy, backup plan/dashboard/alarms tồn tại.",
 [
  "Self-healing dựa vào health check + ASG, không phải reboot tay.",
  "Backup phải có restore test, không chỉ có plan.",
  "Production readiness: observability + HA + backup + runbook.",
 ],
 [
  "1. Instance cũ đi đâu?",
  "2. ASG biết app chết bằng gì?",
  "3. Backup plan đã được test restore chưa?",
 ],
 "",
),
"23": (
 "Final boss: 5 faults cùng lúc", "All domains", 240, "yes",
 "Bài cuối: 5 lỗi cùng lúc. Không có hint. Bạn phải ưu tiên user-facing path, rồi data, rồi quyền, và chứng minh từng lớp.",
 "App stack chạy. `break 23` inject: health check path sai, SG app chặn 8080, SG DB chặn 5432, IAM deny S3, CPU load.",
 """Client → ALB → Target Group (path sai)
                    ├── App SG chặn 8080
                    ├── DB SG chặn 5432
                    ├── IAM deny s3:GetObject
                    └── CPU load""",
 "Nhiều triệu chứng cùng lúc: 503, /db timeout, S3 AccessDenied, CPU cao. Bạn phải lập bảng symptom → layer → evidence.",
 [
  ("User-facing path có 200 không?", "`/health`"),
  ("Target có healthy không?", "Target health"),
  ("DB path có 200 không?", "`/db`"),
  ("Instance có đọc S3 không?", "SSM: `aws s3 ls s3://<bucket>`"),
  ("CPU còn cao không?", "CloudWatch CPU"),
 ],
 "`verify 23` PASS: path `/health`, SG app/DB allow, IAM không deny, `/db` 200, S3 OK, CPU < 60%, target healthy.",
 [
  "Triage: user-facing → data → identity → performance.",
  "Mỗi fix phải verify ngay, không gộp.",
  "Không có hint; dùng evidence và thứ tự lớp.",
 ],
 [
  "1. Triệu chứng nào ưu tiên nhất?",
  "2. Lỗi nào bị che?",
  "3. Bạn chứng minh từng lớp bằng gì?",
 ],
 "",
),
}

HEADER = """# Lab {id} — {title}

> **Chế độ người mới.** Đọc mục **0** và **5c** trước khi bấm. Không mở
> `scripts/lib/labs.sh` trong 20 phút đầu.
> Nếu bạn mới hoàn toàn: đọc [`docs/learner-quickstart.md`](../../docs/learner-quickstart.md).

| Thông tin | Giá trị |
|---|---|
| Domain | {domain} |
| Thời gian | ~{minutes} phút |
| Cần app stack | {app} |
| Chi phí | {cost} |
| Lab ID | `{id}` |

## 0. Đọc nhanh (60 giây)

- **Bạn sẽ làm gì:** {purpose}
- **Việc đầu tiên:** {first_step}
- **Xong khi:** {success}
- **Nếu lạc:** `./bin/lab console {id}` → mục 5c; AI sẽ chỉ từng màn hình, từng nút.

> Người mới: đọc bảng **Từ vựng nhanh** ở mục 5c trước khi bấm.
> Quy trình AI dạy từng nút: [`docs/ai-mentor-runbook.md`](../../docs/ai-mentor-runbook.md).

## 1. Lab này để làm gì?

{purpose}

## 2. Hiện tại có gì?

{state}

## 3. Kiến trúc

```text
{arch}
```

## 4. Trước khi bắt đầu

```bash
make doctor
make cost
```

{prereq}

- Đọc `labs/{id}-*/README.md` (file này) và dòng lab `{id}` trong `docs/exam-map.md`.
- Không mở `scripts/lib/labs.sh`.
- Nếu app stack đang chạy, giữ nguyên cho các lab tiếp theo; cuối buổi `make app-down`.

## 5. Các bước

{steps_block}

{special_block}
{console_block}
{brief_block}
## 6. Hiện tượng bạn sẽ thấy

{symptom}

## 7. Tự chẩn đoán: nhìn đâu?

| Câu hỏi | Nơi xem / lệnh |
|---|---|
{observe_table}

## 8. Thành công trông như thế nào?

{success}

Nếu FAIL, đọc:

```bash
cat labs/{id}-*/evidence/verify-last.txt
```

## 9. Exam takeaway

{exam_list}

## 10. Note mẫu

{note_list}

## 11. Cleanup

```bash
./bin/lab down {id}
make cost
```

Nếu hết buổi:

```bash
make app-down
make inventory
make cost
```

{cleanup_note}

## 12. Nếu bí

```bash
./bin/lab hint {id}
```

Hint tăng dần 1 → 2 → 3. `reset` chỉ dùng sau khi đã thử ít nhất 3 giả thuyết.

Prompt cho AI mentor:

```text
Tôi đang làm lab {id}. Đừng đưa đáp án.
Hãy giải thích khái niệm bằng ngôn ngữ người mới.
Khi hướng dẫn console, nói rõ: service → menu trái → trang → tab → nút,
tên tài nguyên cần tìm, ô cần đọc, và tôi sẽ thấy gì.
Rồi hỏi tôi 3 câu để tôi tự tìm root cause.
```

## Nguồn

- [SOA-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/sysops-administrator-associate-03.html)
- [In-scope services](https://docs.aws.amazon.com/aws-certification/latest/sysops-administrator-associate-03/soa-03-in-scope-services.md)
"""


def render(lid, data):
    (title, domain, minutes, needs_app, purpose, state, arch, symptom,
     observe, success, exam, note, special) = data
    app = "Có (`make app-up`)" if needs_app == "yes" else "Không"
    cost = "Trung bình" if lid in {"07", "08", "15", "16", "17", "18", "19", "22", "23"} else "Thấp"
    prereq = ("- Cần app stack. Nếu chưa có: `make app-up` (ALB + ASG + EC2 + RDS, ~$0.30/3h)."
              if needs_app == "yes" else
              "- Chỉ cần core stack; không cần app stack.")
    observe_table = "\n".join(f"| {q} | {w} |" for q, w in observe)
    exam_list = "\n".join(f"- {x}" for x in exam)
    note_list = "\n".join(f"- {x}" for x in note)
    clean = ("- Lab này có resource riêng; `down` sẽ dọn. Nếu đã dùng `reset`, ghi `SOLUTION_USED: yes` vào note."
             if special or needs_app == "yes" else
             "- Lab 00 không có resource riêng; core stack được giữ lại cho các lab sau.")
    special_block = f"## 5b. Ghi chú / lệnh riêng\n\n{special}\n" if special else ""
    console_block = render_console(lid, PREFIX, REGION)
    brief_block = render_brief(lid) if lid in BRIEFS else ""
    if lid == "00":
        steps_block = """1. Chuẩn bị baseline:

   ```bash
   ./bin/lab up 00
   ```

2. Lab 00 **không có fault**. Không cần break, không cần hint.

3. Verify baseline:

   ```bash
   ./bin/lab verify 00
   ```

4. Ghi note:

   ```bash
   ./bin/lab note 00
   ```

5. Không cần `down`; core stack được giữ cho các lab sau."""
    else:
        steps_block = f"""1. Chuẩn bị resource của lab:

   ```bash
   ./bin/lab up {lid}
   ```

2. Inject fault:

   ```bash
   ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break {lid}
   ```

3. **Tự chẩn đoán 20 phút.** Không hint, không AI, không answer key.
4. Hết 20 phút mới dùng:

   ```bash
   ./bin/lab hint {lid}
   ```

5. Sửa/quan sát, rồi verify:

   ```bash
   ./bin/lab verify {lid}
   ```

6. Ghi note:

   ```bash
   ./bin/lab note {lid}
   ```

7. Dọn resource của lab:

   ```bash
   ./bin/lab down {lid}
   ```"""
    return HEADER.format(
        id=lid, title=title, domain=domain, minutes=minutes, app=app, cost=cost,
        purpose=purpose, state=state, arch=arch, prereq=prereq,
        first_step=first_step(lid),
        special_block=special_block, console_block=console_block, brief_block=brief_block, steps_block=steps_block,
        symptom=symptom, observe_table=observe_table, success=success,
        exam_list=exam_list, note_list=note_list, cleanup_note=clean,
    )


def main():
    check = "--check" in sys.argv[1:]
    stale = 0
    for lid, data in L.items():
        matches = list(LABS.glob(f"{lid}-*"))
        if not matches:
            print("missing dir", lid)
            continue
        path = matches[0] / "README.md"
        text = render(lid, data).strip() + "\n"
        if check:
            if not path.exists() or path.read_text() != text:
                print(f"STALE {path.relative_to(ROOT)} (run tools/gen_lab_docs.py)")
                stale += 1
            continue
        path.write_text(text)

    glossary_path = DOCS / "glossary.md"
    glossary = glossary_markdown()
    if DOCS.is_dir():
        if check:
            if not glossary_path.exists() or glossary_path.read_text() != glossary:
                print("STALE docs/glossary.md (run tools/gen_lab_docs.py)")
                stale += 1
        else:
            glossary_path.write_text(glossary)
    if check:
        print(f"{len(L)} lab READMEs + glossary: {'STALE' if stale else 'up to date'}")
        return 1 if stale else 0
    print(f"wrote {len(L)} lab READMEs + docs/glossary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
