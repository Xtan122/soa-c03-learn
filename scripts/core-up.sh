#!/usr/bin/env bash
# Deploy or update the persistent core stack.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_account
EMAIL="$ALERT_EMAIL"; [[ "$EMAIL" == "you@example.com" ]] && EMAIL=""
aws cloudformation deploy \
  --stack-name "$CORE_STACK" \
  --template-file "$ROOT/platform/core.yaml" \
  --parameter-overrides \
      "ProjectName=$LAB_PREFIX" "AlertEmail=$EMAIL" "ExpiryDate=$EXPIRY_DATE" \
      "LogRetentionDays=7" "EnableFlowLogs=false" "EnableNat=false" \
  --capabilities CAPABILITY_NAMED_IAM --tags $LAB_TAGS --no-fail-on-empty-changeset
ok "core stack $CORE_STACK: $(stack_status "$CORE_STACK")"
