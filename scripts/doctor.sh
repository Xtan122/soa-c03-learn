#!/usr/bin/env bash
# Pre-flight / daily health check. Read-only.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"

FAILS=0
pass() { ok "$*"; }
fail() { warn "$*"; FAILS=$((FAILS + 1)); }

show_banner
require_account
info "identity: $(aws sts get-caller-identity --query Arn --output text)"
info "region: $AWS_REGION"

for c in aws jq curl python3 base64; do
  command -v "$c" >/dev/null 2>&1 && pass "command $c" || fail "command $c missing"
done

DAYS_LEFT=$(( ($(date -u -d "$EXPIRY_DATE" +%s) - $(date -u +%s)) / 86400 ))
if (( DAYS_LEFT >= 0 )); then
  pass "cleanup deadline $EXPIRY_DATE (${DAYS_LEFT} days left)"
else
  fail "cleanup deadline $EXPIRY_DATE has passed"
fi

if [[ "${ALLOW_BREAK:-no}" == "yes" ]]; then
  warn "ALLOW_BREAK=yes: break scripts are armed. Set back to no when finished."
else
  pass "break scripts disarmed (ALLOW_BREAK=no)"
fi

if aws budgets describe-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "${LAB_PREFIX}-monthly" >/dev/null 2>&1; then
  pass "budget ${LAB_PREFIX}-monthly exists"
else
  fail "budget ${LAB_PREFIX}-monthly missing (run make bootstrap)"
fi

if stack_exists "$CORE_STACK"; then
  status="$(stack_status "$CORE_STACK")"
  is_stack_healthy "$status" && pass "core stack $CORE_STACK: $status" || fail "core stack $CORE_STACK: $status"
else
  fail "core stack $CORE_STACK missing (run make bootstrap)"
fi

if stack_exists "$APP_STACK"; then
  status="$(stack_status "$APP_STACK")"
  is_stack_healthy "$status" && pass "app stack $APP_STACK: $status" || fail "app stack $APP_STACK: $status"

  URL="$(app_url)"
  CODE="$(http_code "$URL/health")"
  [[ "$CODE" == "200" ]] && pass "app health $URL/health -> 200" || fail "app health $URL/health -> $CODE"

  DB_CODE="$(http_code "$URL/db" 10)"
  [[ "$DB_CODE" == "200" ]] && pass "app database path -> 200" || warn "app database path -> $DB_CODE (RDS may still be starting)"

  TG="$(app_tg 2>/dev/null || true)"
  if [[ -n "$TG" ]]; then
    HEALTHY="$(aws elbv2 describe-target-health --target-group-arn "$TG" \
      --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text 2>/dev/null || echo 0)"
    TOTAL="$(aws elbv2 describe-target-health --target-group-arn "$TG" \
      --query 'length(TargetHealthDescriptions)' --output text 2>/dev/null || echo 0)"
    UNHEALTHY="$(aws elbv2 describe-target-health --target-group-arn "$TG" \
      --query "length(TargetHealthDescriptions[?TargetHealth.State=='unhealthy'])" --output text 2>/dev/null || echo 0)"
    if [[ "$HEALTHY" -ge 1 && "$UNHEALTHY" -eq 0 ]]; then
      pass "targets healthy: $HEALTHY/$TOTAL"
    else
      fail "targets healthy=$HEALTHY/$TOTAL unhealthy=$UNHEALTHY (run make app-down && make app-up after fixing)"
    fi
  fi

  ID="$(app_instance 2>/dev/null || true)"
  if [[ -n "$ID" ]]; then
    SSM="$(aws ssm describe-instance-information \
      --filters "Key=InstanceIds,Values=$ID" \
      --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null || echo None)"
    [[ "$SSM" == "Online" ]] && pass "SSM agent $ID: Online" || fail "SSM agent $ID: $SSM"
  else
    warn "no InService app instance yet"
  fi
else
  warn "app stack $APP_STACK not deployed (normal between sessions)"
fi

if stack_exists "$CORE_STACK"; then
  TRAIL="$(stack_output "$CORE_STACK" TrailName)"
  LOGGING="$(aws cloudtrail get-trail-status --name "$TRAIL" --query IsLogging --output text 2>/dev/null || echo False)"
  [[ "$LOGGING" == "True" ]] && pass "CloudTrail $TRAIL is logging" || fail "CloudTrail $TRAIL is not logging"

  BUCKET="$(stack_output "$CORE_STACK" DataBucketName)"
  BPA="$(aws s3api get-public-access-block --bucket "$BUCKET" \
    --query 'PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]' \
    --output text 2>/dev/null | tr '\t' ' ' || true)"
  [[ "$BPA" == "True True True True" ]] && pass "S3 bucket public access blocked" || fail "S3 bucket BPA not fully on: $BPA"
fi

echo
if (( FAILS == 0 )); then
  ok "doctor: all critical checks passed"
else
  warn "doctor: $FAILS critical check(s) failed"
  exit 1
fi
