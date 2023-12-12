import boto3
import os

#Variables
region = 'us-west-2'
profile = '$profile'

def add_tag_to_all_rds_instances(tag_key, tag_value):
    aws_region = region
    session = boto3.Session(profile_name=profile)
    rds_client = session.client('rds',region_name=region)
    # Retrieve a list of all RDS instances
    response = rds_client.describe_db_instances()

    # Add tag to each RDS instance
    for instance in response['DBInstances']:
        instance_identifier = instance['DBInstanceIdentifier']
        print(f"Adding tag to RDS instance: {instance_identifier}")

        # Add the specified tag to the RDS instance
        rds_client.describe_db_instances()
        rds_client.add_tags_to_resource(
            ResourceName=instance['DBInstanceArn'],
            Tags=[
                {
                    'Key': 'SomeKey',
                    'Value': 'SomeValue'
                }
            ]
        )

    print("Tags added to all RDS instances.")

# # Replace 'your-region', 'your-tag-key', and 'your-tag-value' with your AWS region and desired tag key and value
add_tag_to_all_rds_instances(tag_key='your-tag-key', tag_value='your-tag-value')

