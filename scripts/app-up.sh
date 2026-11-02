#!/usr/bin/env bash
# Deploy the on-demand app stack: ALB + ASG + EC2 + RDS + alarms.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"

require_account
require_core
"$ROOT/scripts/upload-app.sh"

BUCKET="$(stack_output_required "$CORE_STACK" DataBucketName)"
KMS="$(stack_output_required "$CORE_STACK" KmsKeyArn)"
LOG_GROUP="$(stack_output_required "$CORE_STACK" AppLogGroupName)"
TOPIC="$(stack_output_required "$CORE_STACK" AlertTopicArn)"
PROFILE="$(stack_output_required "$CORE_STACK" AppInstanceProfileName)"

info "deploying $APP_STACK (ALB + ASG + RDS; ~8-12 minutes)"
aws cloudformation deploy \
  --stack-name "$APP_STACK" \
  --template-file "$ROOT/platform/app.yaml" \
  --parameter-overrides \
      "ProjectName=$LAB_PREFIX" \
      "InstanceType=t4g.micro" \
      "MinSize=1" "MaxSize=2" "DesiredCapacity=1" \
      "DBInstanceClass=db.t4g.micro" \
      "DBName=cloudops" "DBUser=cloudops" "AppPort=8080" \
      "MultiAZ=false" \
      "ExpiryDate=$EXPIRY_DATE" \
      "AlertTopicArn=$TOPIC" "BucketName=$BUCKET" "KmsKeyArn=$KMS" \
      "LogGroupName=$LOG_GROUP" "InstanceProfileName=$PROFILE" \
  --tags $LAB_TAGS \
  --no-fail-on-empty-changeset

ok "app stack: $(stack_status "$APP_STACK")"
"$ROOT/scripts/create-dashboard.sh" || warn "dashboard not created yet"

URL="$(app_url)"
info "waiting for $URL/health (up to 8 minutes)"
if wait_until 480 10 bash -c "[[ \"\$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 '$URL/health')\" == 200 ]]"; then
  ok "app is healthy: $URL"
else
  warn "app is not healthy yet. Check: aws elbv2 describe-target-health --target-group-arn $(app_tg)"
fi

echo
echo "  URL      : $URL"
echo "  ASG      : $(app_asg)"
echo "  RDS      : $(db_id)"
echo "  Dashboard: ${LAB_PREFIX}-ops"
echo
echo "Remember: make app-down when the session is finished."
