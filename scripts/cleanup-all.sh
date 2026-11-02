#!/usr/bin/env bash
# Full teardown. Order matters:
#   1. delete app/lab stacks
#   2. delete VPC-scoped leftovers (ENIs, EC2, RDS, ECS, endpoints, SGs)
#   3. delete the core stack (VPC, KMS, CloudTrail, SNS, IAM, SSM, logs)
#   4. delete retained buckets and anything left by tag/prefix
#
# Usage:
#   DRY_RUN=yes make cleanup
#   CONFIRM_DESTROY=yes make cleanup
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/load-env.sh"
source "$ROOT/scripts/lib/common.sh"

DRY_RUN="${DRY_RUN:-no}"
if [[ "$DRY_RUN" == "yes" ]]; then
  export LAB_DRY_RUN=1
  warn "DRY RUN: no AWS resources will be changed"
fi

require_account
if [[ "$DRY_RUN" != "yes" ]]; then
  [[ "${CONFIRM_DESTROY:-}" == "yes" ]] || die "set CONFIRM_DESTROY=yes to destroy everything"
  confirm "This deletes ALL $LAB_PREFIX resources in $LAB_ACCOUNT_ID/$AWS_REGION. Type yes"
fi

info "account=$LAB_ACCOUNT_ID region=$AWS_REGION prefix=$LAB_PREFIX expiry=$EXPIRY_DATE"
START_EPOCH=$SECONDS

delete_stack() {
  local name="$1"
  stack_exists "$name" || return 0
  info "delete stack $name"
  aws cloudformation delete-stack --stack-name "$name" || true
  if [[ "$DRY_RUN" != "yes" ]]; then
    aws cloudformation wait stack-delete-complete --stack-name "$name" 2>/dev/null || \
      warn "stack $name did not delete cleanly; check the console"
  fi
}

empty_bucket() {
  local bucket="$1" key version
  info "empty bucket $bucket"
  aws s3 rm "s3://$bucket" --recursive --only-show-errors >/dev/null 2>&1 || true
  [[ "$DRY_RUN" == "yes" ]] && return 0
  while read -r key version; do
    [[ -n "$key" && -n "$version" ]] || continue
    aws s3api delete-object --bucket "$bucket" --key "$key" --version-id "$version" >/dev/null 2>&1 || true
  done < <(aws s3api list-object-versions --bucket "$bucket" \
            --query 'Versions[].[Key,VersionId]' --output text 2>/dev/null || true)
  while read -r key version; do
    [[ -n "$key" && -n "$version" ]] || continue
    aws s3api delete-object --bucket "$bucket" --key "$key" --version-id "$version" >/dev/null 2>&1 || true
  done < <(aws s3api list-object-versions --bucket "$bucket" \
            --query 'DeleteMarkers[].[Key,VersionId]' --output text 2>/dev/null || true)
}

# Capture the VPC before the core stack is deleted. If core deletion fails we
# can still clean flow logs / NACLs / SGs.
VPC_ID="$(aws ec2 describe-vpcs --filters "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'Vpcs[0].VpcId' --output text 2>/dev/null || true)"
[[ "$VPC_ID" == "None" ]] && VPC_ID=""

# ================================================================ 1. stacks
delete_stack "$APP_STACK"

if stack_exists "${LAB_PREFIX}-lab11"; then
  LAB11_BUCKET="$(stack_output "${LAB_PREFIX}-lab11" BucketName || true)"
  if [[ -n "$LAB11_BUCKET" && "$LAB11_BUCKET" != "None" ]]; then
    empty_bucket "$LAB11_BUCKET"
  fi
fi

while read -r s; do
  [[ -n "$s" && "$s" != "$CORE_STACK" ]] || continue
  delete_stack "$s"
done < <(aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE ROLLBACK_COMPLETE CREATE_FAILED \
  --query "StackSummaries[?starts_with(StackName, '$LAB_PREFIX')].StackName" --output text 2>/dev/null | tr '\t' '\n')

# ====================================================== 2. VPC-scoped leftovers
for c in $(aws ecs list-clusters --query "clusterArns[?contains(@, '$LAB_PREFIX')]" --output text 2>/dev/null | tr '\t' '\n'); do
  info "ecs cluster ${c##*/}"
  for s in $(aws ecs list-services --cluster "$c" --query 'serviceArns[]' --output text 2>/dev/null | tr '\t' '\n'); do
    aws ecs update-service --cluster "$c" --service "$s" --desired-count 0 >/dev/null 2>&1 || true
    aws ecs delete-service --cluster "$c" --service "$s" --force >/dev/null 2>&1 || true
  done
  aws ecs delete-cluster --cluster "$c" >/dev/null 2>&1 || true
done

for e in $(aws eks list-clusters --query "clusters[?starts_with(@, '$LAB_PREFIX')]" --output text 2>/dev/null); do
  info "eks cluster $e"
  aws eks delete-cluster --name "$e" >/dev/null 2>&1 || true
done

for db in $(aws rds describe-db-instances \
  --query "DBInstances[?starts_with(DBInstanceIdentifier, '$LAB_PREFIX')].DBInstanceIdentifier" \
  --output text 2>/dev/null); do
  info "rds instance $db"
  aws rds modify-db-instance --db-instance-identifier "$db" --no-deletion-protection --apply-immediately >/dev/null 2>&1 || true
  aws rds delete-db-instance --db-instance-identifier "$db" --skip-final-snapshot --delete-automated-backups >/dev/null 2>&1 || true
done
for db in $(aws rds describe-db-instances \
  --query "DBInstances[?starts_with(DBInstanceIdentifier, '$LAB_PREFIX')].DBInstanceIdentifier" \
  --output text 2>/dev/null); do
  [[ "$DRY_RUN" == "yes" ]] || aws rds wait db-instance-deleted --db-instance-identifier "$db" 2>/dev/null || true
done

for cluster in $(aws rds describe-db-clusters \
  --query "DBClusters[?starts_with(DBClusterIdentifier, '$LAB_PREFIX')].DBClusterIdentifier" \
  --output text 2>/dev/null); do
  info "rds cluster $cluster"
  aws rds delete-db-cluster --db-cluster-identifier "$cluster" --skip-final-snapshot >/dev/null 2>&1 || true
done

for snap in $(aws rds describe-db-snapshots --snapshot-type manual \
  --query "DBSnapshots[?starts_with(DBSnapshotIdentifier, '$LAB_PREFIX')].DBSnapshotIdentifier" \
  --output text 2>/dev/null); do
  info "rds snapshot $snap"
  aws rds delete-db-snapshot --db-snapshot-identifier "$snap" >/dev/null 2>&1 || true
done

INSTANCES="$(aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=pending,running,stopping,stopped" "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'Reservations[].Instances[].InstanceId' --output text 2>/dev/null || true)"
if [[ -n "$INSTANCES" ]]; then
  info "terminating instances: $INSTANCES"
  aws ec2 terminate-instances --instance-ids $INSTANCES >/dev/null 2>&1 || true
  if [[ "$DRY_RUN" != "yes" ]]; then
    aws ec2 wait instance-terminated --instance-ids $INSTANCES 2>/dev/null || true
  fi
fi

for eg in $(aws ec2 describe-egress-only-internet-gateways \
  --filters "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'EgressOnlyInternetGateways[].EgressOnlyInternetGatewayId' --output text 2>/dev/null || true); do
  igw="$(aws ec2 describe-egress-only-internet-gateways --egress-only-internet-gateway-ids "$eg" \
    --query 'EgressOnlyInternetGateways[0].Attachments[0].VpcId' --output text 2>/dev/null || true)"
  [[ -n "$igw" && "$igw" != "None" ]] && aws ec2 delete-egress-only-internet-gateway \
    --egress-only-internet-gateway-id "$eg" >/dev/null 2>&1 || true
done

for lb in $(aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?starts_with(LoadBalancerName, '$LAB_PREFIX')].LoadBalancerArn" \
  --output text 2>/dev/null); do
  info "load balancer $lb"
  aws elbv2 delete-load-balancer --load-balancer-arn "$lb" >/dev/null 2>&1 || true
done
for tg in $(aws elbv2 describe-target-groups \
  --query "TargetGroups[?starts_with(TargetGroupName, '$LAB_PREFIX')].TargetGroupArn" \
  --output text 2>/dev/null); do
  info "target group $tg"
  aws elbv2 delete-target-group --target-group-arn "$tg" >/dev/null 2>&1 || true
done

for vpce in $(aws ec2 describe-vpc-endpoints --filters "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'VpcEndpoints[].VpcEndpointId' --output text 2>/dev/null); do
  info "vpc endpoint $vpce"
  aws ec2 delete-vpc-endpoints --vpc-endpoint-ids "$vpce" >/dev/null 2>&1 || true
done
sleep 15

for path in $(aws ec2 describe-network-insights-paths \
  --filters "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'NetworkInsightsPaths[].NetworkInsightsPathId' --output text 2>/dev/null || true); do
  info "reachability path $path"
  aws ec2 delete-network-insights-path --network-insights-path-id "$path" >/dev/null 2>&1 || true
done

# ENIs and custom SGs must be gone before the core VPC can be deleted.
if [[ -n "$VPC_ID" ]]; then
  for eni in $(aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" \
    "Name=tag:Project,Values=$LAB_PREFIX" --query 'NetworkInterfaces[].NetworkInterfaceId' \
    --output text 2>/dev/null); do
    info "eni $eni"
    aws ec2 delete-network-interface --network-interface-id "$eni" >/dev/null 2>&1 || true
  done
  sleep 15
  for attempt in 1 2 3; do
    remaining=0
    for sg in $(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" \
      --query "SecurityGroups[?GroupName!='default'].GroupId" --output text 2>/dev/null); do
      info "security group $sg (attempt $attempt)"
      aws ec2 delete-security-group --group-id "$sg" >/dev/null 2>&1 || remaining=$((remaining + 1))
    done
    (( remaining == 0 )) && break
    sleep 10
  done
fi

info "waiting 15s for ENIs/load balancers to release before core deletion"
sleep 15

# ================================================================ 3. core
delete_stack "$CORE_STACK"

# ============================================================ 4. post-core
for nat in $(aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'NatGateways[].NatGatewayId' --output text 2>/dev/null); do
  info "nat gateway $nat"
  aws ec2 delete-nat-gateway --nat-gateway-id "$nat" >/dev/null 2>&1 || true
done
for eip in $(aws ec2 describe-addresses --filters "Name=tag:Project,Values=$LAB_PREFIX" \
  --query 'Addresses[].AllocationId' --output text 2>/dev/null); do
  info "release eip $eip"
  aws ec2 release-address --allocation-id "$eip" >/dev/null 2>&1 || true
done

if [[ -n "$VPC_ID" ]]; then
  for fl in $(aws ec2 describe-flow-logs --filter "Name=resource-id,Values=$VPC_ID" \
    --query 'FlowLogs[].FlowLogId' --output text 2>/dev/null); do
    info "flow log $fl"
    aws ec2 delete-flow-logs --flow-log-ids "$fl" >/dev/null 2>&1 || true
  done
  for nacl in $(aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'NetworkAcls[].NetworkAclId' --output text 2>/dev/null); do
    while read -r rule egress; do
      [[ -n "$rule" ]] || continue
      if [[ "$egress" == "True" ]]; then
        aws ec2 delete-network-acl-entry --network-acl-id "$nacl" --rule-number "$rule" --egress >/dev/null 2>&1 || true
      else
        aws ec2 delete-network-acl-entry --network-acl-id "$nacl" --rule-number "$rule" --ingress >/dev/null 2>&1 || true
      fi
    done < <(aws ec2 describe-network-acls --network-acl-ids "$nacl" \
      --query "NetworkAcls[0].Entries[?RuleAction=='deny' && PortRange.From==\`8080\`].[RuleNumber,Egress]" \
      --output text 2>/dev/null || true)
  done
fi

for fn in $(aws lambda list-functions --query "Functions[?starts_with(FunctionName, '$LAB_PREFIX')].FunctionName" --output text 2>/dev/null); do
  info "lambda $fn"
  aws lambda delete-function --function-name "$fn" >/dev/null 2>&1 || true
done
for q in $(aws sqs list-queues --queue-name-prefix "$LAB_PREFIX" \
  --query 'QueueUrls[]' --output text 2>/dev/null | tr '\t' '\n'); do
  info "sqs $q"
  aws sqs delete-queue --queue-url "$q" >/dev/null 2>&1 || true
done
for t in $(aws sns list-topics --query "Topics[?contains(TopicArn, ':$LAB_PREFIX-')].TopicArn" --output text 2>/dev/null); do
  info "sns $t"
  aws sns delete-topic --topic-arn "$t" >/dev/null 2>&1 || true
done

for prefix in "/aws/cloudops/$LAB_PREFIX" "/aws/vpc/$LAB_PREFIX" "/aws/ecs/$LAB_PREFIX" "/aws/lambda/$LAB_PREFIX" "$LAB_PREFIX"; do
  for lg in $(aws logs describe-log-groups --log-group-name-prefix "$prefix" \
    --query 'logGroups[].logGroupName' --output text 2>/dev/null); do
    info "log group $lg"
    aws logs delete-log-group --log-group-name "$lg" >/dev/null 2>&1 || true
  done
done
for a in $(aws cloudwatch describe-alarms --alarm-name-prefix "$LAB_PREFIX" \
  --query 'MetricAlarms[].AlarmName' --output text 2>/dev/null); do
  info "alarm $a"
  aws cloudwatch delete-alarms --alarm-names "$a" >/dev/null 2>&1 || true
done
for d in $(aws cloudwatch list-dashboards --query "DashboardEntries[?starts_with(DashboardName, '$LAB_PREFIX')].DashboardName" --output text 2>/dev/null); do
  info "dashboard $d"
  aws cloudwatch delete-dashboards --dashboard-names "$d" >/dev/null 2>&1 || true
done

for s in $(aws secretsmanager list-secrets \
  --query "SecretList[?starts_with(Name, '$LAB_PREFIX')].ARN" --output text 2>/dev/null); do
  info "secret $s"
  aws secretsmanager delete-secret --secret-id "$s" --force-delete-without-recovery >/dev/null 2>&1 || true
done
for p in $(aws ssm get-parameters-by-path --path "/$LAB_PREFIX" --recursive \
  --query 'Parameters[].Name' --output text 2>/dev/null); do
  info "ssm parameter $p"
  aws ssm delete-parameter --name "$p" >/dev/null 2>&1 || true
done

for plan in $(aws backup list-backup-plans --query "BackupPlansList[?starts_with(BackupPlanName, '$LAB_PREFIX')].BackupPlanId" --output text 2>/dev/null); do
  info "backup plan $plan"
  aws backup delete-backup-plan --backup-plan-id "$plan" >/dev/null 2>&1 || true
done
for vault in $(aws backup list-backup-vaults --query "BackupVaultList[?starts_with(BackupVaultName, '$LAB_PREFIX')].BackupVaultName" --output text 2>/dev/null); do
  for rp in $(aws backup list-recovery-points-by-backup-vault --backup-vault-name "$vault" \
    --query 'RecoveryPoints[].RecoveryPointArn' --output text 2>/dev/null); do
    aws backup delete-recovery-point --backup-vault-name "$vault" --recovery-point-arn "$rp" >/dev/null 2>&1 || true
  done
  info "backup vault $vault"
  aws backup delete-backup-vault --backup-vault-name "$vault" >/dev/null 2>&1 || true
done

for rec in $(aws configservice describe-configuration-recorders \
  --query 'ConfigurationRecorders[].name' --output text 2>/dev/null); do
  aws configservice stop-configuration-recorder --configuration-recorder-name "$rec" >/dev/null 2>&1 || true
  aws configservice delete-configuration-recorder --configuration-recorder-name "$rec" >/dev/null 2>&1 || true
done
for ch in $(aws configservice describe-delivery-channels \
  --query 'DeliveryChannels[].name' --output text 2>/dev/null); do
  aws configservice delete-delivery-channel --delivery-channel-name "$ch" >/dev/null 2>&1 || true
done
for rule in $(aws configservice describe-config-rules \
  --query "ConfigRules[?starts_with(ConfigRuleName, '$LAB_PREFIX')].ConfigRuleName" --output text 2>/dev/null); do
  aws configservice delete-config-rule --config-rule-name "$rule" >/dev/null 2>&1 || true
done

for repo in $(aws ecr describe-repositories \
  --query "repositories[?starts_with(repositoryName, '$LAB_PREFIX')].repositoryName" --output text 2>/dev/null); do
  info "ecr $repo"
  aws ecr delete-repository --repository-name "$repo" --force >/dev/null 2>&1 || true
done

for b in $(aws s3api list-buckets --query "Buckets[?starts_with(Name, '$LAB_PREFIX')].Name" --output text 2>/dev/null); do
  empty_bucket "$b"
  info "delete bucket $b"
  aws s3api delete-bucket --bucket "$b" >/dev/null 2>&1 || true
done

for ip in $(aws iam list-instance-profiles \
  --query "InstanceProfiles[?starts_with(InstanceProfileName, '$LAB_PREFIX')].InstanceProfileName" --output text 2>/dev/null); do
  for r in $(aws iam get-instance-profile --instance-profile-name "$ip" \
    --query 'InstanceProfile.Roles[].RoleName' --output text 2>/dev/null); do
    aws iam remove-role-from-instance-profile --instance-profile-name "$ip" --role-name "$r" >/dev/null 2>&1 || true
  done
  aws iam delete-instance-profile --instance-profile-name "$ip" >/dev/null 2>&1 || true
done
for role in $(aws iam list-roles \
  --query "Roles[?starts_with(RoleName, '$LAB_PREFIX')].RoleName" --output text 2>/dev/null); do
  info "iam role $role"
  for p in $(aws iam list-attached-role-policies --role-name "$role" \
    --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null); do
    aws iam detach-role-policy --role-name "$role" --policy-arn "$p" >/dev/null 2>&1 || true
  done
  for p in $(aws iam list-role-policies --role-name "$role" \
    --query 'PolicyNames[]' --output text 2>/dev/null); do
    aws iam delete-role-policy --role-name "$role" --policy-name "$p" >/dev/null 2>&1 || true
  done
  aws iam delete-role --role-name "$role" >/dev/null 2>&1 || true
done
for pol in $(aws iam list-policies --scope Local \
  --query "Policies[?starts_with(PolicyName, '$LAB_PREFIX')].Arn" --output text 2>/dev/null); do
  aws iam delete-policy --policy-arn "$pol" >/dev/null 2>&1 || true
done

for trail in $(aws cloudtrail describe-trails \
  --query "trailList[?starts_with(Name, '$LAB_PREFIX')].Name" --output text 2>/dev/null); do
  info "trail $trail"
  aws cloudtrail stop-logging --name "$trail" >/dev/null 2>&1 || true
  aws cloudtrail delete-trail --name "$trail" >/dev/null 2>&1 || true
done

for alias in $(aws kms list-aliases \
  --query "Aliases[?starts_with(AliasName, 'alias/$LAB_PREFIX')].AliasName" --output text 2>/dev/null); do
  key_id="$(aws kms list-aliases --query "Aliases[?AliasName=='$alias'].TargetKeyId" --output text 2>/dev/null || true)"
  if [[ -n "$key_id" && "$key_id" != "None" ]]; then
    info "schedule KMS key deletion: $key_id"
    aws kms schedule-key-deletion --key-id "$key_id" --pending-window-in-days 7 >/dev/null 2>&1 || true
  fi
done

for analyzer in $(aws accessanalyzer list-analyzers \
  --query "analyzers[?starts_with(name, '$LAB_PREFIX')].arn" --output text 2>/dev/null || true); do
  info "access analyzer $analyzer"
  aws accessanalyzer delete-analyzer --analyzer-arn "$analyzer" >/dev/null 2>&1 || true
done

# If the first core deletion was blocked by an orphan ENI/SG, retry after the
# post-core cleanup above.
if stack_exists "$CORE_STACK"; then
  warn "core stack still exists; retrying deletion after leftover cleanup"
  delete_stack "$CORE_STACK"
fi

aws budgets delete-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "${LAB_PREFIX}-monthly" >/dev/null 2>&1 || true

echo
ok "cleanup finished in $((SECONDS - START_EPOCH))s"
cat <<'EOF'

Manual checks before you close the account:
  1. GuardDuty / Security Hub: disable detectors if a lab enabled them.
  2. KMS keys: deletion is scheduled for 7 days; verify in KMS console.
  3. Cost Explorer: filter by service and confirm the last 7 days trend to zero.
  4. CloudTrail: check all regions for trails you created manually.
  5. EC2 -> Network Interfaces: confirm no orphan ENI keeps a VPC alive.

Run: make cost && make inventory
EOF
