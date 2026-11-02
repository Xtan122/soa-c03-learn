#!/usr/bin/env bash
# Shared helpers for every lab script and the `lab` CLI.
# Source this file; do not execute it.

if [[ -n "${__SOA_COMMON_LOADED:-}" ]]; then
  return 0
fi
__SOA_COMMON_LOADED=1

set -Eeuo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export ROOT

if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'; C_DIM=$'\033[2m'
  C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_CYAN=$'\033[36m'
else
  C_RESET=""; C_BOLD=""; C_DIM=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_CYAN=""
fi

info() { printf '%s==>%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
ok()   { printf '%s OK %s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '%sWARN%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
die()  { printf '%sFAIL%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }
dim()  { printf '%s%s%s\n' "$C_DIM" "$*" "$C_RESET"; }

require_cmds() {
  local missing=0 c
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || { warn "missing command: $c"; missing=1; }
  done
  [[ $missing -eq 0 ]] || die "install the missing commands and retry"
}

# All AWS calls go through this wrapper so LAB_DRY_RUN=1 is safe.
aws() {
  if [[ "${LAB_DRY_RUN:-0}" == "1" ]]; then
    printf 'DRY: aws %s\n' "$*" >&2
    return 0
  fi
  command aws "$@"
}

now_utc() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
today_utc() { date -u +"%Y-%m-%d"; }

confirm() {
  local prompt="${1:-Continue?}" answer
  if [[ "${CONFIRM:-}" == "yes" ]]; then return 0; fi
  if [[ ! -t 0 ]]; then die "non-interactive: set CONFIRM=yes to proceed"; fi
  read -r -p "$prompt [type yes]: " answer
  [[ "$answer" == "yes" ]] || die "aborted"
}

require_account() {
  [[ -n "${LAB_ACCOUNT_ID:-}" ]] || die "LAB_ACCOUNT_ID missing; run make init"
  if [[ "${LAB_DRY_RUN:-0}" == "1" ]]; then
    _SOA_ACCOUNT_OK=1
    return 0
  fi
  if [[ "${_SOA_ACCOUNT_OK:-}" == "1" ]]; then return 0; fi
  local current
  current="$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)"
  [[ -n "$current" ]] || die "no AWS credentials. Configure AWS CLI first."
  [[ "$current" == "$LAB_ACCOUNT_ID" ]] || die "wrong account: current=$current expected=$LAB_ACCOUNT_ID"
  _SOA_ACCOUNT_OK=1
  export _SOA_ACCOUNT_OK
}

require_break() {
  [[ "${ALLOW_BREAK:-no}" == "yes" ]] || die "safety: set ALLOW_BREAK=yes in .env before breaking things"
  require_account
  local today expiry
  today="$(date -u +%Y%m%d)"
  expiry="${EXPIRY_DATE//-/}"
  [[ "$today" -le "$expiry" ]] || die "EXPIRY_DATE $EXPIRY_DATE has passed. Run make cleanup."
}

stack_exists() {
  aws cloudformation describe-stacks --stack-name "$1" >/dev/null 2>&1
}

stack_status() {
  aws cloudformation describe-stacks --stack-name "$1" \
    --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "MISSING"
}

stack_output() {
  local stack="$1" key="$2"
  aws cloudformation describe-stacks --stack-name "$stack" \
    --query "Stacks[0].Outputs[?OutputKey=='${key}'].OutputValue" --output text 2>/dev/null || true
}

stack_output_required() {
  local value
  value="$(stack_output "$1" "$2")"
  [[ -n "$value" && "$value" != "None" ]] || die "missing output $2 from stack $1"
  printf '%s' "$value"
}

is_stack_healthy() {
  [[ "$1" == "CREATE_COMPLETE" || "$1" == "UPDATE_COMPLETE" ]]
}

require_core() {
  stack_exists "${CORE_STACK}" || die "core stack ${CORE_STACK} missing. Run: make bootstrap"
  local status; status="$(stack_status "${CORE_STACK}")"
  is_stack_healthy "$status" || die "core stack not healthy: $status (fix/delete and re-bootstrap)"
}

require_app() {
  require_core
  stack_exists "${APP_STACK}" || die "app stack ${APP_STACK} missing. Run: make app-up"
  local status; status="$(stack_status "${APP_STACK}")"
  is_stack_healthy "$status" || die "app stack not healthy: $status (check Stack Events, then delete/recreate)"
}

app_url() {
  local dns
  dns="$(stack_output_required "${APP_STACK}" AlbDnsName)"
  printf 'http://%s' "$dns"
}

app_asg() { stack_output_required "${APP_STACK}" AsgName; }
app_tg()  { stack_output_required "${APP_STACK}" TargetGroupArn; }
app_alb_full_name() { stack_output_required "${APP_STACK}" AlbFullName; }
app_tg_full_name() { stack_output_required "${APP_STACK}" TargetGroupFullName; }
db_id()   { stack_output_required "${APP_STACK}" DbInstanceIdentifier; }
db_secret_arn() { stack_output_required "${APP_STACK}" DbSecretArn; }

app_instance() {
  local asg id
  asg="$(app_asg)"
  id="$(aws autoscaling describe-auto-scaling-groups \
        --auto-scaling-group-names "$asg" \
        --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
        --output text 2>/dev/null | awk '{print $1; exit}')"
  [[ -n "$id" && "$id" != "None" ]] || return 1
  printf '%s' "$id"
}

app_instance_required() {
  local id
  id="$(app_instance)" || die "no InService app instance. Wait for the ASG or run make app-up"
  printf '%s' "$id"
}

http_code() {
  curl -s -o /dev/null -w '%{http_code}' --max-time "${2:-5}" "${1}" || true
}

http_body() {
  curl -s --max-time "${2:-5}" "${1}" || true
}

wait_until() {
  local timeout="${1:-300}" interval="${2:-5}"
  shift 2
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep "$interval"
  done
  return 1
}

alarm_state() {
  aws cloudwatch describe-alarms --alarm-names "$1" \
    --query 'MetricAlarms[0].StateValue' --output text 2>/dev/null || echo "MISSING"
}

secret_json() {
  aws secretsmanager get-secret-value --secret-id "$1" \
    --query SecretString --output text 2>/dev/null
}

# Run a shell script on an instance through SSM. Usage:
#   ssm_run "$instance" <<'EOS'
#   df -h
#   EOS
ssm_run() {
  local instance="$1" script b64 cmd cid status deadline
  script="$(cat)"
  [[ -n "$script" ]] || die "ssm_run: empty script"
  b64="$(printf '%s' "$script" | base64 | tr -d '\n')"
  cmd="echo ${b64} | base64 -d | bash"

  cid="$(aws ssm send-command \
    --instance-ids "$instance" \
    --document-name AWS-RunShellScript \
    --comment "soa-c03 lab $(date -u +%H:%M:%S)" \
    --parameters "$(jq -nc --arg c "$cmd" '{commands:[$c]}')" \
    --query 'Command.CommandId' --output text 2>/dev/null || true)"
  [[ -n "$cid" && "$cid" != "None" ]] || die "SSM SendCommand failed for $instance (agent offline?)"

  deadline=$((SECONDS + 180))
  while (( SECONDS < deadline )); do
    status="$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$instance" \
      --query Status --output text 2>/dev/null || echo Pending)"
    case "$status" in
      Success|Failed|TimedOut|Cancelled) break ;;
      *) sleep 2 ;;
    esac
  done

  local out err
  out="$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$instance" \
    --query StandardOutputContent --output text 2>/dev/null || true)"
  err="$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$instance" \
    --query StandardErrorContent --output text 2>/dev/null || true)"

  printf '%s' "$out"
  if [[ "$status" != "Success" ]]; then
    printf '\n--- stderr ---\n%s\n' "$err" >&2
    return 1
  fi
}

record_event() {
  local lab="$1" action="$2" status="${3:-ok}" note="${4:-}"
  mkdir -p "$ROOT/progress"
  jq -nc \
    --arg ts "$(now_utc)" --arg lab "$lab" --arg action "$action" \
    --arg status "$status" --arg note "$note" \
    --arg account "${LAB_ACCOUNT_ID:-}" --arg region "${AWS_REGION:-}" \
    '{ts:$ts,lab:$lab,action:$action,status:$status,note:$note,account:$account,region:$region}' \
    >> "$ROOT/progress/events.jsonl"
}

tagged_resources() {
  aws resourcegroupstaggingapi get-resources \
    --tag-filters "Key=Project,Values=${LAB_PREFIX}" \
    --query 'ResourceTagMappingList[].ResourceARN' --output text | tr '\t' '\n' | sed '/^$/d'
}

show_banner() {
  printf '%s\n' "${C_BOLD}SOA-C03 CloudOps Lab${C_RESET}  ${C_DIM}$(now_utc)${C_RESET}"
}

require_cmds aws jq curl base64 python3
