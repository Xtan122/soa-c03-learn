#!/usr/bin/env bash
# Lab implementations. Sourced by bin/lab.
# The user is NOT supposed to read this before diagnosing. It is the answer key.

# --------------------------------------------------------------- helpers
lab_default_build() {
  if [[ "${NEEDS_APP:-no}" == "yes" ]]; then
    require_app
    ensure_app_healthy
  else
    require_core
  fi
}

lab_default_cleanup() { :; }

ensure_app_healthy() {
  require_app
  local url tg total unhealthy
  url="$(app_url)"
  if ! wait_until 360 10 bash -c "[[ \"\$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 '$url/health')\" == 200 ]]"; then
    die "app is not healthy: $url/health"
  fi
  tg="$(app_tg)"
  total="$(aws elbv2 describe-target-health --target-group-arn "$tg" \
    --query 'length(TargetHealthDescriptions)' --output text 2>/dev/null || echo 0)"
  unhealthy="$(aws elbv2 describe-target-health --target-group-arn "$tg" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='unhealthy'])" --output text 2>/dev/null || echo 0)"
  if [[ "${total:-0}" -eq 0 || "${unhealthy:-0}" -gt 0 ]]; then
    die "app stack baseline is not clean: targets=$total unhealthy=$unhealthy. Run 'make app-down && make app-up' after fixing the app, then retry."
  fi
}

ensure_ssm_online() {
  local id; id="$(app_instance_required)"
  if ! wait_until 300 10 bash -c "[[ \"\$(aws ssm describe-instance-information --filters 'Key=InstanceIds,Values=$id' --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null)\" == Online ]]"; then
    die "SSM agent is not online on $id"
  fi
  printf '%s' "$id"
}

app_role_name() { stack_output_required "$CORE_STACK" AppInstanceRoleName; }
app_sg_id()     { stack_output_required "$APP_STACK" AppSecurityGroupId; }
alb_sg_id()     { stack_output_required "$APP_STACK" AlbSecurityGroupId; }
db_sg_id()      { stack_output_required "$APP_STACK" DbSecurityGroupId; }
core_bucket()   { stack_output_required "$CORE_STACK" DataBucketName; }
core_topic()    { stack_output_required "$CORE_STACK" AlertTopicArn; }
core_kms_id()   { stack_output_required "$CORE_STACK" KmsKeyId; }
core_log_group(){ stack_output_required "$CORE_STACK" AppLogGroupName; }
core_vpc_id()   { stack_output_required "$CORE_STACK" VpcId; }
core_public_1() { stack_output_required "$CORE_STACK" PublicSubnet1; }
core_private_1(){ stack_output_required "$CORE_STACK" PrivateSubnet1; }

app_public_subnet() {
  aws ec2 describe-instances --instance-ids "$(app_instance_required)" \
    --query 'Reservations[0].Instances[0].SubnetId' --output text
}

app_private_route_table() {
  local rt
  rt="$(aws ec2 describe-route-tables \
    --filters "Name=association.subnet-id,Values=$(core_private_1)" \
    --query 'RouteTables[0].RouteTableId' --output text 2>/dev/null || true)"
  if [[ -z "$rt" || "$rt" == "None" ]]; then
    # Subnet may use the VPC main route table instead of an explicit one.
    rt="$(aws ec2 describe-route-tables \
      --filters "Name=vpc-id,Values=$(core_vpc_id)" "Name=association.main,Values=true" \
      --query 'RouteTables[0].RouteTableId' --output text)"
  fi
  printf '%s' "$rt"
}

alb_eni() {
  aws ec2 describe-network-interfaces \
    --filters "Name=description,Values=ELB app/${LAB_PREFIX}-alb/*" \
    --query 'NetworkInterfaces[0].NetworkInterfaceId' --output text
}

app_eni() {
  aws ec2 describe-instances --instance-ids "$(app_instance_required)" \
    --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' --output text
}

set_health_check_path() {
  aws elbv2 modify-target-group --target-group-arn "$(app_tg)" \
    --health-check-path "$1" >/dev/null
}

revoke_app_8080() {
  aws ec2 revoke-security-group-ingress --group-id "$(app_sg_id)" \
    --protocol tcp --port 8080 --source-group "$(alb_sg_id)" >/dev/null 2>&1 || true
}

authorize_app_8080() {
  aws ec2 authorize-security-group-ingress --group-id "$(app_sg_id)" \
    --protocol tcp --port 8080 --source-group "$(alb_sg_id)" >/dev/null 2>&1 || true
}

revoke_db_5432() {
  aws ec2 revoke-security-group-ingress --group-id "$(db_sg_id)" \
    --protocol tcp --port 5432 --source-group "$(app_sg_id)" >/dev/null 2>&1 || true
}

authorize_db_5432() {
  aws ec2 authorize-security-group-ingress --group-id "$(db_sg_id)" \
    --protocol tcp --port 5432 --source-group "$(app_sg_id)" >/dev/null 2>&1 || true
}

metric_sum() {
  local ns="$1" metric="$2" dim_name="${3:-}" dim_value="${4:-}" minutes="${5:-15}"
  # Align start/end to the minute: CloudWatch buckets start at the exact
  # --start-time, so a stray seconds offset shifts every bucket and silently
  # drops datapoints that sit on a minute boundary (metric filters do).
  local args=(--namespace "$ns" --metric-name "$metric"
    --start-time "$(date -u -d "$minutes minutes ago" '+%Y-%m-%dT%H:%M:00Z')"
    --end-time "$(date -u '+%Y-%m-%dT%H:%M:00Z')"
    --period 60 --statistics Sum --query 'Datapoints[].Sum' --output text)
  [[ -n "$dim_name" ]] && args+=(--dimensions "Name=$dim_name,Value=$dim_value")
  # --output text puts every datapoint on ONE line, tab separated: sum all
  # fields, not just $1, or only the first datapoint is counted.
  aws cloudwatch get-metric-statistics "${args[@]}" 2>/dev/null \
    | awk '{for (i = 1; i <= NF; i++) s += $i} END {print s + 0}'
}

metric_max() {
  local ns="$1" metric="$2" dim_name="$3" dim_value="$4" minutes="${5:-15}"
  aws cloudwatch get-metric-statistics --namespace "$ns" --metric-name "$metric" \
    --dimensions "Name=$dim_name,Value=$dim_value" \
    --start-time "$(date -u -d "$minutes minutes ago" '+%Y-%m-%dT%H:%M:00Z')" \
    --end-time "$(date -u '+%Y-%m-%dT%H:%M:00Z')" \
    --period 60 --statistics Maximum --query 'Datapoints[].Maximum' --output text 2>/dev/null \
    | awk '{for (i = 1; i <= NF; i++) if ($i > m) m = $i} END {print m + 0}'
}

# True if the alarm entered ALARM at any point in the last N minutes. Needed
# because an alarm with a metric-filter metric and defaultValue=0 returns to OK
# one period after the burst, so a single instantaneous state read is racy.
alarm_fired_within() {
  local name="$1" minutes="${2:-30}"
  aws cloudwatch describe-alarm-history --alarm-name "$name" \
    --history-item-type StateUpdate \
    --start-date "$(date -u -d "$minutes minutes ago" +%Y-%m-%dT%H:%M:%SZ)" \
    --query 'AlarmHistoryItems[].HistorySummary' --output text 2>/dev/null \
    | grep -q 'to ALARM'
}

wait_alarm() {
  local name="$1" state="$2" timeout="${3:-420}"
  wait_until "$timeout" 15 bash -c "[[ \"\$(aws cloudwatch describe-alarms --alarm-names '$name' --query 'MetricAlarms[0].StateValue' --output text 2>/dev/null)\" == '$state' ]]"
}

create_alarm() {
  local name="$1" ns="$2" metric="$3" dim_name="$4" dim_value="$5"
  local threshold="$6" op="$7" stat="$8" period="$9" eval="${10}"
  local args=(--alarm-name "$name" --namespace "$ns" --metric-name "$metric"
    --threshold "$threshold" --comparison-operator "$op"
    --statistic "$stat" --period "$period" --evaluation-periods "$eval"
    --treat-missing-data notBreaching
    --alarm-actions "$(core_topic)" --ok-actions "$(core_topic)")
  [[ -n "$dim_name" ]] && args+=(--dimensions "Name=$dim_name,Value=$dim_value")
  aws cloudwatch put-metric-alarm "${args[@]}"
}

create_sqs() {
  local name="$1" url
  url="$(aws sqs create-queue --queue-name "$name" --query QueueUrl --output text)"
  aws sqs tag-queue --queue-url "$url" \
    --tags "Project=$LAB_PREFIX,ExpiryDate=$EXPIRY_DATE" >/dev/null 2>&1 || true
  printf '%s' "$url"
}

queue_arn() {
  aws sqs get-queue-attributes --queue-url "$1" --attribute-names QueueArn \
    --query Attributes.QueueArn --output text
}

set_sqs_policy() {
  local url="$1" service="$2" source_arn="$3" arn policy
  arn="$(queue_arn "$url")"
  policy="$(jq -nc --arg q "$arn" --arg svc "$service" --arg src "$source_arn" '
    {Version:"2012-10-17",Statement:[{Effect:"Allow",Principal:{Service:$svc},
     Action:"sqs:SendMessage",Resource:$q,Condition:{ArnEquals:{"aws:SourceArn":$src}}}]}')"
  aws sqs set-queue-attributes --queue-url "$url" \
    --attributes "$(jq -nc --arg p "$policy" '{Policy:$p}')"
}

subscribe_sns_sqs() {
  local topic="$1" url="$2" arn existing
  arn="$(queue_arn "$url")"
  existing="$(aws sns list-subscriptions-by-topic --topic-arn "$topic" \
    --query "Subscriptions[?Endpoint=='$arn' && Protocol=='sqs'].SubscriptionArn" \
    --output text 2>/dev/null || true)"
  if [[ -n "$existing" && "$existing" != "None" ]]; then
    printf '%s' "$existing"
    return 0
  fi
  aws sns subscribe --topic-arn "$topic" --protocol sqs \
    --notification-endpoint "$arn" --attributes RawMessageDelivery=true \
    --query SubscriptionArn --output text
}

assume_role_env() {
  local arn="$1" session="${2:-lab}" out
  # Must fail loudly: piping straight into awk hid AssumeRole denials, so
  # callers saw an empty (but successful) eval and the wrong error message.
  out="$(aws sts assume-role --role-arn "$arn" --role-session-name "$session" \
    --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text 2>/dev/null)" || return 1
  [[ -n "$out" ]] || return 1
  printf '%s\n' "$out" \
    | awk '{printf "export AWS_ACCESS_KEY_ID=%s\nexport AWS_SECRET_ACCESS_KEY=%s\nexport AWS_SESSION_TOKEN=%s\n",$1,$2,$3}'
}

vpc_id() { core_vpc_id; }

create_canary() {
  local name="$1" ami pub sg id vpc
  vpc="$(vpc_id)"
  # Re-running `up` must rebuild the canary, not fail on a duplicate SG or
  # leave a second billable instance behind.
  destroy_canary "$name"
  ami="$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query Parameter.Value --output text)"
  pub="$(core_public_1)"
  sg="$(aws ec2 create-security-group --group-name "${name}-sg" \
        --description "canary for ${name}" --vpc-id "$vpc" --query GroupId --output text 2>/dev/null || \
        aws ec2 describe-security-groups \
          --filters "Name=group-name,Values=${name}-sg" "Name=vpc-id,Values=$vpc" \
          --query 'SecurityGroups[0].GroupId' --output text)"
  [[ -n "$sg" && "$sg" != "None" ]] || { warn "cannot create or find SG ${name}-sg"; return 1; }
  aws ec2 create-tags --resources "$sg" \
    --tags "Key=Name,Value=${name}-sg" "Key=Project,Value=$LAB_PREFIX" "Key=ExpiryDate,Value=$EXPIRY_DATE" >/dev/null
  id="$(aws ec2 run-instances --image-id "$ami" --instance-type t4g.nano \
        --subnet-id "$pub" --security-group-ids "$sg" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$name},{Key=Project,Value=$LAB_PREFIX},{Key=ExpiryDate,Value=$EXPIRY_DATE}]" \
        --query 'Instances[0].InstanceId' --output text)"
  aws ec2 wait instance-running --instance-ids "$id"
  printf '%s %s\n' "$id" "$sg" > "$ROOT/var/${name}.id"
  printf '%s' "$id"
}

destroy_canary() {
  local name="$1" id sg
  [[ -f "$ROOT/var/${name}.id" ]] || return 0
  read -r id sg < "$ROOT/var/${name}.id"
  aws ec2 terminate-instances --instance-ids "$id" >/dev/null 2>&1 || true
  aws ec2 wait instance-terminated --instance-ids "$id" 2>/dev/null || true
  aws ec2 delete-security-group --group-id "$sg" >/dev/null 2>&1 || true
  rm -f "$ROOT/var/${name}.id"
}

rds_psql_secret() {
  local host="$1" secret_arn="$2" sql="$3" id b64
  id="$(app_instance_required)"
  b64="$(printf '%s' "$sql" | base64 | tr -d '\n')"
  ssm_run "$id" <<EOS
set -euo pipefail
set -a; source /etc/cloudops.env; set +a
SECRET=\$(aws secretsmanager get-secret-value --secret-id "$secret_arn" --query SecretString --output text)
export PGPASSWORD=\$(printf '%s' "\$SECRET" | jq -r .password)
SQL=\$(echo $b64 | base64 -d)
psql -tA -h "$host" -p "\$DB_PORT" -U "\$DB_USER" -d "\$DB_NAME" -v ON_ERROR_STOP=1 -c "\$SQL"
EOS
}

rds_psql() {
  rds_psql_secret "$1" "$(db_secret_arn)" "$2"
}

lambda_zip() {
  local src="$1" out="$2"
  python3 - "$src" "$out" <<'PY'
import pathlib, sys, zipfile
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(src, arcname=src.name)
PY
}

wait_vpc_endpoints_deleted() {
  local ids=("$@") deadline=$((SECONDS + 300)) remaining
  ((${#ids[@]})) || return 0
  while (( SECONDS < deadline )); do
    remaining="$(aws ec2 describe-vpc-endpoints --vpc-endpoint-ids "${ids[@]}" \
      --query "length(VpcEndpoints[?State!='deleted'])" --output text 2>/dev/null || echo 0)"
    [[ "${remaining:-0}" == "0" ]] && return 0
    sleep 10
  done
  return 1
}

enable_lab_flow_logs() {
  local suffix="$1" lg role vpc
  vpc="$(vpc_id)"
  lg="/aws/vpc/${LAB_PREFIX}/${suffix}"
  # Re-running `up` must not add a second flow log (and a second log group
  # bill). Tear down this lab's previous flow log first; other labs use a
  # different suffix.
  disable_lab_flow_logs "$suffix"
  aws logs create-log-group --log-group-name "$lg" >/dev/null 2>&1 || true
  aws logs put-retention-policy --log-group-name "$lg" --retention-in-days 1 >/dev/null 2>&1 || true
  role="$(aws iam create-role --role-name "${LAB_PREFIX}-flow-${suffix}" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"vpc-flow-logs.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "${LAB_PREFIX}-flow-${suffix}" --query 'Role.Arn' --output text)"
  aws iam put-role-policy --role-name "${LAB_PREFIX}-flow-${suffix}" --policy-name flow \
    --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"logs:CreateLogStream\",\"logs:PutLogEvents\",\"logs:DescribeLogGroups\",\"logs:DescribeLogStreams\"],\"Resource\":\"arn:aws:logs:${AWS_REGION}:${LAB_ACCOUNT_ID}:log-group:${lg}:*\"}]}" >/dev/null 2>&1 || true
  local flow_id
  flow_id="$(aws ec2 create-flow-logs --resource-ids "$vpc" --resource-type VPC --traffic-type ALL \
    --log-destination-type cloud-watch-logs --log-group-name "$lg" \
    --deliver-logs-permission-arn "$role" \
    --query 'FlowLogIds[0]' --output text)"
  printf '%s' "$lg" > "$ROOT/var/flow-${suffix}.log-group"
  printf '%s' "$flow_id" > "$ROOT/var/flow-${suffix}.id"
}

disable_lab_flow_logs() {  local suffix="$1" ids
  ids=""
  [[ -f "$ROOT/var/flow-${suffix}.id" ]] && ids="$(cat "$ROOT/var/flow-${suffix}.id")"
  [[ -n "$ids" ]] && aws ec2 delete-flow-logs --flow-log-ids $ids >/dev/null 2>&1 || true
  rm -f "$ROOT/var/flow-${suffix}.id"
  if [[ -f "$ROOT/var/flow-${suffix}.log-group" ]]; then
    aws logs delete-log-group --log-group-name "$(cat "$ROOT/var/flow-${suffix}.log-group")" >/dev/null 2>&1 || true
    rm -f "$ROOT/var/flow-${suffix}.log-group"
  fi
  aws iam delete-role-policy --role-name "${LAB_PREFIX}-flow-${suffix}" --policy-name flow >/dev/null 2>&1 || true
  aws iam delete-role --role-name "${LAB_PREFIX}-flow-${suffix}" >/dev/null 2>&1 || true
}

# --------------------------------------------------------------- lab 00
lab00_build() {
  if ! stack_exists "$CORE_STACK"; then
    info "core stack missing; running bootstrap"
    "$ROOT/scripts/bootstrap.sh"
  fi
  require_core
}

lab00_break() {
  info "bootstrap lab has no fault. Verify the baseline instead."
}

lab00_verify() {
  require_core
  local trail bucket bpa
  is_stack_healthy "$(stack_status "$CORE_STACK")" || { warn "core stack not healthy"; return 1; }
  trail="$(stack_output "$CORE_STACK" TrailName)"
  [[ "$(aws cloudtrail get-trail-status --name "$trail" --query IsLogging --output text)" == "True" ]] || { warn "CloudTrail not logging"; return 1; }
  bucket="$(stack_output "$CORE_STACK" DataBucketName)"
  bpa="$(aws s3api get-public-access-block --bucket "$bucket" --query 'PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]' --output text | tr '\t' ' ')"
  [[ "$bpa" == "True True True True" ]] || { warn "S3 BPA not fully on: $bpa"; return 1; }
  aws ssm get-parameter --name "/${LAB_PREFIX}/app/port" >/dev/null || { warn "SSM parameter missing"; return 1; }
  aws kms describe-key --key-id "$(core_kms_id)" >/dev/null || { warn "KMS key missing"; return 1; }
  aws budgets describe-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "${LAB_PREFIX}-monthly" >/dev/null || { warn "budget missing"; return 1; }
  ok "core baseline verified"
}

lab00_reset() { :; }
lab00_cleanup() { :; }

# --------------------------------------------------------------- lab 01
lab01_build() {
  ensure_app_healthy
  # Lab 01 observes CPU; do not let target tracking scale the ASG and create
  # extra instances (cost + noise) while the CPU load is running.
  aws autoscaling suspend-processes --auto-scaling-group-name "$(app_asg)" \
    --scaling-processes AlarmNotification >/dev/null 2>&1 || true
  local q url
  q="$(create_sqs "${LAB_PREFIX}-lab01-events")"
  subscribe_sns_sqs "$(core_topic)" "$q" > "$ROOT/var/lab01-subscription"
  set_sqs_policy "$q" sns.amazonaws.com "$(core_topic)"
  printf '%s\n' "$q" > "$ROOT/var/lab01-queue-url"
  local instance; instance="$(app_instance_required)"
  printf '%s\n' "$instance" > "$ROOT/var/lab01-instance"
  create_alarm "${LAB_PREFIX}-lab01-cpu-high" AWS/EC2 CPUUtilization \
    InstanceId "$instance" 50 GreaterThanThreshold Average 60 1
}

lab01_break() {
  local url; url="$(app_url)"
  curl -s "$url/load?seconds=1800&workers=2" >/dev/null
  info "CPU load injected for 30 minutes (enough time to diagnose)"
}

lab01_verify() {
  local cpu state
  cpu="$(metric_max AWS/EC2 CPUUtilization InstanceId "$(cat "$ROOT/var/lab01-instance")")"
  state="$(alarm_state "${LAB_PREFIX}-lab01-cpu-high")"
  [[ "${cpu%.*}" -ge 50 ]] || { warn "CPU max ${cpu} < 50"; return 1; }
  wait_alarm "${LAB_PREFIX}-lab01-cpu-high" ALARM 300 || { warn "alarm state=$state (expected ALARM)"; return 1; }
  ok "CPU max=$cpu alarm=ALARM"
}

lab01_reset() {
  local qarn
  curl -s "$(app_url)/stop" >/dev/null 2>&1 || true
  aws autoscaling resume-processes --auto-scaling-group-name "$(app_asg)" \
    --scaling-processes AlarmNotification >/dev/null 2>&1 || true
  aws cloudwatch delete-alarms --alarm-names "${LAB_PREFIX}-lab01-cpu-high" >/dev/null 2>&1 || true
  if [[ -f "$ROOT/var/lab01-subscription" ]]; then
    aws sns unsubscribe --subscription-arn "$(cat "$ROOT/var/lab01-subscription")" >/dev/null 2>&1 || true
    rm -f "$ROOT/var/lab01-subscription"
  fi
  if [[ -f "$ROOT/var/lab01-queue-url" ]]; then
    qarn="$(queue_arn "$(cat "$ROOT/var/lab01-queue-url")" 2>/dev/null || true)"
    if [[ -n "$qarn" && "$qarn" != "None" ]]; then
      for sub in $(aws sns list-subscriptions \
        --query "Subscriptions[?Endpoint=='$qarn'].SubscriptionArn" --output text 2>/dev/null || true); do
        aws sns unsubscribe --subscription-arn "$sub" >/dev/null 2>&1 || true
      done
    fi
    aws sqs delete-queue --queue-url "$(cat "$ROOT/var/lab01-queue-url")" >/dev/null 2>&1 || true
    rm -f "$ROOT/var/lab01-queue-url"
  fi
}
lab01_cleanup() { lab01_reset; }

# --------------------------------------------------------------- lab 02
lab02_build() {
  ensure_app_healthy
  aws logs put-metric-filter --log-group-name "$(core_log_group)" \
    --filter-name "${LAB_PREFIX}-lab02-errors" \
    --filter-pattern '{ $.level = "ERROR" }' \
    --metric-transformations metricName=ErrorCount,metricNamespace=CloudOpsLab,metricValue=1,defaultValue=0 >/dev/null
  create_alarm "${LAB_PREFIX}-lab02-errors" CloudOpsLab ErrorCount "" "" 5 GreaterThanOrEqualToThreshold Sum 60 1
}

lab02_break() {
  local url; url="$(app_url)"
  for _ in $(seq 1 15); do curl -s "$url/error" >/dev/null; done
  curl -s "$url/log?level=ERROR&msg=lab02_manual_error" >/dev/null
  sleep 10
  info "15 x HTTP 500 + 1 manual ERROR log"
}

lab02_verify() {
  local count metric state raw qid
  count=0
  for _ in $(seq 1 4); do
    qid="$(aws logs start-query --log-group-name "$(core_log_group)" \
      --start-time "$(date -u -d '30 minutes ago' +%s)" --end-time "$(date -u +%s)" \
      --query-string 'fields @timestamp, level | filter level = "ERROR" | stats count() as errors' \
      --query queryId --output text)"
    sleep 8
    # AWS CLI prints "None" when the query has no result row yet; keep only digits
    # so the numeric test below cannot trip `set -u`. `stats count()` returns a
    # single row/cell, so index it directly: JMESPath `"errors"` is a quoted
    # identifier (a field name), not a string literal, and always filters to [].
    raw="$(aws logs get-query-results --query-id "$qid" \
      --query 'results[0][0].value' --output text 2>/dev/null || true)"
    count="${raw//[^0-9]/}"
    count="${count:-0}"
    [[ "$count" -ge 10 ]] && break
    sleep 10
  done
  metric="$(metric_sum CloudOpsLab ErrorCount "" "" 30)"
  state="$(alarm_state "${LAB_PREFIX}-lab02-errors")"
  [[ "${count:-0}" -ge 10 ]] || { warn "ERROR log count=$count (<10)"; return 1; }
  [[ "${metric%.*}" -ge 5 ]] || { warn "metric ErrorCount=$metric (<5)"; return 1; }
  if [[ "$state" != "ALARM" ]] && ! alarm_fired_within "${LAB_PREFIX}-lab02-errors" 30; then
    warn "alarm state=$state and no OK->ALARM transition in the last 30m"
    return 1
  fi
  ok "ERROR logs=$count metric=$metric alarm=$state"
}

lab02_reset() {
  aws logs delete-metric-filter --log-group-name "$(core_log_group)" --filter-name "${LAB_PREFIX}-lab02-errors" >/dev/null 2>&1 || true
  aws cloudwatch delete-alarms --alarm-names "${LAB_PREFIX}-lab02-errors" >/dev/null 2>&1 || true
}
lab02_cleanup() { lab02_reset; }

# --------------------------------------------------------------- lab 03
lab03_build() {
  require_core
  local id q rule_arn
  id="$(create_canary "${LAB_PREFIX}-lab03-canary")"
  q="$(create_sqs "${LAB_PREFIX}-lab03-events")"
  aws events put-rule --name "${LAB_PREFIX}-lab03-ec2-state" \
    --event-pattern '{"source":["aws.ec2"],"detail-type":["EC2 Instance State-change Notification"],"detail":{"state":["terminated","stopped"]}}' >/dev/null
  rule_arn="$(aws events describe-rule --name "${LAB_PREFIX}-lab03-ec2-state" --query Arn --output text)"
  set_sqs_policy "$q" events.amazonaws.com "$rule_arn"
  aws events put-targets --rule "${LAB_PREFIX}-lab03-ec2-state" \
    --targets "Id=1,Arn=$(queue_arn "$q")" >/dev/null
  printf '%s\n' "$q" > "$ROOT/var/lab03-queue-url"
  printf '%s\n' "$id" > "$ROOT/var/lab03-canary-instance"
}

lab03_break() {
  local role id env
  role="$(stack_output_required "$CORE_STACK" LabOperatorRoleArn)"
  id="$(cat "$ROOT/var/lab03-canary-instance")"
  # If AssumeRole fails, the terminate would run as the caller's own identity
  # and the CloudTrail evidence the lab teaches would be wrong.
  env="$(assume_role_env "$role" lab03-break)" \
    || { warn "AssumeRole failed — fault NOT injected"; return 1; }
  eval "$env"
  aws ec2 terminate-instances --instance-ids "$id" >/dev/null
}
lab03_verify() {
  local id event role
  id="$(cat "$ROOT/var/lab03-canary-instance")"
  event=""
  # Window must outlive the lab contract (150m + 20m blind diagnosis), otherwise a
  # correct run ages out before verify. CloudTrail keeps 90 days, so 12h is cheap.
  for _ in $(seq 1 20); do
    event="$(aws cloudtrail lookup-events \
      --lookup-attributes AttributeKey=EventName,AttributeValue=TerminateInstances \
      --start-time "$(date -u -d '12 hours ago' +%Y-%m-%dT%H:%M:%SZ)" \
      --query "Events[?contains(CloudTrailEvent, '$id')].CloudTrailEvent | [0]" --output text 2>/dev/null || true)"
    [[ -n "$event" && "$event" != "None" ]] && break
    sleep 15
  done
  [[ -n "$event" && "$event" != "None" ]] || { warn "no TerminateInstances event for $id"; return 1; }
  echo "$event" | jq -e '.userIdentity.type == "AssumedRole"' >/dev/null || { warn "event actor is not AssumedRole"; return 1; }
  echo "$event" | jq -e '.sourceIPAddress' >/dev/null || { warn "event missing sourceIPAddress"; return 1; }
  ok "CloudTrail: $(echo "$event" | jq -r '.userIdentity.arn // .userIdentity.userName') from $(echo "$event" | jq -r '.sourceIPAddress')"
}
lab03_reset() { :; }
lab03_cleanup() {
  aws events remove-targets --rule "${LAB_PREFIX}-lab03-ec2-state" --ids 1 >/dev/null 2>&1 || true
  aws events delete-rule --name "${LAB_PREFIX}-lab03-ec2-state" >/dev/null 2>&1 || true
  if [[ -f "$ROOT/var/lab03-queue-url" ]]; then
    aws sqs delete-queue --queue-url "$(cat "$ROOT/var/lab03-queue-url")" >/dev/null 2>&1 || true
    rm -f "$ROOT/var/lab03-queue-url"
  fi
  destroy_canary "${LAB_PREFIX}-lab03-canary"
  rm -f "$ROOT/var/lab03-canary-instance"
}

# --------------------------------------------------------------- lab 04
lab04_build() {
  ensure_app_healthy
  local q rule_arn
  aws logs put-metric-filter --log-group-name "$(core_log_group)" \
    --filter-name "${LAB_PREFIX}-lab04-errors" \
    --filter-pattern '{ $.level = "ERROR" }' \
    --metric-transformations metricName=CapstoneErrorCount,metricNamespace=CloudOpsLab,metricValue=1,defaultValue=0 >/dev/null
  create_alarm "${LAB_PREFIX}-lab04-errors" CloudOpsLab CapstoneErrorCount "" "" 4 GreaterThanOrEqualToThreshold Sum 60 1
  q="$(create_sqs "${LAB_PREFIX}-lab04-events")"
  aws events put-rule --name "${LAB_PREFIX}-lab04-alarm" \
    --event-pattern "{\"source\":[\"aws.cloudwatch\"],\"detail-type\":[\"CloudWatch Alarm State Change\"],\"detail\":{\"alarmName\":[\"${LAB_PREFIX}-lab04-errors\"],\"state\":{\"value\":[\"ALARM\"]}}}" >/dev/null
  rule_arn="$(aws events describe-rule --name "${LAB_PREFIX}-lab04-alarm" --query Arn --output text)"
  set_sqs_policy "$q" events.amazonaws.com "$rule_arn"
  aws events put-targets --rule "${LAB_PREFIX}-lab04-alarm" \
    --targets "Id=1,Arn=$(queue_arn "$q")" >/dev/null
  printf '%s\n' "$q" > "$ROOT/var/lab04-queue-url"
}

lab04_break() {
  local url; url="$(app_url)"
  for _ in $(seq 1 12); do curl -s "$url/error" >/dev/null; done
  info "12 x HTTP 500"
}

lab04_verify() {
  local metric state msgs
  sleep 10
  metric="$(metric_sum CloudOpsLab CapstoneErrorCount)"
  wait_alarm "${LAB_PREFIX}-lab04-errors" ALARM 300 || true
  state="$(alarm_state "${LAB_PREFIX}-lab04-errors")"
  [[ "${metric%.*}" -ge 4 ]] || { warn "metric=$metric (<4)"; return 1; }
  [[ "$state" == "ALARM" ]] || { warn "alarm=$state"; return 1; }
  msgs="[]"
  for _ in $(seq 1 6); do
    msgs="$(aws sqs receive-message --queue-url "$(cat "$ROOT/var/lab04-queue-url")" --max-number-of-messages 5 --wait-time-seconds 5 --query 'Messages' --output json 2>/dev/null || echo '[]')"
    [[ "$msgs" != "[]" && -n "$msgs" ]] && break
    sleep 10
  done
  [[ "$msgs" != "[]" && -n "$msgs" ]] || { warn "no EventBridge message in SQS"; return 1; }
  ok "metric=$metric alarm=ALARM event=delivered"
}

lab04_reset() {
  aws events remove-targets --rule "${LAB_PREFIX}-lab04-alarm" --ids 1 >/dev/null 2>&1 || true
  aws events delete-rule --name "${LAB_PREFIX}-lab04-alarm" >/dev/null 2>&1 || true
  aws cloudwatch delete-alarms --alarm-names "${LAB_PREFIX}-lab04-errors" >/dev/null 2>&1 || true
  aws logs delete-metric-filter --log-group-name "$(core_log_group)" --filter-name "${LAB_PREFIX}-lab04-errors" >/dev/null 2>&1 || true
  if [[ -f "$ROOT/var/lab04-queue-url" ]]; then
    aws sqs delete-queue --queue-url "$(cat "$ROOT/var/lab04-queue-url")" >/dev/null 2>&1 || true
    rm -f "$ROOT/var/lab04-queue-url"
  fi
}
lab04_cleanup() { lab04_reset; }

# --------------------------------------------------------------- lab 05
lab05_build() {
  ensure_app_healthy
  set_health_check_path /health
}

lab05_break() {
  set_health_check_path /does-not-exist
  info "health check path changed. Wait ~45s, then test the URL."
  sleep 45
}

lab05_verify() {
  local path code healthy
  path="$(aws elbv2 describe-target-groups --target-group-arns "$(app_tg)" \
    --query 'TargetGroups[0].HealthCheckPath' --output text)"
  code="$(http_code "$(app_url)/health")"
  healthy="$(aws elbv2 describe-target-health --target-group-arn "$(app_tg)" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  [[ "$path" == "/health" ]] || { warn "health check path=$path"; return 1; }
  [[ "$code" == "200" ]] || { warn "app /health -> $code"; return 1; }
  [[ "$healthy" -ge 1 ]] || { warn "healthy targets=$healthy"; return 1; }
  ok "path=$path code=$code healthy=$healthy"
}

lab05_reset() { set_health_check_path /health; }
lab05_cleanup() { stack_exists "$APP_STACK" && lab05_reset || true; }

# --------------------------------------------------------------- lab 06
lab06_build() {
  ensure_app_healthy
  local lt ver saved_lt
  lt="$(stack_output_required "$APP_STACK" LaunchTemplateId)"
  ver="$(stack_output_required "$APP_STACK" LaunchTemplateVersion)"
  # Keep the original version across a re-run after `break 06` (which points
  # the ASG at a broken version). Only reset the saved copy if the app stack
  # was recreated and the launch template ID changed.
  saved_lt="$(cat "$ROOT/var/lab06-lt-id" 2>/dev/null || true)"
  if [[ -z "$saved_lt" || "$saved_lt" != "$lt" ]]; then
    printf '%s\n' "$lt" > "$ROOT/var/lab06-lt-id"
    printf '%s\n' "$ver" > "$ROOT/var/lab06-lt-version"
    # A previous session may have died after `break` left alarm-driven scaling
    # suspended. Resume only on a fresh app stack (the block above), so a
    # deliberate re-run after `break` keeps the fault in place.
    aws autoscaling resume-processes --auto-scaling-group-name "$(app_asg)" \
      --scaling-processes AlarmNotification >/dev/null 2>&1 || true
  fi
}

lab06_break() {
  local lt ver bad
  lt="$(cat "$ROOT/var/lab06-lt-id")"
  ver="$(cat "$ROOT/var/lab06-lt-version")"
  bad="$(printf '#!/bin/bash\nexit 1\n' | base64 | tr -d '\n')"
  # The app stack's CPU TargetTracking policy scales in when CPU is idle and
  # would pull desired capacity back to 1 within ~9 minutes. Worse, its default
  # termination policy picks the instance on the *oldest* launch template,
  # which is the only healthy one. Suspend alarm-driven scaling for the lab;
  # reset/cleanup resumes it.
  aws autoscaling suspend-processes --auto-scaling-group-name "$(app_asg)" \
    --scaling-processes AlarmNotification >/dev/null
  aws ec2 create-launch-template-version --launch-template-id "$lt" --source-version "$ver" \
    --launch-template-data "{\"UserData\":\"$bad\"}" >/dev/null
  aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$(app_asg)" \
    --launch-template "LaunchTemplateId=$lt,Version=\$Latest" >/dev/null
  aws autoscaling set-desired-capacity --auto-scaling-group-name "$(app_asg)" --desired-capacity 2 >/dev/null
  info "ASG now uses a launch template whose user-data exits 1. Wait for the new instance to fail its health check."
  sleep 60
}

lab06_verify() {
  local desired healthy lt_ver failed
  desired="$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$(app_asg)" \
    --query 'AutoScalingGroups[0].DesiredCapacity' --output text)"
  healthy="$(aws elbv2 describe-target-health --target-group-arn "$(app_tg)" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  lt_ver="$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$(app_asg)" \
    --query 'AutoScalingGroups[0].LaunchTemplate.Version' --output text)"
  # Bad user-data does not make the launch API fail: the instance starts and
  # then fails the ELB health check, so the ASG records the failed scale-out as
  # an ELB health-check replacement, not as StatusCode=Failed. Accept either.
  failed="$(aws autoscaling describe-scaling-activities --auto-scaling-group-name "$(app_asg)" \
    --max-items 50 --query "Activities[?StatusCode=='Failed' || contains(Cause, 'ELB system health check failure')] | length(@)" --output text 2>/dev/null || echo 0)"
  [[ "$desired" == "2" ]] || { warn "desired=$desired (expected 2)"; return 1; }
  [[ "$healthy" -ge 2 ]] || { warn "healthy=$healthy (expected 2)"; return 1; }
  [[ "$lt_ver" == "$(cat "$ROOT/var/lab06-lt-version")" ]] || { warn "launch template version=$lt_ver"; return 1; }
  [[ "${failed:-0}" -ge 1 ]] || { warn "no failed scale-out found (no Failed status, no ELB health-check replacement)"; return 1; }
  ok "desired=$desired healthy=$healthy template=$lt_ver failedActivities=$failed"
}

lab06_reset() {
  local lt ver
  lt="$(cat "$ROOT/var/lab06-lt-id" 2>/dev/null || true)"
  ver="$(cat "$ROOT/var/lab06-lt-version" 2>/dev/null || true)"
  [[ -n "$lt" && -n "$ver" ]] && aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name "$(app_asg)" \
    --launch-template "LaunchTemplateId=$lt,Version=$ver" >/dev/null 2>&1 || true
  aws autoscaling set-desired-capacity --auto-scaling-group-name "$(app_asg)" --desired-capacity 1 >/dev/null 2>&1 || true
  # Undo the suspension done by `break` so later labs (e.g. 01 CPU scale-out)
  # still get alarm-driven scaling.
  aws autoscaling resume-processes --auto-scaling-group-name "$(app_asg)" \
    --scaling-processes AlarmNotification >/dev/null 2>&1 || true
}
lab06_cleanup() {
  stack_exists "$APP_STACK" && lab06_reset || true
  rm -f "$ROOT/var/lab06-lt-id" "$ROOT/var/lab06-lt-version"
}

# --------------------------------------------------------------- lab 07
lab07_build() {
  ensure_app_healthy
  rds_psql "$(stack_output_required "$APP_STACK" DbEndpoint)" \
    "DROP TABLE IF EXISTS lab07; CREATE TABLE lab07(id int primary key, note text); INSERT INTO lab07 VALUES (1,'one'),(2,'two'),(3,'three'),(4,'four'),(5,'five');" >/dev/null
  # A previous `up` may have left the snapshot. Recreate it so the snapshot
  # always contains the fresh 5-row table instead of failing with
  # DBSnapshotAlreadyExists.
  if aws rds describe-db-snapshots --db-snapshot-identifier "${LAB_PREFIX}-lab07-snapshot" >/dev/null 2>&1; then
    info "replacing existing snapshot ${LAB_PREFIX}-lab07-snapshot"
    aws rds delete-db-snapshot --db-snapshot-identifier "${LAB_PREFIX}-lab07-snapshot" >/dev/null
    aws rds wait db-snapshot-deleted --db-snapshot-identifier "${LAB_PREFIX}-lab07-snapshot" 2>/dev/null || true
  fi
  aws rds create-db-snapshot --db-instance-identifier "$(db_id)" \
    --db-snapshot-identifier "${LAB_PREFIX}-lab07-snapshot" >/dev/null
  info "waiting for snapshot ${LAB_PREFIX}-lab07-snapshot"
  aws rds wait db-snapshot-completed --db-snapshot-identifier "${LAB_PREFIX}-lab07-snapshot"
}

lab07_break() {
  rds_psql "$(stack_output_required "$APP_STACK" DbEndpoint)" "DELETE FROM lab07;" >/dev/null
  info "rows deleted. Restore the snapshot to a new DB named ${LAB_PREFIX}-lab07-restored."
}

lab07_verify() {
  local status rows
  status="$(aws rds describe-db-instances --db-instance-identifier "${LAB_PREFIX}-lab07-restored" \
    --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo MISSING)"
  [[ "$status" == "available" ]] || { warn "restored DB status=$status (create ${LAB_PREFIX}-lab07-restored)"; return 1; }
  local endpoint restored_secret
  endpoint="$(aws rds describe-db-instances --db-instance-identifier "${LAB_PREFIX}-lab07-restored" \
    --query 'DBInstances[0].Endpoint.Address' --output text)"
  restored_secret="$(aws rds describe-db-instances --db-instance-identifier "${LAB_PREFIX}-lab07-restored" \
    --query 'DBInstances[0].MasterUserSecret.SecretArn' --output text 2>/dev/null || true)"
  [[ -n "$restored_secret" && "$restored_secret" != "None" ]] || restored_secret="$(db_secret_arn)"
  rows="$(rds_psql_secret "$endpoint" "$restored_secret" "SELECT count(*) FROM lab07;" | tr -dc '0-9')"
  [[ "${rows:-0}" -ge 5 ]] || { warn "restored row count=$rows"; return 1; }
  ok "restored DB available, lab07 rows=$rows"
}

lab07_reset() {
  aws rds delete-db-instance --db-instance-identifier "${LAB_PREFIX}-lab07-restored" \
    --skip-final-snapshot --delete-automated-backups >/dev/null 2>&1 || true
  rds_psql "$(stack_output_required "$APP_STACK" DbEndpoint)" \
    "DROP TABLE IF EXISTS lab07; CREATE TABLE lab07(id int primary key, note text); INSERT INTO lab07 VALUES (1,'one'),(2,'two'),(3,'three'),(4,'four'),(5,'five');" >/dev/null 2>&1 || true
}
lab07_cleanup() {
  lab07_reset
  aws rds delete-db-snapshot --db-snapshot-identifier "${LAB_PREFIX}-lab07-snapshot" >/dev/null 2>&1 || true
}

# --------------------------------------------------------------- lab 08
lab08_build() {
  ensure_app_healthy
  local multi
  aws rds wait db-instance-available --db-instance-identifier "$(db_id)" 2>/dev/null || true
  multi="$(aws rds describe-db-instances --db-instance-identifier "$(db_id)" \
    --query 'DBInstances[0].MultiAZ' --output text)"
  if [[ "$multi" == "True" ]]; then
    info "RDS is already Multi-AZ; nothing to modify"
    return 0
  fi
  aws rds modify-db-instance --db-instance-identifier "$(db_id)" \
    --multi-az --apply-immediately >/dev/null
  info "waiting for Multi-AZ modification (up to 12 minutes)"
  aws rds wait db-instance-available --db-instance-identifier "$(db_id)"
}

lab08_break() {
  aws rds reboot-db-instance --db-instance-identifier "$(db_id)" --force-failover >/dev/null
  info "failover requested. Measure RTO: time until $(app_url)/db returns 200."
}

lab08_verify() {
  local az available events code
  az="$(aws rds describe-db-instances --db-instance-identifier "$(db_id)" \
    --query 'DBInstances[0].MultiAZ' --output text)"
  available="$(aws rds describe-db-instances --db-instance-identifier "$(db_id)" \
    --query 'DBInstances[0].DBInstanceStatus' --output text)"
  events="$(aws rds describe-events --source-identifier "$(db_id)" --source-type db-instance \
    --duration 30 --query "Events[?contains(Message, 'failover')] | length(@)" --output text 2>/dev/null || echo 0)"
  wait_until 120 5 bash -c "[[ \"\$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 '$(app_url)/db')\" == 200 ]]" || true
  code="$(http_code "$(app_url)/db" 15)"
  [[ "$az" == "True" ]] || { warn "MultiAZ=$az"; return 1; }
  [[ "$available" == "available" ]] || { warn "DB status=$available"; return 1; }
  [[ "${events:-0}" -ge 1 ]] || { warn "no failover event"; return 1; }
  [[ "$code" == "200" ]] || { warn "app /db -> $code"; return 1; }
  ok "MultiAZ=$az status=$available failoverEvent=yes app/db=200"
}

lab08_reset() {
  aws rds modify-db-instance --db-instance-identifier "$(db_id)" \
    --no-multi-az --apply-immediately >/dev/null 2>&1 || true
  aws rds wait db-instance-available --db-instance-identifier "$(db_id)" 2>/dev/null || true
}
lab08_cleanup() { stack_exists "$APP_STACK" && lab08_reset || true; }

# --------------------------------------------------------------- lab 09
lab09_build() {
  ensure_app_healthy
  ensure_ssm_online >/dev/null
  aws ssm put-parameter --name "/${LAB_PREFIX}/lab09/message" \
    --value "hello-from-parameter-store" --type String --overwrite >/dev/null
}

lab09_break() {
  local id; id="$(app_instance_required)"
  ssm_run "$id" <<'EOS'
systemctl stop cloudops-app
EOS
  info "cloudops-app stopped via SSM Run Command. No SSH was used."
}

lab09_verify() {
  local id state code value
  id="$(app_instance_required)"
  state="$(ssm_run "$id" <<'EOS'
systemctl is-active cloudops-app
EOS
)"
  code="$(http_code "$(app_url)/health")"
  value="$(aws ssm get-parameter --name "/${LAB_PREFIX}/lab09/message" --query Parameter.Value --output text)"
  [[ "$state" == "active" ]] || { warn "service state=$state"; return 1; }
  [[ "$code" == "200" ]] || { warn "app health=$code"; return 1; }
  [[ "$value" == "hello-from-parameter-store" ]] || { warn "parameter value=$value"; return 1; }
  ok "service=$state health=$code parameter=$value"
}

lab09_reset() {
  local id; id="$(app_instance_required 2>/dev/null || true)"
  [[ -n "$id" ]] && ssm_run "$id" <<'EOS' >/dev/null 2>&1 || true
systemctl start cloudops-app
EOS
}
lab09_cleanup() {
  stack_exists "$APP_STACK" && lab09_reset || true
  aws ssm delete-parameter --name "/${LAB_PREFIX}/lab09/message" >/dev/null 2>&1 || true
}

# --------------------------------------------------------------- lab 10
lab10_build() {
  ensure_app_healthy
  local role secret bucket
  role="$(app_role_name)"
  bucket="$(core_bucket)"
  secret="$(aws secretsmanager create-secret --name "/${LAB_PREFIX}/lab10/api-key" \
    --description "lab10" --secret-string "lab10-$(date +%s)" \
    --query ARN --output text 2>/dev/null || \
    aws secretsmanager describe-secret --secret-id "/${LAB_PREFIX}/lab10/api-key" --query ARN --output text)"
  printf '%s\n' "$secret" > "$ROOT/var/lab10-secret-arn"
  printf 'kms-lab-object\n' > "$ROOT/var/lab10-object.txt"
  aws s3 cp "$ROOT/var/lab10-object.txt" "s3://$bucket/lab10/secret.txt" \
    --sse aws:kms --sse-kms-key-id "$(core_kms_id)" --only-show-errors >/dev/null

  if ! aws iam get-role --role-name "${LAB_PREFIX}-lab10-reader" >/dev/null 2>&1; then
    aws iam create-role --role-name "${LAB_PREFIX}-lab10-reader" \
      --assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::${LAB_ACCOUNT_ID}:root\"},\"Action\":\"sts:AssumeRole\"}]}" >/dev/null
  fi
  local role_arn="arn:aws:iam::${LAB_ACCOUNT_ID}:role/${LAB_PREFIX}-lab10-reader"
  aws iam put-role-policy --role-name "${LAB_PREFIX}-lab10-reader" --policy-name lab10-read \
    --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::${bucket}/lab10/*\"},{\"Effect\":\"Allow\",\"Action\":[\"secretsmanager:GetSecretValue\"],\"Resource\":\"${secret}\"}]}" >/dev/null

  # Keep an untouched copy of the key policy. If `up 10` is run again after a
  # `break 10`, the current policy already contains Lab10Deny; saving that as
  # "original" would make `down 10` restore the deny and wedge the lab.
  if [[ ! -f "$ROOT/var/lab10-key-original.json" ]]; then
    aws kms get-key-policy --key-id "$(core_kms_id)" --policy-name default --query Policy --output text \
      > "$ROOT/var/lab10-key-raw.json"
    jq '.Statement |= map(select(((.Sid // "") | startswith("Lab10")) | not))' \
      "$ROOT/var/lab10-key-raw.json" > "$ROOT/var/lab10-key-original.json"
    rm -f "$ROOT/var/lab10-key-raw.json"
  fi
  # Start from the clean policy, then add the reader allow.
  aws kms put-key-policy --key-id "$(core_kms_id)" --policy-name default \
    --policy file://"$ROOT/var/lab10-key-original.json" >/dev/null
  jq --arg arn "$role_arn" '.Statement += [{"Sid":"Lab10Reader","Effect":"Allow","Principal":{"AWS":$arn},"Action":["kms:Decrypt","kms:GenerateDataKey"],"Resource":"*"}]' \
    "$ROOT/var/lab10-key-original.json" > "$ROOT/var/lab10-key-allow.json"
  # IAM is eventually consistent: a role created a few seconds ago can still be
  # rejected by KMS as an "invalid principal" (MalformedPolicyDocumentException).
  # Retry briefly instead of failing the whole `up 10`.
  if ! wait_until 60 5 bash -c "aws kms put-key-policy --key-id '$(core_kms_id)' --policy-name default --policy file://'$ROOT/var/lab10-key-allow.json' >/dev/null 2>&1"; then
    aws kms put-key-policy --key-id "$(core_kms_id)" --policy-name default \
      --policy file://"$ROOT/var/lab10-key-allow.json" >/dev/null
  fi
}

lab10_break() {
  local role_arn="arn:aws:iam::${LAB_ACCOUNT_ID}:role/${LAB_PREFIX}-lab10-reader"
  jq --arg arn "$role_arn" '.Statement += [{"Sid":"Lab10Deny","Effect":"Deny","Principal":{"AWS":$arn},"Action":"kms:*","Resource":"*"}]' \
    "$ROOT/var/lab10-key-allow.json" > "$ROOT/var/lab10-key-deny.json"
  aws kms put-key-policy --key-id "$(core_kms_id)" --policy-name default \
    --policy file://"$ROOT/var/lab10-key-deny.json" >/dev/null
  info "KMS key policy now has an explicit deny for ${LAB_PREFIX}-lab10-reader"
}

lab10_verify() {
  local role_arn bucket secret out env
  role_arn="arn:aws:iam::${LAB_ACCOUNT_ID}:role/${LAB_PREFIX}-lab10-reader"
  bucket="$(core_bucket)"
  secret="$(cat "$ROOT/var/lab10-secret-arn" 2>/dev/null || true)"
  env="$(assume_role_env "$role_arn" lab10-verify)" \
    || { warn "AssumeRole failed for ${LAB_PREFIX}-lab10-reader"; return 1; }
  eval "$env"
  out="$(aws s3 cp "s3://$bucket/lab10/secret.txt" - 2>&1)" || { warn "S3 read failed: $out"; return 1; }
  aws secretsmanager get-secret-value --secret-id "$secret" --query SecretString --output text >/dev/null 2>&1 \
    || { warn "secret read failed"; return 1; }
  ok "role ${LAB_PREFIX}-lab10-reader decrypted S3 object and read the secret"
}

lab10_reset() {
  [[ -f "$ROOT/var/lab10-key-original.json" ]] && aws kms put-key-policy \
    --key-id "$(core_kms_id)" --policy-name default \
    --policy file://"$ROOT/var/lab10-key-original.json" >/dev/null 2>&1 || true
}

lab10_cleanup() {
  lab10_reset
  aws iam delete-role-policy --role-name "${LAB_PREFIX}-lab10-reader" --policy-name lab10-read >/dev/null 2>&1 || true
  aws iam delete-role --role-name "${LAB_PREFIX}-lab10-reader" >/dev/null 2>&1 || true
  [[ -f "$ROOT/var/lab10-secret-arn" ]] && aws secretsmanager delete-secret \
    --secret-id "$(cat "$ROOT/var/lab10-secret-arn")" --force-delete-without-recovery >/dev/null 2>&1 || true
  aws s3 rm "s3://$(core_bucket)/lab10/secret.txt" >/dev/null 2>&1 || true
  rm -f "$ROOT/var/lab10-secret-arn" "$ROOT/var/lab10-object.txt" \
        "$ROOT/var/lab10-key-original.json" "$ROOT/var/lab10-key-allow.json" \
        "$ROOT/var/lab10-key-deny.json" "$ROOT/var/lab10-key-raw.json"
}

# --------------------------------------------------------------- lab 11
lab11_build() {
  require_core
  local dir="$ROOT/labs/11-cloudformation-cdk"
  aws cloudformation deploy --stack-name "${LAB_PREFIX}-lab11" \
    --template-file "$dir/template.yaml" \
    --parameter-overrides "ProjectName=$LAB_PREFIX" "ExpiryDate=$EXPIRY_DATE" \
    --tags $LAB_TAGS --no-fail-on-empty-changeset
}

lab11_break() {
  local dir="$ROOT/labs/11-cloudformation-cdk"
  info "updating stack with a broken template; rollback is expected"
  aws cloudformation update-stack --stack-name "${LAB_PREFIX}-lab11" \
    --template-body "file://$dir/template-broken.yaml" \
    --parameters "ParameterKey=ProjectName,ParameterValue=$LAB_PREFIX" \
                 "ParameterKey=ExpiryDate,ParameterValue=$EXPIRY_DATE" >/dev/null 2>&1 || true
  sleep 15
  aws cloudformation describe-stack-events --stack-name "${LAB_PREFIX}-lab11" \
    --max-items 5 --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
    --output table 2>/dev/null || true
}

lab11_verify() {
  local status
  for _ in $(seq 1 60); do
    status="$(stack_status "${LAB_PREFIX}-lab11")"
    [[ "$status" != *IN_PROGRESS* ]] && break
    sleep 5
  done
  [[ "$status" == "UPDATE_COMPLETE" || "$status" == "CREATE_COMPLETE" ]] || { warn "stack status=$status"; return 1; }
  aws cloudformation describe-stacks --stack-name "${LAB_PREFIX}-lab11" \
    --query 'Stacks[0].Outputs' --output table >/dev/null || return 1
  ok "stack ${LAB_PREFIX}-lab11 status=$status (rollback recovered)"
}

lab11_reset() {
  local dir="$ROOT/labs/11-cloudformation-cdk"
  aws cloudformation update-stack --stack-name "${LAB_PREFIX}-lab11" \
    --template-body "file://$dir/template.yaml" \
    --parameters "ParameterKey=ProjectName,ParameterValue=$LAB_PREFIX" \
                 "ParameterKey=ExpiryDate,ParameterValue=$EXPIRY_DATE" >/dev/null 2>&1 || true
  aws cloudformation wait stack-update-complete --stack-name "${LAB_PREFIX}-lab11" 2>/dev/null || true
}

lab11_cleanup() {
  if stack_exists "${LAB_PREFIX}-lab11"; then
    local bucket
    bucket="$(aws cloudformation describe-stacks --stack-name "${LAB_PREFIX}-lab11" \
      --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text 2>/dev/null || true)"
    [[ -n "$bucket" ]] && aws s3 rm "s3://$bucket" --recursive >/dev/null 2>&1 || true
    aws cloudformation delete-stack --stack-name "${LAB_PREFIX}-lab11"
    aws cloudformation wait stack-delete-complete --stack-name "${LAB_PREFIX}-lab11" 2>/dev/null || true
  fi
}

# --------------------------------------------------------------- lab 12
lab12_build() {
  ensure_app_healthy
  local role fn_arn rule_arn q id dir zip
  role="$(stack_output_required "$CORE_STACK" LambdaRemediationRoleArn)"
  q="$(create_sqs "${LAB_PREFIX}-lab12-events")"
  printf '%s\n' "$q" > "$ROOT/var/lab12-queue-url"
  dir="$ROOT/var/lab12"; mkdir -p "$dir"
  cat > "$dir/index.py" <<'PY'
import boto3
ec2 = boto3.client("ec2")

def handler(event, context):
    detail = event.get("detail", {})
    if detail.get("state") != "stopped":
        return {"skipped": True}
    instance_id = detail.get("instance-id")
    if not instance_id:
        return {"error": "no instance-id"}
    info = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    tags = {t["Key"]: t["Value"] for t in info.get("Tags", [])}
    if tags.get("auto-remediate") != "true":
        print(f"skip {instance_id}: auto-remediate != true")
        return {"skipped": True, "instance": instance_id}
    ec2.start_instances(InstanceIds=[instance_id])
    print(f"started {instance_id}")
    return {"started": instance_id}
PY
  zip="$ROOT/var/lab12.zip"; lambda_zip "$dir/index.py" "$zip"
  aws lambda delete-function --function-name "${LAB_PREFIX}-lab12-remediate" >/dev/null 2>&1 || true
  aws lambda create-function --function-name "${LAB_PREFIX}-lab12-remediate" \
    --runtime python3.12 --handler index.handler --role "$role" \
    --zip-file "fileb://$zip" --timeout 30 --memory-size 128 >/dev/null
  fn_arn="$(aws lambda get-function --function-name "${LAB_PREFIX}-lab12-remediate" --query Configuration.FunctionArn --output text)"

  aws events put-rule --name "${LAB_PREFIX}-lab12-remediate" \
    --event-pattern '{"source":["aws.ec2"],"detail-type":["EC2 Instance State-change Notification"],"detail":{"state":["stopped"]}}' >/dev/null
  rule_arn="$(aws events describe-rule --name "${LAB_PREFIX}-lab12-remediate" --query Arn --output text)"
  aws lambda remove-permission --function-name "${LAB_PREFIX}-lab12-remediate" \
    --statement-id lab12-events >/dev/null 2>&1 || true
  aws lambda add-permission --function-name "${LAB_PREFIX}-lab12-remediate" \
    --statement-id lab12-events --action lambda:InvokeFunction \
    --principal events.amazonaws.com --source-arn "$rule_arn" >/dev/null
  set_sqs_policy "$q" events.amazonaws.com "$rule_arn"
  aws events put-targets --rule "${LAB_PREFIX}-lab12-remediate" \
    --targets "Id=1,Arn=$fn_arn" "Id=2,Arn=$(queue_arn "$q")" >/dev/null

  id="$(create_canary "${LAB_PREFIX}-lab12-canary")"
  aws ec2 create-tags --resources "$id" --tags "Key=auto-remediate,Value=true" >/dev/null
  printf '%s\n' "$id" > "$ROOT/var/lab12-canary-instance"
}

lab12_break() {
  aws ec2 stop-instances --instance-ids "$(cat "$ROOT/var/lab12-canary-instance")" >/dev/null
  info "canary stopped. EventBridge → Lambda should start it again."
}

lab12_verify() {
  local id state logs msgs
  id="$(cat "$ROOT/var/lab12-canary-instance")"
  wait_until 180 10 bash -c "[[ \"\$(aws ec2 describe-instances --instance-ids '$id' --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null)\" == running ]]" \
    || { warn "canary is not running"; return 1; }
  state="$(aws ec2 describe-instances --instance-ids "$id" --query 'Reservations[0].Instances[0].State.Name' --output text)"
  logs=""
  for _ in $(seq 1 10); do
    logs="$(aws logs filter-log-events --log-group-name "/aws/lambda/${LAB_PREFIX}-lab12-remediate" \
      --start-time "$(date -u -d '10 minutes ago' +%s000)" \
      --filter-pattern "started" --query 'events[].message' --output text 2>/dev/null || true)"
    [[ -n "$logs" ]] && break
    sleep 10
  done
  msgs="$(aws sqs receive-message --queue-url "$(cat "$ROOT/var/lab12-queue-url")" \
    --max-number-of-messages 5 --wait-time-seconds 5 --query 'Messages' --output json 2>/dev/null || echo '[]')"
  [[ "$state" == "running" ]] || { warn "state=$state"; return 1; }
  [[ -n "$logs" ]] || { warn "no Lambda log line with 'started'"; return 1; }
  [[ "$msgs" != "[]" && -n "$msgs" ]] || { warn "no EventBridge message"; return 1; }
  ok "canary=running lambda=started event=delivered"
}

lab12_reset() {
  [[ -f "$ROOT/var/lab12-canary-instance" ]] && aws ec2 start-instances \
    --instance-ids "$(cat "$ROOT/var/lab12-canary-instance")" >/dev/null 2>&1 || true
}

lab12_cleanup() {
  lab12_reset
  aws events remove-targets --rule "${LAB_PREFIX}-lab12-remediate" --ids 1 2 >/dev/null 2>&1 || true
  aws events delete-rule --name "${LAB_PREFIX}-lab12-remediate" >/dev/null 2>&1 || true
  aws lambda delete-function --function-name "${LAB_PREFIX}-lab12-remediate" >/dev/null 2>&1 || true
  [[ -f "$ROOT/var/lab12-queue-url" ]] && aws sqs delete-queue \
    --queue-url "$(cat "$ROOT/var/lab12-queue-url")" >/dev/null 2>&1 || true
  destroy_canary "${LAB_PREFIX}-lab12-canary"
  rm -f "$ROOT/var/lab12-queue-url" "$ROOT/var/lab12-canary-instance" "$ROOT/var/lab12.zip"
}

# --------------------------------------------------------------- lab 13
lab13_build() {
  require_core
  local bucket trust
  bucket="$(core_bucket)"
  trust="{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::${LAB_ACCOUNT_ID}:root\"},\"Action\":\"sts:AssumeRole\"}]}"
  printf '%s\n' "$trust" > "$ROOT/var/lab13-trust-good.json"
  aws iam create-role --role-name "${LAB_PREFIX}-lab13-target" \
    --assume-role-policy-document file://"$ROOT/var/lab13-trust-good.json" >/dev/null 2>&1 || true
  aws iam put-role-policy --role-name "${LAB_PREFIX}-lab13-target" --policy-name lab13-s3 \
    --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:ListBucket\"],\"Resource\":\"arn:aws:s3:::${bucket}\"},{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::${bucket}/*\"}]}" >/dev/null
}

lab13_break() {
  local bad arn principal
  # A trust policy must name a principal that exists: aws rejects unknown
  # account IDs and unknown role ARNs ("Invalid principal in policy"), which
  # made the old break a silent no-op. A Condition is always accepted and
  # denies this session because it never authenticates with MFA.
  bad="{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::${LAB_ACCOUNT_ID}:root\"},\"Action\":\"sts:AssumeRole\",\"Condition\":{\"Bool\":{\"aws:MultiFactorAuthPresent\":\"true\"}}}]}"
  printf '%s\n' "$bad" > "$ROOT/var/lab13-trust-bad.json"
  aws iam update-assume-role-policy --role-name "${LAB_PREFIX}-lab13-target" \
    --policy-document file://"$ROOT/var/lab13-trust-bad.json" >/dev/null \
    || { warn "could not update trust policy — fault NOT injected"; return 1; }
  principal="$(aws iam get-role --role-name "${LAB_PREFIX}-lab13-target" \
    --query 'Role.AssumeRolePolicyDocument.Statement[0].Condition.Bool."aws:MultiFactorAuthPresent"' \
    --output text 2>/dev/null)"
  [[ "$principal" == "true" ]] || { warn "trust policy unchanged — fault NOT injected"; return 1; }
  # IAM is eventually consistent: assume-role can still succeed for a few
  # seconds. Wait until the denial is observable, otherwise the learner starts
  # the 20-minute diagnosis on a role that still works.
  arn="arn:aws:iam::${LAB_ACCOUNT_ID}:role/${LAB_PREFIX}-lab13-target"
  wait_until 60 5 bash -c "! aws sts assume-role --role-arn '$arn' --role-session-name lab13-break-probe >/dev/null 2>&1" \
    || { warn "AssumeRole still succeeds — fault NOT observed"; return 1; }
  info "trust policy now carries an extra Condition"
}

lab13_verify() {
  local arn env bucket
  arn="arn:aws:iam::${LAB_ACCOUNT_ID}:role/${LAB_PREFIX}-lab13-target"
  # Read the bucket BEFORE assuming the role: the role only has S3 permissions,
  # so a cloudformation call made with its credentials returns AccessDenied and
  # the bucket name would be empty.
  bucket="$(core_bucket)"
  env="$(assume_role_env "$arn" lab13-verify)" \
    || { warn "AssumeRole failed (trust policy?)"; return 1; }
  eval "$env"
  aws sts get-caller-identity --query Arn --output text | grep -q "assumed-role/${LAB_PREFIX}-lab13-target" \
    || { warn "unexpected identity"; return 1; }
  # `aws s3 ls s3://bucket` pages the whole CloudTrail keyspace and hangs (>60s
  # measured). A delimiter call needs the same s3:ListBucket permission but returns
  # in ~1s.
  aws s3api list-objects-v2 --bucket "$bucket" --delimiter / --max-keys 5 >/dev/null \
    || { warn "S3 access failed"; return 1; }
  ok "AssumeRole works and role can list S3"
}

lab13_reset() {
  [[ -f "$ROOT/var/lab13-trust-good.json" ]] && aws iam update-assume-role-policy \
    --role-name "${LAB_PREFIX}-lab13-target" \
    --policy-document file://"$ROOT/var/lab13-trust-good.json" >/dev/null 2>&1 || true
}

lab13_cleanup() {
  aws iam delete-role-policy --role-name "${LAB_PREFIX}-lab13-target" --policy-name lab13-s3 >/dev/null 2>&1 || true
  aws iam delete-role --role-name "${LAB_PREFIX}-lab13-target" >/dev/null 2>&1 || true
  rm -f "$ROOT/var/lab13-trust-good.json" "$ROOT/var/lab13-trust-bad.json"
}

# --------------------------------------------------------------- lab 14
lab14_build() {
  require_core
  local bucket="${LAB_PREFIX}-lab14-${LAB_ACCOUNT_ID}"
  printf '%s\n' "$bucket" > "$ROOT/var/lab14-bucket"
  if ! aws s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; then
    if [[ "$AWS_REGION" == "us-east-1" ]]; then
      aws s3api create-bucket --bucket "$bucket" >/dev/null
    else
      aws s3api create-bucket --bucket "$bucket" \
        --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
    fi
  fi
  aws s3api put-public-access-block --bucket "$bucket" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
  printf 'lab14-secret\n' > "$ROOT/var/lab14-object.txt"
  aws s3api put-object --bucket "$bucket" --key secret.txt --body "$ROOT/var/lab14-object.txt" >/dev/null
  aws s3api put-bucket-tagging --bucket "$bucket" \
    --tagging "TagSet=[{Key=Project,Value=$LAB_PREFIX},{Key=ExpiryDate,Value=$EXPIRY_DATE}]" >/dev/null 2>&1 || true
  if ! aws accessanalyzer list-analyzers --query "analyzers[?name=='${LAB_PREFIX}-lab14'].arn" --output text 2>/dev/null | grep -q .; then
    aws accessanalyzer create-analyzer --analyzer-name "${LAB_PREFIX}-lab14" --type ACCOUNT >/dev/null 2>&1 || true
  fi
}

lab14_break() {
  local bucket; bucket="$(cat "$ROOT/var/lab14-bucket")"
  aws s3api put-public-access-block --bucket "$bucket" \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
  aws s3api put-bucket-policy --bucket "$bucket" --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicRead\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::${bucket}/*\"}]}"
  info "bucket is now public. Prove it with the object URL, then fix it."
}

lab14_verify() {
  local bucket bpa status code
  bucket="$(cat "$ROOT/var/lab14-bucket")"
  bpa="$(aws s3api get-public-access-block --bucket "$bucket" --query 'PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]' --output text | tr '\t' ' ')"
  status="$(aws s3api get-bucket-policy-status --bucket "$bucket" --query 'PolicyStatus.IsPublic' --output text 2>/dev/null || echo MISSING)"
  code="$(curl -s -o /dev/null -w '%{http_code}' "https://${bucket}.s3.${AWS_REGION}.amazonaws.com/secret.txt" || true)"
  [[ "$bpa" == "True True True True" ]] || { warn "BPA=$bpa"; return 1; }
  [[ "$status" != "True" ]] || { warn "policy public=$status"; return 1; }
  [[ "$code" == "403" ]] || { warn "anonymous access returned $code (expected 403)"; return 1; }
  ok "BPA on, policy private, anonymous=$code"
}

lab14_reset() {
  local bucket; bucket="$(cat "$ROOT/var/lab14-bucket" 2>/dev/null || true)"
  [[ -n "$bucket" ]] && aws s3api put-public-access-block --bucket "$bucket" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" >/dev/null 2>&1 || true
  [[ -n "$bucket" ]] && aws s3api delete-bucket-policy --bucket "$bucket" >/dev/null 2>&1 || true
}

lab14_cleanup() {
  lab14_reset
  local bucket analyzer
  bucket="$(cat "$ROOT/var/lab14-bucket" 2>/dev/null || true)"
  if [[ -n "$bucket" ]]; then
    aws s3 rm "s3://$bucket" --recursive >/dev/null 2>&1 || true
    aws s3api delete-bucket --bucket "$bucket" >/dev/null 2>&1 || true
  fi
  analyzer="$(aws accessanalyzer list-analyzers --query "analyzers[?name=='${LAB_PREFIX}-lab14'].arn" --output text 2>/dev/null || true)"
  # delete-analyzer takes --analyzer-name (not --analyzer-arn); the wrong flag failed
  # silently and left the analyzer behind.
  [[ -n "$analyzer" ]] && aws accessanalyzer delete-analyzer --analyzer-name "${LAB_PREFIX}-lab14" >/dev/null 2>&1 || true
  if aws accessanalyzer list-analyzers --query "analyzers[?name=='${LAB_PREFIX}-lab14'].arn" --output text 2>/dev/null | grep -q .; then
    warn "analyzer ${LAB_PREFIX}-lab14 still exists — delete it manually"
  fi
  rm -f "$ROOT/var/lab14-bucket" "$ROOT/var/lab14-object.txt"
}

# --------------------------------------------------------------- lab 15
# Every analysis path this lab could have created (ALB -> app, TCP 8080).
# Lab 15 is the only creator of such paths, so they are safe to replace/delete.
lab15_all_paths() {
  aws ec2 describe-network-insights-paths \
    --filters "Name=source,Values=$(alb_eni)" \
    --query 'NetworkInsightsPaths[?DestinationPort==`8080`].NetworkInsightsPathId' \
    --output text 2>/dev/null || true
}

# Path that points at the *live* app instance. Empty when it still targets a
# terminated ENI: the ASG replaces the instance when health checks fail, which
# is exactly what this lab's fault causes.
lab15_path_id() {
  local id app_e
  app_e="$(app_eni)"
  for id in $(lab15_all_paths); do
    [[ "$id" =~ ^nip- ]] || continue
    if [[ "$(aws ec2 describe-network-insights-paths --network-insights-path-ids "$id" \
        --query 'NetworkInsightsPaths[0].Destination' --output text 2>/dev/null || true)" == "$app_e" ]]; then
      printf '%s' "$id"
      return 0
    fi
  done
  return 0
}

lab15_delete_paths() {
  local id a n
  for id in $(lab15_all_paths); do
    [[ "$id" =~ ^nip- ]] || continue
    # DeleteNetworkInsightsPath fails with AnalysisExistsForNetworkInsightsPath
    # while any analysis exists, and an analysis can still be running.
    # DescribeNetworkInsightsAnalyses only accepts the filters status/path-found,
    # so match the path client-side.
    for a in $(aws ec2 describe-network-insights-analyses \
        --query "NetworkInsightsAnalyses[?NetworkInsightsPathId=='$id'].NetworkInsightsAnalysisId" \
        --output text 2>/dev/null || true); do
      [[ "$a" =~ ^nia- ]] || continue
      for n in 1 2 3 4 5 6; do
        aws ec2 delete-network-insights-analysis --network-insights-analysis-id "$a" >/dev/null 2>&1 && break
        sleep 10
      done
      if aws ec2 describe-network-insights-analyses --network-insights-analysis-ids "$a" \
          --query 'NetworkInsightsAnalyses[0].NetworkInsightsAnalysisId' --output text 2>/dev/null | grep -q '^nia-'; then
        warn "could not delete analysis $a"
      fi
    done
    aws ec2 delete-network-insights-path --network-insights-path-id "$id" >/dev/null 2>&1 \
      || warn "could not delete path $id"
  done
  rm -f "$ROOT/var/lab15-path"
}

# Create the path and record it. Prints the id; dies only if nothing works.
# Tags go in the create call: a separate create-tags was silently swallowed by
# `|| true` when the CLI returned an empty id (transient DNS failure).
lab15_create_path() {
  local alb_e app_e path
  alb_e="$(alb_eni)"; app_e="$(app_eni)"
  [[ "$alb_e" =~ ^eni- ]] || die "cannot find ALB ENI"
  [[ "$app_e" =~ ^eni- ]] || die "cannot find app ENI"
  path="$(aws ec2 create-network-insights-path \
    --source "$alb_e" --destination "$app_e" \
    --protocol tcp --destination-port 8080 \
    --tag-specifications "ResourceType=network-insights-path,Tags=[{Key=Name,Value=${LAB_PREFIX}-lab15-path},{Key=Project,Value=${LAB_PREFIX}},{Key=ExpiryDate,Value=$EXPIRY_DATE}]" \
    --query NetworkInsightsPathId --output text 2>/dev/null || true)"
  if [[ ! "$path" =~ ^nip- ]]; then
    warn "create-network-insights-path returned '${path}'; looking for an existing path"
    path="$(lab15_path_id)"
  fi
  [[ "$path" =~ ^nip- ]] || die "cannot create or find the lab15 reachability path"
  printf '%s\n' "$path" > "$ROOT/var/lab15-path"
  printf '%s' "$path"
}

lab15_build() {
  ensure_app_healthy
  enable_lab_flow_logs lab15
  # Re-running `up` must replace the previous analysis path, not bill for a
  # second one.
  lab15_delete_paths
  lab15_create_path >/dev/null
}

# Verify runs after the learner fixed the SG, i.e. often after the ASG already
# replaced the instance — so re-create the path when it targets a dead ENI.
lab15_ensure_path() {
  local id
  id="$(lab15_path_id)"
  if [[ -n "$id" ]]; then printf '%s' "$id"; return 0; fi
  # warn(), not info(): info() writes to stdout and would corrupt the $(...) value
  warn "reachability path points at a replaced instance; recreating it"
  lab15_delete_paths
  lab15_create_path
}

lab15_break() {
  revoke_app_8080
  info "app SG no longer allows 8080 from the ALB SG"
}

lab15_verify() {
  local path analysis status found rule code
  rule="$(aws ec2 describe-security-groups --group-ids "$(app_sg_id)" \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`8080\`] | length(@)" --output text)"
  code="$(http_code "$(app_url)/health")"
  [[ "$rule" -ge 1 ]] || { warn "app SG is missing 8080 ingress"; return 1; }
  [[ "$code" == "200" ]] || { warn "app health=$code"; return 1; }
  path="$(lab15_ensure_path)"
  [[ -n "$path" ]] || { warn "no Reachability Analyzer path; run ./bin/lab up 15"; return 1; }
  analysis="$(aws ec2 start-network-insights-analysis --network-insights-path-id "$path" \
    --query 'NetworkInsightsAnalysis.NetworkInsightsAnalysisId' --output text 2>/dev/null || true)"
  [[ "$analysis" =~ ^nia- ]] || { warn "cannot start analysis on path $path"; return 1; }
  for _ in $(seq 1 30); do
    status="$(aws ec2 describe-network-insights-analyses --network-insights-analysis-ids "$analysis" \
      --query 'NetworkInsightsAnalyses[0].Status' --output text 2>/dev/null || echo running)"
    [[ "$status" == "succeeded" || "$status" == "failed" ]] && break
    sleep 5
  done
  found="$(aws ec2 describe-network-insights-analyses --network-insights-analysis-ids "$analysis" \
    --query 'NetworkInsightsAnalyses[0].NetworkPathFound' --output text 2>/dev/null || echo False)"
  [[ "$found" == "True" ]] || { warn "Reachability Analyzer: pathFound=$found status=$status"; return 1; }
  ok "SG rule present, app=$code, reachability=reachable (path $path)"
}

lab15_reset() { authorize_app_8080; }
lab15_cleanup() {
  stack_exists "$APP_STACK" && lab15_reset || true
  lab15_delete_paths
  if [[ -n "$(lab15_all_paths)" ]]; then
    warn "a Reachability Analyzer path still exists — delete it manually"
  fi
  disable_lab_flow_logs lab15
  rm -f "$ROOT/var/lab15-path"
}

# --------------------------------------------------------------- lab 16
lab16_build() {
  require_core
  local vpc private_sg endpoint_sg instance rt s3_vpce old_ep
  vpc="$(vpc_id)"

  # Re-running `up` must not create a second private instance or a second set
  # of endpoints (each interface endpoint bills hourly). Clean the previous
  # run first, using both var/lab16.env and the Lab=lab16 tag.
  if [[ -f "$ROOT/var/lab16.env" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/var/lab16.env"
    aws ec2 terminate-instances --instance-ids "$INSTANCE" >/dev/null 2>&1 || true
    aws ec2 wait instance-terminated --instance-ids "$INSTANCE" 2>/dev/null || true
    # shellcheck disable=SC2086
    aws ec2 delete-vpc-endpoints --vpc-endpoint-ids $EP_IDS "$S3_VPCE" >/dev/null 2>&1 || true
    # shellcheck disable=SC2086
    wait_vpc_endpoints_deleted $EP_IDS "$S3_VPCE" || true
    rm -f "$ROOT/var/lab16.env"
  fi
  for old_ep in $(aws ec2 describe-vpc-endpoints \
      --filters "Name=vpc-id,Values=$vpc" "Name=tag:Lab,Values=lab16" \
      --query 'VpcEndpoints[].VpcEndpointId' --output text 2>/dev/null || true); do
    [[ -n "$old_ep" && "$old_ep" != "None" ]] || continue
    aws ec2 delete-vpc-endpoints --vpc-endpoint-ids "$old_ep" >/dev/null 2>&1 || true
    wait_vpc_endpoints_deleted "$old_ep" || true
  done

  private_sg="$(aws ec2 create-security-group --group-name "${LAB_PREFIX}-lab16-private" \
    --description "private instance" --vpc-id "$vpc" --query GroupId --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
      --filters "Name=group-name,Values=${LAB_PREFIX}-lab16-private" "Name=vpc-id,Values=$vpc" \
      --query 'SecurityGroups[0].GroupId' --output text)"
  endpoint_sg="$(aws ec2 create-security-group --group-name "${LAB_PREFIX}-lab16-endpoint" \
    --description "interface endpoints" --vpc-id "$vpc" --query GroupId --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
      --filters "Name=group-name,Values=${LAB_PREFIX}-lab16-endpoint" "Name=vpc-id,Values=$vpc" \
      --query 'SecurityGroups[0].GroupId' --output text)"
  [[ -n "$private_sg" && "$private_sg" != "None" && -n "$endpoint_sg" && "$endpoint_sg" != "None" ]] \
    || die "cannot create/find lab16 security groups"
  aws ec2 create-tags --resources "$private_sg" "$endpoint_sg" \
    --tags "Key=Lab,Value=lab16" "Key=Project,Value=$LAB_PREFIX" "Key=ExpiryDate,Value=$EXPIRY_DATE" >/dev/null
  aws ec2 authorize-security-group-ingress --group-id "$endpoint_sg" \
    --protocol tcp --port 443 --source-group "$private_sg" >/dev/null 2>&1 || true
  aws ec2 authorize-security-group-egress --group-id "$private_sg" \
    --protocol tcp --port 443 --source-group "$endpoint_sg" >/dev/null 2>&1 || true

  local ep_ids=()
  for svc in ssm ssmmessages ec2messages; do
    ep_ids+=("$(aws ec2 create-vpc-endpoint \
      --vpc-id "$vpc" --vpc-endpoint-type Interface \
      --service-name "com.amazonaws.${AWS_REGION}.${svc}" \
      --subnet-ids "$(core_private_1)" --security-group-ids "$endpoint_sg" \
      --private-dns-enabled \
      --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${LAB_PREFIX}-lab16-${svc}},{Key=Lab,Value=lab16},{Key=Project,Value=$LAB_PREFIX},{Key=ExpiryDate,Value=$EXPIRY_DATE}]" \
      --query VpcEndpoint.VpcEndpointId --output text)")
  done
  rt="$(app_private_route_table)"
  s3_vpce="$(aws ec2 create-vpc-endpoint --vpc-id "$vpc" --vpc-endpoint-type Gateway \
    --service-name "com.amazonaws.${AWS_REGION}.s3" --route-table-ids "$rt" \
    --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${LAB_PREFIX}-lab16-s3},{Key=Lab,Value=lab16},{Key=Project,Value=$LAB_PREFIX},{Key=ExpiryDate,Value=$EXPIRY_DATE}]" \
    --query VpcEndpoint.VpcEndpointId --output text)"

  local ami
  ami="$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query Parameter.Value --output text)"
  instance="$(aws ec2 run-instances --image-id "$ami" --instance-type t4g.nano \
    --subnet-id "$(core_private_1)" --security-group-ids "$private_sg" \
    --iam-instance-profile "Name=$(stack_output_required "$CORE_STACK" AppInstanceProfileName)" \
    --no-associate-public-ip-address \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${LAB_PREFIX}-lab16-private},{Key=Lab,Value=lab16},{Key=Project,Value=$LAB_PREFIX},{Key=ExpiryDate,Value=$EXPIRY_DATE}]" \
    --query 'Instances[0].InstanceId' --output text)"
  aws ec2 wait instance-running --instance-ids "$instance"

  cat > "$ROOT/var/lab16.env" <<EOF
INSTANCE=$instance
PRIVATE_SG=$private_sg
ENDPOINT_SG=$endpoint_sg
S3_VPCE=$s3_vpce
EP_IDS="${ep_ids[*]}"
RT=$rt
EOF
  info "waiting for SSM registration on the private instance (up to 5 minutes)"
  wait_until 300 10 bash -c "[[ \"\$(aws ssm describe-instance-information --filters 'Key=InstanceIds,Values=$instance' --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null)\" == Online ]]" \
    || die "private instance did not register with SSM"
}

lab16_break() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab16.env"
  aws ec2 delete-vpc-endpoints --vpc-endpoint-ids "$S3_VPCE" >/dev/null
  info "lab 16 change applied"
}

lab16_verify() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab16.env"
  local s3_ep out
  s3_ep="$(aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$(vpc_id)" \
    --query "VpcEndpoints[?ServiceName=='com.amazonaws.${AWS_REGION}.s3' && State=='available'].VpcEndpointId" \
    --output text)"
  [[ -n "$s3_ep" ]] || { warn "S3 gateway endpoint is missing"; return 1; }
  out="$(ssm_run "$INSTANCE" <<EOS
timeout 10 aws s3 ls "s3://$(core_bucket)" >/dev/null && echo S3_OK
EOS
)"
  [[ "$out" == *S3_OK* ]] || { warn "private instance cannot reach S3: $out"; return 1; }
  ok "S3 gateway endpoint=$s3_ep, private instance S3 access=OK"
}

lab16_reset() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab16.env" 2>/dev/null || return 0
  local new_id
  new_id="$(aws ec2 create-vpc-endpoint --vpc-id "$(vpc_id)" --vpc-endpoint-type Gateway \
    --service-name "com.amazonaws.${AWS_REGION}.s3" --route-table-ids "$RT" \
    --query VpcEndpoint.VpcEndpointId --output text 2>/dev/null || true)"
  [[ -n "$new_id" ]] && sed -i "s|^S3_VPCE=.*|S3_VPCE=$new_id|" "$ROOT/var/lab16.env"
}

lab16_cleanup() {
  local vpc ep ep_lab ep_name sg_id sg_left
  vpc="$(core_vpc_id 2>/dev/null || true)"
  if [[ -f "$ROOT/var/lab16.env" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/var/lab16.env"
    aws ec2 terminate-instances --instance-ids "$INSTANCE" >/dev/null 2>&1 || true
    aws ec2 wait instance-terminated --instance-ids "$INSTANCE" 2>/dev/null || true
    # shellcheck disable=SC2086
    aws ec2 delete-vpc-endpoints --vpc-endpoint-ids $EP_IDS "$S3_VPCE" >/dev/null 2>&1 || true
    # shellcheck disable=SC2086
    wait_vpc_endpoints_deleted $EP_IDS "$S3_VPCE" || true
    rm -f "$ROOT/var/lab16.env"
  fi
  if [[ -n "$vpc" ]]; then
    # Fallback for a run that failed before var/lab16.env was written.
    for ep in $(aws ec2 describe-vpc-endpoints \
        --filters "Name=vpc-id,Values=$vpc" "Name=tag:Lab,Values=lab16" \
        --query 'VpcEndpoints[].VpcEndpointId' --output text 2>/dev/null || true); do
      [[ -n "$ep" && "$ep" != "None" ]] || continue
      aws ec2 delete-vpc-endpoints --vpc-endpoint-ids "$ep" >/dev/null 2>&1 || true
      wait_vpc_endpoints_deleted "$ep" || true
    done
    # An endpoint re-created by hand (console/CLI) carries no Lab tag and is not
    # in var/lab16.env, so the loops above miss it: interface endpoints would
    # keep billing hourly. Sweep the lab VPC, but never touch another lab's or
    # the core stack's endpoints.
    while read -r ep ep_lab ep_name; do
      [[ -n "$ep" && "$ep" != "None" ]] || continue
      [[ "$ep_lab" == "None" ]] && ep_lab=""
      [[ "$ep_name" == "None" ]] && ep_name=""
      [[ -n "$ep_lab" && "$ep_lab" != "lab16" ]] && continue
      [[ -n "$ep_name" && "$ep_name" != *lab16* ]] && continue
      warn "deleting VPC endpoint not tracked by lab 16 state: $ep ${ep_name:+($ep_name)}"
      aws ec2 delete-vpc-endpoints --vpc-endpoint-ids "$ep" >/dev/null 2>&1 || true
      wait_vpc_endpoints_deleted "$ep" || true
    done <<< "$(aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$vpc" \
        --query 'VpcEndpoints[?State!=`deleted`].[VpcEndpointId, join(`,`,Tags[?Key==`Lab`].Value), join(`,`,Tags[?Key==`Name`].Value)]' \
        --output text 2>/dev/null || true)"
    sleep 20
    # The two lab SGs reference each other (endpoint SG allows inbound 443 from
    # the private SG, the private SG allows egress 443 to the endpoint SG), so
    # AWS refuses to delete either one first (DependencyViolation) and the old
    # `|| true` hid the failure. Revoke the cross references, then delete.
    if [[ -n "${PRIVATE_SG:-}" && -n "${ENDPOINT_SG:-}" ]]; then
      aws ec2 revoke-security-group-ingress --group-id "$ENDPOINT_SG" \
        --ip-permissions "IpProtocol=tcp,FromPort=443,ToPort=443,UserIdGroupPairs=[{GroupId=$PRIVATE_SG}]" \
        >/dev/null 2>&1 || true
      aws ec2 revoke-security-group-egress --group-id "$PRIVATE_SG" \
        --ip-permissions "IpProtocol=tcp,FromPort=443,ToPort=443,UserIdGroupPairs=[{GroupId=$ENDPOINT_SG}]" \
        >/dev/null 2>&1 || true
    fi
    for sg_id in "${PRIVATE_SG:-}" "${ENDPOINT_SG:-}"; do
      [[ -n "$sg_id" ]] || continue
      sg_left=1
      for _ in 1 2 3 4 5 6; do
        if aws ec2 delete-security-group --group-id "$sg_id" >/dev/null 2>&1; then
          sg_left=0
          break
        fi
        sleep 10
      done
      if (( sg_left )); then
        warn "security group left behind by lab 16 cleanup: $sg_id"
      fi
    done
    for sg_id in $(aws ec2 describe-security-groups \
        --filters "Name=vpc-id,Values=$vpc" "Name=group-name,Values=${LAB_PREFIX}-lab16-private,${LAB_PREFIX}-lab16-endpoint" \
        --query 'SecurityGroups[].GroupId' --output text 2>/dev/null || true); do
      [[ -n "$sg_id" && "$sg_id" != "None" ]] || continue
      aws ec2 delete-security-group --group-id "$sg_id" >/dev/null 2>&1 || true
    done
  fi
}

# --------------------------------------------------------------- lab 17
lab17_build() {
  ensure_app_healthy
  enable_lab_flow_logs lab17
}

lab17_break() {
  revoke_app_8080
  local subnet nacl
  subnet="$(app_public_subnet)"
  nacl="$(aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=$subnet" \
    --query 'NetworkAcls[0].NetworkAclId' --output text)"
  aws ec2 delete-network-acl-entry --network-acl-id "$nacl" --rule-number 50 --ingress >/dev/null 2>&1 || true
  aws ec2 create-network-acl-entry --network-acl-id "$nacl" --rule-number 50 \
    --protocol tcp --rule-action deny --cidr-block 0.0.0.0/0 \
    --port-range From=8080,To=8080 --ingress >/dev/null
  set_health_check_path /nope
  printf '%s\n' "$nacl" > "$ROOT/var/lab17-nacl"
  info "three faults: SG 8080, NACL deny 8080, health check path"
}

lab17_verify() {
  local rule deny path code healthy subnet nacl
  rule="$(aws ec2 describe-security-groups --group-ids "$(app_sg_id)" \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`8080\`] | length(@)" --output text)"
  subnet="$(app_public_subnet)"
  nacl="$(aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=$subnet" \
    --query 'NetworkAcls[0].NetworkAclId' --output text)"
  deny="$(aws ec2 describe-network-acls --network-acl-ids "$nacl" \
    --query "NetworkAcls[0].Entries[?RuleAction=='deny' && PortRange.From==\`8080\`] | length(@)" --output text)"
  path="$(aws elbv2 describe-target-groups --target-group-arns "$(app_tg)" \
    --query 'TargetGroups[0].HealthCheckPath' --output text)"
  code="$(http_code "$(app_url)/health")"
  healthy="$(aws elbv2 describe-target-health --target-group-arn "$(app_tg)" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  [[ "$rule" -ge 1 ]] || { warn "SG 8080 missing"; return 1; }
  [[ "${deny:-0}" == "0" ]] || { warn "NACL still denies 8080"; return 1; }
  [[ "$path" == "/health" ]] || { warn "health path=$path"; return 1; }
  [[ "$code" == "200" && "$healthy" -ge 1 ]] || { warn "health=$code healthy=$healthy"; return 1; }
  ok "SG=allow NACL=allow path=/health health=200 targets=$healthy"
}

lab17_reset() {
  authorize_app_8080
  local nacl
  nacl="$(cat "$ROOT/var/lab17-nacl" 2>/dev/null || true)"
  [[ -n "$nacl" ]] && aws ec2 delete-network-acl-entry --network-acl-id "$nacl" \
    --rule-number 50 --ingress >/dev/null 2>&1 || true
  set_health_check_path /health
}

lab17_cleanup() {
  stack_exists "$APP_STACK" && lab17_reset || true
  disable_lab_flow_logs lab17
  rm -f "$ROOT/var/lab17-nacl"
}

# --------------------------------------------------------------- lab 18
lab18_build() {
  ensure_app_healthy
  local cluster="${LAB_PREFIX}-lab18" role sg log_group service vpc pub
  vpc="$(vpc_id)"; pub="$(core_public_1)"
  role="$(aws iam create-role --role-name "${LAB_PREFIX}-lab18-exec" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "${LAB_PREFIX}-lab18-exec" --query 'Role.Arn' --output text)"
  aws iam attach-role-policy --role-name "${LAB_PREFIX}-lab18-exec" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy >/dev/null 2>&1 || true
  sg="$(aws ec2 create-security-group --group-name "${LAB_PREFIX}-lab18-ecs" \
    --description "lab18 ecs" --vpc-id "$vpc" --query GroupId --output text 2>/dev/null || \
    aws ec2 describe-security-groups --filters "Name=group-name,Values=${LAB_PREFIX}-lab18-ecs" --query 'SecurityGroups[0].GroupId' --output text)"
  aws ec2 authorize-security-group-ingress --group-id "$sg" --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null 2>&1 || true
  log_group="/aws/ecs/${LAB_PREFIX}/lab18"
  aws logs create-log-group --log-group-name "$log_group" >/dev/null 2>&1 || true
  aws ecs create-cluster --cluster-name "$cluster" \
    --settings name=containerInsights,value=enabled >/dev/null 2>&1 || true

  cat > "$ROOT/var/lab18-taskdef.json" <<JSON
{
  "family": "${LAB_PREFIX}-lab18",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "$role",
  "containerDefinitions": [{
    "name": "web",
    "image": "public.ecr.aws/nginx/nginx:latest",
    "essential": true,
    "portMappings": [{"containerPort": 80, "protocol": "tcp"}],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "$log_group",
        "awslogs-region": "$AWS_REGION",
        "awslogs-stream-prefix": "nginx"
      }
    }
  }]
}
JSON
  aws ecs register-task-definition --cli-input-json file://"$ROOT/var/lab18-taskdef.json" >/dev/null
  aws ecs create-service --cluster "$cluster" --service-name "${LAB_PREFIX}-lab18-web" \
    --task-definition "${LAB_PREFIX}-lab18" --desired-count 1 --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$pub],securityGroups=[$sg],assignPublicIp=ENABLED}" >/dev/null 2>&1 || true
  aws ecs wait services-stable --cluster "$cluster" --services "${LAB_PREFIX}-lab18-web"

  aws ecr create-repository --repository-name "${LAB_PREFIX}-lab18-nginx" >/dev/null 2>&1 || true
  aws ecr put-lifecycle-policy --repository-name "${LAB_PREFIX}-lab18-nginx" \
    --lifecycle-policy-text '{"rules":[{"rulePriority":1,"description":"keep 5","selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":5},"action":{"type":"expire"}}]}' >/dev/null 2>&1 || true

  cat > "$ROOT/var/lab18.env" <<EOF
CLUSTER=$cluster
SERVICE=${LAB_PREFIX}-lab18-web
SG=$sg
ROLE=${LAB_PREFIX}-lab18-exec
LOG_GROUP=$log_group
TASKDEF=${LAB_PREFIX}-lab18
EOF
}

lab18_task_ip() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab18.env"
  local task eni
  task="$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" \
    --query 'taskArns[0]' --output text 2>/dev/null || true)"
  [[ -n "$task" && "$task" != "None" ]] || return 1
  eni="$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task" \
    --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text 2>/dev/null || true)"
  [[ -n "$eni" && "$eni" != "None" ]] || return 1
  aws ec2 describe-network-interfaces --network-interface-ids "$eni" \
    --query 'NetworkInterfaces[0].Association.PublicIp' --output text
}

lab18_break() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab18.env"
  local task
  task="$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" --query 'taskArns[0]' --output text)"
  aws ecs stop-task --cluster "$CLUSTER" --task "$task" --reason "lab18 self-healing test" >/dev/null
  info "task stopped; ECS service must replace it"
}

lab18_verify() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab18.env"
  local running ip code
  wait_until 300 10 bash -c "[[ \"\$(aws ecs describe-services --cluster '$CLUSTER' --services '$SERVICE' --query 'services[0].runningCount' --output text 2>/dev/null)\" == 1 ]]" \
    || { warn "service runningCount != 1"; return 1; }
  running="$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0].runningCount' --output text)"
  ip="$(lab18_task_ip)" || { warn "no task public IP"; return 1; }
  code="$(http_code "http://$ip" 10)"
  [[ "$code" == "200" ]] || { warn "nginx task returned $code"; return 1; }
  ok "service running=$running task=$ip http=$code"
}

lab18_reset() {
  # shellcheck disable=SC1091
  source "$ROOT/var/lab18.env" 2>/dev/null || return 0
  aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --force-new-deployment >/dev/null 2>&1 || true
}

lab18_cleanup() {
  if [[ -f "$ROOT/var/lab18.env" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/var/lab18.env"
    aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --desired-count 0 >/dev/null 2>&1 || true
    aws ecs delete-service --cluster "$CLUSTER" --service "$SERVICE" --force >/dev/null 2>&1 || true
    for td in $(aws ecs list-task-definitions --family-prefix "$TASKDEF" --query 'taskDefinitionArns[]' --output text 2>/dev/null); do
      aws ecs deregister-task-definition --task-definition "$td" >/dev/null 2>&1 || true
    done
    aws ecs delete-cluster --cluster "$CLUSTER" >/dev/null 2>&1 || true
    aws logs delete-log-group --log-group-name "$LOG_GROUP" >/dev/null 2>&1 || true
    aws ec2 delete-security-group --group-id "$SG" >/dev/null 2>&1 || true
    aws iam detach-role-policy --role-name "$ROLE" --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy >/dev/null 2>&1 || true
    aws iam delete-role --role-name "$ROLE" >/dev/null 2>&1 || true
    aws ecr delete-repository --repository-name "${LAB_PREFIX}-lab18-nginx" --force >/dev/null 2>&1 || true
    rm -f "$ROOT/var/lab18.env" "$ROOT/var/lab18-taskdef.json"
  fi
}

# --------------------------------------------------------------- lab 19
lab19_build() {
  ensure_app_healthy
  local bucket role plan db_arn plan_id vault job
  bucket="${LAB_PREFIX}-lab19-config-${LAB_ACCOUNT_ID}"
  vault="${LAB_PREFIX}-lab19"
  printf '%s\n' "$bucket" > "$ROOT/var/lab19-bucket"
  printf '%s\n' "$vault" > "$ROOT/var/lab19-vault"

  # ---- backup role + vault + plan + selection
  role="$(aws iam create-role --role-name "${LAB_PREFIX}-lab19-backup" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"backup.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "${LAB_PREFIX}-lab19-backup" --query 'Role.Arn' --output text)"
  aws iam attach-role-policy --role-name "${LAB_PREFIX}-lab19-backup" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup >/dev/null 2>&1 || true
  aws iam attach-role-policy --role-name "${LAB_PREFIX}-lab19-backup" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores >/dev/null 2>&1 || true
  aws backup create-backup-vault --backup-vault-name "$vault" >/dev/null 2>&1 || true

  cat > "$ROOT/var/lab19-plan.json" <<JSON
{"BackupPlan":{"BackupPlanName":"${LAB_PREFIX}-lab19-plan","Rules":[{"RuleName":"daily","TargetBackupVaultName":"$vault","ScheduleExpression":"cron(0 5 ? * * *)","Lifecycle":{"DeleteAfterDays":7}}]}}
JSON
  plan_id="$(aws backup list-backup-plans \
    --query "BackupPlansList[?BackupPlanName=='${LAB_PREFIX}-lab19-plan'].BackupPlanId | [0]" \
    --output text 2>/dev/null || true)"
  if [[ -z "$plan_id" || "$plan_id" == "None" ]]; then
    plan_id="$(aws backup create-backup-plan --backup-plan file://"$ROOT/var/lab19-plan.json" \
      --query 'BackupPlanId' --output text)"
  fi
  printf '%s\n' "$plan_id" > "$ROOT/var/lab19-plan-id"
  if ! aws backup list-backup-selections --backup-plan-id "$plan_id" \
      --query "BackupSelectionsList[?SelectionName=='tagged'] | length(@)" --output text 2>/dev/null \
      | grep -qx '[1-9][0-9]*'; then
    aws backup create-backup-selection --backup-plan-id "$plan_id" \
      --backup-selection "{\"SelectionName\":\"tagged\",\"IamRoleArn\":\"$role\",\"ListOfTags\":[{\"ConditionType\":\"STRINGEQUALS\",\"ConditionKey\":\"Backup\",\"ConditionValue\":\"lab19\"}]}" >/dev/null 2>&1 || true
  fi

  db_arn="arn:aws:rds:${AWS_REGION}:${LAB_ACCOUNT_ID}:db:$(db_id)"
  aws rds add-tags-to-resource --resource-name "$db_arn" --tags Key=Backup,Value=lab19 >/dev/null 2>&1 || true
  # Reuse a running job from a previous `up` instead of hitting the concurrent
  # job limit or paying for a second snapshot.
  job="$(aws backup list-backup-jobs --by-resource-arn "$db_arn" \
    --query "BackupJobs[?State=='CREATED' || State=='RUNNING' || State=='PENDING'].BackupJobId | [0]" \
    --output text 2>/dev/null || true)"
  if [[ -z "$job" || "$job" == "None" ]]; then
    job="$(aws backup start-backup-job --backup-vault-name "$vault" --resource-arn "$db_arn" \
      --iam-role-arn "$role" --query 'BackupJobId' --output text)"
  fi
  printf '%s\n' "$job" > "$ROOT/var/lab19-backup-job"
  info "backup job $job started (RDS snapshot can take a few minutes)"

  # ---- config: bucket + role + recorder + rule
  if ! aws s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; then
    if [[ "$AWS_REGION" == "us-east-1" ]]; then
      aws s3api create-bucket --bucket "$bucket" >/dev/null
    else
      aws s3api create-bucket --bucket "$bucket" --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
    fi
  fi
  aws s3api put-public-access-block --bucket "$bucket" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" >/dev/null
  aws s3api put-bucket-policy --bucket "$bucket" --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"config.amazonaws.com\"},\"Action\":[\"s3:GetBucketAcl\",\"s3:ListBucket\"],\"Resource\":\"arn:aws:s3:::${bucket}\"},{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"config.amazonaws.com\"},\"Action\":\"s3:PutObject\",\"Resource\":\"arn:aws:s3:::${bucket}/*\",\"Condition\":{\"StringEquals\":{\"s3:x-amz-acl\":\"bucket-owner-full-control\"}}}]}" >/dev/null

  local cfg_role
  cfg_role="$(aws iam create-role --role-name "${LAB_PREFIX}-lab19-config" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"config.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "${LAB_PREFIX}-lab19-config" --query 'Role.Arn' --output text)"
  aws iam attach-role-policy --role-name "${LAB_PREFIX}-lab19-config" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWS_ConfigRole >/dev/null 2>&1 || true

  cat > "$ROOT/var/lab19-delivery.json" <<JSON
{"name":"${LAB_PREFIX}-lab19","s3BucketName":"$bucket","configSnapshotDeliveryProperties":{"deliveryFrequency":"TwentyFour_Hours"}}
JSON
  aws configservice put-delivery-channel --delivery-channel file://"$ROOT/var/lab19-delivery.json" >/dev/null 2>&1 || true
  cat > "$ROOT/var/lab19-recorder.json" <<JSON
{"name":"${LAB_PREFIX}-lab19","roleARN":"$cfg_role","recordingGroup":{"allSupported":true,"includeGlobalResourceTypes":true}}
JSON
  aws configservice put-configuration-recorder --configuration-recorder file://"$ROOT/var/lab19-recorder.json" >/dev/null 2>&1 || true
  aws configservice start-configuration-recorder --configuration-recorder-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
  aws configservice put-config-rule --config-rule "{\"ConfigRuleName\":\"${LAB_PREFIX}-lab19-encrypted-volumes\",\"Source\":{\"Owner\":\"AWS\",\"SourceIdentifier\":\"ENCRYPTED_VOLUMES\"}}" >/dev/null 2>&1 || true

  # ---- cost: a small dedicated budget
  cat > "$ROOT/var/lab19-budget.json" <<JSON
{"BudgetName":"${LAB_PREFIX}-lab19","BudgetLimit":{"Amount":"5","Unit":"USD"},"TimeUnit":"MONTHLY","BudgetType":"COST"}
JSON
  aws budgets create-budget --account-id "$LAB_ACCOUNT_ID" \
    --budget file://"$ROOT/var/lab19-budget.json" >/dev/null 2>&1 || true
}

lab19_break() {
  aws configservice stop-configuration-recorder \
    --configuration-recorder-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
  info "Config recorder stopped. Compliance data is now stale."
}

lab19_verify() {
  local job status rp recording budget ce
  job="$(cat "$ROOT/var/lab19-backup-job" 2>/dev/null || true)"
  status="$(aws backup describe-backup-job --backup-job-id "$job" --query 'State' --output text 2>/dev/null || echo MISSING)"
  rp="$(aws backup list-recovery-points-by-backup-vault --backup-vault-name "${LAB_PREFIX}-lab19" \
    --query 'RecoveryPoints | length(@)' --output text 2>/dev/null || echo 0)"
  recording="$(aws configservice describe-configuration-recorder-status \
    --query "ConfigurationRecordersStatus[?name=='${LAB_PREFIX}-lab19'].recording" --output text 2>/dev/null || echo False)"
  budget="$(aws budgets describe-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "${LAB_PREFIX}-lab19" --query 'Budget.BudgetName' --output text 2>/dev/null || true)"
  ce="$(aws ce get-cost-and-usage --time-period "Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d)" \
    --granularity DAILY --metrics UnblendedCost --query 'ResultsByTime | length(@)' --output text 2>/dev/null || echo 0)"
  [[ "$status" == "COMPLETED" ]] || { warn "backup job=$status (wait, then re-run verify)"; return 1; }
  [[ "${rp:-0}" -ge 1 ]] || { warn "no recovery point"; return 1; }
  [[ "$recording" == "True" ]] || { warn "Config recording=$recording"; return 1; }
  [[ -n "$budget" ]] || { warn "lab19 budget missing"; return 1; }
  if [[ "${ce:-0}" -lt 1 ]]; then
    warn "Cost Explorer has no data yet (it can lag up to 24h); continuing"
  fi
  ok "backup=$status recoveryPoints=$rp config=recording budget=$budget costExplorer=${ce:-0}"
}

lab19_reset() {
  aws configservice start-configuration-recorder \
    --configuration-recorder-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
}

lab19_cleanup() {
  # backup
  local plan_id vault bucket
  plan_id="$(cat "$ROOT/var/lab19-plan-id" 2>/dev/null || true)"
  vault="$(cat "$ROOT/var/lab19-vault" 2>/dev/null || true)"
  [[ -n "$plan_id" ]] && aws backup delete-backup-plan --backup-plan-id "$plan_id" >/dev/null 2>&1 || true
  # Fallback if var/ was lost: delete every plan with the lab's name.
  for plan_id in $(aws backup list-backup-plans \
      --query "BackupPlansList[?BackupPlanName=='${LAB_PREFIX}-lab19-plan'].BackupPlanId" \
      --output text 2>/dev/null || true); do
    [[ -n "$plan_id" && "$plan_id" != "None" ]] || continue
    aws backup delete-backup-plan --backup-plan-id "$plan_id" >/dev/null 2>&1 || true
  done
  if [[ -n "$vault" ]]; then
    for rp in $(aws backup list-recovery-points-by-backup-vault --backup-vault-name "$vault" --query 'RecoveryPoints[].RecoveryPointArn' --output text 2>/dev/null); do
      aws backup delete-recovery-point --backup-vault-name "$vault" --recovery-point-arn "$rp" >/dev/null 2>&1 || true
    done
    aws backup delete-backup-vault --backup-vault-name "$vault" >/dev/null 2>&1 || true
  fi
  aws iam detach-role-policy --role-name "${LAB_PREFIX}-lab19-backup" --policy-arn arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup >/dev/null 2>&1 || true
  aws iam detach-role-policy --role-name "${LAB_PREFIX}-lab19-backup" --policy-arn arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores >/dev/null 2>&1 || true
  aws iam delete-role --role-name "${LAB_PREFIX}-lab19-backup" >/dev/null 2>&1 || true

  # config
  aws configservice stop-configuration-recorder --configuration-recorder-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
  aws configservice delete-configuration-recorder --configuration-recorder-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
  aws configservice delete-delivery-channel --delivery-channel-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
  aws configservice delete-config-rule --config-rule-name "${LAB_PREFIX}-lab19-encrypted-volumes" >/dev/null 2>&1 || true
  aws iam detach-role-policy --role-name "${LAB_PREFIX}-lab19-config" --policy-arn arn:aws:iam::aws:policy/service-role/AWS_ConfigRole >/dev/null 2>&1 || true
  aws iam delete-role --role-name "${LAB_PREFIX}-lab19-config" >/dev/null 2>&1 || true

  bucket="$(cat "$ROOT/var/lab19-bucket" 2>/dev/null || true)"
  [[ -n "$bucket" ]] && aws s3 rm "s3://$bucket" --recursive >/dev/null 2>&1 || true
  [[ -n "$bucket" ]] && aws s3api delete-bucket --bucket "$bucket" >/dev/null 2>&1 || true
  aws budgets delete-budget --account-id "$LAB_ACCOUNT_ID" --budget-name "${LAB_PREFIX}-lab19" >/dev/null 2>&1 || true
  rm -f "$ROOT/var/lab19-"* 
}

# --------------------------------------------------------------- lab 20
lab20_build() { ensure_app_healthy; }

lab20_break() {
  local url; url="$(app_url)"
  curl -s "$url/load?seconds=300&workers=2" >/dev/null
  for _ in $(seq 1 20); do curl -s "$url/error" >/dev/null; done
  for _ in $(seq 1 5); do curl -s "$url/slow?ms=2500" >/dev/null; done
  info "CPU load + 20 x 500 + slow requests injected"
}

lab20_verify() {
  local cpu code db code_target
  curl -s "$(app_url)/stop" >/dev/null 2>&1 || true
  local cpu
  for _ in $(seq 1 20); do
    cpu="$(metric_max AWS/EC2 CPUUtilization InstanceId "$(app_instance_required)")"
    [[ "${cpu%.*}" -lt 60 ]] && break
    sleep 15
  done
  code="$(http_code "$(app_url)/health")"
  db="$(http_code "$(app_url)/db" 15)"
  code_target="$(aws elbv2 describe-target-health --target-group-arn "$(app_tg)" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  [[ "${cpu%.*}" -lt 60 ]] || { warn "CPU still high: $cpu"; return 1; }
  [[ "$code" == "200" ]] || { warn "health=$code"; return 1; }
  [[ "$db" == "200" ]] || { warn "db=$db"; return 1; }
  [[ "$code_target" -ge 1 ]] || { warn "no healthy target"; return 1; }
  ok "CPU=$cpu health=$code db=$db targets=$code_target"
}

lab20_reset() { curl -s "$(app_url)/stop" >/dev/null 2>&1 || true; }
lab20_cleanup() { stack_exists "$APP_STACK" && lab20_reset || true; }

# --------------------------------------------------------------- lab 21
lab21_build() { ensure_app_healthy; }

lab21_break() {
  revoke_db_5432
  aws iam put-role-policy --role-name "$(app_role_name)" --policy-name lab21-deny-secret \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":["secretsmanager:GetSecretValue"],"Resource":"*"}]}' >/dev/null
  info "DB SG no longer allows 5432 + app role has an explicit deny on GetSecretValue"
}

lab21_verify() {
  local rule deny code out
  rule="$(aws ec2 describe-security-groups --group-ids "$(db_sg_id)" \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`5432\`] | length(@)" --output text)"
  deny="$(aws iam list-role-policies --role-name "$(app_role_name)" \
    --query "PolicyNames[?contains(@, 'lab21-deny-secret')] | length(@)" --output text)"
  code="$(http_code "$(app_url)/db" 15)"
  out="$(ssm_run "$(app_instance_required)" <<EOS
set -euo pipefail
aws secretsmanager get-secret-value --secret-id "$(db_secret_arn)" --query SecretString --output text >/dev/null && echo SECRET_OK
EOS
)"
  [[ "$rule" -ge 1 ]] || { warn "DB SG missing 5432 from app SG"; return 1; }
  [[ "${deny:-0}" == "0" ]] || { warn "inline deny policy still attached"; return 1; }
  [[ "$code" == "200" ]] || { warn "app /db -> $code"; return 1; }
  [[ "$out" == *SECRET_OK* ]] || { warn "app role cannot read the secret"; return 1; }
  ok "DB SG allows 5432, secret readable, app/db=200"
}

lab21_reset() {
  authorize_db_5432
  aws iam delete-role-policy --role-name "$(app_role_name)" --policy-name lab21-deny-secret >/dev/null 2>&1 || true
}
lab21_cleanup() { stack_exists "$APP_STACK" && lab21_reset || true; }

# --------------------------------------------------------------- lab 22
lab22_build() {
  ensure_app_healthy
  local role vault db_arn
  app_instance_required > "$ROOT/var/lab22-original-instance"
  role="$(aws iam create-role --role-name "${LAB_PREFIX}-lab22-backup" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"backup.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --query 'Role.Arn' --output text 2>/dev/null || aws iam get-role --role-name "${LAB_PREFIX}-lab22-backup" --query 'Role.Arn' --output text)"
  aws iam attach-role-policy --role-name "${LAB_PREFIX}-lab22-backup" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup >/dev/null 2>&1 || true
  vault="${LAB_PREFIX}-lab22"
  aws backup create-backup-vault --backup-vault-name "$vault" >/dev/null 2>&1 || true
  cat > "$ROOT/var/lab22-plan.json" <<JSON
{"BackupPlan":{"BackupPlanName":"${LAB_PREFIX}-lab22","Rules":[{"RuleName":"daily","TargetBackupVaultName":"$vault","ScheduleExpression":"cron(0 5 ? * * *)","Lifecycle":{"DeleteAfterDays":7}}]}}
JSON
  if ! aws backup list-backup-plans \
      --query "BackupPlansList[?BackupPlanName=='${LAB_PREFIX}-lab22'] | length(@)" \
      --output text 2>/dev/null | grep -qx '[1-9][0-9]*'; then
    aws backup create-backup-plan --backup-plan file://"$ROOT/var/lab22-plan.json" >/dev/null
  fi
  db_arn="arn:aws:rds:${AWS_REGION}:${LAB_ACCOUNT_ID}:db:$(db_id)"
  aws rds add-tags-to-resource --resource-name "$db_arn" --tags Key=Backup,Value=lab22 >/dev/null 2>&1 || true
  printf '%s\n' "$vault" > "$ROOT/var/lab22-vault"

  # Production readiness needs observability before verify. Create the four
  # baseline alarms + dashboard here so `up 22` is self-contained instead of
  # depending on alarms left over from labs 01/02/04.
  local inst
  inst="$(app_instance_required)"
  "$ROOT/scripts/create-dashboard.sh" >/dev/null
  create_alarm "${LAB_PREFIX}-lab22-alb-5xx" AWS/ApplicationELB HTTPCode_ELB_5XX_Count \
    LoadBalancer "$(app_alb_full_name)" 1 GreaterThanOrEqualToThreshold Sum 60 1
  create_alarm "${LAB_PREFIX}-lab22-ec2-cpu" AWS/EC2 CPUUtilization \
    InstanceId "$inst" 80 GreaterThanThreshold Average 300 2
  create_alarm "${LAB_PREFIX}-lab22-rds-cpu" AWS/RDS CPUUtilization \
    DBInstanceIdentifier "$(db_id)" 80 GreaterThanThreshold Average 300 2
  create_alarm "${LAB_PREFIX}-lab22-rds-storage" AWS/RDS FreeStorageSpace \
    DBInstanceIdentifier "$(db_id)" 1073741824 LessThanThreshold Average 300 1
}

lab22_break() {
  ssm_run "$(app_instance_required)" <<'EOS' >/dev/null
systemctl stop cloudops-app
EOS
  info "app stopped. The ALB health check should make the ASG replace the instance."
}

lab22_verify() {
  local old new code db health plan dashboard alarms
  old="$(cat "$ROOT/var/lab22-original-instance" 2>/dev/null || true)"
  wait_until 420 15 bash -c "[[ \"\$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 '$(app_url)/health')\" == 200 ]]" \
    || { warn "app did not recover in time"; return 1; }
  new="$(app_instance_required)"
  code="$(http_code "$(app_url)/health")"
  db="$(http_code "$(app_url)/db" 15)"
  health="$(aws elbv2 describe-target-health --target-group-arn "$(app_tg)" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  plan="$(aws backup list-backup-plans --query "BackupPlansList[?BackupPlanName=='${LAB_PREFIX}-lab22'] | length(@)" --output text 2>/dev/null || echo 0)"
  dashboard="$(aws cloudwatch list-dashboards --query "DashboardEntries[?DashboardName=='${LAB_PREFIX}-ops'] | length(@)" --output text 2>/dev/null || echo 0)"
  alarms="$(aws cloudwatch describe-alarms --alarm-name-prefix "$LAB_PREFIX" --query 'MetricAlarms | length(@)' --output text)"
  [[ "$code" == "200" && "$db" == "200" ]] || { warn "health=$code db=$db"; return 1; }
  [[ "$health" -ge 1 ]] || { warn "no healthy target"; return 1; }
  [[ "$plan" -ge 1 ]] || { warn "backup plan missing"; return 1; }
  [[ "$dashboard" -ge 1 ]] || { warn "dashboard missing"; return 1; }
  [[ "$alarms" -ge 4 ]] || { warn "alarms=$alarms (expected >=4)"; return 1; }
  ok "self-healed: old=${old:-?} new=$new health=$code db=$db targets=$health alarms=$alarms"
}

lab22_reset() {
  ssm_run "$(app_instance_required 2>/dev/null || true)" <<'EOS' >/dev/null 2>&1 || true
systemctl start cloudops-app
EOS
}

lab22_cleanup() {
  local vault
  aws cloudwatch delete-alarms --alarm-names \
    "${LAB_PREFIX}-lab22-alb-5xx" "${LAB_PREFIX}-lab22-ec2-cpu" \
    "${LAB_PREFIX}-lab22-rds-cpu" "${LAB_PREFIX}-lab22-rds-storage" >/dev/null 2>&1 || true
  vault="$(cat "$ROOT/var/lab22-vault" 2>/dev/null || true)"
  aws backup list-backup-plans --query "BackupPlansList[?BackupPlanName=='${LAB_PREFIX}-lab22'].BackupPlanId" --output text 2>/dev/null | tr '\t' '\n' | while read -r p; do
    [[ -n "$p" ]] && aws backup delete-backup-plan --backup-plan-id "$p" >/dev/null 2>&1 || true
  done
  if [[ -n "$vault" ]]; then
    for rp in $(aws backup list-recovery-points-by-backup-vault --backup-vault-name "$vault" --query 'RecoveryPoints[].RecoveryPointArn' --output text 2>/dev/null); do
      aws backup delete-recovery-point --backup-vault-name "$vault" --recovery-point-arn "$rp" >/dev/null 2>&1 || true
    done
    aws backup delete-backup-vault --backup-vault-name "$vault" >/dev/null 2>&1 || true
  fi
  aws iam detach-role-policy --role-name "${LAB_PREFIX}-lab22-backup" --policy-arn arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup >/dev/null 2>&1 || true
  aws iam delete-role --role-name "${LAB_PREFIX}-lab22-backup" >/dev/null 2>&1 || true
  rm -f "$ROOT/var/lab22-"*
}

# --------------------------------------------------------------- lab 23
lab23_build() { ensure_app_healthy; }

lab23_break() {
  set_health_check_path /nope
  revoke_app_8080
  revoke_db_5432
  aws iam put-role-policy --role-name "$(app_role_name)" --policy-name lab23-deny-s3 \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":["s3:GetObject"],"Resource":"*"}]}' >/dev/null
  curl -s "$(app_url)/load?seconds=300&workers=2" >/dev/null
  info "five faults injected: health path, app SG, DB SG, IAM deny, CPU load"
}

lab23_verify() {
  local path rule db_rule deny code db out cpu health
  path="$(aws elbv2 describe-target-groups --target-group-arns "$(app_tg)" \
    --query 'TargetGroups[0].HealthCheckPath' --output text)"
  rule="$(aws ec2 describe-security-groups --group-ids "$(app_sg_id)" \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`8080\`] | length(@)" --output text)"
  db_rule="$(aws ec2 describe-security-groups --group-ids "$(db_sg_id)" \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`5432\`] | length(@)" --output text)"
  deny="$(aws iam list-role-policies --role-name "$(app_role_name)" \
    --query "PolicyNames[?contains(@, 'lab23-deny-s3')] | length(@)" --output text)"
  curl -s "$(app_url)/stop" >/dev/null 2>&1 || true
  sleep 20
  code="$(http_code "$(app_url)/health")"
  db="$(http_code "$(app_url)/db" 15)"
  cpu="$(metric_max AWS/EC2 CPUUtilization AutoScalingGroupName "$(app_asg)")"
  health="$(aws elbv2 describe-target-health --target-group-arn "$(app_tg)" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  out="$(ssm_run "$(app_instance_required)" <<EOS
set -euo pipefail
aws s3 ls "s3://$(core_bucket)" >/dev/null && echo S3_OK
EOS
)"
  [[ "$path" == "/health" ]] || { warn "health path=$path"; return 1; }
  [[ "$rule" -ge 1 ]] || { warn "app SG missing 8080"; return 1; }
  [[ "$db_rule" -ge 1 ]] || { warn "DB SG missing 5432"; return 1; }
  [[ "${deny:-0}" == "0" ]] || { warn "IAM deny still attached"; return 1; }
  [[ "$code" == "200" && "$db" == "200" ]] || { warn "health=$code db=$db"; return 1; }
  [[ "${cpu%.*}" -lt 60 ]] || { warn "CPU=$cpu"; return 1; }
  [[ "$health" -ge 1 ]] || { warn "targets healthy=$health"; return 1; }
  [[ "$out" == *S3_OK* ]] || { warn "S3 access failed"; return 1; }
  ok "all five faults fixed: path=/health SG=allow DB=allow IAM=allow cpu=$cpu health=200"
}

lab23_reset() {
  set_health_check_path /health
  authorize_app_8080
  authorize_db_5432
  aws iam delete-role-policy --role-name "$(app_role_name)" --policy-name lab23-deny-s3 >/dev/null 2>&1 || true
  curl -s "$(app_url)/stop" >/dev/null 2>&1 || true
}
lab23_cleanup() { stack_exists "$APP_STACK" && lab23_reset || true; }

