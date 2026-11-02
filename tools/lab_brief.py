#!/usr/bin/env python3
"""Pre-lab brief and teaching script for all 24 labs.

The point is to remove the "blind diagnosis" problem:

  1. explain what exists and what "healthy" looks like (baseline)
  2. give a diagnostic map (question -> layer -> evidence), not the answer
  3. make the learner predict before the fault is injected
  4. teach with I do -> We do -> You do
  5. keep the actual change in a sealed note until the learner asks

Commands:
  python3 tools/lab_brief.py brief 03
  python3 tools/lab_brief.py baseline 03
  python3 tools/lab_brief.py baseline 03 --live
  python3 tools/lab_brief.py teach 03
  python3 tools/lab_brief.py change 03 [--sealed]
  python3 tools/lab_brief.py record-change 03
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LABS = ROOT / "labs"


BRIEFS: dict[str, dict] = {
    "03": {
        "title": "CloudTrail + EventBridge: ai đã terminate EC2?",
        "why": (
            "Lab này dạy forensic: khi một EC2 biến mất, làm sao biết ai làm, "
            "lúc nào, từ đâu, và automation có bắt được sự kiện không."
        ),
        "concepts": [
            ("CloudTrail", "Camera ghi lại ai gọi API gì, lúc nào, từ IP nào. Giữ event 90 ngày."),
            ("EventBridge", "Bộ lọc sự kiện: EC2 đổi trạng thái → rule khớp → đẩy thông báo tới SQS."),
            ("Canary", "Một EC2 nhỏ để thử. Không phải app thật, không phục vụ user."),
            ("SQS", "Hàng đợi nhận thông báo. Dùng để chứng minh event có tới."),
            ("IAM role", "Thẻ quyền tạm thời. Lab dùng role để terminate canary."),
        ],
        "inventory": [
            ("Canary EC2", "soa-c03-lab03-canary", "running", "EC2 → Instances → search tên"),
            ("CloudTrail", "soa-c03-trail", "Logging ON", "CloudTrail → Dashboard"),
            ("EventBridge rule", "soa-c03-lab03-ec2-state", "Enabled; target SQS", "EventBridge → Rules"),
            ("SQS", "soa-c03-lab03-events", "0 message", "SQS → Queues"),
            ("IAM role", "soa-c03-lab-operator", "tồn tại", "IAM → Roles"),
        ],
        "map": [
            ("Ai đã làm?", "CloudTrail → Event history", "userIdentity.type, arn, sessionName"),
            ("Lúc nào?", "Event record", "eventTime"),
            ("Từ đâu?", "Event record", "sourceIPAddress, userAgent"),
            ("Automation có thấy?", "EventBridge → rule → Monitoring", "Invocations, FailedInvocations"),
            ("Message có tới?", "SQS → Send and receive messages", "body, detail.state"),
            ("Cái gì bị ảnh hưởng?", "EC2 → Instances", "Instance state"),
        ],
        "predict": [
            "Canary đang ở trạng thái nào?",
            "Nếu canary bị terminate, 3 nơi nào sẽ thay đổi?",
            "Bạn sẽ xem gì đầu tiên để trả lời “ai làm”?",
        ],
        "announce": (
            "Canary EC2 sẽ bị terminate. CloudTrail, EventBridge rule, SQS và IAM role "
            "vẫn giữ nguyên."
        ),
        "change": (
            "Canary EC2 đã bị terminate. CloudTrail, EventBridge rule, SQS và IAM role "
            "vẫn giữ nguyên."
        ),
        "sealed": (
            "Canary bị terminate bằng AssumeRole của role soa-c03-lab-operator "
            "(session name: lab03-break)."
        ),
        "ido": (
            "Mở CloudTrail → Event history, lọc một event bình thường (ví dụ "
            "DescribeInstances). Đọc `userIdentity.type` và `eventTime`. Đây là mẫu; "
            "chưa phải event gây lỗi."
        ),
        "wedo": (
            "Mở EventBridge → Rules → `soa-c03-lab03-ec2-state` → tab Monitoring. "
            "Cùng đọc `Invocations`. Nếu 0, rule chưa nhận event."
        ),
        "youdo": (
            "Tự lọc Event name = `TerminateInstances` trong CloudTrail, mở event mới "
            "nhất, trả lời: ai, lúc nào, từ IP nào. Sau đó kiểm tra SQS có message."
        ),
        "debrief": [
            "Root cause trong 3 câu.",
            "Evidence nào mạnh nhất?",
            "Nếu gặp lại, 3 bước đầu là gì?",
            "Guardrail nào ngăn tái diễn?",
        ],
    },
}

# Full 24-lab data lives in a separate file to keep this module readable.
try:
    from lab_brief_data import BRIEFS as _EXTRA_BRIEFS
except ImportError:  # pragma: no cover
    _EXTRA_BRIEFS = {}
BRIEFS.update(_EXTRA_BRIEFS)


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_lab_env(lid: str) -> dict[str, str]:
    wanted = f"{int(lid):02d}"
    for path in sorted(LABS.iterdir()):
        if path.is_dir() and path.name.startswith(wanted + "-"):
            values: dict[str, str] = {}
            for line in (path / "lab.env").read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    values[key.strip()] = value.strip().strip('"').strip("'")
            return values
    return {}


def generic_brief(lid: str) -> dict:
    """Fallback so `brief` is useful before every lab, not only the pilot."""
    env = read_lab_env(lid)
    title = env.get("LAB_TITLE", f"Lab {lid}")
    needs_app = env.get("NEEDS_APP", "no") == "yes"
    app_line = ("App stack", "soa-c03-app", "CREATE_COMPLETE, /health 200",
                "./bin/lab status") if needs_app else (
                "Core stack", "soa-c03-core", "CREATE_COMPLETE", "./bin/lab status")
    return {
        "title": title,
        "why": f"Lab {lid}: {title}. Đọc mục 1–3 và 5c của README để biết lab này dạy gì.",
        "concepts": [
            ("Khái niệm chính", "Đọc bảng Từ vựng nhanh ở mục 5c của README."),
            ("Baseline", "Trạng thái bình thường trước khi phá: dùng ./bin/lab status và preflight --live."),
            ("Evidence", "Metric, log, event, target health hoặc cấu hình — chọn theo bản đồ bên dưới."),
        ],
        "inventory": [
            app_line,
            ("Core stack", "soa-c03-core", "CREATE_COMPLETE", "./bin/lab status"),
            ("Lab resources", f"soa-c03-lab{lid}-*", "xem README mục 2", "./bin/lab status"),
        ],
        "map": [
            ("Triệu chứng là gì?", "README mục 6–7", "status code, metric, log, event"),
            ("Lớp nào có thể hỏng?", "Chuỗi kiến trúc ở mục 3", "identity → network → compute → data → config"),
            ("Evidence rẻ nhất?", "README mục 7", "target health, /health, log, alarm state"),
            ("Đã đổi gì gần đây?", "CloudTrail / lab change note", "eventName, eventTime, actor"),
        ],
        "predict": [
            "Hệ thống đang có những thành phần nào?",
            "Nếu một thành phần hỏng, triệu chứng người dùng thấy là gì?",
            "Bạn sẽ xem evidence nào đầu tiên? Vì sao?",
        ],
        "announce": f"Fault của lab {lid} sẽ được inject. Xem README mục 2 để biết loại thay đổi; không có đáp án root cause ở đây.",
        "change": f"Fault của lab {lid} đã được inject. Xem README mục 2 để biết loại thay đổi; không có đáp án root cause ở đây.",
        "sealed": "Chi tiết nằm trong scripts/lib/labs.sh (answer key). Chỉ mở sau khi đã thử đủ giả thuyết.",
        "ido": "Chọn một resource lành trong baseline, mở đúng màn hình 5c, đọc một ô bình thường. Đây là mẫu, chưa phải chỗ hỏng.",
        "wedo": "Cùng kiểm tra evidence rẻ nhất trong bản đồ (ví dụ target health hoặc /health).",
        "youdo": "Tự kiểm tra evidence tiếp theo, nói lớp nào đang chặn, rồi mới sửa.",
        "debrief": [
            "Root cause trong 3 câu.",
            "Evidence nào mạnh nhất?",
            "Nếu gặp lại, 3 bước đầu là gì?",
            "Guardrail nào ngăn tái diễn?",
        ],
    }


def require_brief(lid: str) -> dict:
    key = f"{int(lid):02d}"
    if key in BRIEFS:
        data = generic_brief(key)
        data.update(BRIEFS[key])
        return data
    return generic_brief(key)


def markdown_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def render_brief(lid: str) -> str:
    data = require_brief(lid)
    key = f"{int(lid):02d}"
    heading = "## 5d. Brief trước khi phá — đọc trước khi `break`"
    gate = "### Trước khi phá, bạn phải trả lời 3 câu"
    gate_tail = "Trả lời được 3 câu này rồi mới chạy `break`."
    if key == "00":
        heading = "## 5d. Baseline — kiểm tra nền trước khi làm lab khác"
        gate = "### Trước khi làm lab khác, bạn phải trả lời 3 câu"
        gate_tail = "Trả lời được 3 câu này rồi mới chuyển sang lab khác."
    concepts = "\n".join(f"- **{t}**: {d}" for t, d in data["concepts"])
    n_concepts = len(data["concepts"])
    inventory = markdown_table(data["inventory"], ("Thành phần", "Tên thật", "Trạng thái khoẻ", "Xem ở đâu"))
    mapping = markdown_table(data["map"], ("Câu hỏi", "Xem ở đâu", "Đọc gì"))
    predict = "\n".join(f"{i}. {q}" for i, q in enumerate(data["predict"], 1))
    return f"""{heading}

> Mục này để bạn **không mù**: biết hệ thống đang có gì, “bình thường” trông như thế nào,
> và sẽ tìm evidence ở đâu. Không có đáp án root cause ở đây.

**Vì sao có lab này.** {data["why"]}

### Bạn cần biết {n_concepts} khái niệm

{concepts}

### Hệ thống hiện tại (baseline)

{inventory}

### Bản đồ chẩn đoán

{mapping}

{gate}

{predict}

> {gate_tail} Nếu chưa, quay lại mục 5c hoặc hỏi AI.
> Lệnh hỗ trợ: `./bin/lab baseline {lid} --live` và `./bin/lab teach {lid}`.
"""


def render_teach(lid: str) -> str:
    data = require_brief(lid)
    key = f"{int(lid):02d}"
    if key == "00":
        concepts = "\n".join(f"   - {t}: {d}" for t, d in data["concepts"])
        inventory = "\n".join(
            f"   - {c}: {n} — kỳ vọng {h} — xem {w}" for c, n, h, w in data["inventory"]
        )
        return f"""# Teaching script — lab 00: {data["title"]}

> Lab 00 **không có fault**. Đây là baseline check. Không chạy `break`.

## Pha A — Giải thích baseline (10 phút)

{concepts}

Cho người học xem:
{inventory}

## Pha B — Không có fault

Không chạy `break`. Kiểm tra:
- CloudFormation `soa-c03-core` = `CREATE_COMPLETE`.
- CloudTrail `soa-c03-trail` Logging ON.
- S3 bucket private (4 cờ BPA).
- KMS alias `alias/soa-c03-lab` Enabled.
- SSM `/soa-c03/app/port` tồn tại.
- Budget `soa-c03-monthly` tồn tại.

Nếu thiếu: `make bootstrap` (xin phép trước; ~$1–2/tháng).

## Pha C — I do / We do / You do

- **I do:** mở CloudFormation → Outputs, đọc một output.
- **We do:** cùng mở CloudTrail Dashboard, đọc Logging status.
- **You do:** tự kiểm tra S3 BPA + Parameter Store, ghi lại 2 giá trị.

## Pha D — Debrief

- Core stack dùng để làm gì?
- Nếu CloudTrail tắt, mất bằng chứng gì?
- Vì sao phải kiểm tra baseline trước mọi lab?
"""
    predict = "\n".join(f"   {i}. {q}" for i, q in enumerate(data["predict"], 1))
    debrief = "\n".join(f"   {i}. {q}" for i, q in enumerate(data["debrief"], 1))
    concepts = "\n".join(f"   - {t}: {d}" for t, d in data["concepts"])
    inventory = "\n".join(
        f"   - {c}: {n} — kỳ vọng {h} — xem {w}" for c, n, h, w in data["inventory"]
    )
    n_concepts = len(data["concepts"])
    return f"""# Teaching script — lab {lid}: {data["title"]}

> Dùng cho AI mentor. Không đọc nguyên file này cho người học; đi từng lượt.

## Pha A — Brief (10–15 phút)

A1. Giải thích {n_concepts} khái niệm (mỗi lần 1 cái, kèm ví dụ đời thường):
{concepts}

A2. Cho người học xem baseline (màn hình thật):
{inventory}

A3. Vẽ bản đồ chẩn đoán, hỏi họ chọn evidence đầu tiên. Không nói lớp nào hỏng.

A4. Hỏi 3 câu dự đoán:
{predict}

A5. **Gate:** người học trả lời được 3 câu + giải thích sơ đồ bằng lời của họ.
    Nếu chưa, dạy lại; không `break`.
    Nếu đạt: `./bin/lab brief {lid} --confirm`.

## Pha B — Break (2 phút)

Nói trước khi phá:

```text
Mình sẽ phá: {data["announce"]}
Mình không nói ai làm — đó là phần bạn tìm.
Thời điểm: <UTC>.
```

Sau đó chạy `ALLOW_BREAK=yes CONFIRM_BREAK=yes ./bin/lab break {lid}`.
Ghi lại thời điểm bằng `./bin/lab change {lid}`.

## Pha C — Chẩn đoán (I do → We do → You do)

### I do — AI làm mẫu trên ví dụ lành

{data["ido"]}

### We do — cùng kiểm tra một evidence

{data["wedo"]}

### You do — người học tự làm

{data["youdo"]}

AI chỉ hỏi, không chỉ màn hình nếu người học đã biết. Không nói root cause.

## Pha D — Debrief (10 phút)

Hỏi lần lượt:
{debrief}

Sau đó yêu cầu note có thêm:
- **Baseline trước break** (3 giá trị quan trọng).
- **Thay đổi gì** (loại thay đổi, thời điểm).
- **Evidence mạnh nhất**.
"""


def aws_json(*args: str, timeout: int = 20):
    try:
        proc = subprocess.run(
            ["aws", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout.strip()


def output_value(stack: str, key: str) -> str | None:
    data = aws_json("cloudformation", "describe-stacks", "--stack-name", stack,
                    "--query", f"Stacks[0].Outputs[?OutputKey=='{key}'].OutputValue | [0]")
    return data if isinstance(data, str) else None


def generic_live_baseline(lid: str, env: dict[str, str]) -> int:
    """Read-only baseline for labs without a bespoke checker (all except 03)."""
    prefix = env.get("LAB_PREFIX", "soa-c03")
    print(f"# Baseline live — lab {lid} (generic)")
    print(f"# region={env.get('AWS_REGION', 'ap-southeast-1')} account={env.get('LAB_ACCOUNT_ID', '?')}")
    print("")

    ident = aws_json("sts", "get-caller-identity", "--query", "[Account,Arn]")
    if ident is None:
        print("FAIL không gọi được sts:get-caller-identity (credentials?)")
        return 1
    print(f"identity: {ident[0]}  {ident[1]}")
    if env.get("LAB_ACCOUNT_ID") and ident[0] != env["LAB_ACCOUNT_ID"]:
        print("FAIL account không khớp .env")
        return 1

    core = aws_json("cloudformation", "describe-stacks", "--stack-name", "soa-c03-core",
                    "--query", "Stacks[0].StackStatus")
    print(f"core stack: {core or 'MISSING'}")
    if core not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
        print("FAIL core stack chưa healthy; không nên up lab")
        return 1

    lab_env = read_lab_env(lid)
    needs_app = lab_env.get("NEEDS_APP") == "yes"
    rows: list[tuple[str, str, str, str]] = []

    trail = output_value("soa-c03-core", "TrailName")
    trail_ok = False
    if trail:
        trail_ok = aws_json("cloudtrail", "get-trail-status", "--name", trail,
                            "--query", "IsLogging") is True
    rows.append(("CloudTrail", trail or "?", "Logging ON", "OK" if trail_ok else "WARN"))

    bucket = output_value("soa-c03-core", "DataBucketName")
    bpa = None
    if bucket:
        bpa = aws_json("s3api", "get-public-access-block", "--bucket", bucket,
                       "--query", "PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]")
    bpa_ok = isinstance(bpa, list) and all(bpa)
    rows.append(("S3 Block Public Access", str(bpa) if bpa else "?", "4 cờ true",
                 "OK" if bpa_ok else "WARN"))

    key_id = output_value("soa-c03-core", "KmsKeyId")
    key_state = None
    if key_id:
        key_state = aws_json("kms", "describe-key", "--key-id", key_id,
                             "--query", "KeyMetadata.KeyState")
    rows.append(("KMS key", key_state or "?", "Enabled",
                 "OK" if key_state == "Enabled" else "WARN"))

    port_param = f"/{prefix}/app/port"
    param = aws_json("ssm", "get-parameter", "--name", port_param, "--query", "Parameter.Value")
    rows.append(("SSM parameter", port_param, "tồn tại", "OK" if param else "WARN"))

    budget = aws_json("budgets", "describe-budget",
                      "--account-id", env.get("LAB_ACCOUNT_ID", ""),
                      "--budget-name", f"{prefix}-monthly",
                      "--query", "Budget.BudgetName")
    rows.append(("Budget", f"{prefix}-monthly", "tồn tại", "OK" if budget else "WARN"))

    app = aws_json("cloudformation", "describe-stacks", "--stack-name", "soa-c03-app",
                   "--query", "Stacks[0].StackStatus")
    if app in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
        dns = output_value("soa-c03-app", "AlbDnsName")
        code = "?"
        if dns:
            try:
                code = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                     "--max-time", "8", f"http://{dns}/health"],
                    capture_output=True, text=True, timeout=12,
                ).stdout.strip()
            except (OSError, subprocess.TimeoutExpired):
                code = "?"
        tg = output_value("soa-c03-app", "TargetGroupArn")
        healthy = "?"
        if tg:
            raw = aws_json("elbv2", "describe-target-health", "--target-group-arn", tg,
                           "--query", "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])")
            healthy = str(raw) if raw is not None else "?"
        ok = code == "200" and healthy not in ("0", "?")
        rows.append(("App /health", f"{code}, healthy targets={healthy}",
                     "200, >=1", "OK" if ok else "WARN"))
    else:
        rows.append(("App stack", app or "MISSING", "chỉ cần nếu NEEDS_APP=yes",
                     "OK" if not needs_app else "FAIL"))

    alarms = aws_json("cloudwatch", "describe-alarms", "--alarm-name-prefix",
                      f"{prefix}-lab{lid}", "--query", "MetricAlarms[].[AlarmName,StateValue]")
    rows.append(("Alarms lab" + lid, str(len(alarms)) if alarms else "0",
                 "theo brief", "info"))

    queues = aws_json("sqs", "list-queues", "--queue-name-prefix", f"{prefix}-lab{lid}",
                      "--query", "QueueUrls")
    nq = len(queues.get("QueueUrls", [])) if isinstance(queues, dict) else 0
    rows.append(("SQS lab" + lid, str(nq), "theo brief", "info"))

    rules = aws_json("events", "list-rules", "--name-prefix", f"{prefix}-lab{lid}",
                     "--query", "Rules[].[Name,State]")
    rows.append(("EventBridge lab" + lid, str(len(rules)) if rules else "0",
                 "theo brief", "info"))

    instances = aws_json("ec2", "describe-instances",
                         "--filters", f"Name=tag:Project,Values={prefix}",
                         "Name=instance-state-name,Values=pending,running,stopping,stopped",
                         "--query", "Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key=='Name'].Value|[0]]")
    if instances:
        named = [f"{i} ({s})" for i, s, n in instances if n and f"lab{lid}" in n]
    else:
        named = []
    rows.append(("EC2 lab" + lid, ", ".join(named) if named else "0",
                 "theo brief", "info"))

    groups = aws_json("logs", "describe-log-groups", "--log-group-name-prefix", "/aws/",
                      "--query", "logGroups[].logGroupName")
    lab_groups = [g for g in groups if f"lab{lid}" in g] if groups else []
    rows.append(("Log groups lab" + lid, str(len(lab_groups)), "theo brief", "info"))

    clusters = aws_json("ecs", "list-clusters", "--query", "clusterArns")
    lab_clusters = [c for c in clusters if f"lab{lid}" in c] if clusters else []
    rows.append(("ECS clusters lab" + lid, str(len(lab_clusters)), "theo brief", "info"))

    plans = aws_json("backup", "list-backup-plans", "--query", "BackupPlansList[].BackupPlanName")
    lab_plans = [p for p in plans if f"lab{lid}" in p] if plans else []
    rows.append(("Backup plans lab" + lid, str(len(lab_plans)), "theo brief", "info"))

    roles = aws_json("iam", "list-roles", "--query", "Roles[].RoleName")
    lab_roles = [r for r in roles if f"lab{lid}" in r] if roles else []
    rows.append(("IAM roles lab" + lid, str(len(lab_roles)), "theo brief", "info"))

    dbs = aws_json("rds", "describe-db-instances",
                   "--query", "DBInstances[].[DBInstanceIdentifier,DBInstanceStatus]")
    lab_dbs = [f"{i} ({s})" for i, s in dbs if f"lab{lid}" in i] if dbs else []
    rows.append(("RDS lab" + lid, ", ".join(lab_dbs) if lab_dbs else "0",
                 "theo brief", "info"))

    eps = aws_json("ec2", "describe-vpc-endpoints", "--filters", f"Name=tag:Lab,Values=lab{lid}",
                   "--query", "VpcEndpoints[].[VpcEndpointId,State]")
    rows.append(("VPC endpoints lab" + lid, str(len(eps)) if eps else "0",
                 "theo brief", "info"))

    print("")
    print(markdown_table(rows, ("Thành phần", "Giá trị thực", "Kỳ vọng", "Kết quả")))
    print("")
    print("Đây là baseline generic. Bảng inventory chi tiết nằm trong `./bin/lab brief", lid + "`.")
    print("Nếu app/core FAIL: dừng, sửa baseline trước khi break.")
    print("Nếu các dòng lab là 0: có thể lab chưa `up`, hoặc lab không tạo resource riêng.")
    return 0


def live_baseline(lid: str) -> int:
    env = load_env()
    prefix = env.get("LAB_PREFIX", "soa-c03")
    key = f"{int(lid):02d}"
    if key != "03":
        return generic_live_baseline(key, env)
    data = require_brief(lid)
    print(f"# Baseline live — lab {lid}")
    print(f"# region={env.get('AWS_REGION', 'ap-southeast-1')} account={env.get('LAB_ACCOUNT_ID', '?')}")
    print("")

    ident = aws_json("sts", "get-caller-identity", "--query", "[Account,Arn]")
    if ident is None:
        print("FAIL không gọi được sts:get-caller-identity (credentials?)")
        return 1
    print(f"identity: {ident[0]}  {ident[1]}")
    if env.get("LAB_ACCOUNT_ID") and ident[0] != env["LAB_ACCOUNT_ID"]:
        print("FAIL account không khớp .env")
        return 1

    core = aws_json("cloudformation", "describe-stacks", "--stack-name", "soa-c03-core",
                    "--query", "Stacks[0].StackStatus")
    print(f"core stack: {core or 'MISSING'}")
    if core not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
        print("FAIL core stack chưa healthy; không nên up lab")
        return 1

    checks: list[tuple[str, str, str, str]] = []

    trail = output_value("soa-c03-core", "TrailName")
    if trail:
        status = aws_json("cloudtrail", "get-trail-status", "--name", trail,
                          "--query", "IsLogging")
        ok = status is True
        checks.append(("CloudTrail", trail, "Logging ON", "OK" if ok else "WARN"))
    else:
        checks.append(("CloudTrail", "?", "Logging ON", "FAIL"))

    raw = aws_json("ec2", "describe-instances",
                   "--filters", f"Name=tag:Name,Values={prefix}-lab03-canary",
                   "Name=instance-state-name,Values=pending,running,stopping,stopped",
                   "--query", "Reservations[].Instances[].[InstanceId,State.Name]")
    if raw:
        states = ", ".join(f"{i}={s}" for i, s in raw)
        checks.append(("Canary EC2", f"{prefix}-lab03-canary", "running",
                       "OK" if any(s == "running" for _, s in raw) else "WARN",))
        print(f"  canary: {states}")
    else:
        checks.append(("Canary EC2", f"{prefix}-lab03-canary", "running", "FAIL (chưa up 03?)"))

    rule = aws_json("events", "describe-rule", "--name", f"{prefix}-lab03-ec2-state",
                    "--query", "[State,Arn]")
    checks.append(("EventBridge rule", f"{prefix}-lab03-ec2-state", "ENABLED",
                   "OK" if rule and rule[0] == "ENABLED" else "FAIL (chưa up 03?)"))
    if rule:
        targets = aws_json("events", "list-targets-by-rule",
                           "--rule", f"{prefix}-lab03-ec2-state",
                           "--query", "Targets | length(@)")
        checks.append(("EventBridge targets", f"{prefix}-lab03-ec2-state", "1 target",
                       "OK" if targets == 1 else f"WARN ({targets})"))

    qurl = aws_json("sqs", "get-queue-url", "--queue-name", f"{prefix}-lab03-events",
                    "--query", "QueueUrl")
    if qurl:
        attrs = aws_json("sqs", "get-queue-attributes", "--queue-url", qurl,
                         "--attribute-names", "ApproximateNumberOfMessages")
        count = attrs.get("Attributes", {}).get("ApproximateNumberOfMessages", "?") if attrs else "?"
        checks.append(("SQS", f"{prefix}-lab03-events", "0 message", f"OK ({count} message)"))
    else:
        checks.append(("SQS", f"{prefix}-lab03-events", "0 message", "FAIL (chưa up 03?)"))

    role = aws_json("iam", "get-role", "--role-name", f"{prefix}-lab-operator",
                    "--query", "Role.RoleName")
    checks.append(("IAM role", f"{prefix}-lab-operator", "tồn tại",
                   "OK" if role else "FAIL"))

    print("")
    print(markdown_table([(a, b, c, d) for a, b, c, d in checks],
                         ("Thành phần", "Tên thật", "Kỳ vọng", "Kết quả")))
    print("")
    print("Nếu có FAIL: chạy `./bin/lab up 03` (sau khi được phép), rồi baseline lại.")
    print("Nếu tất cả OK: đây là baseline để so sánh sau khi break.")
    return 0


def record_change(lid: str) -> int:
    data = require_brief(lid)
    var = ROOT / "var"
    var.mkdir(exist_ok=True)
    path = var / f"lab{int(lid):02d}-change.md"
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(
        f"time={now}\n"
        f"change={data['change']}\n"
        f"sealed={data['sealed']}\n"
    )
    print(f"change note: {path.relative_to(ROOT)}")
    return 0


def show_change(lid: str, sealed: bool) -> int:
    path = ROOT / "var" / f"lab{int(lid):02d}-change.md"
    if not path.exists():
        print("Chưa có change note. Chạy `./bin/lab break <id>` trước.")
        return 1
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    print(f"Thời điểm: {values.get('time', '?')}")
    print(f"Thay đổi:  {values.get('change', '?')}")
    if sealed:
        print(f"Sealed:    {values.get('sealed', '?')}")
    else:
        print("(Chi tiết ai làm được giữ kín. Dùng --sealed khi đã thử đủ giả thuyết.)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=[
        "brief", "baseline", "teach", "change", "record-change",
    ])
    parser.add_argument("lab", help="lab id, e.g. 03")
    parser.add_argument("--live", action="store_true", help="read-only AWS baseline")
    parser.add_argument("--sealed", action="store_true", help="show the sealed detail")
    args = parser.parse_args()

    if args.command == "brief":
        print(render_brief(args.lab))
        return 0
    if args.command == "teach":
        print(render_teach(args.lab))
        return 0
    if args.command == "baseline":
        if args.live:
            return live_baseline(args.lab)
        print(render_brief(args.lab).split("### Hệ thống hiện tại (baseline)", 1)[0])
        print("### Hệ thống hiện tại (baseline)\n")
        data = require_brief(args.lab)
        print(markdown_table(data["inventory"],
                             ("Thành phần", "Tên thật", "Trạng thái khoẻ", "Xem ở đâu")))
        print("\nDùng `--live` để đọc giá trị thật từ AWS (read-only).")
        return 0
    if args.command == "change":
        return show_change(args.lab, args.sealed)
    if args.command == "record-change":
        return record_change(args.lab)
    return 1


if __name__ == "__main__":
    sys.exit(main())
