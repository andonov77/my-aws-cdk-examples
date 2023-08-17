
# Amazon Global Datastore for Redis CDK Python project!

![global-datastore-for-redis-arch](./global-datastore-for-redis-arch.png)

This is an Amazon Global Datastore for Redis project for CDK development with Python.

### Step 1: Create a Primary cluster

Create a redis-cluster in `us-east-1` region.

<pre>
$ aws configure set region <i>us-east-1</i>
$ cd ./my-aws-cdk-examples/elasticache/redis-cluster
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
(.venv) $ cdk deploy --all
</pre>

### Step 2: Create a Secondary cluster

Create a redis-cluster in `us-west-2` region.

<pre>
(.venv) $ aws configure set region <i>us-west-2</i>
(.venv) $ pip install -r requirements.txt
(.venv) $ cdk deploy --all
</pre>

### Step 3: Create a Global Datastore for redis

1. Change the directory
    <pre>
    (.venv) $ pwd
    my-aws-cdk-examples/elasticache/redis-cluster
    (.venv) $ deactivate
    $ cd ../global-datastore-for-redis
    $ pwd
    my-aws-cdk-examples/elasticache/global-datastore-for-redis
    </pre>
2. Create a virtualenv and activate it
    <pre>
    $ aws configure set region <i>us-east-1</i>
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    </pre>
3. Install the required dependencies
   <pre>
   (.venv) $ pip install -r requirements.txt
   </pre>
4. Set up CDK configuration
   <pre>
   (.venv) $ cat cdk.context.json
   {
    "global_datastore_for_redis": {
      "name_suffix": "global-redis",
      "secondary_region": "<i>us-west-2</i>",
      "primary_group_id": "<i>primary-redis-id</i>",
      "secondary_group_id": "<i>secondary-redis-id</i>"
    }
   }
   </pre>
5. Create the CDK stack
   <pre>
   (.venv) $ cdk deploy --all
   </pre>


## Clean Up

Delete the CloudFormation stack for Global Datastores for Redis by running the below command.

```
(.venv) $ cdk destroy --force --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## References

 * [Now Available: Amazon ElastiCache Global Datastore for Redis (2020-03-16)](https://aws.amazon.com/blogs/aws/now-available-amazon-elasticache-global-datastore-for-redis/)
 * [Replication across AWS Regions using global datastores - Prerequisites and limitations](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Redis-Global-Datastores-Getting-Started.html)
 * [How To Install and Secure Redis on CentOS 7](https://www.digitalocean.com/community/tutorials/how-to-install-secure-redis-centos-7)
