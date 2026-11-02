# Audit report — 2026-10-23

## Scope

- 24 lab, numbering 00–23.
- CloudFormation: `platform/core.yaml`, `platform/app.yaml`, Lab 11 templates.
- Bash: `bin/lab`, `scripts/*.sh`, `scripts/lib/*.sh`.
- Docs: README, PLAN, exam map, cost guardrails, troubleshooting.
- Safety: no AWS Organizations / OU / SCP / Control Tower / IAM Identity Center APIs.

## Checks run

| Check | Result |
|---|---|
| `make test` (bash `-n`, Python compile, YAML parse, manifests) | PASS |
| `cfn-lint` on all templates | PASS |
| `aws cloudformation validate-template` core + app | PASS |
| `shellcheck -S warning` all shell scripts | PASS |
| Local Markdown link check | 0 broken |
| Lab ID ↔ directory ↔ function mapping | 24/24 |
| `./bin/lab list`, `hint` for 00–23 | PASS |
| `aws organizations` API calls | 0 |
| Old lab-number references | 0 |
| `.env` / `var/` / `events.jsonl` ignored | PASS |
| Cost anchors verified with AWS Price List API (`ap-southeast-1`, 2026-10-24) | PASS |
| Legacy 6-week files removed / links fixed | PASS |
| AI rules present (`AGENTS.md`, `docs/ai-rules.md`) | PASS |

## Re-audit 2026-10-25

- Found a real initialization bug: EC2 user-data ran `pip3 install` into system
  Python, breaking AWS CLI v2 (`dateutil`), so a newly scaled instance could not
  download the app. Fixed by using `/opt/cloudops/venv` and launching the service
  with the venv Python.
- Lab 01 now suspends ASG `AlarmNotification` while CPU load runs, so a monitoring
  lab does not create extra instances or leave the `unhealthy-hosts` alarm.
- Caught a second initialization mismatch: the service file used
  `/opt/cloudops/venv/bin/python`, but the template user-data still ran `pip3 install`
  and never created the venv. The instance started, could not run the app, and the
  target was unhealthy. Fixed by creating the venv in user-data and installing
  `boto3`/`pg8000` there.
- Existing app stack from before the fix needs another `make app-up` (or
  `make app-down` + `make app-up`) so a new launch template version replaces the bad
  instance. Not run automatically; requires user approval.
- All 24 lab READMEs rewritten for beginners: purpose, current state, architecture,
  symptom, where to look, success criteria, exam takeaway, note, cleanup.
- Added `docs/beginner-mentor.md` and wired beginner mode into `START-HERE.md`,
  `AGENTS.md`, and `docs/ai-rules.md`.

### Verify/metric bugs found while running lab 02 (same day)

Found by actually running the lab, not by reading the code. `verify 02` failed three
times for reasons unrelated to the learner's diagnosis.

1. **Crash `None: unbound variable`.** AWS CLI prints `None` when a Logs Insights query
   has no result row yet. That string went straight into `[[ -ge ]]` under `set -u`.
   Fixed: strip to digits, default `0`.
2. **`count` always 0.** JMESPath `results[0][?field=="errors"].value` treats `"errors"`
   as a *quoted identifier* (a field name), not a string literal, so it always filtered
   to `[]`. Fixed: `results[0][0].value` (`stats count()` returns one row/cell).
3. **`metric_sum` / `metric_max` read only the first datapoint.** `--query 'Datapoints[].Sum'
   --output text` prints every datapoint on one tab-separated line; the awk used `$1`.
   Any lab with more than one datapoint read 0 (lab 01, 04, 20, 22). Fixed: scan all fields.
4. **Unaligned metric window.** `--start-time` carried seconds, and CloudWatch starts its
   buckets at the exact start time, so datapoints sitting on a minute boundary (metric
   filters) fell between buckets and vanished. Fixed: truncate start/end to `:00`.
5. **Racy alarm check.** A metric-filter alarm with `defaultValue=0` republishes 0 every
   period and returns to `OK` ~60 s after the burst, so an instantaneous
   `describe-alarms` read almost always saw `OK`. `verify 02` now accepts `ALARM` now
   **or** an `OK -> ALARM` transition in the last 30 minutes (`alarm_fired_within`).
   Thresholds are unchanged: >= 10 ERROR logs, >= 5 metric, alarm must actually fire.
6. **Window shorter than the lab contract.** `verify 02` looked back 15 minutes while
   `START-HERE.md` gives 20 minutes of blind diagnosis, so a correct run aged out.
   Widened to 30 minutes for lab 02 only.

`make test` passes after all six fixes. `shellcheck` and `cfn-lint` are not installed on
this machine, so `make test` skips them.

### Verify bug found while running lab 03 (2026-10-26)

7. **Window shorter than the lab contract, again.** `verify 03` looked back only 30
   minutes for the CloudTrail `TerminateInstances` event, but lab 03 is 150 minutes and
   the learner spent 36 minutes between `break` and `verify`. The event existed (the
   learner had already read it in Event history) yet verify reported
   `no TerminateInstances event for i-...` and burned 5 minutes in the retry loop.
   Fixed: `--start-time` widened to 12 hours, with a comment tying the window to the lab
   contract. Checks are unchanged: the event must still match the canary instance ID, the
   actor must still be `AssumedRole`, and `sourceIPAddress` must still be present.

`verify 03` PASS after the fix (`CloudTrail: arn:aws:sts::...:assumed-role/soa-c03-lab-operator/lab03-break from 183.80.57.52`).

### Lab doc gap found while running lab 05 (2026-10-28)

Learner ran lab 05 end-to-end (verify PASS at `07:12:10Z`, 17 minutes, 0 hints) and hit
two places where the repo's description does not match live behaviour.

8. **README promises 503, the lab produces 200/502.** `labs/05-alb-health-503/README.md`
   mục 6 says "Trình duyệt/curl nhận 503". After `break 05` (health check path →
   `/does-not-exist`) the target group held **one** target. `describe-target-health`
   reported `unhealthy` / `Target.ResponseCodeMismatch` / `Health checks failed with
   these codes: [404]`, but client requests still got `200` (target still serving) and
   later `502` (target terminating) — never `503`. With every target unhealthy, the ALB
   fail-open path keeps sending traffic, so `503` only appears when the target group has
   more than one target and none is healthy. The learner's first 10 minutes were spent
   asking "why 200 and 502, not 503?", which is the wrong question for the fault being
   taught. Not fixed yet — needs a decision: either reword mục 6 to describe fail-open
   and the 200/502 signature, or raise the lab's ASG `MinSize` to 2 so a real 503 shows.

9. **`soa-c03-unhealthy-hosts` fires too late to be a guardrail.** Timeline observed with
   `describe-alarm-history`: first `UnHealthyHostCount = 1` datapoint at `13:53`,
   ASG `TerminateInstance` at `13:54:57` ("in response to an ELB system health check
   failure"), alarm `OK → ALARM` at `13:56:29`. The alarm lags the ASG replacement by
   ~1.5 minutes, so the SNS email is a notification, not a guardrail. It also fired twice
   in one session (13:44:29 while targets were still starting, 13:56:29 for the real
   fault), which is alert-fatigue material. Suggested: shorten `Period` / raise
   `EvaluationPeriods` explicitly for this alarm and document it in mục 9 as the
   "detection is slower than remediation" exam point. Kept as-is for now; no check
   weakened.

### Lab 06 runtime defect found on first run (2026-10-30)

First real `break 06` (app stack up 23:20, break 23:30) exposed two defects that make
`verify 06` impossible to pass. The lab had never been run at runtime (`labs/06-*/evidence/`
was empty; this file's "Verification" section records "Not run: `up` for all 24 labs").

10. **The app stack's own CPU TargetTracking policy undoes the lab.** `soa-c03-asg` has
    `soa-c03-app-CpuTargetTrackingPolicy-*` (`ASGAverageCPUUtilization`, target 50,
    `DisableScaleIn=false`, Min 1, Max 2). `break 06` sets desired 2, but the policy's
    `AlarmLow` fired 9 minutes later (16:39:36Z) and scaled back to 1. Because the default
    termination policy prefers the instance on the *oldest* launch template, it removed
    the only healthy instance (version 1) and left the broken `$Latest` one, so the ASG
    then churned a replacement every ~12 minutes (16:41, 16:53, 17:05) and the app stayed
    down. Fixed: `lab06_break` now runs
    `suspend-processes --scaling-processes AlarmNotification` before changing the template,
    and `lab06_build`/`lab06_reset` resume it. Documented in README mục 5b.

11. **`verify 06` required an activity that bad user-data cannot produce.** The check
    counted `Activities[?StatusCode=='Failed']`, but a failing user-data script does not
    fail the launch API: the instance starts, then fails the ELB health check, and the ASG
    records `Successful` launch/terminate pairs with `Cause = "... ELB system health check
    failure"`. All 20 most recent activities were `Successful`. Fixed: the check now counts
    `StatusCode=='Failed'` **or** `contains(Cause, 'ELB system health check failure')`
    (`--max-items 50`), which is the real signature of a failed scale-out here. The other
    three conditions (desired 2, 2 healthy, original template version) are unchanged, so
    the check is not relaxed. README mục 0 and mục 8 reworded to match.

### Lab 07 run (2026-10-31 00:26 → 01:5x +07): doc + tooling gaps

Learner ran lab 07 end-to-end (verify PASS `18:35:40Z`, 0 hints, AI wrote the note on
explicit request). Three mismatches between repo docs/tooling and live behaviour:

12. **README 5c bước 9 is not runnable as written.** The step says "Từ app instance qua
    SSM, chạy `psql`". Following mục 5b style, the natural next command is
    `aws rds describe-db-instances` from that instance — which fails with
    `AccessDenied ... not authorized to perform: rds:DescribeDBInstances`. That is correct
    by design (`soa-c03-app-instance` only has secret/SSM read), but the README never says
    the endpoint must come from the console. The learner lost ~5 minutes on it and
    `psql -h ""` fell back to the local unix socket
    (`connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed`).
    Suggested: in 5c bước 9 and 5b, state "lấy Endpoint ở tab Connectivity & security của
    `soa-c03-lab07-restored`; role của app instance không có `rds:Describe*`", and add the
    `psql -h ""` symptom to the troubleshooting table.

13. **`./bin/lab preflight 07 --live` false-positive "Elastic IPs: 2".** With the app stack
    up, `describe-addresses` returns the two public IPv4 addresses of the public ALB
    (`eni-...` described as `ELB app/soa-c03-alb/...`), so the expensive-leftover check
    warns while `make cost` correctly reports `Elastic IPs: 0`. Not a cost risk (ALB public
    IPv4 is part of ALB pricing), but it trains the learner to ignore a WARN. Suggested:
    filter on `Association.InstanceId` / tag instead of counting every address.

14. **"Estimated monthly costs" does not exist on the Restore-snapshot page.** The mentor
    runbook standard ("read the cost field yourself") cannot be used for lab 07: the
    restore page has no cost estimate (only *Create database* has it). Suggested: 5c should
    say the per-hour figure (`db.t4g.micro` $0.025/h + gp3 20 GB ~$0.004/h) and point to
    `make cost` as the only control.

Leftover after cleanup (unchanged pattern): two automated RDS snapshots created by deletion
(`rds:soa-c03-db-2026-10-30-17-35`, `rds:soa-c03-lab07-restored-2026-10-30-18-24`, 20 GB
each). AWS refuses manual deletion; they expire with the instance's backup retention
(default 7 days → ~2026-11-06). If they survive a month they are worth ~$3.8/month.

### Lab 08 run (2026-10-31 17:29Z → 18:5xZ): one real bug + two doc gaps

Learner ran lab 08 end-to-end (verify PASS `18:14:14Z`, 0 hints, RTO 12s measured,
AI wrote the note on explicit request). App stack was kept up; `down 08` returned the DB
to `MultiAZ=False` at 18:30Z.

15. **`./bin/lab up 08` prints "OK lab 08 is ready" before Multi-AZ is applied.** The
    command returned while RDS was still in the request-accepted state:

    ```text
    Status=modifying  MultiAZ=false  PendingModifiedValues.MultiAZ=true
    event 17:41:19Z "Applying modification to convert to a Multi-AZ DB Instance"
    ```

    Multi-AZ actually became `true` at 17:47:21Z and `available` at 17:49:24Z — ~8 minutes
    after the "ready" line. A learner who runs `./bin/lab verify 08` right after `up 08`
    gets a FAIL (`MultiAZ=False`) and may "fix" a non-problem. The wait loop appears to
    poll the modification-*requested* state instead of `MultiAZ == true && status ==
    available`. Fix: wait on those two fields, and print the elapsed time.

16. **Console CloudWatch: searching `soa-c03-alb` matches deleted load balancers.** The
    account has 9 historical ALBs with the same name prefix, so `ApplicationELB → Per
    AppELB Metrics` + search returns 11 series and an unreadable graph. The learner must
    filter on the exact dimension
    `LoadBalancer = app/soa-c03-alb/e0ebbd2efe1dc5c9` (visible in
    `aws elbv2 describe-load-balancers`). Suggested: add a 5c note, or prefer the CLI:

    ```bash
    aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB \
      --metric-name HTTPCode_Target_5XX_Count \
      --dimensions Name=LoadBalancer,Value=app/soa-c03-alb/<suffix> \
      --start-time ... --end-time ... --period 60 --statistics Sum
    ```

17. **The lab's own lesson is about a blind alarm — worth stating explicitly.** The stack
    ships `soa-c03-alb-5xx` on `HTTPCode_ELB_5XX_Count` (threshold 5, 60s). During the
    measured failover that metric was **0** and the app emitted **4** × `503`
    (`HTTPCode_Target_5XX_Count = 4`), so the alarm could not fire for two independent
    reasons: wrong metric, and threshold above the observed count. This is excellent
    SOA-C03 material but the README/exam-takeaway never mentions it. Suggested: add to
    mục 9 "`ELB_5XX` vs `Target_5XX`: ai sinh lỗi" and to mục 6, and consider pointing the
    existing alarm at `Target_5XX` (cost: one more alarm, $0.10/month).

18. **First `./bin/lab up 10` fails: `MalformedPolicyDocumentException … invalid principals`.**
    Observed 2026-11-02 07:48:37Z. `lab10_build` creates `soa-c03-lab10-reader` and
    immediately puts a KMS key policy that names it as a principal. IAM is eventually
    consistent, so KMS rejects the brand-new role ARN:

    ```text
    role created   07:48:50Z
    put-key-policy FAIL (invalid principals)  ~07:48:51Z
    put-key-policy OK on retry 07:50:03Z
    ```

    Damage is limited: the first `put-key-policy` (restore of the clean policy) succeeds,
    so the key is left **without** `Lab10Reader` and `up 10` aborts before `break`. Re-running
    `up 10` fixes it, but a first-time learner sees a scary AWS error. Fix applied: the
    `Lab10Reader` policy put now retries via `wait_until 60 5` and only surfaces the error
    if every attempt fails; `make test` still passes (24/24). `shellcheck` was not installed
    on this machine, so the edit is lint-unverified.

Note for future cleanup passes: the automated snapshots listed in item 13/14 were gone by
2026-10-31 (`describe-db-snapshots --snapshot-type automated` returns empty), so the
7-day retention assumption holds.

## Re-audit 2026-10-26 (brief for all 24 labs)

- Added `BRIEFS` for labs 00–23 in `tools/lab_brief_data.py`: inventory, healthy
  values, diagnostic map, three prediction questions, announce/change/sealed,
  and I do / We do / You do.
- All 24 READMEs now have a **5d** section (lab 00 uses a baseline heading).
- `./bin/lab brief`, `baseline`, `teach`, `change` work for every lab.
  Lab 03 keeps the detailed live checker; other labs use a generic read-only
  baseline that also checks CloudTrail, S3 BPA, KMS, SSM parameter, budget,
  app health, alarms, SQS, EventBridge, EC2, logs, ECS, backup, IAM, RDS and
  VPC endpoints.
- `break` warns when the brief is not confirmed; `REQUIRE_BRIEF=yes` enforces it.
- `make test` now also checks 5d structure and resource names for every lab.

## Re-audit 2026-10-25 (console guidance + lab readiness)

Feedback from labs 01/02: the AI explained too little and gave vague console
locations ("vào CloudWatch xem") without showing where to click.

### Guidance

- Added `docs/console-guide.md`: the 5-part answer contract (concept → exact
  path → action → expected screen → meaning/question), deep-link map, UI-drift
  rules, console-vs-CLI guidance.
- Added `docs/learner-quickstart.md` for humans: how to read a lab, 60-second
  card, safe-click rules, prompts for asking the AI, recovery when lost.
- Added `docs/ai-mentor-runbook.md`: a 7-step teaching loop, per-turn template,
  button-level contract, recovery scripts, anti-patterns, and a 20-minute
  navigation-vs-hint rule.
- Added the pre-break **Brief + baseline gate** for **all 24 labs**:
  `./bin/lab brief <id>`, `./bin/lab baseline <id> --live`,
  `./bin/lab teach <id>`, `./bin/lab change <id>`. `break` warns if the learner
  has not confirmed the baseline. Each brief shows inventory + healthy values +
  diagnostic map + three prediction questions, so diagnosis is no longer blind.
- Generated `docs/glossary.md` from all lab term tables (114 terms, lab-tagged).
- Added a **0. Đọc nhanh (60 giây)** card to all 24 READMEs; concepts in 5c are
  now split into one-sentence bullets and the glossary comes before concepts.
- `tools/gen_lab_docs.py --check` is now part of `make test`, so READMEs and
  glossary cannot drift from `tools/lab_console.py`.
- Added a **5c. Console — bấm ở đâu, thấy gì** section to all 24 READMEs via
  `tools/lab_console.py` + `tools/gen_lab_docs.py`. Each lab now has:
  per-lab concepts, glossary, numbered click path, fields to read, deep links,
  and "if you don't see it" fallbacks.
- Added `./bin/lab console <id>` (print walkthrough) and `--links` / `--open`.
- Updated `AGENTS.md`, `docs/ai-rules.md`, `docs/beginner-mentor.md`, and
  `START-HERE.md`: exact console paths are now part of the mentor contract.

### Readiness

- Added `tools/check_labs.py` (offline): manifest, functions, NEEDS_APP vs code,
  console section structure, unresolved placeholders, us-east-1 links, unknown
  resource names. Wired into `make test` and `make audit`.
- Added `tools/lab_preflight.py` + `./bin/lab preflight <id> [--live]`:
  static gate plus zero-cost AWS describe/list checks (account, core/app,
  leftover canary/snapshot/endpoint/backup plan, NAT/EIP/EKS/Multi-AZ).
- `bin/lab up` now refuses to run if the lab fails static checks.
- Fixed re-run (`up` a second time) failures and leaks:
  - labs 03/12: canary SG duplicate + orphan instance; Lambda permission conflict.
  - lab 07: duplicate RDS snapshot name.
  - lab 08: Multi-AZ modification when already enabled.
  - lab 10: key policy "original" could capture a deny and wedge cleanup.
  - labs 15/17: duplicate Flow Logs; lab 15 duplicate Reachability path.
  - lab 16: duplicate private instance + VPC endpoints (hourly cost).
  - labs 19/22: duplicate AWS Backup plans/selections/jobs.
  - lab 22: verify required a dashboard + 4 alarms that `up 22` never created.
  - lab 06: re-running `up` after `break` saved the broken launch template as "original".
  - lab 01: unbound/local `qarn`.
- Corrected `NEEDS_APP`: labs 13/14 were `yes` but only use core; labs 03/16 only
  need core and no longer force the app stack.

### Verification

- `make test` PASS (now includes the static readiness gate).
- `python3 tools/check_labs.py` → 24 labs, 0 failure.
- `./bin/lab console 01` and `./bin/lab preflight 01` produce useful output.
- **Not run:** `up` for all 24 labs (would create billable resources and violate
  the no-casual-deploy rule). Runtime readiness is still `preflight --live` +
  one lab per session, with cleanup.

## Re-audit 2026-10-24

- Removed legacy 6-week curriculum (`week1`–`week6`, `sources/source-index.md`).
- Kept the user's 5 personal notes under `notes/`, with a clear legacy README.
- Replaced us-east-1 prices with **ap-southeast-1** prices from AWS Price List API.
- Added `AGENTS.md` and `docs/ai-rules.md` (cost/safety/mentor contract).
- Re-verified 24/24 lab mapping, links, manifests, CloudFormation and shell scripts.
- Cleanup order re-tested statically; runtime test still requires the first real deploy.

## Fixed during this audit

1. **Cleanup order was dangerous.** Old script deleted core resources (SNS, IAM, SSM, logs, S3, KMS) before deleting the core stack, which can leave CloudFormation in `DELETE_FAILED`. New order:
   - delete app/lab stacks
   - delete VPC-scoped leftovers (EC2, RDS, ECS, endpoints, ENIs, SGs)
   - delete core stack
   - delete retained buckets and post-core leftovers
   - retry core deletion if blocked
2. Added missing `lab_default_build`.
3. Stack health checks now reject `ROLLBACK_COMPLETE` / `DELETE_FAILED`; only `CREATE_COMPLETE` and `UPDATE_COMPLETE` pass.
4. `ssm_run` now fails clearly when SendCommand fails, instead of looping 180s.
5. Fixed S3 Block Public Access parsing (tabs vs spaces).
6. Made Lab 16 SG/endpoint creation idempotent and tagged endpoints for cleanup.
7. Added IMDSv2 support to the app (launch template requires tokens).
8. Added Lab 14 / Lab 16 idempotency fixes.
9. Removed all Organizations/SCP hands-on content and renumbered to 24 labs.
10. Added psql install fallback so app boot does not fail if `postgresql15` is unavailable.
11. Increased ASG health check grace to 10 minutes (package install can be slow).
12. Added `make test` coverage for Python tooling and GitHub Actions lint workflow.

## Residual risks (must test on first real deploy)

These are **not** detectable without creating resources:

| Risk | Why | Mitigation |
|---|---|---|
| Nested `Fn::Sub` attributes for RDS secret/endpoint | `${Database.Endpoint.Address}`, `${Database.MasterUserSecret.SecretArn}` | If app stack fails, read Stack Events; replace with explicit SSM parameter/dynamic reference |
| AL2023 package names (`postgresql15`, `awscli-2`) | Region/AMI package availability can change | User-data log `/var/log/cloudops-bootstrap.log`; fallback added for psql/AWS CLI |
| Fargate public image pull | `public.ecr.aws` access from task | Check ECS stopped reason; use ECR image if blocked |
| AWS Backup + Config permissions | Service roles and bucket policy are strict | Lab 19 verify prints the failing layer; skip Config if time is short |
| `sts:AssumeRole` permission | User must be allowed to assume lab roles | If AccessDenied, attach `sts:AssumeRole` for `soa-c03-lab10-reader` / `soa-c03-lab13-target` |
| GuardDuty/Security Hub not automated | They can bill after trial | No lab enables them now; manual check on cleanup |

## Go / no-go

**Go for the 30-day track.** Static quality is good and the failure modes are documented.
The first `make bootstrap` is the real integration test. If it fails, capture:

```bash
aws cloudformation describe-stack-events --stack-name soa-c03-core \
  --max-items 20 --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
  --output table
```

Then fix the first `*_FAILED` event, not the last one.

## Next action

```bash
make init
make doctor
make bootstrap
./bin/lab up 00
./bin/lab break 00
./bin/lab verify 00
```
