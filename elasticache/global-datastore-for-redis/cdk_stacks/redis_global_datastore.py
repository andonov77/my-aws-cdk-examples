# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_elasticache
)
from constructs import Construct

class GlobalDatastoreForRedisStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    config_global_datastore_for_redis = self.node.try_get_context('global_datastore_for_redis')
    global_datastore_name_suffix = config_global_datastore_for_redis['name_suffix']
    global_datastore_primary_group_id = config_global_datastore_for_redis['primary_group_id']
    global_datastore_secondary_group_id = config_global_datastore_for_redis['secondary_group_id']
    global_datastore_secondary_region = config_global_datastore_for_redis['secondary_region']

    cfn_global_replication_group = aws_elasticache.CfnGlobalReplicationGroup(self, 'RedisGlobalReplicationGroup',
      members=[
        #XXX: GlobalReplicationGroup cannot be created with multiple members
        aws_elasticache.CfnGlobalReplicationGroup.GlobalReplicationGroupMemberProperty(
          replication_group_id=global_datastore_primary_group_id,
          replication_group_region=cdk.Aws.REGION,
          role="PRIMARY"
        )
      ],
      automatic_failover_enabled=True, # `AutomaticFailoverEnabled`` must be enabled for Redis (cluster mode enabled) replication groups.
      #XXX: `cache_parameter_group_name` must not be specified for Create Global Datastore operation
      engine_version="7.0",
      global_node_group_count=3,
      global_replication_group_description="global data store for redis cluster",
      global_replication_group_id_suffix=global_datastore_name_suffix,
      regional_configurations=[
        aws_elasticache.CfnGlobalReplicationGroup.RegionalConfigurationProperty(
          replication_group_id=global_datastore_primary_group_id,
          replication_group_region=cdk.Aws.REGION
        ),
        aws_elasticache.CfnGlobalReplicationGroup.RegionalConfigurationProperty(
          replication_group_id=global_datastore_secondary_group_id,
          replication_group_region=global_datastore_secondary_region
        )
      ]
    )
    cfn_global_replication_group.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'GloballDataStoreId',
      value=cfn_global_replication_group.attr_global_replication_group_id,
      export_name=f'{self.stack_name}-GloballDataStoreId')
