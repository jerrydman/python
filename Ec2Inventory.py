##Script to get all ec2 from aws account in all regions
##Expected output
##+-----------------+--------------+---------------------+------------------------------+---------+-------+-------------+------------------------------------------------+-----------+---------------+---------------+------+--------------+------------------+
##|  Account Alias  |  Account ID  |     Instance ID     |           Hostname           |  State  |  SOX  | Environment |                   Technology                   | Tech Code |   IP Address  | Instance Type | vCPU | Memory (GiB) | Operating System |
##+-----------------+--------------+---------------------+------------------------------+---------+-------+-------------+------------------------------------------------+-----------+---------------+---------------+------+--------------+------------------+
## Jerry Reid


import boto3
import argparse
from prettytable import PrettyTable

def get_regions(profile_name):
    session = boto3.Session(profile_name=profile_name)
    ec2 = session.client('ec2', region_name='us-west-2')
    regions = ec2.describe_regions()
    return [region['RegionName'] for region in regions['Regions']]

def get_instance_type_details(ec2, instance_type):
    try:
        response = ec2.describe_instance_types(InstanceTypes=[instance_type])
        instance_type_info = response['InstanceTypes'][0]
        vcpu = instance_type_info['VCpuInfo']['DefaultVCpus']
        memory = instance_type_info['MemoryInfo']['SizeInMiB'] / 1024  #convert to gb
        return vcpu, memory
    except Exception as e:
        print(f"Error fetching details for instance type {instance_type}: {str(e)}")
        return "Unknown", "Unknown"

def get_account_alias(profile_name):
    session = boto3.Session(profile_name=profile_name)
    iam = session.client('iam')
    try:
        response = iam.list_account_aliases()
        account_aliases = response['AccountAliases']
        return account_aliases[0] if account_aliases else 'No Alias'
    except Exception as e:
        print(f"Error fetching account alias: {str(e)}")
        return 'Unknown'

def get_instance_details(profile_name, region):
    session = boto3.Session(profile_name=profile_name, region_name=region)
    ec2 = session.client('ec2', region_name=region)
    instances_details = []

    try:
        paginator = ec2.get_paginator('describe_instances')
        page_iterator = paginator.paginate()

        for page in page_iterator:
            for reservation in page['Reservations']:
                account_id = reservation['OwnerId']
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    private_ip = instance.get('PrivateIpAddress', 'N/A')
                    state = instance['State']['Name']
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    hostname = tags.get('Hostname', 'N/A')
                    sox = tags.get('SOX', 'N/A')
                    environment = tags.get('Environment', 'N/A')
                    technology = tags.get('Technology', 'N/A')
                    tech_code = tags.get('TechnologyCode', 'N/A')
                    os = tags.get('PlatformOS','N/A')
                    version = tags.get('PlatformOSMajor','N/A')

                    vcpu, memory = get_instance_type_details(ec2, instance_type)

                    instances_details.append([
                        account_id, instance_id, hostname, state ,sox, environment,
                        technology, tech_code, private_ip, instance_type, vcpu, memory, os + ' ' + version
                    ])
    except Exception as e:
        print(f"An error occurred in region {region}: {str(e)}")

    return instances_details

def main():
    parser = argparse.ArgumentParser(description='Get details of all EC2 instances across all regions.')
    parser.add_argument('--profile', required=True, help='The AWS profile name to use.')
    args = parser.parse_args()

    profile_name = args.profile

    try:
        all_instances_details = []
        account_alias = get_account_alias(profile_name)

        regions = get_regions(profile_name)

        for region in regions:
            print(f"Checking region {region}...")
            instances_details = get_instance_details(profile_name, region)
            all_instances_details.extend(instances_details)

        if all_instances_details:
            # Create and print the pretty table
            table = PrettyTable()
            table.field_names = ["Account Alias", "Account ID", "Instance ID", "Hostname", "State", "SOX", "Environment", "Technology", "Tech Code",
                                 "IP Address", "Instance Type", "vCPU", "Memory (GiB)", "Operating System"]
            for detail in all_instances_details:
                table.add_row([account_alias] + detail)

            print(table)
        else:
            print("No instances found.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
