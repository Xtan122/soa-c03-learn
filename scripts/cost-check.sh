#!/usr/bin/env bash
# Spend + leftover resource report. Read-only.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_account

START_7="$(date -u -d '7 days ago' +%Y-%m-%d)"
START_MONTH="$(date -u +%Y-%m-01)"
END="$(date -u +%Y-%m-%d)"
EXPIRY_EPOCH="$(date -u -d "$EXPIRY_DATE" +%s)"
DAYS_LEFT=$(( (EXPIRY_EPOCH - $(date -u +%s)) / 86400 ))

show_banner
printf 'Region: %s   Account: %s\n' "$AWS_REGION" "$LAB_ACCOUNT_ID"
if (( DAYS_LEFT < 0 )); then
  warn "EXPIRY_DATE $EXPIRY_DATE has passed. Run: make cleanup"
else
  printf 'Cleanup deadline: %s (%s days left)\n' "$EXPIRY_DATE" "$DAYS_LEFT"
fi

cost_for() {
  local start="$1" label="$2"
  aws ce get-cost-and-usage \
    --time-period "Start=$start,End=$END" \
    --granularity DAILY --metrics UnblendedCost \
    --query 'ResultsByTime[].Total.UnblendedCost.Amount' --output text 2>/dev/null \
    | awk -v l="$label" '{s+=$1} END {printf "%-18s USD %.2f\n", l, s+0}'
}

echo
info "spend"
cost_for "$START_7" "last 7 days"
cost_for "$START_MONTH" "month to date"

echo
info "running / billable resources"
EC2_COUNT="$(aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'length(Reservations[].Instances[])' --output text 2>/dev/null || echo 0)"
ALB_COUNT="$(aws elbv2 describe-load-balancers \
  --query "length(LoadBalancers[?starts_with(LoadBalancerName, '$LAB_PREFIX')])" --output text 2>/dev/null || echo 0)"
NAT_COUNT="$(aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'length(NatGateways)' --output text 2>/dev/null || echo 0)"
RDS_COUNT="$(aws rds describe-db-instances \
  --query "length(DBInstances[?starts_with(DBInstanceIdentifier, '$LAB_PREFIX')])" --output text 2>/dev/null || echo 0)"
EIP_COUNT="$(aws ec2 describe-addresses \
  --filters "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'length(Addresses)' --output text 2>/dev/null || echo 0)"
ESC_COUNT="$(aws ecs list-clusters --query "length(clusterArns[?contains(@, '$LAB_PREFIX')])" --output text 2>/dev/null || echo 0)"
EKS_COUNT="$(aws eks list-clusters --query "length(clusters[?starts_with(@, '$LAB_PREFIX')])" --output text 2>/dev/null || echo 0)"

printf '  EC2 running      : %s\n' "$EC2_COUNT"
printf '  RDS instances    : %s\n' "$RDS_COUNT"
printf '  ALB/NLB          : %s\n' "$ALB_COUNT"
printf '  NAT gateways     : %s  (~USD 0.059/hour each)\n' "$NAT_COUNT"
printf '  Elastic IPs      : %s  (~USD 0.005/hour each)\n' "$EIP_COUNT"
printf '  ECS clusters     : %s\n' "$ESC_COUNT"
printf '  EKS clusters     : %s  (~USD 0.10/hour each)\n' "$EKS_COUNT"

if [[ "$EC2_COUNT" != "0" || "$RDS_COUNT" != "0" || "$ALB_COUNT" != "0" || "$NAT_COUNT" != "0" ]]; then
  warn "billable resources are running. Finish the lab and run: make app-down"
fi
if [[ "$EKS_COUNT" != "0" ]]; then
  warn "EKS control plane is ~USD 73/month. Delete it now unless the lab is active."
fi

echo
info "budget"
aws budgets describe-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "${LAB_PREFIX}-monthly" \
  --query 'Budget.{Limit:BudgetLimit.Amount,Actual:CalculatedSpend.ActualSpend.Amount,Forecast:CalculatedSpend.ForecastedSpend.Amount}' \
  --output table 2>/dev/null || echo "  no budget named ${LAB_PREFIX}-monthly"

echo
echo "Hard rule: every resource must be gone by $EXPIRY_DATE."
echo "Full teardown: CONFIRM_DESTROY=yes make cleanup"
