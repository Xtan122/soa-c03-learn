#!/usr/bin/env bash
# Inventory every resource tagged Project=<prefix>.
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"
require_account

show_banner
info "resources tagged Project=$LAB_PREFIX"
aws resourcegroupstaggingapi get-resources \
  --tag-filters "Key=Project,Values=$LAB_PREFIX" \
  --query 'ResourceTagMappingList[].ResourceARN' --output text 2>/dev/null \
  | tr '\t' '\n' | sed '/^$/d' | sort || true

echo
info "CloudFormation stacks"
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE ROLLBACK_COMPLETE \
  --query "StackSummaries[?starts_with(StackName, '$LAB_PREFIX')].[StackName,StackStatus]" \
  --output table 2>/dev/null || true

echo
info "S3 buckets"
aws s3api list-buckets \
  --query "Buckets[?starts_with(Name, '$LAB_PREFIX')].Name" --output text 2>/dev/null || true

echo
info "KMS aliases"
aws kms list-aliases \
  --query "Aliases[?starts_with(AliasName, 'alias/$LAB_PREFIX')].[AliasName,TargetKeyId]" \
  --output table 2>/dev/null || true
