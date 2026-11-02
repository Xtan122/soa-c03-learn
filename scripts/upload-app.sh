#!/usr/bin/env bash
# Upload the app + agent config to the lab bucket before deploying the app stack.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_core

BUCKET="$(stack_output_required "$CORE_STACK" DataBucketName)"
info "uploading artifacts to s3://$BUCKET/platform/"
aws s3 cp "$ROOT/platform/app/app.py" "s3://$BUCKET/platform/app.py" --only-show-errors
aws s3 cp "$ROOT/platform/app/cloudops-app.service" "s3://$BUCKET/platform/cloudops-app.service" --only-show-errors
aws s3 cp "$ROOT/platform/app/cloudwatch-agent.json" "s3://$BUCKET/platform/cloudwatch-agent.json" --only-show-errors
ok "artifacts uploaded"
