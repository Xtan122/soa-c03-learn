#!/usr/bin/env python3
"""Optional CDK version of Lab 11.

    cd labs/11-cloudformation-cdk/cdk
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cdk synth
    cdk deploy

The exam expects you to know that CDK synthesizes CloudFormation. You do not
need to deploy both the CDK and the YAML stack.
"""
import aws_cdk as cdk
from aws_cdk import aws_sqs as sqs, aws_ssm as ssm
from constructs import Construct


class Lab11Stack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        queue = sqs.Queue(
            self,
            "LabQueue",
            queue_name="soa-c03-lab11-cdk-queue",
            retention_period=cdk.Duration.hours(1),
        )
        ssm.StringParameter(
            self,
            "QueueUrlParameter",
            parameter_name="/soa-c03/lab11/cdk-queue-url",
            string_value=queue.queue_url,
        )


app = cdk.App()
Lab11Stack(app, "SoaC03Lab11", env=cdk.Environment(region="ap-southeast-1"))
app.synth()
