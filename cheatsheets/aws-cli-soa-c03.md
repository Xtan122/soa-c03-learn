# AWS CLI cheatsheet — SOA-C03 labs

Dùng biến cho gọn:

```bash
export AWS_REGION=ap-southeast-1
export P=soa-c03
export BUCKET=$(aws cloudformation describe-stacks --stack-name $P-core \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" --output text)
export URL=http://$(aws cloudformation describe-stacks --stack-name $P-app \
  --query "Stacks[0].Outputs[?OutputKey=='AlbDnsName'].OutputValue" --output text)
```

## CloudWatch

```bash
# Metrics
aws cloudwatch list-metrics --namespace AWS/EC2 --dimensions Name=InstanceId,Value=<id>
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<id> \
  --start-time "$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 --statistics Average Maximum

# Alarms
aws cloudwatch describe-alarms --alarm-name-prefix $P
aws cloudwatch describe-alarms --alarm-names "$P-alb-5xx" --query 'MetricAlarms[0].StateValue'
aws cloudwatch set-alarm-state --alarm-name "$P-lab01-cpu-high" \
  --state-value ALARM --state-reason "manual test"

# Logs Insights
QID=$(aws logs start-query --log-group-name "/aws/cloudops/$P/app" \
  --start-time "$(date -u -d '30 minutes ago' +%s)" --end-time "$(date -u +%s)" \
  --query-string 'fields @timestamp, level, event, message | filter level = "ERROR" | sort @timestamp desc | limit 50' \
  --query queryId --output text)
sleep 5
aws logs get-query-results --query-id "$QID" --output table

# Metric filter
aws logs put-metric-filter --log-group-name "/aws/cloudops/$P/app" \
  --filter-name "$P-errors" --filter-pattern '{ $.level = "ERROR" }' \
  --metric-transformations metricName=ErrorCount,metricNamespace=CloudOpsLab,metricValue=1,defaultValue=0
```

## CloudTrail / EventBridge / SQS

```bash
aws cloudtrail get-trail-status --name "$P-trail"
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=TerminateInstances \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --query 'Events[].[EventTime,Username,CloudTrailEvent]' --output table

aws events list-rules --query "Rules[?starts_with(Name, '$P')].[Name,State]"
aws events list-targets-by-rule --rule "$P-lab12-remediate"
aws events test-event-pattern --event-pattern file://pattern.json \
  --event file://event.json

aws sqs receive-message --queue-url <url> --wait-time-seconds 5 --max-number-of-messages 5
```

## EC2 / ASG / ALB

```bash
aws ec2 describe-instances --filters "Name=tag:Project,Values=$P" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,SubnetId]' --output table

aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$P-asg" \
  --query 'AutoScalingGroups[0].{Desired:DesiredCapacity,Min:MinSize,Max:MaxSize,Instances:Instances[].InstanceId}'
aws autoscaling describe-scaling-activities --auto-scaling-group-name "$P-asg" \
  --max-items 10 --query 'Activities[].[StartTime,StatusCode,StatusMessage]' --output table

aws elbv2 describe-target-health --target-group-arn <tg-arn>
aws elbv2 describe-load-balancers --names "$P-alb"
aws elbv2 modify-target-group --target-group-arn <tg-arn> --health-check-path /health
```

## RDS

```bash
aws rds describe-db-instances --db-instance-identifier "$P-db" \
  --query 'DBInstances[0].{Status:DBInstanceStatus,MultiAZ:MultiAZ,Endpoint:Endpoint.Address,Secret:MasterUserSecret.SecretArn}'

aws rds create-db-snapshot --db-instance-identifier "$P-db" \
  --db-snapshot-identifier "$P-lab07-snapshot"
aws rds wait db-snapshot-completed --db-snapshot-identifier "$P-lab07-snapshot"

aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier "$P-lab07-restored" \
  --db-snapshot-identifier "$P-lab07-snapshot" \
  --db-instance-class db.t4g.micro \
  --db-subnet-group-name "$P-db-subnet-group" \
  --vpc-security-group-ids <db-sg-id> \
  --no-publicly-accessible
aws rds wait db-instance-available --db-instance-identifier "$P-lab07-restored"

aws rds reboot-db-instance --db-instance-identifier "$P-db" --force-failover
aws rds describe-events --source-identifier "$P-db" --source-type db-instance --duration 30
aws rds modify-db-instance --db-instance-identifier "$P-db" --multi-az --apply-immediately
```

Query từ app instance qua SSM:

```bash
source /etc/cloudops.env
SECRET=$(aws secretsmanager get-secret-value --secret-id "$DB_SECRET_ARN" --query SecretString --output text)
export PGPASSWORD=$(echo "$SECRET" | jq -r .password)
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c 'select 1'
```

## IAM / STS / KMS / Secrets

```bash
aws iam simulate-principal-policy --policy-source-arn <role-arn> \
  --action-names s3:GetObject --resource-arns "arn:aws:s3:::$BUCKET/*"
aws iam get-role --role-name "$P-lab13-target"
aws iam list-role-policies --role-name "$P-lab13-target"

aws sts assume-role --role-arn "arn:aws:iam::<acct>:role/$P-lab13-target" \
  --role-session-name lab13
aws sts get-caller-identity

aws kms get-key-policy --key-id <key-id> --policy-name default --query Policy --output text | jq .
aws kms put-key-policy --key-id <key-id> --policy-name default --policy file://policy.json

aws secretsmanager get-secret-value --secret-id <secret-arn> --query SecretString --output text
aws secretsmanager rotate-secret --secret-id <secret-arn>
```

## S3 security

```bash
aws s3api get-public-access-block --bucket "$BUCKET"
aws s3api get-bucket-policy-status --bucket "$BUCKET"
aws s3api get-bucket-acl --bucket "$BUCKET"
aws accessanalyzer list-findings --analyzer-arn <arn>
curl -s -o /dev/null -w '%{http_code}\n' "https://$BUCKET.s3.$AWS_REGION.amazonaws.com/secret.txt"
```

## VPC / networking

```bash
aws ec2 describe-security-groups --group-ids <sg> \
  --query 'SecurityGroups[0].IpPermissions'
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=<subnet>
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=<subnet>
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc>
aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc>
aws ec2 create-network-insights-path --source <eni> --destination <eni> \
  --protocol tcp --destination-port 8080
aws ec2 start-network-insights-analysis --network-insights-path-id <path>
aws ec2 describe-network-insights-analyses --network-insights-analysis-ids <id>

# From a private instance with SSM
curl -v telnet://<host>:5432 --max-time 5
getent hosts <host>
aws s3 ls "s3://$BUCKET"
```

## SSM

```bash
aws ssm describe-instance-information \
  --filters Key=InstanceIds,Values=<id> --query 'InstanceInformationList[0].PingStatus'
aws ssm start-session --target <id>
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["systemctl status cloudops-app","df -h"]'
aws ssm get-parameter --name "/$P/app/port" --query Parameter.Value
aws ssm put-parameter --name "/$P/lab09/message" --value hello --type String --overwrite
```

## CloudFormation / CDK

```bash
aws cloudformation describe-stacks --stack-name "$P-lab11"
aws cloudformation describe-stack-events --stack-name "$P-lab11" --max-items 10 \
  --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' --output table
aws cloudformation detect-stack-drift --stack-name "$P-lab11"
aws cloudformation describe-stack-resource-drifts --stack-name "$P-lab11" \
  --stack-resource-drift-status-filters MODIFIED DELETED
aws cloudformation update-stack --stack-name "$P-lab11" \
  --use-previous-template --parameters ParameterKey=ProjectName,UsePreviousValue=true
aws cloudformation delete-stack --stack-name "$P-lab11"

cd labs/11-cloudformation-cdk/cdk && cdk synth
```

## ECS / ECR

```bash
aws ecs describe-clusters --clusters "$P-lab18"
aws ecs describe-services --cluster "$P-lab18" --services "$P-lab18-web" \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Events:events[:3].message}'
aws ecs list-tasks --cluster "$P-lab18" --service-name "$P-lab18-web"
aws ecs describe-tasks --cluster "$P-lab18" --tasks <task-arn> \
  --query 'tasks[0].{Last:lastStatus,Health:healthStatus,Stopped:stoppedReason}'
aws logs tail "/aws/ecs/$P/lab18" --follow

aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, '$P')]"
aws ecr get-login-password | docker login --username AWS --password-stdin \
  "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"
```

## Backup / Config / Cost

```bash
aws backup list-backup-plans
aws backup list-recovery-points-by-backup-vault --backup-vault-name "$P-lab20"
aws backup start-backup-job --backup-vault-name "$P-lab20" \
  --resource-arn "arn:aws:rds:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):db:$P-db" \
  --iam-role-arn <backup-role-arn>
aws backup describe-backup-job --backup-job-id <id>

aws configservice describe-configuration-recorder-status
aws configservice describe-compliance-by-config-rule
aws configservice get-compliance-details-by-config-rule --config-rule-name <rule>

aws ce get-cost-and-usage --time-period "Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d)" \
  --granularity DAILY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE
aws budgets describe-budget --account-id "$(aws sts get-caller-identity --query Account --output text)" \
  --budget-name "$P-monthly"
```
