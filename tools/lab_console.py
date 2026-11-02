#!/usr/bin/env python3
"""Console guidance for each lab.

This is the source of truth for the "Console — bấm ở đâu, thấy gì" section in
every lab README. Keep it boring and exact: service -> left nav -> page -> tab
-> button, plus the resource name the learner must search for.

Rules for editing:
- Never invent a resource name. Every `soa-c03-...` token here must also exist
  in scripts/lib/labs.sh or platform/*.yaml (tools/check_labs.py enforces it).
- Prefer list pages + a search term over detail URLs that need a resource ID
  that only exists at runtime.
- Deep links are shortcuts. The numbered click path is the source of truth
  because AWS changes console URLs more often than menu labels.
- Do not state the root cause. Point at the screen and let the learner read it.
"""
from __future__ import annotations

import re

# Console labels are English on purpose: the AWS console is English even when
# the learner's language is Vietnamese.


def _cw(fragment: str = "") -> str:
    return "https://console.aws.amazon.com/cloudwatch/home?region={region}" + fragment


def _ec2(fragment: str = "") -> str:
    return "https://console.aws.amazon.com/ec2/home?region={region}" + fragment


CONSOLE: dict[str, dict] = {
    "00": {
        "concepts": (
            "**Baseline** là trạng thái nền phải đúng trước khi phá bất cứ thứ gì: "
            "audit log đang ghi, bucket không public, khoá mã hoá bật, tham số cấu hình tồn tại, "
            "và có cảnh báo chi phí. Nếu nền sai, mọi lab sau sẽ cho kết quả sai."
        ),
        "terms": [
            ("Core stack", "Nền nhà dùng chung: VPC, S3, KMS, CloudTrail, SNS, IAM, SSM."),
            ("CloudTrail", "Camera ghi lại ai đã gọi API nào, lúc nào."),
            ("Block Public Access", "Công tắc khoá cửa bucket S3, chặn truy cập nặc danh."),
            ("KMS alias", "Tên dễ nhớ trỏ tới một khoá mã hoá, ví dụ `alias/soa-c03-lab`."),
            ("Parameter Store", "Ngăn kéo lưu cấu hình dạng key/value."),
            ("Budget", "Chuông báo chi phí, không phải công tắc chặn chi phí."),
        ],
        "path": """1. Mở ô **Search** trên cùng, gõ `CloudFormation`, chọn **CloudFormation**.
2. Menu trái → **Stacks** → bấm stack `soa-c03-core`.
3. Tab **Outputs**: ghi lại `DataBucketName`, `KmsKeyId`, `AlertTopicArn`, `AppLogGroupName`.
4. Ô **Search** → `CloudTrail` → **Dashboard**. Thẻ **Logging status** phải hiện trail `soa-c03-trail` đang **Logging**.
5. Ô **Search** → `S3` → **Buckets** → bấm bucket vừa ghi ở bước 3 → tab **Permissions**.
6. Mục **Block public access (bucket settings)** → **Edit**: cả 4 dòng phải đang **On**.
7. Ô **Search** → `KMS` → **Customer managed keys** → bấm alias `alias/soa-c03-lab` → xem **Key state** = **Enabled**.
8. Ô **Search** → `Systems Manager` → menu trái **Parameter Store** → tìm `/soa-c03/app/port`.
9. Ô **Search** → `Billing and Cost Management` → **Budgets** → bấm `soa-c03-monthly`.""",
        "read": [
            ("Stack status", "Phải là `CREATE_COMPLETE` hoặc `UPDATE_COMPLETE`."),
            ("Outputs", "Đây là tên thật của bucket, key, topic, log group mà lab sau dùng."),
            ("Logging status", "`On` nghĩa là CloudTrail đang ghi; `Off` nghĩa là không có bằng chứng forensic."),
            ("4 cờ Block Public Access", "Thiếu một cờ là bucket vẫn có thể lộ."),
            ("Key state", "`Enabled` mới dùng được; `Pending deletion` là sắp mất."),
            ("Budget alerts", "Cho biết ngưỡng và email nhận cảnh báo."),
        ],
        "links": [
            ("CloudFormation stack `soa-c03-core`", "https://console.aws.amazon.com/cloudformation/home?region={region}#/stacks"),
            ("CloudTrail dashboard", "https://console.aws.amazon.com/cloudtrail/home?region={region}#/dashboard"),
            ("S3 buckets", "https://console.aws.amazon.com/s3/buckets?region={region}"),
            ("KMS keys", "https://console.aws.amazon.com/kms/home?region={region}#/kms/keys"),
            ("SSM Parameter Store", "https://console.aws.amazon.com/systems-manager/parameters/?region={region}"),
            ("AWS Budgets", "https://console.aws.amazon.com/billing/home?region={region}#/budgets"),
        ],
        "fallback": """- Trang trắng hoặc “no resources”: kiểm tra region ở góc trên phải là **Singapore (ap-southeast-1)**.
- “Access denied”: tài khoản đang dùng thiếu quyền đọc service đó; quay lại CLI `make doctor` để xem lỗi thật.
- Không thấy stack `soa-c03-core`: chưa chạy `make bootstrap`; **hỏi trước khi chạy** vì nó tạo tài nguyên (~$1–2/tháng).""",
    },
    "01": {
        "concepts": (
            "CloudWatch lưu **metric** (con số theo thời gian). Mỗi metric có namespace, tên, "
            "dimension (ví dụ `InstanceId`) và được gộp theo **period**. **Alarm** chỉ là một quy tắc "
            "đọc metric đó: lấy statistic nào, trong bao nhiêu period, vượt ngưỡng bao nhiêu lần thì đổi trạng thái."
        ),
        "terms": [
            ("Metric", "Đồng hồ đo, ví dụ CPUUtilization."),
            ("Namespace", "Ngăn tủ chứa metric, ví dụ `AWS/EC2`."),
            ("Dimension", "Nhãn để chỉ đúng đối tượng, ví dụ `InstanceId=i-...`."),
            ("Period", "Mỗi bao lâu lấy một điểm, ví dụ 60 giây."),
            ("Statistic", "Cách gộp các điểm trong period: Average, Maximum, Sum..."),
            ("Evaluation periods", "Cần bao nhiêu period liên tiếp vượt ngưỡng mới đổi trạng thái."),
            ("INSUFFICIENT_DATA", "Chưa đủ dữ liệu để kết luận, không phải lỗi."),
        ],
        "path": """1. Ô **Search** → `CloudWatch` → menu trái **Metrics** → **All metrics**.
2. Chọn namespace **EC2** → **Per-Instance Metrics**.
3. Ở ô search của bảng metric, dán instance ID. Lấy ID bằng `./bin/lab status` (dòng `ec2  : i-...`).
4. Tick metric **CPUUtilization**.
5. Phía trên biểu đồ: chọn **Average** và **Maximum**; time range **1h**; nếu có, period **1 minute**.
6. Menu trái → **Alarms** → **All alarms** → bấm `soa-c03-lab01-cpu-high`.
7. Tab **Details**: đọc **State**, **Threshold**, **Period**, **Evaluation periods**, **Statistic**.
8. Tab **History**: tìm dòng `OK -> ALARM` và giờ chuyển.
9. Ô **Search** → `SQS` → **Queues** → `soa-c03-lab01-events` → **Send and receive messages** → **Poll for messages**.""",
        "read": [
            ("CPUUtilization Average vs Maximum", "Average thấp mà Maximum cao nghĩa là chỉ một lúc bị đẩy lên; alarm dùng Average sẽ chậm hơn."),
            ("Alarm State", "`OK`, `ALARM`, hoặc `INSUFFICIENT_DATA`."),
            ("Threshold + comparison", "Ví dụ `> 50` nghĩa là vượt 50% mới tính."),
            ("Period × Evaluation periods", "Thời gian tối thiểu trước khi alarm có thể đổi trạng thái."),
            ("History", "Bằng chứng alarm đã từng kêu, kể cả khi giờ đã về `OK`."),
            ("SQS message body", "Thông báo thật đã đi qua SNS tới queue hay chưa."),
        ],
        "links": [
            ("CloudWatch metrics", _cw("#metricsV2:")),
            ("Alarm `soa-c03-lab01-cpu-high`", _cw("#alarmsV2:alarm/{prefix}-lab01-cpu-high")),
            ("All alarms", _cw("#alarmsV2:alarms")),
            ("SQS queues", "https://console.aws.amazon.com/sqs/v3/home?region={region}#/queues"),
            ("SNS topics", "https://console.aws.amazon.com/sns/v3/home?region={region}#/topics"),
        ],
        "fallback": """- Không thấy metric EC2: instance mới tạo có thể chưa có datapoint; đợi 2–5 phút, hoặc kiểm tra detailed monitoring.
- Không thấy alarm: `./bin/lab up 01` chưa chạy hoặc đã `down`.
- Queue trống: alarm chưa từng vào `ALARM`, hoặc subscription SNS→SQS sai; xem tab **History** trước.
- Đừng kết luận “alarm hỏng” chỉ vì state đang `OK`; alarm có thể đã kêu rồi tự về `OK`.""",
    },
    "02": {
        "concepts": (
            "**Log group** là thư mục, **log stream** là một dãy sự kiện từ một nguồn (ví dụ một file). "
            "**Metric filter** biến một dòng khớp pattern thành datapoint; nó chỉ chạy trên log đến **sau** khi filter được tạo. "
            "**Logs Insights** là nơi query nhiều stream cùng lúc, khác với bấm đọc từng dòng."
        ),
        "terms": [
            ("Log group", "Thư mục log, ví dụ `/aws/cloudops/soa-c03/app`."),
            ("Log stream", "Một dãy log từ một nguồn, thường là một file trên một instance."),
            ("Metric filter", "Bộ lọc biến dòng log khớp pattern thành metric."),
            ("Logs Insights", "Ngôn ngữ query log có `fields`, `filter`, `stats`, `sort`."),
            ("Retention", "Bao lâu thì log tự bị xoá."),
            ("Ingestion delay", "Độ trễ từ lúc app ghi log đến lúc CloudWatch thấy."),
        ],
        "path": """1. Ô **Search** → `CloudWatch` → menu trái **Log groups**.
2. Bấm log group `/aws/cloudops/soa-c03/app`.
3. Tab **Log streams**: bấm stream mới nhất (tên thường có ngày/instance).
4. Trong stream, bấm một event để mở JSON: đọc `timestamp`, `level`, `msg`.
5. Menu trái → **Logs Insights**. Ở dropdown log group, chọn `/aws/cloudops/soa-c03/app`.
6. Dán query đếm lỗi rồi bấm **Run query**:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | stats count() as errors
   ```
7. Đổi query để xem dòng mới nhất:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | sort @timestamp desc
   | limit 50
   ```
8. Menu trái → **Metrics** → **All metrics** → namespace **CloudOpsLab** → **ErrorCount**.
9. Menu trái → **Alarms** → `soa-c03-lab02-errors` → tab **Details** + **History**.
10. Quay lại log group → tab **Metric filters** → bấm `soa-c03-lab02-errors` để xem pattern.""",
        "read": [
            ("Event JSON", "`level` có đúng `ERROR` không; `msg` nói lỗi gì."),
            ("Logs Insights result", "`errors` là tổng số dòng khớp trong time range đang chọn."),
            ("Time range", "Mặc định có thể là 1h; nếu vừa break xong, chọn **1h** hoặc **3h**."),
            ("ErrorCount datapoints", "Metric filter chỉ tạo datapoint khi có log khớp pattern."),
            ("Alarm History", "Bằng chứng `OK -> ALARM`, kể cả khi state đã về `OK`."),
            ("Metric filter pattern", "Pattern JSON `{ $.level = \"ERROR\" }` chỉ khớp log JSON có field `level`."),
        ],
        "links": [
            ("Log group `/aws/cloudops/soa-c03/app`", _cw("#logsV2:log-groups/log-group/%2Faws%2Fcloudops%2Fsoa-c03%2Fapp")),
            ("Logs Insights", _cw("#logsV2:logs-insights")),
            ("Metric `CloudOpsLab/ErrorCount`", _cw("#metricsV2:")),
            ("Alarm `soa-c03-lab02-errors`", _cw("#alarmsV2:alarm/{prefix}-lab02-errors")),
        ],
        "fallback": """- Không thấy log group: CloudWatch Agent chưa chạy hoặc instance mới chưa gửi log; xem `/var/log/amazon/amazon-cloudwatch-agent/amazon-cloudwatch-agent.log` qua SSM.
- Có log nhưng query 0 dòng: time range sai, hoặc field không phải `level`; bấm một event để xem tên field thật.
- Metric có graph nhưng alarm `OK`: kiểm tra threshold, period, và thời điểm filter được tạo (filter không tính log cũ).
- Log lên chậm 30–90 giây là bình thường.""",
    },
    "03": {
        "concepts": (
            "**CloudTrail** trả lời “ai gọi API gì, từ đâu” và giữ event 90 ngày. "
            "**EventBridge** là bus sự kiện gần thời gian thực: rule khớp `source`, `detail-type`, `detail` rồi đẩy tới target. "
            "Hai thứ bổ sung nhau: CloudTrail để điều tra, EventBridge để tự động phản ứng."
        ),
        "terms": [
            ("Management event", "Sự kiện gọi API quản trị, ví dụ TerminateInstances."),
            ("Event history", "Danh sách event CloudTrail, chỉ giữ 90 ngày."),
            ("Event pattern", "Bộ điều kiện JSON để EventBridge chọn event."),
            ("Event bus", "Đường ống sự kiện; mặc định là `default`."),
            ("AssumeRole session", "Danh tính tạm thời khi một role gọi API."),
        ],
        "path": """1. Ô **Search** → `CloudTrail` → menu trái **Event history**.
2. Bộ lọc **Event name** = `TerminateInstances`; time range **1h** (hoặc **3h**).
3. Bấm event mới nhất → mở **Event record** (JSON).
4. Đọc `userIdentity.type`, `userIdentity.arn`, `userIdentity.sessionContext`, `eventTime`, `sourceIPAddress`, `userAgent`, `requestParameters`.
5. Ô **Search** → `EventBridge` → menu trái **Rules** → bấm `soa-c03-lab03-ec2-state`.
6. Tab **Event pattern**: xem `source`, `detail-type`, `detail.state`.
7. Tab **Targets**: phải có SQS `soa-c03-lab03-events`.
8. Tab **Monitoring**: xem **Invocations** và **Failed invocations** trong 1h.
9. Ô **Search** → `SQS` → `soa-c03-lab03-events` → **Send and receive messages** → **Poll for messages**.
10. Ô **Search** → `EC2` → **Instances** → search `soa-c03-lab03-canary` → xem **Instance state**.""",
        "read": [
            ("userIdentity.type", "`AssumedRole` nghĩa là một role, không phải user gốc."),
            ("userIdentity.arn", "Role nào và session nào đã gọi."),
            ("sourceIPAddress", "Gọi từ IP nào; có thể là IP của AWS service nếu là event do service tạo."),
            ("requestParameters", "Instance ID nào bị terminate."),
            ("Rule Invocations", "0 nghĩa là event không khớp pattern hoặc rule bị disable."),
            ("SQS message", "Payload thật EventBridge gửi, gồm `detail.instance-id` và `state`."),
        ],
        "links": [
            ("CloudTrail event history", "https://console.aws.amazon.com/cloudtrail/home?region={region}#/events"),
            ("EventBridge rule `soa-c03-lab03-ec2-state`", "https://console.aws.amazon.com/events/home?region={region}#/eventbus/default/rules/{prefix}-lab03-ec2-state"),
            ("SQS queues", "https://console.aws.amazon.com/sqs/v3/home?region={region}#/queues"),
            ("EC2 instances", _ec2("#Instances:")),
        ],
        "fallback": """- CloudTrail chưa có event: có thể trễ vài phút; mở rộng time range lên **3h**.
- Event history chỉ có management events; nếu lab dùng data event thì phải xem trail/log khác.
- Rule không invocation: bấm **Event pattern** so khớp chính xác `detail-type` và `detail.state`.
- SQS trống: rule đã gửi nhưng target sai ARN, hoặc policy queue thiếu quyền `events.amazonaws.com`.""",
    },
    "04": {
        "concepts": (
            "Đây là một **chuỗi**: app trả 500 → log ghi ERROR → metric filter đếm → alarm đổi trạng thái → "
            "EventBridge bắt **alarm state change** → SQS nhận message. Mỗi mắt xích có thể đúng riêng lẻ nhưng chuỗi vẫn đứt."
        ),
        "terms": [
            ("5xx", "Nhóm HTTP status 500–599, lỗi phía server/ALB."),
            ("Metric filter", "Biến dòng log ERROR thành metric `CapstoneErrorCount`."),
            ("Alarm state change", "Sự kiện riêng của CloudWatch khi alarm đổi trạng thái."),
            ("EventBridge rule", "Bộ lọc bắt sự kiện alarm rồi đẩy tới SQS."),
            ("DLQ", "Queue nhận message không xử lý được; lab này chưa dùng."),
        ],
        "path": """1. Terminal: `curl -i http://<alb-dns>/error` (lấy DNS bằng `./bin/lab status`). Đọc dòng status.
2. CloudWatch → **Log groups** → `/aws/cloudops/soa-c03/app` → **Logs Insights**.
3. Query:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | stats count() as errors
   ```
4. CloudWatch → **Metrics** → **All metrics** → **CloudOpsLab** → `CapstoneErrorCount`.
5. **Alarms** → `soa-c03-lab04-errors` → **Details** + **History**.
6. **EventBridge** → **Rules** → `soa-c03-lab04-alarm` → **Event pattern**, **Targets**, **Monitoring**.
7. **SQS** → `soa-c03-lab04-events` → **Send and receive messages** → **Poll for messages**.""",
        "read": [
            ("HTTP status từ `/error`", "Phải là 500 để có log ERROR."),
            ("Số ERROR trong Insights", "Nếu 0, chuỗi đứt ngay từ log."),
            ("Metric `CapstoneErrorCount`", "Nếu log có mà metric 0, filter/pattern sai."),
            ("Alarm History", "Nếu metric có mà alarm không đổi, threshold/period sai."),
            ("Rule Monitoring", "Nếu alarm đổi mà invocation 0, event pattern sai."),
            ("SQS message", "Nếu invocation có mà queue trống, target/policy sai."),
        ],
        "links": [
            ("CloudWatch alarms", _cw("#alarmsV2:alarms")),
            ("Logs Insights", _cw("#logsV2:logs-insights")),
            ("EventBridge rules", "https://console.aws.amazon.com/events/home?region={region}#/eventbus/default/rules"),
            ("SQS queues", "https://console.aws.amazon.com/sqs/v3/home?region={region}#/queues"),
        ],
        "fallback": """- Alarm đã ở `ALARM` trước khi rule được tạo thì không có **state change** mới; đợi nó về `OK` rồi lên `ALARM` lại, hoặc xem History.
- Rule chỉ bắt `state.value = ALARM`; đổi sang `OK` không khớp.
- Nếu SQS trống, thử **Poll for messages** lần nữa với thời gian chờ dài hơn.""",
    },
    "05": {
        "concepts": (
            "**ALB** nhận request, **listener** quyết định chuyển tới **target group** nào. "
            "Target group chỉ chuyển traffic tới target đang **healthy**. Health check là request định kỳ của ALB vào target; "
            "sai path/port/protocol thì target bị đánh `unhealthy` và ALB trả 503 dù app vẫn sống."
        ),
        "terms": [
            ("Listener", "Cửa của ALB, ví dụ HTTP:80."),
            ("Target group", "Danh sách instance/container nhận traffic."),
            ("Health check", "Lễ tân gọi vào phòng xem app còn trả lời."),
            ("Healthy / Unhealthy", "Target có vượt qua health check hay không."),
            ("503", "ALB không có target khoẻ để chuyển request."),
            ("502 / 504", "Target trả lỗi / target trả lời quá chậm."),
        ],
        "path": """1. Ô **Search** → `EC2` → menu trái **Load Balancers** → bấm `soa-c03-alb`.
2. Tab **Listeners**: bấm listener HTTP:80 → xem **Default action** trỏ tới target group nào.
3. Menu trái **Target groups** → bấm `soa-c03-tg`.
4. Tab **Targets**: đọc cột **Health status** và **Health status details**.
5. Tab **Health checks** → **Edit**: đọc path, port, protocol, interval, timeout, healthy/unhealthy threshold.
6. Terminal: `curl -i http://<alb-dns>/health`; so sánh status code.
7. Ô **Search** → `EC2` → **Instances** → bấm instance đang chạy → tab **Security** → xem security group.
8. Mở security group của app → **Inbound rules**: phải có TCP 8080 từ SG của ALB.""",
        "read": [
            ("Target Health status", "`healthy`, `unhealthy`, `initial`, `draining`, `unused`."),
            ("Health status details", "Ví dụ `Target.FailedHealthChecks`, `Target.Timeout`, `Target.ResponseCodeMismatch`."),
            ("Health check path/port", "Phải trùng route và port app thật sự nghe."),
            ("Matcher", "Mặc định chỉ chấp nhận HTTP 200."),
            ("ALB response code", "503 = không có target khoẻ; 502 = target trả lỗi."),
            ("SG inbound 8080", "Thiếu rule này thì health check không bao giờ tới app."),
        ],
        "links": [
            ("Load balancers", _ec2("#LoadBalancers:")),
            ("Target groups", _ec2("#TargetGroups:")),
            ("Instances", _ec2("#Instances:")),
            ("Security groups", _ec2("#SecurityGroups:")),
        ],
        "fallback": """- Target group không có target: ASG chưa đăng ký instance; xem **ASG → Activity**.
- Target `unhealthy` nhưng app `/health` vẫn 200 từ ngoài: health check có thể dùng port/path khác, hoặc SG chỉ mở cho IP của bạn.
- Sửa xong phải đợi ít nhất `healthy threshold × interval` trước khi thấy healthy.""",
    },
    "06": {
        "concepts": (
            "**Launch template** là bản thiết kế máy; **version** là từng bản sửa. ASG có thể dùng một version cụ thể hoặc `$Latest`. "
            "Mỗi lần ASG muốn thêm máy, nó gọi template; nếu template hỏng (user-data lỗi), máy có thể vẫn `running` nhưng app không chạy, "
            "và **scaling activity** ghi lại lý do."
        ),
        "terms": [
            ("Launch template", "Bản thiết kế EC2: AMI, instance type, user-data, SG."),
            ("Version", "Một bản snapshot của template; `$Latest` là bản mới nhất."),
            ("Desired capacity", "Số instance ASG muốn có."),
            ("Scaling activity", "Nhật ký ASG thử thêm/bớt máy và kết quả."),
            ("Health check type", "ASG kiểm tra EC2 hay kiểm tra qua ELB."),
            ("Cooldown", "Thời gian ASG chờ trước khi scale tiếp."),
        ],
        "path": """1. Ô **Search** → `EC2` → **Auto Scaling Groups** → bấm `soa-c03-asg`.
2. Tab **Details**: đọc **Desired capacity**, **Min/Max**, **Launch template** (tên + version).
3. Tab **Activity**: đọc các dòng mới nhất, cột **Status** và **Status message**.
4. Tab **Instance management**: xem instance nào đang InService.
5. Menu trái **Launch templates** → bấm `soa-c03-app` → tab **Versions**.
6. Bấm version mới nhất → tab **Launch template contents** → mở **User data** và so với version gốc.
7. Menu trái **Instances** → search instance mới → tab **Status checks**, **Monitoring**, **Tags**.
8. Target group `soa-c03-tg` → **Targets** → xem instance mới có healthy không.""",
        "read": [
            ("Desired capacity", "2 nghĩa là ASG đang cố tạo thêm một máy."),
            ("Launch template version", "Nếu là `$Latest` hoặc version mới, đó là bản đang được dùng."),
            ("Scaling activity Status", "`Failed`, `Successful`, `InProgress`."),
            ("Status message", "Nói lý do: hết capacity, user-data lỗi, không qua health check..."),
            ("Instance status checks", "`2/2 checks passed` mới là máy khoẻ."),
            ("User data", "Script chạy lần đầu; lỗi ở đây làm app không start."),
        ],
        "links": [
            ("Auto Scaling groups", _ec2("#AutoScalingGroups:")),
            ("Launch templates", _ec2("#LaunchTemplates:")),
            ("Instances", _ec2("#Instances:")),
            ("Target groups", _ec2("#TargetGroups:")),
        ],
        "fallback": """- Activity trống: ASG chưa thực sự scale; kiểm tra **Desired** và suspended processes.
- Instance mới `running` nhưng target `unhealthy`: đọc user-data và `/var/log/cloudops-bootstrap.log` qua SSM.
- Đừng sửa template gốc; tạo version mới rồi trỏ ASG về version đúng.""",
    },
    "07": {
        "concepts": (
            "**Snapshot** là ảnh chụp storage tại một thời điểm. **Restore** luôn tạo một DB **mới** từ snapshot, "
            "không ghi đè DB đang chạy. DB mới phải nằm trong subnet group và security group đúng thì app mới kết nối được."
        ),
        "terms": [
            ("Snapshot", "Ảnh chụp dữ liệu tại một thời điểm."),
            ("Restore", "Tạo DB mới từ snapshot."),
            ("DB subnet group", "Tập subnet mà RDS được phép đặt DB."),
            ("Endpoint", "Địa chỉ DNS + port để kết nối DB."),
            ("RPO", "Mất tối đa bao nhiêu dữ liệu tính từ lần backup gần nhất."),
            ("RTO", "Mất bao lâu để dịch vụ chạy lại."),
        ],
        "path": """1. Ô **Search** → `RDS` → menu trái **Snapshots** → tab **Manual**.
2. Bấm snapshot `soa-c03-lab07-snapshot`; xem **Status**, **Snapshot creation time**, **Engine**.
3. **Actions** → **Restore snapshot**.
4. Trang restore: **DB instance identifier** = `soa-c03-lab07-restored`; **DB instance class** = `db.t4g.micro`.
5. Mục **Connectivity**: chọn đúng **VPC**, **DB subnet group** và **Existing VPC security groups** của DB gốc.
6. **Public access** = **No** → bấm **Restore DB instance**.
7. Menu trái **Databases** → bấm `soa-c03-lab07-restored` → chờ **Status = Available**.
8. Tab **Connectivity & security**: ghi **Endpoint** và **Port**.
9. Từ app instance qua SSM, chạy `psql` và `SELECT count(*) FROM lab07;` (lệnh mẫu ở mục 5b của README).""",
        "read": [
            ("Snapshot Status", "`available` mới restore được."),
            ("Snapshot time", "Dữ liệu trong snapshot dừng ở thời điểm này."),
            ("DB Status", "`creating` → `backing-up` → `available`."),
            ("Subnet group", "Sai subnet group có thể đặt DB ra subnet không kết nối được."),
            ("Security group", "Phải cho app SG vào port 5432."),
            ("Row count", "`5` chứng minh dữ liệu đã quay lại, không chỉ DB bật."),
        ],
        "links": [
            ("RDS snapshots", "https://console.aws.amazon.com/rds/home?region={region}#snapshots:"),
            ("RDS databases", "https://console.aws.amazon.com/rds/home?region={region}#databases:"),
        ],
        "fallback": """- Không thấy snapshot: `./bin/lab up 07` chưa xong; snapshot RDS có thể mất vài phút.
- Restore báo lỗi subnet/SG: copy đúng giá trị từ DB gốc (tab **Configuration** / **Connectivity & security**).
- DB `available` nhưng `psql` timeout: kiểm tra SG 5432, subnet route, và endpoint có đúng DB mới không.
- Đừng restore đè lên DB gốc; RDS không cho làm vậy.""",
    },
    "08": {
        "concepts": (
            "**Multi-AZ** tạo một standby đồng bộ ở AZ khác. Khi failover, DNS endpoint **không đổi**; "
            "RDS chuyển vai primary/standby. Vì vậy app phải reconnect, và bạn đo **RTO** bằng thời gian từ lúc reboot đến khi `/db` trả 200."
        ),
        "terms": [
            ("Multi-AZ", "Một primary + một standby đồng bộ ở AZ khác."),
            ("Failover", "Chuyển vai primary sang standby."),
            ("Endpoint", "DNS name giữ nguyên qua failover."),
            ("RTO", "Thời gian downtime thực tế."),
            ("Read replica", "Bản sao chỉ đọc, khác Multi-AZ."),
        ],
        "path": """1. Ô **Search** → `RDS` → **Databases** → bấm `soa-c03-db`.
2. Tab **Configuration**: mục **Availability and durability** → **Multi-AZ** phải là **Yes**; xem **Primary AZ**.
3. Tab **Monitoring**: xem CPU, connections, read/write latency trong 1h.
4. Menu trái **Events** (hoặc tab **Events** của DB): lọc theo DB instance, tìm event failover.
5. Để đo RTO: mở terminal chạy `while true; do curl -s -o /dev/null -w '%{http_code} %{time_total}\n' http://<alb>/db; sleep 2; done`.
6. Quay lại DB → **Actions** → **Reboot** → tick **Reboot with failover?** (nếu có) → confirm.
7. Đọc chuỗi status code cho tới khi `200` trở lại.""",
        "read": [
            ("Multi-AZ", "`Yes` nghĩa là có standby."),
            ("Primary AZ / Secondary AZ", "Hai AZ khác nhau chứng minh HA thật."),
            ("DB status", "`rebooting` → `available`."),
            ("RDS event", "Câu chữ chứa `failover` và thời điểm."),
            ("Chuỗi HTTP code", "Các dòng 000/502/503 xen giữa là downtime."),
            ("Thời gian tới 200", "Đó là RTO bạn đo được, không phải con số lý thuyết."),
        ],
        "links": [
            ("RDS databases", "https://console.aws.amazon.com/rds/home?region={region}#databases:"),
            ("RDS events", "https://console.aws.amazon.com/rds/home?region={region}#events:"),
        ],
        "fallback": """- Multi-AZ vẫn `No`: `up 08` có thể chưa chạy xong; modification có thể mất 10–12 phút.
- Không thấy event failover: mở rộng time range; event có thể trễ vài phút.
- `/db` vẫn lỗi sau failover: kiểm tra SG/subnet và app có tự reconnect không.
- Nhớ `./bin/lab down 08` để trả về single-AZ, tránh tốn gấp đôi.""",
    },
    "09": {
        "concepts": (
            "**SSM Agent** là con bot chạy trên EC2, kết nối ra ngoài tới Systems Manager. "
            "**Run Command** chạy lệnh hàng loạt không cần SSH; **Session Manager** mở shell tương tác; "
            "**Parameter Store** lưu cấu hình. Cả ba cần IAM role đúng và đường mạng ra endpoint SSM."
        ),
        "terms": [
            ("SSM Agent", "Bot trên EC2 nói chuyện với Systems Manager."),
            ("Fleet Manager", "Màn hình quản lý instance và trạng thái agent."),
            ("Run Command", "Chạy script trên nhiều instance, có lịch sử output."),
            ("Session Manager", "Shell từ xa không cần SSH hay public IP."),
            ("Parameter Store", "Kho key/value cho cấu hình."),
            ("Instance profile", "Thẻ IAM gắn vào EC2."),
        ],
        "path": """1. Ô **Search** → `Systems Manager` → menu trái **Fleet Manager**.
2. Tìm instance đang chạy (lấy ID bằng `./bin/lab status`); cột **Ping status** phải là **Online**.
3. Menu trái **Run Command** → **Run a command**.
4. Command document: `AWS-RunShellScript`; **Command parameters**: `commands` = `systemctl is-active cloudops-app`.
5. **Targets** → **Choose instances manually** → tick instance → **Run**.
6. Ở **Command history**, bấm command vừa chạy → đọc **Output** và **Status**.
7. Menu trái **Session Manager** → **Start session** → chọn instance → mở terminal.
8. Menu trái **Parameter Store** → search `/soa-c03/lab09/message` → bấm để xem **Value**.""",
        "read": [
            ("Ping status", "`Online` mới điều khiển được; `ConnectionLost` là agent/mạng/role."),
            ("Command Status", "`Success`, `Failed`, `TimedOut`."),
            ("Command output", "Kết quả thật của lệnh, không phải suy đoán."),
            ("Parameter value", "Phải khớp giá trị lab tạo."),
            ("Session", "Nếu mở được shell, chứng minh agent + role + endpoint đều đúng."),
            ("App service", "`active` và `/health` 200 là tiêu chí cuối."),
        ],
        "links": [
            ("Fleet Manager", "https://console.aws.amazon.com/systems-manager/managed-instances?region={region}"),
            ("Run Command", "https://console.aws.amazon.com/systems-manager/run-command/execute-command?region={region}"),
            ("Session Manager", "https://console.aws.amazon.com/systems-manager/session-manager/start-session?region={region}"),
            ("Parameter Store", "https://console.aws.amazon.com/systems-manager/parameters/?region={region}"),
        ],
        "fallback": """- Instance không xuất hiện trong Fleet Manager: agent chưa chạy, instance profile thiếu quyền, hoặc không có đường ra `ssm.ap-southeast-1.amazonaws.com`.
- Run Command `Failed`: bấm command → **Output** đọc stderr; đừng đoán.
- Session Manager báo lỗi: kiểm tra IAM role có `ssm:StartSession` và instance có agent mới.
- Private subnet không NAT cần interface endpoint cho `ssm`, `ssmmessages`, `ec2messages`.""",
    },
    "10": {
        "concepts": (
            "Object S3 mã hoá **SSE-KMS** cần **hai** lần cho phép: quyền `s3:GetObject` trên object **và** quyền `kms:Decrypt` trên key. "
            "**Key policy** là resource policy của key; **explicit deny** trong key policy hoặc IAM thắng mọi allow. "
            "Secrets Manager cũng dùng KMS key riêng."
        ),
        "terms": [
            ("SSE-KMS", "S3 mã hoá object bằng một key KMS."),
            ("Key policy", "Ai được dùng key, gắn trực tiếp vào key."),
            ("IAM policy", "Role/user được phép gọi action nào."),
            ("Explicit deny", "Câu `Deny` luôn thắng `Allow`."),
            ("AssumeRole", "Mượn danh tính tạm thời của một role."),
        ],
        "path": """1. Ô **Search** → `Secrets Manager` → **Secrets** → bấm `/soa-c03/lab10/api-key`.
2. Tab **Overview**: xem **Secret ARN**, **Encryption key**, **Last retrieved**.
3. Ô **Search** → `KMS` → **Customer managed keys** → bấm alias `alias/soa-c03-lab`.
4. Tab **Key policy**: bấm **Switch to policy view** (nếu đang ở dạng editor) → tìm các `Sid` có `Lab10Reader` / `Lab10Deny`.
5. Tab **Key overview**: **Key state** phải **Enabled**; xem **Key ARN**.
6. Ô **Search** → `IAM` → **Roles** → `soa-c03-lab10-reader` → tab **Permissions** → bấm policy `lab10-read`.
7. Ô **Search** → `S3` → bucket core (Outputs) → thư mục `lab10/` → bấm `secret.txt` → tab **Properties** → **Server-side encryption**.
8. Ô **Search** → `CloudTrail` → **Event history** → filter **Event name** = `Decrypt` hoặc `GetSecretValue` → xem `errorCode`.""",
        "read": [
            ("Encryption key", "Object/secret đang dùng key nào; phải là key bạn đang sửa policy."),
            ("Key policy statements", "Có `Allow` cho role reader và có `Deny` chen vào không."),
            ("IAM policy actions", "Có `s3:GetObject` và `secretsmanager:GetSecretValue` chưa."),
            ("Object encryption", "`AWS KMS` + key ARN, không phải `SSE-S3`."),
            ("CloudTrail errorCode", "`AccessDenied` kèm message nói thiếu quyền gì."),
            ("Key state", "Key bị disable/delete thì mọi thứ fail."),
        ],
        "links": [
            ("Secrets Manager", "https://console.aws.amazon.com/secretsmanager/landing?region={region}"),
            ("KMS keys", "https://console.aws.amazon.com/kms/home?region={region}#/kms/keys"),
            ("IAM roles", "https://console.aws.amazon.com/iam/home#/roles"),
            ("S3 buckets", "https://console.aws.amazon.com/s3/buckets?region={region}"),
            ("CloudTrail events", "https://console.aws.amazon.com/cloudtrail/home?region={region}#/events"),
        ],
        "fallback": """- Sửa key policy xong vẫn lỗi: policy có thể mất vài giây để áp dụng; thử lại.
- Không thấy statement lab: `up 10` chưa chạy hoặc `down 10` đã dọn.
- Đừng sửa IAM policy nếu lỗi là `kms:Decrypt`; đọc message trong CloudTrail trước.
- Nếu bạn không có quyền `sts:AssumeRole`, lab này sẽ fail ở bước assume; đó là quyền của user, không phải lỗi lab.""",
    },
    "11": {
        "concepts": (
            "**Stack** là một tập tài nguyên do CloudFormation quản lý. Khi update lỗi, CloudFormation **rollback** về trạng thái trước; "
            "**Stack Events** là nơi duy nhất nói chính xác resource nào fail và vì sao. **Drift** là khi ai đó sửa tay resource ngoài CloudFormation."
        ),
        "terms": [
            ("Stack", "Một nhóm tài nguyên được quản lý chung."),
            ("Update rollback", "Tự quay về trạng thái trước khi update lỗi."),
            ("Stack event", "Nhật ký từng bước tạo/sửa/xoá resource."),
            ("Drift", "Resource bị sửa ngoài CloudFormation."),
            ("Change set", "Bản nháp cho biết update sẽ thay đổi gì."),
        ],
        "path": """1. Ô **Search** → `CloudFormation` → **Stacks** → bấm `soa-c03-lab11`.
2. Tab **Stack info**: đọc **Status** và **Status reason**.
3. Tab **Events**: danh sách mới nhất ở trên. Tìm event `*_FAILED` **đầu tiên** của lần update (kéo xuống gần cuối nhóm update).
4. Bấm event `*_FAILED` → mở **Resource status reason**; đây là lỗi gốc.
5. Tab **Resources**: xem logical ID, physical ID, status.
6. **Stack actions** → **Detect drift** → chờ → xem cột **Drift status**.
7. (Tuỳ chọn) Terminal: `cd labs/11-cloudformation-cdk/cdk && cdk synth` để xem template sinh ra.""",
        "read": [
            ("Stack Status", "`UPDATE_ROLLBACK_COMPLETE` nghĩa là update lỗi nhưng đã rollback xong."),
            ("Status reason", "Câu lỗi thật, thường ở event `*_FAILED` đầu tiên."),
            ("Logical ID", "Tên resource trong template, dùng để sửa đúng chỗ."),
            ("Physical ID", "Tên thật trên AWS, dùng để tra tiếp."),
            ("Drift status", "`DRIFTED` nghĩa là có người sửa ngoài template."),
            ("CDK synth", "Chỉ tạo template ở máy, không deploy."),
        ],
        "links": [
            ("CloudFormation stacks", "https://console.aws.amazon.com/cloudformation/home?region={region}#/stacks"),
            ("Stack `soa-c03-lab11` events", "https://console.aws.amazon.com/cloudformation/home?region={region}#/stacks/events?stackId={prefix}-lab11"),
        ],
        "fallback": """- Không thấy stack: `up 11` chưa chạy; đây là lab không cần app stack.
- `ROLLBACK_COMPLETE` khi **tạo** stack nghĩa là lần tạo đầu lỗi; phải xoá rồi tạo lại, không update tiếp.
- Đừng đọc event cuối cùng; lỗi thật là event `*_FAILED` đầu tiên trong chuỗi.
- Drift chỉ có sau khi bạn sửa tay một resource; lab không tự tạo drift.""",
    },
    "12": {
        "concepts": (
            "**EventBridge rule** khớp event `EC2 Instance State-change` với `state=stopped` rồi gọi **Lambda**. "
            "Lambda cần **execution role** để start instance và **resource-based permission** để EventBridge được phép gọi nó. "
            "Remediation phải idempotent vì một event có thể đến nhiều lần."
        ),
        "terms": [
            ("Event pattern", "Bộ lọc JSON quyết định event nào khớp rule."),
            ("Target", "Đích rule gọi tới: Lambda, SQS, SNS..."),
            ("Resource-based policy", "Ai được phép gọi Lambda."),
            ("Execution role", "Role Lambda dùng khi chạy code."),
            ("Idempotency", "Chạy lại nhiều lần vẫn cho cùng kết quả."),
        ],
        "path": """1. Ô **Search** → `EventBridge` → **Rules** → bấm `soa-c03-lab12-remediate`.
2. Tab **Event pattern**: đọc JSON, chú ý `source`, `detail-type`, `detail.state`.
3. Tab **Targets**: xem Lambda `soa-c03-lab12-remediate` và SQS `soa-c03-lab12-events`.
4. Tab **Monitoring**: xem **Invocations**, **Failed invocations**, **Throttles** trong 1h.
5. Ô **Search** → `Lambda` → **Functions** → `soa-c03-lab12-remediate`.
6. Tab **Monitor** → **View CloudWatch logs** → mở stream mới nhất → tìm dòng `started` hoặc `skip`.
7. Tab **Configuration** → **Permissions** → xem **Resource-based policy** (principal `events.amazonaws.com`).
8. Ô **Search** → `EC2` → **Instances** → `soa-c03-lab12-canary` → tab **Tags** (`auto-remediate=true`), **Instance state**.
9. Ô **Search** → `SQS` → `soa-c03-lab12-events` → poll message.""",
        "read": [
            ("Event pattern", "Thiếu `detail.state` hoặc sai `detail-type` là rule không khớp."),
            ("Rule Invocations", "0 nghĩa là event không tới rule."),
            ("Lambda log", "`started <id>` chứng minh code đã chạy; `skip` nghĩa là tag sai."),
            ("Resource-based policy", "Thiếu statement cho `events.amazonaws.com` thì rule gọi bị từ chối."),
            ("Execution role", "Thiếu `ec2:StartInstances` thì Lambda lỗi."),
            ("Canary tag", "`auto-remediate=true` là điều kiện code kiểm tra."),
        ],
        "links": [
            ("EventBridge rules", "https://console.aws.amazon.com/events/home?region={region}#/eventbus/default/rules"),
            ("Lambda functions", "https://console.aws.amazon.com/lambda/home?region={region}#/functions"),
            ("SQS queues", "https://console.aws.amazon.com/sqs/v3/home?region={region}#/queues"),
            ("EC2 instances", _ec2("#Instances:")),
        ],
        "fallback": """- Rule invocation 0: kiểm tra rule **Enabled** và event pattern.
- Lambda lỗi: tab **Monitor** → log; lỗi thường là role thiếu quyền.
- Lambda không được gọi: **Permissions** thiếu statement hoặc sai `source-arn`.
- Canary vẫn stopped: có thể tag sai hoặc Lambda chưa chạy; đọc log trước.""",
    },
    "13": {
        "concepts": (
            "**Trust policy** trả lời “ai được assume role này”; **permission policy** trả lời “sau khi assume thì làm được gì”. "
            "`AssumeRole` lỗi vì trust policy sai không liên quan gì tới quyền S3. "
            "Sau khi assume, bạn có credential tạm thời và danh tính `assumed-role/...`."
        ),
        "terms": [
            ("Trust policy", "Danh sách principal được phép assume role."),
            ("Permission policy", "Quyền của role sau khi được assume."),
            ("AssumeRole", "Đổi sang danh tính tạm thời của role."),
            ("Session", "Phiên assume, có thời hạn."),
            ("External ID", "Chuỗi bí mật thêm vào trust để tránh confused deputy."),
        ],
        "path": """1. Ô **Search** → `IAM` → **Roles** → bấm `soa-c03-lab13-target`.
2. Tab **Trust relationships** → **Edit trust policy**: đọc `Principal.AWS`.
3. Tab **Permissions** → bấm policy `lab13-s3`: đọc action/resource.
4. Terminal: `aws sts assume-role --role-arn arn:aws:iam::<account>:role/soa-c03-lab13-target --role-session-name test`.
5. Nếu thành công, export 3 biến credential rồi chạy `aws sts get-caller-identity`.
6. Nếu lỗi, đọc `AccessDenied` message: principal nào, action nào.
7. Ô **Search** → `CloudTrail` → **Event history** → filter `AssumeRole` → xem `errorCode`/`errorMessage`.""",
        "read": [
            ("Trust Principal", "Phải là account/role của bạn, không phải account khác."),
            ("Conditions", "Có thể yêu cầu MFA hoặc ExternalId."),
            ("Permission actions", "Role có `s3:ListBucket`/`GetObject` không."),
            ("AccessDenied message", "Nói rõ trust policy hay permission policy chặn."),
            ("get-caller-identity ARN", "Phải chứa `assumed-role/soa-c03-lab13-target`."),
            ("Session duration", "Mặc định 1h; hết hạn phải assume lại."),
        ],
        "links": [
            ("IAM roles", "https://console.aws.amazon.com/iam/home#/roles"),
            ("CloudTrail events", "https://console.aws.amazon.com/cloudtrail/home?region={region}#/events"),
        ],
        "fallback": """- User của bạn không có `sts:AssumeRole`: thêm quyền cho user, không sửa trust policy của role lab.
- Trust policy đúng nhưng vẫn lỗi: có thể account ID trong ARN sai hoặc role name sai.
- Sau khi assume, credential chỉ nằm trong shell hiện tại; mở terminal mới phải export lại.
- `get-caller-identity` trả user gốc nghĩa là chưa export credential.""",
    },
    "14": {
        "concepts": (
            "Bucket S3 có **ba lớp** bảo vệ: **Block Public Access** (công tắc tổng), **bucket policy** (luật tài nguyên), và **ACL** (quyền cũ). "
            "**Access Analyzer** tìm cấu hình cho phép truy cập ngoài account. "
            "Một bucket có thể private theo BPA nhưng policy vẫn public nếu BPA bị tắt."
        ),
        "terms": [
            ("Block Public Access", "4 công tắc chặn public ở mức bucket/account."),
            ("Bucket policy", "JSON policy gắn vào bucket."),
            ("ACL", "Quyền kiểu cũ, thường nên tắt."),
            ("Access Analyzer", "Dịch vụ tìm resource cho phép truy cập ngoài."),
            ("Anonymous access", "Truy cập không có credential, ví dụ curl không ký."),
        ],
        "path": """1. Ô **Search** → `S3` → **Buckets** → search `soa-c03-lab14` → bấm bucket.
2. Tab **Permissions** → mục **Block public access (bucket settings)** → **Edit** → đọc 4 cờ.
3. Cùng tab → **Bucket policy** → **Edit** → tìm `"Principal": "*"` hoặc `"AWS": "*"`.
4. Cùng tab → **Access control list (ACL)** → xem grant cho `AllUsers`/`AuthenticatedUsers`.
5. Ô **Search** → `Access Analyzer` → **Access Analyzer** → analyzer `soa-c03-lab14` → tab **Findings**.
6. Terminal: `curl -I https://<bucket>.s3.ap-southeast-1.amazonaws.com/secret.txt` (không kèm credential).""",
        "read": [
            ("4 cờ BPA", "Phải cùng `On`; thiếu `BlockPublicPolicy` là policy public vẫn có hiệu lực."),
            ("Policy Principal", "`*` nghĩa là bất kỳ ai."),
            ("Policy status", "`IsPublic = true` là bằng chứng bucket đang public."),
            ("ACL grants", "`AllUsers` = public; `AuthenticatedUsers` = mọi AWS account."),
            ("Finding status", "`Active` nghĩa là đường public đang mở."),
            ("HTTP code", "`200` là public; `403` là đã chặn."),
        ],
        "links": [
            ("S3 buckets", "https://console.aws.amazon.com/s3/buckets?region={region}"),
            ("Access Analyzer", "https://console.aws.amazon.com/access-analyzer/home?region={region}#/analyzer"),
        ],
        "fallback": """- Không thấy bucket: search theo prefix `soa-c03-lab14`; tên bucket có account ID.
- BPA `On` nhưng vẫn public: kiểm tra policy; BPA không tự xoá policy.
- curl trả 403 ngay cả trước khi sửa: có thể bucket ở region khác hoặc object key sai.
- Access Analyzer cần vài phút mới có finding; đừng kết luận vội.""",
    },
    "15": {
        "concepts": (
            "Mạng đi qua nhiều lớp: **Security Group** (stateful, chỉ cần cho chiều vào), **NACL** (stateless, phải cho cả chiều về), "
            "**route table**, rồi tới app. **Flow Logs** ghi ACCEPT/REJECT; **Reachability Analyzer** chỉ ra lớp nào chặn trên đường đi."
        ),
        "terms": [
            ("Security group", "Tường lửa stateful gắn vào ENI."),
            ("NACL", "Tường lửa stateless gắn vào subnet."),
            ("Route table", "Bảng chỉ đường ra Internet/giữa subnet."),
            ("Flow Logs", "Nhật ký luồng IP, có ACCEPT/REJECT."),
            ("Reachability Analyzer", "Công cụ mô phỏng đường đi và tìm điểm chặn."),
            ("Ephemeral port", "Port tạm cho chiều về, thường 1024–65535."),
        ],
        "path": """1. Ô **Search** → `EC2` → **Target groups** → `soa-c03-tg` → **Targets**: đọc health reason.
2. **Security groups** → SG của app → tab **Inbound rules**: phải có TCP 8080 từ SG của ALB.
3. Ô **Search** → `VPC` → **Network ACLs** → bấm NACL gắn với subnet của app → **Inbound rules** + **Outbound rules**.
4. **Route tables** → bấm route table của subnet → tab **Routes** và **Subnet associations**.
5. **Flow logs** → bấm flow log của VPC → link tới log group `/aws/vpc/soa-c03/lab15`.
6. Trong log group → **Logs Insights**, chạy:
   ```sql
   fields @timestamp, srcaddr, dstaddr, srcport, dstport, action
   | filter dstport = 8080
   | sort @timestamp desc
   | limit 20
   ```
7. **Reachability Analyzer** → **Create and analyze path** → chọn source ALB ENI, destination app ENI, port 8080 → **Create path** → **Run analysis**.""",
        "read": [
            ("Target health reason", "Cho biết health check fail vì timeout, response code, hay connection."),
            ("SG inbound", "Chỉ cần cho chiều vào; stateful tự cho chiều về."),
            ("NACL inbound/outbound", "Phải cho cả 8080 và ephemeral ports; deny theo số thứ tự thấp hơn sẽ thắng."),
            ("Route", "`local` cho nội bộ VPC; `0.0.0.0/0` qua IGW/NAT cho Internet."),
            ("Flow log action", "`REJECT` chỉ ra lớp chặn; `ACCEPT` chứng minh đã qua."),
            ("Analyzer path", "Chỉ ra từng hop `ACCEPT`/`BLOCKED` và lý do."),
        ],
        "links": [
            ("Target groups", _ec2("#TargetGroups:")),
            ("Security groups", _ec2("#SecurityGroups:")),
            ("VPC console", "https://console.aws.amazon.com/vpcconsole/home?region={region}"),
            ("Flow logs", "https://console.aws.amazon.com/vpcconsole/home?region={region}#FlowLogs:"),
            ("Reachability Analyzer", "https://console.aws.amazon.com/vpcconsole/home?region={region}#ReachabilityAnalyzer:"),
        ],
        "fallback": """- Flow Logs có thể trễ 5–10 phút; đừng kết luận “không có traffic” quá sớm.
- Analyzer chỉ kiểm tra cấu hình, không chứng minh app trả 200.
- NACL là stateless: thiếu outbound ephemeral ports là lỗi rất hay gặp.
- Sửa một lớp rồi kiểm tra lại; đừng sửa SG + NACL + route cùng lúc.""",
    },
    "16": {
        "concepts": (
            "Private subnet không có NAT thì không ra Internet. **Gateway endpoint** (S3, DynamoDB) gắn vào route table và miễn phí. "
            "**Interface endpoint** tạo ENI + security group trong subnet, tốn phí theo giờ. "
            "**Private DNS** giúp tên service phân giải thành IP nội bộ."
        ),
        "terms": [
            ("Gateway endpoint", "Cửa vào S3/DynamoDB qua route table, miễn phí."),
            ("Interface endpoint", "ENI riêng trong subnet cho phần lớn service khác, có phí."),
            ("Private DNS", "Phân giải tên service thành IP nội bộ."),
            ("Route table association", "Gắn endpoint với route table của subnet."),
            ("ENI", "Card mạng ảo của instance/endpoint."),
        ],
        "path": """1. Ô **Search** → `VPC` → **Endpoints** → lọc theo VPC của core.
2. Bấm endpoint S3 (type **Gateway**) → tab **Route tables**: phải có route table của private subnet.
3. Bấm một interface endpoint (SSM) → tab **Subnets** và **Security groups**.
4. Ô **Search** → `EC2` → **Instances** → `soa-c03-lab16-private` → tab **Networking**: không có **Public IPv4**.
5. Ô **Search** → `Systems Manager` → **Fleet Manager**: instance private phải **Online**.
6. **Session Manager** → **Start session** → chạy `aws s3 ls s3://<bucket-core>`.
7. Nếu cần xem DNS: trong session chạy `getent hosts ssm.ap-southeast-1.amazonaws.com`.""",
        "read": [
            ("Endpoint type", "`Gateway` cho S3; `Interface` cho SSM/SSM Messages/EC2 Messages."),
            ("Endpoint state", "`available` mới dùng được; `pending` thì chờ."),
            ("Route tables", "Gateway endpoint phải gắn đúng route table của subnet private."),
            ("Security group của endpoint", "Phải cho private SG vào 443."),
            ("Public IPv4", "Phải trống; có public IP là không còn “private”."),
            ("S3 result", "`aws s3 ls` thành công chứng minh đường S3 đi qua endpoint."),
        ],
        "links": [
            ("VPC endpoints", "https://console.aws.amazon.com/vpcconsole/home?region={region}#Endpoints:"),
            ("EC2 instances", _ec2("#Instances:")),
            ("Fleet Manager", "https://console.aws.amazon.com/systems-manager/managed-instances?region={region}"),
            ("Session Manager", "https://console.aws.amazon.com/systems-manager/session-manager/start-session?region={region}"),
        ],
        "fallback": """- Instance không Online: kiểm tra 3 interface endpoint và private DNS.
- `aws s3 ls` timeout: gateway endpoint thiếu route table association, hoặc SG endpoint chặn 443.
- Endpoint `pending` vài phút là bình thường.
- Interface endpoint tốn phí; `./bin/lab down 16` ngay sau lab.""",
    },
    "17": {
        "concepts": (
            "Ba lỗi cùng lúc ở ba lớp: **health check path**, **security group**, **NACL**. "
            "Một lỗi có thể che lỗi khác, nên phải sửa từng lớp và chứng minh bằng target health + Flow Logs. "
            "NACL là stateless: deny inbound 8080 là đủ làm app chết dù SG đúng."
        ),
        "terms": [
            ("Health check path", "Đường dẫn ALB gọi để kiểm tra app."),
            ("Security group", "Tường lửa stateful ở ENI."),
            ("NACL", "Tường lửa stateless ở subnet, có số thứ tự."),
            ("Flow Logs", "Bằng chứng ACCEPT/REJECT."),
            ("Layered fix", "Sửa một lớp, verify, rồi mới sang lớp tiếp."),
        ],
        "path": """1. **EC2** → **Target groups** → `soa-c03-tg` → **Targets**: đọc health reason.
2. Cùng target group → **Health checks**: đọc path hiện tại.
3. **EC2** → **Security groups** → SG app → **Inbound rules**: tìm TCP 8080.
4. **VPC** → **Network ACLs** → NACL của subnet app → **Inbound rules**: tìm rule deny port 8080 và số rule.
5. **VPC** → **Flow logs** → log group `/aws/vpc/soa-c03/lab17` → **Logs Insights** query `filter dstport = 8080`.
6. Sửa path trước → đợi health check → xem target.
7. Sửa SG → xem target.
8. Sửa NACL → xem target + `/health` 200.""",
        "read": [
            ("Health check path", "Phải là `/health`, không phải đường dẫn không tồn tại."),
            ("SG inbound 8080", "Phải cho SG của ALB, không phải `0.0.0.0/0`."),
            ("NACL rule number", "Rule số nhỏ hơn được đánh giá trước; deny thắng allow."),
            ("Flow log REJECT", "Chứng minh gói bị chặn ở lớp nào."),
            ("Target health sau mỗi fix", "Chỉ một lớp thay đổi mỗi lần để biết nhân quả."),
            ("HTTP `/health`", "200 là tiêu chí cuối, không phải target `healthy` đơn thuần."),
        ],
        "links": [
            ("Target groups", _ec2("#TargetGroups:")),
            ("Security groups", _ec2("#SecurityGroups:")),
            ("Network ACLs", "https://console.aws.amazon.com/vpcconsole/home?region={region}#NetworkAcls:"),
            ("Flow logs", "https://console.aws.amazon.com/vpcconsole/home?region={region}#FlowLogs:"),
        ],
        "fallback": """- Target vẫn unhealthy sau khi sửa path: chờ ít nhất 3 × interval.
- Flow Logs chưa có dữ liệu: có thể trễ 5–10 phút.
- NACL có nhiều rule: đọc theo số thứ tự từ thấp lên, không chỉ nhìn rule bạn vừa sửa.
- Đừng sửa cả ba lớp cùng lúc; bạn sẽ không biết lớp nào thật sự chặn.""",
    },
    "18": {
        "concepts": (
            "**Task definition** là bản thiết kế container; **task** là một lần chạy; **service** giữ số task luôn đủ. "
            "Fargate cần **execution role** để pull image và ghi log. "
            "**Container Insights** là metric bổ sung ở cluster, có thể trễ vài phút."
        ),
        "terms": [
            ("Task definition", "Bản thiết kế container: image, CPU, memory, log."),
            ("Task", "Một container đang chạy."),
            ("Service", "Bộ quản lý giữ số task đúng desired count."),
            ("Fargate", "Chạy container không cần quản lý EC2."),
            ("Execution role", "Role để ECS agent pull image/ghi log."),
            ("Container Insights", "Metric/log nâng cao cho cluster."),
        ],
        "path": """1. Ô **Search** → `ECS` → **Clusters** → `soa-c03-lab18`.
2. Tab **Services** → bấm `soa-c03-lab18-web`.
3. Tab **Health** / **Events**: đọc deployment events và lý do task bị thay.
4. Tab **Tasks** → bấm task đang chạy → **Configuration**: xem **Last status**, **Stopped reason**.
5. Tab **Logs** của task → mở stream để đọc log nginx.
6. Tab **Monitoring** → xem Container Insights (CPU/memory) — có thể trễ.
7. Task **Networking** → lấy **Public IP** → mở `http://<ip>` trên browser.
8. Ô **Search** → `ECR` → **Repositories** → `soa-c03-lab18-nginx` → xem lifecycle policy.""",
        "read": [
            ("Running / Desired count", "Service phải giữ 1 task running."),
            ("Deployment events", "Nói vì sao task bị stop và service có stabilize không."),
            ("Stopped reason", "`Essential container exited`, image pull error, OOM..."),
            ("Container log", "Lỗi thật từ bên trong container."),
            ("Public IP + HTTP", "`200` chứng minh task phục vụ được."),
            ("Execution role", "Thiếu quyền pull/ghi log thì task không start."),
        ],
        "links": [
            ("ECS cluster `soa-c03-lab18`", "https://console.aws.amazon.com/ecs/v2/clusters/{prefix}-lab18/services?region={region}"),
            ("ECS service", "https://console.aws.amazon.com/ecs/v2/clusters/{prefix}-lab18/services/{prefix}-lab18-web/health?region={region}"),
            ("CloudWatch log group", _cw("#logsV2:log-groups/log-group/%2Faws%2Fecs%2Fsoa-c03%2Flab18")),
            ("ECR repositories", "https://console.aws.amazon.com/ecr/repositories?region={region}"),
        ],
        "fallback": """- Task `STOPPED` ngay: đọc **Stopped reason** và log, thường là image pull hoặc execution role.
- Service không stabilize: xem **Events**; có thể subnet không public IP hoặc SG thiếu egress.
- Container Insights trống: mới bật, chờ vài phút.
- `public.ecr.aws` bị chặn: push image lên ECR rồi sửa task definition.""",
    },
    "19": {
        "concepts": (
            "**AWS Backup** dùng vault + plan + resource assignment để tạo **recovery point**. "
            "**AWS Config** ghi lại trạng thái tài nguyên và chấm compliance bằng rule; recorder phải đang chạy. "
            "**Budget** chỉ cảnh báo, không chặn chi phí; **Cost Explorer** có thể trễ tới 24h."
        ),
        "terms": [
            ("Backup vault", "Kho chứa recovery point."),
            ("Backup plan", "Lịch backup và thời gian giữ."),
            ("Recovery point", "Một bản backup cụ thể."),
            ("Config recorder", "Bộ ghi trạng thái tài nguyên."),
            ("Config rule", "Luật compliance, ví dụ EBS phải mã hoá."),
            ("Budget", "Cảnh báo chi phí theo ngưỡng."),
        ],
        "path": """1. Ô **Search** → `AWS Backup` → **Backup vaults** → bấm `soa-c03-lab19`.
2. Tab **Recovery points**: xem recovery point mới nhất, **Status = Completed**.
3. Menu trái **Backup plans** → `soa-c03-lab19-plan` → **Resource assignments**: tag `Backup=lab19`.
4. Menu trái **Jobs** → bấm job gần nhất → đọc **Status**, **Resource**, **Completion time**.
5. Ô **Search** → `AWS Config` → **Rules** → `soa-c03-lab19-encrypted-volumes` → **Compliance**.
6. Menu trái **Settings**: xem **Recording is on/off** và delivery channel.
7. Ô **Search** → `Billing and Cost Management` → **Budgets** → `soa-c03-lab19`.
8. **Cost Explorer** → **Cost and usage** → group by **Service**.""",
        "read": [
            ("Recovery point status", "`Completed` mới dùng để restore."),
            ("Backup job status", "`COMPLETED`, `FAILED`, `EXPIRED`."),
            ("Resource assignment", "Tag đúng thì RDS mới được chọn."),
            ("Config recording", "`On` thì rule mới có dữ liệu."),
            ("Rule compliance", "`COMPLIANT`/`NON_COMPLIANT`; mới bật có thể `INSUFFICIENT_DATA`."),
            ("Budget vs Cost Explorer", "Budget là ngưỡng; Cost Explorer là số tiền thực tế."),
        ],
        "links": [
            ("AWS Backup vaults", "https://console.aws.amazon.com/backup/home?region={region}#backup/vaults"),
            ("AWS Backup plans", "https://console.aws.amazon.com/backup/home?region={region}#backup/plans"),
            ("AWS Config dashboard", "https://console.aws.amazon.com/config/home?region={region}#/dashboard"),
            ("AWS Budgets", "https://console.aws.amazon.com/billing/home?region={region}#/budgets"),
            ("Cost Explorer", "https://console.aws.amazon.com/costmanagement/home?region={region}#/cost-explorer"),
        ],
        "fallback": """- Backup job chưa xong: RDS snapshot có thể mất vài phút; quay lại sau.
- Config `INSUFFICIENT_DATA`: recorder mới bật hoặc rule mới tạo; chờ vài phút.
- Cost Explorer trống: dữ liệu có thể trễ 24h; không kết luận là không tốn tiền.
- Budget không chặn chi phí; nó chỉ gửi cảnh báo.""",
    },
    "20": {
        "concepts": (
            "Incident có nhiều **symptom** cùng lúc: CPU cao, 5xx, chậm. Symptom không phải root cause. "
            "Đi từ user-facing path (`/health`, ALB) xuống target, instance, process, log, DB. "
            "Scale out có thể che symptom nhưng không chứng minh đã sửa gốc."
        ),
        "terms": [
            ("Symptom", "Cái người dùng thấy: chậm, 500, 503."),
            ("Root cause", "Lớp thật sự hỏng."),
            ("5xx", "Lỗi server/ALB."),
            ("Latency", "Thời gian phản hồi."),
            ("Triage", "Ưu tiên kiểm tra theo thứ tự user-facing trước."),
        ],
        "path": """1. Ô **Search** → `CloudWatch` → **Metrics** → **EC2** → tick `CPUUtilization` của instance; time range **1h**, xem Average/Maximum.
2. **Alarms** → **All alarms** → filter prefix `soa-c03`: xem state và history.
3. Ô **Search** → `EC2` → **Target groups** → `soa-c03-tg` → **Targets**: healthy/unhealthy.
4. **CloudWatch** → **Logs Insights** → log group app → query:
   ```sql
   fields @timestamp, level, msg
   | filter level = "ERROR"
   | sort @timestamp desc
   | limit 50
   ```
5. **CloudWatch** → **Metrics** → **RDS** → CPU/connections của `soa-c03-db`.
6. Terminal: `curl -i http://<alb>/health`, `/db`, `/slow?ms=1000`.
7. Nếu cần process: **Systems Manager** → **Run Command** → `top -b -n1` và `ps aux --sort=-%cpu`.""",
        "read": [
            ("CPU timeline", "CPU tăng đúng lúc symptom bắt đầu hay từ trước?"),
            ("Alarm history", "Alarm nào kêu trước, alarm nào kêu sau."),
            ("Target health", "Nếu unhealthy, lỗi ở network/app; nếu healthy, lỗi có thể ở app/DB."),
            ("Log ERROR", "Thông điệp lỗi thật và timestamp."),
            ("RDS metrics", "CPU/connections có tăng bất thường không."),
            ("HTTP code từng endpoint", "Tách `/health` (app sống) khỏi `/db` (đường DB)."),
        ],
        "links": [
            ("CloudWatch metrics", _cw("#metricsV2:")),
            ("CloudWatch alarms", _cw("#alarmsV2:alarms")),
            ("Target groups", _ec2("#TargetGroups:")),
            ("Logs Insights", _cw("#logsV2:logs-insights")),
            ("RDS databases", "https://console.aws.amazon.com/rds/home?region={region}#databases:"),
        ],
        "fallback": """- CPU đã giảm nhưng vẫn 5xx: CPU có thể là hậu quả, không phải nguyên nhân; đọc log.
- Target healthy nhưng `/db` lỗi: đi tiếp xuống DB/SG/secret.
- ASG vừa scale: instance mới có thể chưa có metric/log; chờ vài phút.
- Đừng stop load trước khi verify nếu verify cần metric.""",
    },
    "21": {
        "concepts": (
            "Hai đường hỏng độc lập: **data path** (app → SG → RDS) và **identity path** (app role → Secrets Manager). "
            "DB timeout thường do SG/NACL/route/DNS; `AccessDenied` thường do identity/resource policy, KMS, hoặc explicit deny. "
            "Phải chứng minh từng đường bằng một evidence riêng."
        ),
        "terms": [
            ("DB timeout", "Kết nối TCP không thành công hoặc quá chậm."),
            ("AccessDenied", "Lỗi quyền, không phải lỗi mạng."),
            ("Explicit deny", "Câu Deny thắng mọi Allow."),
            ("Secret", "Chuỗi bí mật lưu trong Secrets Manager."),
            ("App role", "Role gắn vào EC2 app qua instance profile."),
        ],
        "path": """1. Ô **Search** → `EC2` → **Security groups** → SG DB (`soa-c03-db-...`) → **Inbound rules**: TCP 5432 từ SG app.
2. Ô **Search** → `IAM` → **Roles** → role app (lấy tên từ CloudFormation Outputs `AppInstanceRoleName`) → tab **Permissions** → tìm inline `lab21-deny-secret`.
3. Ô **Search** → `Secrets Manager` → secret DB (Output `DbSecretArn`) → **Overview**; thử **Retrieve secret value**.
4. **CloudWatch** → **Logs Insights** → log app → filter `db_check_failed` hoặc `AccessDenied`.
5. Terminal: `curl -i http://<alb>/db`.
6. **Systems Manager** → **Run Command** → `aws secretsmanager get-secret-value ...` để tách lỗi quyền khỏi app.""",
        "read": [
            ("SG 5432", "Thiếu rule là DB timeout ngay."),
            ("Inline policy name", "`lab21-deny-secret` là deny chủ động, không phải policy thiếu."),
            ("Secret retrieve", "Nếu console đọc được mà app không, so role của bạn với role app."),
            ("Log error", "`timeout` vs `AccessDenied` cho biết đường nào hỏng."),
            ("`/db` code", "200 chỉ khi cả SG và secret đều đúng."),
            ("CloudTrail", "`GetSecretValue` + `errorCode` là bằng chứng quyền."),
        ],
        "links": [
            ("Security groups", _ec2("#SecurityGroups:")),
            ("IAM roles", "https://console.aws.amazon.com/iam/home#/roles"),
            ("Secrets Manager", "https://console.aws.amazon.com/secretsmanager/landing?region={region}"),
            ("Logs Insights", _cw("#logsV2:logs-insights")),
        ],
        "fallback": """- Sửa SG xong vẫn timeout: kiểm tra NACL outbound ephemeral ports.
- Secret đọc được nhưng app vẫn lỗi: app có thể cache secret cũ; restart service qua SSM.
- IAM policy thay đổi có thể mất vài giây; thử lại.
- Đừng sửa cả hai lớp cùng lúc; mỗi lần một thay đổi rồi verify.""",
    },
    "22": {
        "concepts": (
            "**Self-healing** dựa vào health check của ALB + ASG thay instance khi target unhealthy. "
            "**Backup plan** chỉ có giá trị khi có recovery point và đã test restore. "
            "Production readiness = observability (dashboard/alarm) + HA + backup + runbook."
        ),
        "terms": [
            ("Self-healing", "Hệ thống tự thay thành phần hỏng."),
            ("Health check grace", "Thời gian ASG chờ app khởi động trước khi đánh unhealthy."),
            ("Recovery point", "Một bản backup."),
            ("Dashboard", "Một trang gom metric/log quan trọng."),
            ("Runbook", "Các bước xử lý khi sự cố."),
        ],
        "path": """1. Ô **Search** → `EC2` → **Auto Scaling Groups** → `soa-c03-asg` → tab **Activity**: tìm launch/terminate gần đây.
2. Tab **Instance management**: so instance ID với lúc bắt đầu break.
3. **EC2** → **Instances** → instance mới → **Launch time**, **Status checks**.
4. **EC2** → **Target groups** → `soa-c03-tg` → **Targets**: healthy.
5. **CloudWatch** → **Dashboards** → `soa-c03-ops`: xem các widget.
6. **CloudWatch** → **Alarms** → filter `soa-c03`: đếm số alarm.
7. **AWS Backup** → **Backup plans** → `soa-c03-lab22`; **Vaults** → `soa-c03-lab22`.
8. Terminal: `curl -i http://<alb>/health` và `/db`.""",
        "read": [
            ("ASG Activity", "Có `Terminating` instance cũ và `Launching` instance mới không."),
            ("Instance ID trước/sau", "Khác nhau chứng minh đã thay, không chỉ restart service."),
            ("Target health", "Instance mới phải healthy."),
            ("Dashboard widgets", "Có metric ALB/EC2/RDS/log."),
            ("Số alarm", "Lab yêu cầu ít nhất 4 alarm prefix `soa-c03`."),
            ("Backup plan + vault", "Phải tồn tại; recovery point có thể chưa có ngay."),
        ],
        "links": [
            ("Auto Scaling groups", _ec2("#AutoScalingGroups:")),
            ("CloudWatch dashboard", _cw("#dashboards:name={prefix}-ops")),
            ("CloudWatch alarms", _cw("#alarmsV2:alarms")),
            ("AWS Backup plans", "https://console.aws.amazon.com/backup/home?region={region}#backup/plans"),
        ],
        "fallback": """- Instance chưa bị thay: health check grace có thể tới 10 phút; xem **Activity**.
- Instance mới nhưng app chưa lên: đọc `/var/log/cloudops-bootstrap.log` qua SSM.
- Dashboard trống: chạy `make dash` (cần app stack).
- Backup plan có nhưng chưa có recovery point: chờ job hoặc chạy on-demand job.""",
    },
    "23": {
        "concepts": (
            "Bài cuối không có hint: năm lỗi ở năm lớp. **Thứ tự triage**: user-facing (`/health`, target) → data (`/db`) → "
            "identity (S3) → performance (CPU). Mỗi fix phải verify ngay; một fix có thể làm lộ lỗi tiếp theo."
        ),
        "terms": [
            ("Triage", "Phân loại và ưu tiên theo mức ảnh hưởng."),
            ("User-facing path", "Đường người dùng đi: ALB → target → app."),
            ("Data path", "Đường app → DB."),
            ("Identity path", "Đường app role → S3/secret."),
            ("Layered fix", "Sửa từng lớp, verify sau mỗi lần."),
        ],
        "path": """1. Terminal: `curl -i http://<alb>/health` → ghi status code.
2. **EC2** → **Target groups** → `soa-c03-tg` → **Targets** + **Health checks**.
3. **EC2** → **Security groups** → SG app → **Inbound** 8080; SG DB → **Inbound** 5432.
4. **IAM** → **Roles** → role app → **Permissions** → inline `lab23-deny-s3`.
5. **CloudWatch** → **Logs Insights** → log app → lọc ERROR/AccessDenied.
6. **Systems Manager** → **Run Command** → `aws s3 ls s3://<bucket>` trên app instance.
7. **CloudWatch** → **Metrics** → EC2 CPU; **RDS** → `/db`.
8. Sửa một lớp → chạy `./bin/lab verify 23` → sang lớp tiếp.""",
        "read": [
            ("`/health` code", "503 thường là target/health check/SG."),
            ("Target health reason", "Chỉ ra lớp mạng hoặc app."),
            ("SG app/DB", "Hai rule độc lập; thiếu một cái là một đường chết."),
            ("Inline deny", "`lab23-deny-s3` là deny chủ động."),
            ("S3 result", "`aws s3 ls` fail = identity path."),
            ("CPU", "Cao có thể do load, không nhất thiết là root cause."),
        ],
        "links": [
            ("Target groups", _ec2("#TargetGroups:")),
            ("Security groups", _ec2("#SecurityGroups:")),
            ("IAM roles", "https://console.aws.amazon.com/iam/home#/roles"),
            ("CloudWatch metrics", _cw("#metricsV2:")),
            ("Logs Insights", _cw("#logsV2:logs-insights")),
        ],
        "fallback": """- Sửa một lỗi mà verify vẫn fail: đọc output verify, nó nói lớp nào còn sai.
- Không chắc lỗi nào trước: làm user-facing trước, rồi data, rồi identity, cuối cùng performance.
- Đừng reset; reset chỉ dùng sau khi đã thử và phải ghi `SOLUTION_USED: yes`.
- Nếu bí quá 30 phút, dùng hint 1 rồi hint 2; không nhảy thẳng đáp án.""",
    },
}


def render_console(lid: str, prefix: str, region: str) -> str:
    """Return the markdown console section for one lab."""
    c = CONSOLE[lid]
    terms = "\n".join(f"| {t} | {d} |" for t, d in c["terms"])
    read = "\n".join(f"| {t} | {d} |" for t, d in c["read"])
    links = "\n".join(f"- [{label}]({url})" for label, url in c["links"])
    # Split the concept paragraph into one-sentence bullets. A 40-50 word
    # paragraph is hard to scan; bullets also make it easy for the AI to
    # explain exactly one idea per turn.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", c["concepts"].strip()) if s.strip()]
    concepts = "\n".join(f"- {s}" for s in sentences)
    body = f"""<!-- console-guide:start -->
## 5c. Console — bấm ở đâu, thấy gì

> **Trước khi bấm:** mở https://console.aws.amazon.com/ và đăng nhập **đúng account lab**
> (không dùng account cá nhân). Kiểm tra region góc trên phải là **Singapore (ap-southeast-1)**.
> Console AWS dùng tiếng Anh; nhãn trong bài là nhãn tiếng Anh.
> **Đường bấm** là nguồn chính; **link nhanh** chỉ là shortcut và có thể đổi khi AWS cập nhật giao diện.
> **Cách AI dạy:** mỗi lượt chỉ một màn hình và một nút. Bạn bấm xong, mô tả bạn thấy gì;
> AI mới đi tiếp. Đừng làm cả danh sách bước một lúc.
> Nhãn tiếng Anh khó hiểu? Tra bảng nút ở [`docs/console-guide.md`](../../docs/console-guide.md) mục 2e.

### Từ vựng nhanh (đọc trước)

| Thuật ngữ | Nghĩa đời thường |
|---|---|
{terms}

### Khái niệm của lab này

{concepts}

### Đường bấm từng bước

{c["path"]}

### Trên màn hình, đọc những ô này

| Ô / cột | Nó trả lời câu hỏi gì |
|---|---|
{read}

### Link nhanh

{links}

### Nếu không thấy mục đó

{c["fallback"]}

### Checkpoint trước khi bấm tiếp

- [ ] Bạn đang ở đúng service/trang (không phải tab khác).
- [ ] Bạn đọc được ít nhất một ô trong bảng “Trên màn hình, đọc những ô này”.
- [ ] Bạn nói được giá trị đó đúng hay sai dựa vào đâu.

> Chưa đạt cả 3? Quay lại một bước, đừng bấm tiếp.
<!-- console-guide:end -->"""
    return body.replace("{prefix}", prefix).replace("{region}", region)


def first_step(lid: str) -> str:
    """First numbered click step, for the 60-second quick card."""
    for line in CONSOLE[lid]["path"].splitlines():
        stripped = line.strip()
        if stripped.startswith("1."):
            return re.sub(r"^1\.\s*", "", stripped)
    return "Mở mục 5c bên dưới."


def glossary_markdown() -> str:
    """Build docs/glossary.md from every lab's term table."""
    from collections import defaultdict

    entries: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for lid, data in CONSOLE.items():
        for term, definition in data["terms"]:
            entries[term].append((lid, definition))

    lines = [
        "# Glossary — thuật ngữ trong 24 lab",
        "",
        "> File này được sinh tự động từ `tools/lab_console.py`.",
        "> Đừng sửa tay; sửa nguồn rồi chạy `python3 tools/gen_lab_docs.py`.",
        ">",
        "> Cách dùng: gặp từ lạ trong lab nào, tra ở đây, rồi quay lại mục 5c của lab đó.",
        "> Một số từ có định nghĩa khác nhau theo lab; cột **Lab** cho biết đang đọc định nghĩa nào.",
        "> Bảng 20 từ cốt lõi nằm trong `docs/beginner-mentor.md` mục 2.",
        "",
    ]
    groups: dict[str, list[str]] = defaultdict(list)
    for term in sorted(entries, key=str.casefold):
        first = term[0].upper()
        if not first.isalpha():
            first = "#"
        for lid, definition in entries[term]:
            groups[first].append(f"| **{term}** | {definition} | {lid} |")

    for letter in sorted(groups):
        lines += [
            f"## {letter}",
            "",
            "| Thuật ngữ | Nghĩa đời thường | Lab |",
            "|---|---|---|",
            *groups[letter],
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"
