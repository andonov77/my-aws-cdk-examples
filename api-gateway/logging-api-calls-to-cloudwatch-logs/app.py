#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_apigateway,
  aws_iam,
  aws_lambda,
  aws_logs,
)
from constructs import Construct


class LoggingApiCallsToCloudwatchLogsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    FIREHOSE_NAME = self.node.try_get_context('firehose_name')
    #assert FIREHOSE_NAME.startswith('amazon-apigateway-')

    firehose_arn = f'arn:aws:firehose:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:deliverystream/{FIREHOSE_NAME}'

    cwl_write_to_firehose_policy_doc = aws_iam.PolicyDocument(
      statements=[aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        resources=[firehose_arn],
        actions=["firehose:PutRecord"]
      )]
    )

    cwl_to_firehose_role = aws_iam.Role(self, 'CWLtoKinesisFirehoseRole',
      role_name="CWLtoKinesisFirehoseRole",
      assumed_by=aws_iam.ServicePrincipal(f"logs.{cdk.Aws.REGION}.amazonaws.com",
        conditions={
          "StringLike": {
            "aws:SourceArn": f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:*"
          }
        },
        region=cdk.Aws.REGION
      ),
      inline_policies={
        "firehose_write_policy": cwl_write_to_firehose_policy_doc
      }
    )

    random_gen_api_log_group = aws_logs.LogGroup(self, 'RandomGenApiLogs')

    cwl_subscription_filter = aws_logs.CfnSubscriptionFilter(self, 'CWLSubscriptionFilter',
      destination_arn=firehose_arn,
      filter_pattern="",
      log_group_name=random_gen_api_log_group.log_group_name,
      role_arn=cwl_to_firehose_role.role_arn
    )

    random_gen_lambda_fn = aws_lambda.Function(self, 'RandomStringsLambdaFn',
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name='RandomStrings',
      handler='random_strings.lambda_handler',
      description='Function that returns strings randomly generated',
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), 'src/main/python')),
      timeout=cdk.Duration.minutes(5)
    )


    #XXX: Using aws_apigateway.AccessLogFormat.custom(json.dumps({..}))
    # or aws_apigateway.AccessLogFormat.json_with_standard_fields()
    # make json's all attributes string data type even if they are numbers
    # So, it's better to define access log format in the string like this.
    # Don't forget the new line to make JSON Lines.
    access_log_format = '{"requestId": "$context.requestId",\
 "ip": "$context.identity.sourceIp",\
 "user": "$context.identity.user",\
 "requestTime": $context.requestTimeEpoch,\
 "httpMethod": "$context.httpMethod",\
 "resourcePath": "$context.resourcePath",\
 "status": $context.status,\
 "protocol": "$context.protocol",\
 "responseLength": $context.responseLength}\n'

    random_strings_rest_api = aws_apigateway.LambdaRestApi(self, 'RandomStringsApi',
      rest_api_name="random-strings",
      handler=random_gen_lambda_fn,
      proxy=False,
      deploy=True,
      deploy_options=aws_apigateway.StageOptions(stage_name='prod',
        data_trace_enabled=True,
        logging_level=aws_apigateway.MethodLoggingLevel.INFO,
        metrics_enabled=True,
        #XXX: You can't use Kinesis Data Firehose as the access_log_destination
        access_log_destination=aws_apigateway.LogGroupLogDestination(random_gen_api_log_group),
        access_log_format=aws_apigateway.AccessLogFormat.custom(access_log_format)
      ),
      endpoint_export_name='RestApiEndpoint'
    )

    random_gen = random_strings_rest_api.root.add_resource('random')
    random_strings_gen = random_gen.add_resource('strings')
    random_strings_gen.add_method('GET',
      aws_apigateway.LambdaIntegration(
        handler=random_gen_lambda_fn
      )
    )

    cdk.CfnOutput(self, 'RestApiAccessLogToFirehoseARN', value=firehose_arn)
    cdk.CfnOutput(self, 'RestApiAccessLogGroupName', value=random_gen_api_log_group.log_group_name)
    cdk.CfnOutput(self, 'RestApiEndpoint',
      value=f'https://{random_strings_rest_api.rest_api_id}.execute-api.{cdk.Aws.REGION}.amazonaws.com/{random_strings_rest_api.deployment_stage.stage_name}/',
      export_name=f'RestApiEndpoint-Prod')


app = cdk.App()
LoggingApiCallsToCloudwatchLogsStack(app, "LoggingApiCallsToCloudwatchLogsStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()

