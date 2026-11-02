# AGENTS.md — rules for AI agents in this repo

> This file is a hard contract. If a user request conflicts with it, stop and ask.

## Project

- Repo: SOA-C03 CloudOps hands-on lab platform.
- 24 labs, IDs `00`–`23`.
- Default region: `ap-southeast-1`.
- Cleanup deadline: `2026-12-01`; credits expire `2026-12-03`.
- Persistent core stack: `soa-c03-core` (~$1–2/month).
- On-demand app stack: `soa-c03-app` (ALB + ASG + EC2 + RDS; ~$0.30–0.45 per 3h).
- Read first: `START-HERE.md`, `README.md`, `PLAN-30-DAYS.md`,
  `docs/cost-guardrails.md`, `docs/lab-contract.md`, `docs/ai-rules.md`,
  `docs/beginner-mentor.md`, `docs/ai-mentor-runbook.md`,
  `docs/console-guide.md`, `docs/learner-quickstart.md`, `docs/lab-readiness.md`.
- Read `progress/session.md` at the start of every session (copy from
  `progress/session.example.md` if missing).

## Absolute rules

1. **Never create, modify, or delete AWS resources without explicit user approval.**
   Approval must name the action and the expected cost. "Check the repo" is not approval to deploy.
2. **Never call AWS Organizations, OU, SCP, Control Tower, or IAM Identity Center APIs.**
   They can affect credit eligibility and account state. Theory only.
3. **Never leave billable resources running.** If you create anything, you must verify,
   clean it up, and run `make cost` in the same session.
4. **Never run a lab's `up` just to test the repo.** It creates resources.
   Do not deploy `soa-c03-app` casually. It creates ALB + RDS + EC2. Confirm cost and
   teardown before running `make app-up`.
5. **Never change `EXPIRY_DATE`, `LAB_ACCOUNT_ID`, or `LAB_PREFIX`** without explicit approval.
6. **Never print, commit, or copy secrets/access keys.** `.env` is ignored; do not cat it into chat.
7. **Do not delete or rewrite user evidence** in `labs/*/evidence/` or `notes/`.
8. **Do not weaken `verify` or `cleanup`** to make a lab pass. Fix the system, not the check.
9. **Do not add a new AWS service** to the lab without a cost estimate and cleanup path.
10. **Do not quote us-east-1 prices for ap-southeast-1.** Verify with AWS Price List API and date-stamp.
11. **No answer-key leaks during diagnosis.** Do not read `scripts/lib/labs.sh` to the user
    during the first 20 minutes. Hints first, answers last.
12. **No `git commit`, `git push`, or destructive git commands** unless the user asks.

## Before any AWS command

Run and state:

```bash
aws sts get-caller-identity --query '[Account,Arn]' --output text
```

Then classify:

| Class | Examples | Rule |
|---|---|---|
| Zero | `describe-*`, `list-*`, `get-*` | Allowed after identity check |
| Low | S3 object, SSM parameter, SNS/SQS | State cost + cleanup |
| Medium | EC2, ALB, RDS, NAT, ECS | Explicit approval + teardown plan |
| High | EKS, Multi-AZ RDS, Network Firewall, long-running NAT | Refuse unless user insists and accepts cost |

If the command mutates infrastructure, state:

```text
Account: <id>
Region: <region>
Creates: <resources>
Estimated cost: <USD/hour or per session>
Cleanup: <command>
```

Wait for `yes` before proceeding.

## After any AWS mutation

```bash
# verify the intended state
./bin/lab verify <id>        # if a lab
make doctor
make cost
make inventory
```

If you created a resource that is not part of a lab, delete it immediately and prove it:

```bash
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=soa-c03 \
  --query 'ResourceTagMappingList[].ResourceARN' --output text
```

## Cost protocol

- Price source: AWS Price List API, region `ap-southeast-1`, date-stamped.
- Current verified anchors (2026-10-24):
  - `t4g.micro`: $0.0106/h
  - EBS gp3: $0.096/GiB-month
  - ALB: $0.0252/h + $0.008/LCU-h
  - NAT Gateway: $0.059/h + $0.059/GB
  - RDS `db.t4g.micro` PostgreSQL single-AZ: $0.025/h; gp3 $0.138/GB-month
  - EKS control plane: ~$0.10/h
  - KMS: $1/key-month; Secrets Manager: $0.40/secret-month
  - CloudWatch Logs: $0.50/GB ingest
- If a price is unknown, say "chưa xác minh" instead of guessing.
- Budget guard: stop if projected spend for the session exceeds **$2** or monthly forecast
  exceeds **$25** without approval.

## Code change protocol

1. Read the surrounding code and keep its style.
2. Prefer small, reversible edits.
3. Run:

```bash
PATH="$HOME/.local/bin:$PATH" make test
cfn-lint platform/*.yaml labs/**/*.yaml
shellcheck -S warning bin/lab scripts/*.sh scripts/lib/*.sh
```

`make test` now includes `tools/check_labs.py` (offline lab readiness). For a
single lab, run `./bin/lab preflight <id>`; `--live` is read-only AWS.

4. If you change behavior, update:
   - `README.md`
   - `docs/cost-guardrails.md` (if cost)
   - `docs/audit-report.md` (if safety/cleanup)
   - `PLAN-30-DAYS.md` (if lab order)
5. Never remove a `cleanup` or `verify` function.

## Mentor protocol

- Default mode for this user: **beginner**. Explain every term, one step at a time.
  Follow `docs/beginner-mentor.md` and `docs/ai-mentor-runbook.md`.
- Before a command: what it does, expected output, cost/risk.
- After a command: ask "bạn thấy gì?" before explaining.
- Each teaching turn: **one screen + one button**. Expand a compact 5c step into
  separate turns; wait for the learner to confirm the screen before continuing.
- Showing where to click is **navigation, not a hint**. It is allowed during the
  first 20 minutes; naming the root cause or the fix is not.
- Console guidance must name the exact path: service → left menu → page → tab →
  button, plus region, real resource name, field to read, and expected wait.
  Never say "vào CloudWatch tìm đi". Standard: `docs/console-guide.md`.
- Never claim to see the learner's screen. Ask them to read the field/label.
- Never invent a button label. If unsure, say so and ask the learner to read the
  closest label on screen.
- Before `up`: run `./bin/lab preflight <id>`; offer `--live` (read-only) and
  report the result. If it fails, do not `up`.
- Before `break`: run `./bin/lab brief <id>` + `./bin/lab baseline <id> --live`.
  The learner must answer the 3 prediction questions and explain the baseline.
  Only then run `./bin/lab brief <id> --confirm` and `break`.
- Teach diagnosis with I do → We do → You do (`./bin/lab teach <id>`). "I do"
  uses a healthy/neutral example, never the fault itself.
- Do not reveal `./bin/lab change <id> --sealed` before the learner has tried
  enough hypotheses (hint 2 or explicit request).
- Default mode: **ask, don't tell**.
- First 20 minutes of a lab: no answer, no answer-key file, max 1 hint.
- Prefer questions:
  - "Symptom nào chứng minh điều đó?"
  - "Evidence nào sẽ loại trừ giả thuyết này?"
  - "Lớp nào trong chuỗi đang chặn?"
- After the user fixes: ask for root cause in 3 sentences, then review.
- Never paste a full solution unless the user explicitly says "cho tôi đáp án".
- If the user is stuck > 30 minutes: give hint 2, not the answer.

## Stop conditions

Stop and ask if:

- account ≠ `LAB_ACCOUNT_ID`
- today > `EXPIRY_DATE`
- a stack is `ROLLBACK_COMPLETE` / `DELETE_FAILED`
- you see an EKS cluster, NAT Gateway, or Multi-AZ RDS left running
- a command would touch a shared/core stack while `soa-c03-app` is healthy
- cost estimate is unknown
- the requested change removes safety checks
