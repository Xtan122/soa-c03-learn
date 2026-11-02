#!/usr/bin/env bash
# Create/update the CloudWatch dashboard from platform/dashboard.json.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_app

ALB="$(stack_output_required "$APP_STACK" AlbFullName)"
TG="$(stack_output_required "$APP_STACK" TargetGroupFullName)"
ASG="$(stack_output_required "$APP_STACK" AsgName)"
DB="$(stack_output_required "$APP_STACK" DbInstanceIdentifier)"
LOG_GROUP="$(stack_output_required "$CORE_STACK" AppLogGroupName)"

BODY="$(python3 - "$ROOT/platform/dashboard.json" "$AWS_REGION" "$LAB_ACCOUNT_ID" "$LAB_PREFIX" "$ALB" "$TG" "$ASG" "$DB" "$LOG_GROUP" <<'PY'
import json, sys
path, region, account, prefix, alb, tg, asg, db, log_group = sys.argv[1:]
data = json.load(open(path))
replacements = {
    "__REGION__": region, "__ACCOUNT__": account, "__PREFIX__": prefix,
    "__ALB__": alb, "__TG__": tg, "__ASG__": asg, "__DB__": db,
    "__LOG_GROUP__": log_group,
}
def walk(node):
    if isinstance(node, dict):
        return {k: walk(v) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v) for v in node]
    if isinstance(node, str):
        for key, value in replacements.items():
            node = node.replace(key, value)
        return node
    return node
print(json.dumps(walk(data)))
PY
)"

aws cloudwatch put-dashboard --dashboard-name "${LAB_PREFIX}-ops" --dashboard-body "$BODY" >/dev/null
ok "dashboard ${LAB_PREFIX}-ops updated"
