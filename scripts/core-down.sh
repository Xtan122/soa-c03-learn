#!/usr/bin/env bash
# Delete the core stack. The data bucket is retained; cleanup-all.sh removes it.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_account
confirm "Delete core stack $CORE_STACK?"
if stack_exists "$CORE_STACK"; then
  aws cloudformation delete-stack --stack-name "$CORE_STACK"
  info "waiting for $CORE_STACK deletion..."
  aws cloudformation wait stack-delete-complete --stack-name "$CORE_STACK"
  ok "deleted $CORE_STACK"
else
  ok "$CORE_STACK does not exist"
fi
warn "S3 bucket and KMS key may be retained. Run make cleanup for a full teardown."
