import boto3
import json
import argparse

def get_ec2_instance_settings(profile_name, region_name, tag_name, tag_value):
    # Initialize boto3 session with specified profile and region
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    ec2 = session.client('ec2')
    iam = session.client('iam')

    # Get all EC2 instances with specific tag 'tag_key=tag_value'
    response = ec2.describe_instances(Filters=[
        {'Name': f'tag:{tag_name}', 'Values': [tag_value]}
    ])

    instances_data = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            state = instance['State']['Name']
            private_ip = instance.get('PrivateIpAddress', 'N/A')
            public_ip = instance.get('PublicIpAddress', 'N/A')
            imdsv2 = instance.get('MetadataOptions', {}).get('HttpTokens', 'N/A')

            # Get instance profile ARN (if exists)
            instance_profile_arn = instance.get('IamInstanceProfile', {}).get('Arn', 'N/A')

            # Get instance profile name and permissions
            instance_profile_name = 'N/A'
            instance_profile_permissions = []
            if instance_profile_arn != 'N/A':
                instance_profile_name = instance_profile_arn.split('/')[-1]
                # Describe instance profile to get associated role permissions
                try:
                    response = iam.get_instance_profile(InstanceProfileName=instance_profile_name)
                    role_name = response['InstanceProfile']['Roles'][0]['RoleName']
                    response = iam.get_role(RoleName=role_name)
                    instance_profile_permissions = response['Role']['AttachedPolicies']
                except Exception as e:
                    instance_profile_permissions = str(e)

            # Get tag with the name 'hostname'
            hostname_tag = 'N/A'
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Hostname':
                    hostname_tag = tag['Value']
                    break

            instance_data = {
                'InstanceId': instance_id,
                'InstanceType': instance_type,
                'State': state,
                'PrivateIpAddress': private_ip,
                'PublicIpAddress': public_ip,
                'IMDSv2': imdsv2,
                'InstanceProfileName': instance_profile_name,
                'Hostname': hostname_tag
            }

            instances_data.append(instance_data)

    return instances_data

def save_to_json(data, filename='ec2_instance_settings.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve EC2 instance settings and output to JSON.')
    parser.add_argument('--profile', required=True, help='AWS profile name from ~/.aws/credentials file')
    parser.add_argument('--region', required=True, help='AWS region from ~/.aws/config file')
    parser.add_argument('--tag-name', required=True, help='Name of the tag to filter instances')
    parser.add_argument('--tag-value', required=True, help='Value of the tag to filter instances')
    parser.add_argument('--output', default='ec2_instance_settings.json', help='Output file name (default: ec2_instance_settings.json)')
    args = parser.parse_args()

    instance_settings = get_ec2_instance_settings(args.profile, args.region, args.tag_name, args.tag_value)
    save_to_json(instance_settings, args.output)
    print(f"Instance settings saved to {args.output}")
