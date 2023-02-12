#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  KdsStack,
  GlueJobRoleStack,
  GlueStreamDataSchemaStack,
  GlueStreamingJobStack,
  DataLakePermissionsStack,
  S3BucketStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

s3_bucket = S3BucketStack(app, 'GlueStreamingCDCtoIcebergS3Path')

kds_stack = KdsStack(app, 'KinesisStreamAsGlueStreamingJobCDCDataSource')
kds_stack.add_dependency(s3_bucket)

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingCDCtoIcebergJobRole')
glue_job_role.add_dependency(kds_stack)

glue_stream_schema = GlueStreamDataSchemaStack(app, 'GlueTableSchemaOnKinesisStream',
  kds_stack.kinesis_stream
)
glue_stream_schema.add_dependency(glue_job_role)

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'GrantLFPermissionsOnGlueJobRole',
  glue_job_role.glue_job_role
)
grant_lake_formation_permissions.add_dependency(glue_job_role)
grant_lake_formation_permissions.add_dependency(glue_stream_schema)

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingCDCtoIceberg',
  glue_job_role.glue_job_role,
  kds_stack.kinesis_stream
)
glue_streaming_job.add_dependency(grant_lake_formation_permissions)

app.synth()
