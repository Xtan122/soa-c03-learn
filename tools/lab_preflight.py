#!/usr/bin/env python3
"""Read-only preflight before `./bin/lab up <id>`.

Static checks run offline. `--live` adds zero-cost AWS describe/list calls so
you can see leftover resources that would collide with a new `up` run.

Nothing here creates, modifies, or deletes a resource. Safe to run often.

Examples:
  python3 tools/lab_preflight.py --lab 05
  python3 tools/lab_preflight.py --lab 05 --live
  ./bin/lab preflight 05 --live
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LABS = ROOT / "labs"


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


def lab_dir(lab_id: str) -> pathlib.Path:
    wanted = f"{int(lab_id):02d}"
    for path in sorted(LABS.iterdir()):
        if path.is_dir() and path.name.startswith(wanted + "-"):
            return path
    raise SystemExit(f"lab {lab_id} not found")


def lab_env(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (path / "lab.env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def aws(*args: str, timeout: int = 20) -> str | None:
    """Run a read-only AWS CLI call. Return None on any failure."""
    try:
        proc = subprocess.run(
            ["aws", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def stack_status(name: str) -> str:
    raw = aws("cloudformation", "describe-stacks", "--stack-name", name,
              "--query", "Stacks[0].StackStatus")
    return "MISSING" if raw is None else raw.strip().strip('"')


def app_health() -> tuple[str, str, str]:
    raw = aws("cloudformation", "describe-stacks", "--stack-name", "soa-c03-app",
              "--query", "Stacks[0].Outputs[?OutputKey=='AlbDnsName'].OutputValue | [0]")
    if raw is None:
        return ("MISSING", "?", "?")
    dns = raw.strip().strip('"')
    try:
        code = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "8", f"http://{dns}/health"],
            capture_output=True, text=True, timeout=12,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        code = "?"
    tg = aws("cloudformation", "describe-stacks", "--stack-name", "soa-c03-app",
             "--query", "Stacks[0].Outputs[?OutputKey=='TargetGroupArn'].OutputValue | [0]")
    healthy = "?"
    if tg:
        arn = tg.strip().strip('"')
        raw = aws("elbv2", "describe-target-health", "--target-group-arn", arn,
                  "--query", "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])")
        healthy = "?" if raw is None else raw.strip()
    return (dns, code, healthy)


def check_live(lab: dict[str, str], env: dict[str, str]) -> int:
    problems = 0
    suggestions: list[str] = []
    prefix = env.get("LAB_PREFIX", "soa-c03")
    region = env.get("AWS_REGION", "ap-southeast-1")
    expected = env.get("LAB_ACCOUNT_ID", "")

    print("== identity (read-only) ==")
    ident = aws("sts", "get-caller-identity", "--query", "[Account,Arn]")
    if ident is None:
        print("FAIL cannot call sts:get-caller-identity (credentials?)")
        return 1
    account, arn = json.loads(ident)
    print(f"account={account} region={region}")
    print(f"arn={arn}")
    if expected and account != expected:
        print(f"FAIL account mismatch: current={account} expected={expected}")
        return 1

    print("\n== stacks ==")
    core = stack_status("soa-c03-core")
    print(f"core : {core}")
    if core not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
        print("FAIL core stack is not healthy; fix before any lab")
        problems += 1
    app = stack_status("soa-c03-app")
    print(f"app  : {app}")
    if lab.get("NEEDS_APP") == "yes":
        if app not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
            print("FAIL this lab needs the app stack; run make app-up (after approval)")
            suggestions.append("make app-up   # ALB+ASG+EC2+RDS ~$0.30–0.45/3h; cần bạn đồng ý")
            problems += 1
        else:
            dns, code, healthy = app_health()
            print(f"app  : http://{dns}/health -> {code}; healthy targets={healthy}")
            if code != "200" or healthy == "0":
                print("FAIL app baseline is not clean; lab up will refuse to start")
                problems += 1

    print("\n== leftover resources that affect this lab ==")
    lid = f"{int(lab['LAB_ID']):02d}"

    def count(service: str, *args: str) -> int:
        raw = aws(service, *args)
        if raw is None:
            return -1
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return -1
        if isinstance(value, list):
            return len(value)
        if isinstance(value, int):
            return value
        return -1

    def note(ok: bool, msg: str) -> None:
        nonlocal problems
        print(("  ok   " if ok else "  warn ") + msg)
        if not ok:
            problems += 1
            suggestions.append(f"./bin/lab down {lid}")

    if lid in ("01", "02", "04"):
        q = aws("sqs", "get-queue-url", "--queue-name", f"{prefix}-lab{lid}-events")
        note(True, f"SQS {prefix}-lab{lid}-events "
                   + ("exists (create is idempotent)" if q else "does not exist"))
    if lid in ("03", "12"):
        inst = aws("ec2", "describe-instances",
                   "--filters", f"Name=tag:Name,Values={prefix}-lab{lid}-canary",
                   "Name=instance-state-name,Values=pending,running,stopping,stopped",
                   "--query", "Reservations[].Instances[].InstanceId")
        n = len(json.loads(inst)) if inst else 0
        note(n == 0, f"canary instances left: {n} (up will rebuild)")
    if lid == "07":
        snap = aws("rds", "describe-db-snapshots",
                   "--db-snapshot-identifier", f"{prefix}-lab07-snapshot")
        note(True, "snapshot exists (up replaces it)" if snap else "snapshot does not exist")
    if lid == "08":
        raw = aws("rds", "describe-db-instances", "--db-instance-identifier", f"{prefix}-db",
                  "--query", "DBInstances[0].MultiAZ")
        note(True, f"RDS MultiAZ={raw.strip() if raw else '?'} (up is a no-op if already on)")
    if lid == "11":
        status = stack_status(f"{prefix}-lab11")
        note(status not in ("ROLLBACK_COMPLETE", "DELETE_FAILED"),
             f"lab11 stack={status}")
    if lid == "15":
        path = aws("ec2", "describe-network-insights-paths",
                   "--filters", f"Name=tag:Name,Values={prefix}-lab15-path",
                   "--query", "NetworkInsightsPaths[].NetworkInsightsPathId")
        n = len(json.loads(path)) if path else 0
        note(n == 0, f"Reachability paths left: {n} (up replaces them)")
    if lid in ("15", "17"):
        lg = f"/aws/vpc/{prefix}/lab{lid}"
        raw = aws("logs", "describe-log-groups", "--log-group-name-prefix", lg,
                  "--query", f"logGroups[?logGroupName=='{lg}'].logGroupName")
        n = len(json.loads(raw)) if raw else 0
        note(True, f"flow log group {lg}: {'exists' if n else 'missing'} (up recreates it)")
    if lid == "16":
        eps = aws("ec2", "describe-vpc-endpoints",
                  "--filters", f"Name=tag:Lab,Values=lab16",
                  "--query", "VpcEndpoints[].VpcEndpointId")
        n = len(json.loads(eps)) if eps else 0
        note(n == 0, f"lab16 endpoints left: {n} (up deletes and recreates)")
    if lid in ("19", "22"):
        plans = aws("backup", "list-backup-plans",
                    "--query", f"BackupPlansList[?BackupPlanName=='{prefix}-lab{lid}']")
        n = len(json.loads(plans)) if plans else 0
        note(n <= 1, f"backup plans named {prefix}-lab{lid}: {n}")
    if lid == "22":
        dash = aws("cloudwatch", "list-dashboards",
                   "--query", f"DashboardEntries[?DashboardName=='{prefix}-ops']")
        alarms = aws("cloudwatch", "describe-alarms", "--alarm-name-prefix", f"{prefix}-lab22",
                     "--query", "MetricAlarms")
        nd = len(json.loads(dash)) if dash else 0
        na = len(json.loads(alarms)) if alarms else 0
        note(nd == 1, f"dashboard {prefix}-ops: {nd}")
        note(na >= 4, f"lab22 alarms: {na}/4 (up creates them)")

    print("\n== expensive leftovers (global) ==")
    nat = count("ec2", "describe-nat-gateways",
                "--filter", "Name=state,Values=available", "--query", "NatGateways")
    eip = count("ec2", "describe-addresses", "--query", "Addresses")
    eks = count("eks", "list-clusters", "--query", "clusters")
    multi = aws("rds", "describe-db-instances",
                "--query", "DBInstances[?MultiAZ==`true`].DBInstanceIdentifier")
    nmulti = len(json.loads(multi)) if multi else 0
    for label, value in (("NAT gateways", nat), ("Elastic IPs", eip),
                         ("EKS clusters", eks), ("Multi-AZ RDS", nmulti)):
        if value < 0:
            print(f"  ?    {label}: unknown (no permission or API unavailable)")
            continue
        note(value == 0, f"{label}: {value}, expected 0")

    print("\n== next ==")
    if problems:
        print("Fix the FAIL/warn lines first. Suggested commands (in order):")
        seen: set[str] = set()
        for item in suggestions:
            if item in seen:
                continue
            seen.add(item)
            print(f"  {item}")
        print("  make cost")
    else:
        print(f"Static + live checks passed. You may run: ./bin/lab up {lid}")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", required=True, help="lab id, e.g. 05")
    parser.add_argument("--live", action="store_true", help="also run read-only AWS checks")
    args = parser.parse_args()

    path = lab_dir(args.lab)
    lab = lab_env(path)
    print(f"preflight lab {lab.get('LAB_ID')} — {lab.get('LAB_TITLE')}", flush=True)
    print(f"dir: {path.relative_to(ROOT)}", flush=True)

    static = subprocess.run(
        [sys.executable, str(ROOT / "tools/check_labs.py"), "--lab", args.lab],
        text=True,
    )
    if static.returncode != 0:
        print("\nStatic checks failed. Fix them before touching AWS.")
        return static.returncode

    if not args.live:
        print("\nStatic checks passed. Add --live for read-only AWS readiness checks.")
        return 0
    return check_live(lab, load_env())


if __name__ == "__main__":
    sys.exit(main())
