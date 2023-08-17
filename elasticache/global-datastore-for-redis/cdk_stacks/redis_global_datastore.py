# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_elasticache
)
from constructs import Construct

class GlobalDatastoreForRedisStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_use_elasticache = aws_ec2.SecurityGroup(self, 'RedisClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis client',
      security_group_name='redis-global-datastore-client-sg'
    )
    cdk.Tags.of(sg_use_elasticache).add('Name', 'redis-global-datastore-client-sg')

    sg_elasticache = aws_ec2.SecurityGroup(self, 'RedisServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redis server',
      security_group_name='redis-global-datastore-server-sg'
    )
    cdk.Tags.of(sg_elasticache).add('Name', 'redis-global-datastore-server-sg')

    sg_elasticache.add_ingress_rule(peer=sg_use_elasticache, connection=aws_ec2.Port.tcp(6379),
      description='redis-global-datastore-client-sg')
    sg_elasticache.add_ingress_rule(peer=sg_elasticache, connection=aws_ec2.Port.all_tcp(),
      description='redis-global-datastore-server-sg')

    redis_cluster_param_group = aws_elasticache.CfnParameterGroup(self, 'RedisClusterParamGroup',
      cache_parameter_group_family='redis7',
      description='parameter group for redis7.0 cluster',
      properties={
        'cluster-enabled': 'yes', # Enable cluster mode
        'tcp-keepalive': '0', # tcp-keepalive: 300 (default)
        'maxmemory-policy': 'volatile-ttl' # maxmemory-policy: volatile-lru (default)
      },
      tags=[cdk.CfnTag(key='Name', value='redis-cluster-parameter-group'),
        cdk.CfnTag(key='desc', value='redis cluster parameter group')]
    )
    redis_cluster_param_group.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    config_global_datastore_for_redis = self.node.try_get_context('global_datastore_for_redis')
    global_datastore_name_suffix = config_global_datastore_for_redis['name_suffix']
    global_datastore_primary_group_id = config_global_datastore_for_redis['primary_group_id']
    global_datastore_secondary_group_id = config_global_datastore_for_redis['secondary_group_id']
    global_datastore_secondary_region = config_global_datastore_for_redis['secondary_region']

    cfn_global_replication_group = aws_elasticache.CfnGlobalReplicationGroup(self, 'RedisGlobalReplicationGroup',
      members=[
        aws_elasticache.CfnGlobalReplicationGroup.GlobalReplicationGroupMemberProperty(
          replication_group_id=global_datastore_primary_group_id,
          replication_group_region=cdk.Aws.REGION,
          role="PRIMARY"
        )
      ],
      automatic_failover_enabled=True, # `AutomaticFailoverEnabled`` must be enabled for Redis (cluster mode enabled) replication groups.
      #XXX: CacheParameterGroupName must not be specified for Create Global Datastore operation
      # cache_parameter_group_name=redis_cluster_param_group.ref,
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

    cfn_global_replication_group.add_dependency(redis_cluster_param_group)
    cfn_global_replication_group.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'GloballDataStoreId',
      value=cfn_global_replication_group.attr_global_replication_group_id,
      export_name=f'{self.stack_name}-GloballDataStoreId')
