#!/usr/bin/env bash
# Delete the app stack. This is the single most important cost-control action.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_account

if stack_exists "$APP_STACK"; then
  info "deleting $APP_STACK (RDS deletion takes ~5 minutes)"
  aws cloudformation delete-stack --stack-name "$APP_STACK"
  aws cloudformation wait stack-delete-complete --stack-name "$APP_STACK" || {
    warn "stack delete did not finish cleanly; check the console"
  }
  ok "deleted $APP_STACK"
else
  ok "$APP_STACK does not exist"
fi

aws cloudwatch delete-dashboards --dashboard-names "${LAB_PREFIX}-ops" >/dev/null 2>&1 || true
info "cost meter stopped. Run make cost to confirm."
