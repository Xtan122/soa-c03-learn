#!/usr/bin/env bash
# One-time setup: budget + persistent core stack + app artifacts.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"

show_banner
require_account

info "Region: $AWS_REGION   Account: $LAB_ACCOUNT_ID   Expiry: $EXPIRY_DATE"

# ---------------------------------------------------------------- budget
BUDGET_NAME="${LAB_PREFIX}-monthly"
BUDGET_EMAIL="$ALERT_EMAIL"
[[ -z "$BUDGET_EMAIL" || "$BUDGET_EMAIL" == "you@example.com" ]] && BUDGET_EMAIL="$LAB_ACCOUNT_ID@example.com"
if aws budgets describe-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "$BUDGET_NAME" >/dev/null 2>&1; then
  ok "budget $BUDGET_NAME already exists"
else
  info "creating AWS Budget $BUDGET_NAME (limit USD 25)"
  mkdir -p "$ROOT/var"
  cat > "$ROOT/var/budget.json" <<JSON
{
  "BudgetName": "$BUDGET_NAME",
  "BudgetLimit": {"Amount": "25", "Unit": "USD"},
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
JSON
  cat > "$ROOT/var/budget-notifications.json" <<JSON
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 50,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {"SubscriptionType": "EMAIL", "Address": "${BUDGET_EMAIL}"}
    ]
  },
  {
    "Notification": {
      "NotificationType": "FORECASTED",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {"SubscriptionType": "EMAIL", "Address": "${BUDGET_EMAIL}"}
    ]
  }
]
JSON
  aws budgets create-budget \
    --account-id "$LAB_ACCOUNT_ID" \
    --budget "file://$ROOT/var/budget.json" \
    --notifications-with-subscribers "file://$ROOT/var/budget-notifications.json" >/dev/null
  ok "budget created (edit the email in AWS Budgets if needed)"
fi

# ------------------------------------------------------------------ core
EMAIL="$ALERT_EMAIL"
[[ "$EMAIL" == "you@example.com" ]] && EMAIL=""

info "deploying core stack $CORE_STACK (first run takes ~3 minutes)"
aws cloudformation deploy \
  --stack-name "$CORE_STACK" \
  --template-file "$ROOT/platform/core.yaml" \
  --parameter-overrides \
      "ProjectName=$LAB_PREFIX" \
      "AlertEmail=$EMAIL" \
      "ExpiryDate=$EXPIRY_DATE" \
      "LogRetentionDays=7" \
      "EnableFlowLogs=false" \
      "EnableNat=false" \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags $LAB_TAGS \
  --no-fail-on-empty-changeset

ok "core stack ready"

# --------------------------------------------------------------- artifacts
"$ROOT/scripts/upload-app.sh"

echo
ok "Bootstrap complete"
echo "  Core stack : $CORE_STACK"
echo "  Bucket     : $(stack_output "$CORE_STACK" DataBucketName)"
echo "  Trail      : $(stack_output "$CORE_STACK" TrailName)"
echo "  Log group  : $(stack_output "$CORE_STACK" AppLogGroupName)"
echo
echo "Next:"
echo "  make doctor"
echo "  ./bin/lab up 00"
echo "  ./bin/lab break 00   # setup lab: no fault, verify the baseline"
