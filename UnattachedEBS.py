import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from prettytable import PrettyTable
import argparse

def estimate_cost(size_gib, cost_per_gb=0.10):
    return (size_gib * cost_per_gb) * 34

def get_unattached_volumes(profile_name):
    try:
        # Initialize a session using the specified profile
        boto3.setup_default_session(profile_name=profile_name, region_name='us-west-2')
        ec2_client = boto3.client('ec2')

        # Get the list of all available AWS regions
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

        unattached_volumes = []
        total_cost = 0

        for region in regions:
            print(f"Checking region: {region}")
            ec2_client = boto3.client('ec2', region_name=region)

            # Describe volumes
            volumes = ec2_client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])

            for volume in volumes['Volumes']:
                if volume['State'] == 'available':
                    volume_tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                    created_by = volume_tags.get('CreatedBy', 'N/A')
                    size_gib = volume['Size']
                    created_date = volume['CreateTime'].strftime('%Y-%m-%d %H:%M:%S')
                    estimated_cost = estimate_cost(size_gib)
                    total_cost += estimated_cost
                    unattached_volumes.append({
                        'VolumeId': volume['VolumeId'],
                        'Region': region,
                        'Size': volume['Size'],
                        'Cost': f"${estimated_cost:.2f}",
                        'CreatedBy': created_by,
                        'CreatedDate': created_date
                    })

        return unattached_volumes, total_cost

    except NoCredentialsError:
        print("Error: No AWS credentials found.")
        return []
    except PartialCredentialsError:
        print("Error: Incomplete AWS credentials.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def print_volumes_table(volumes, total_cost):
    table = PrettyTable()
    table.field_names = ["Volume ID", "Region", "Size (GiB)","Created Date","Monthly Cost", "CreatedBy"]

    for volume in volumes:
        table.add_row([volume['VolumeId'], volume['Region'], volume['Size'],volume['CreatedDate'],volume['Cost'], volume['CreatedBy']])

    print(table)
    print(f"Total estimated cost for Month: ${total_cost:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get all Unattached EBS Volumes.')
    profile_name =  parser.add_argument('--profile', required=True, help='AWS profile name from ~/.aws/credentials file')
    args = parser.parse_args()

    if not profile_name:
        print("Profile name is required.")
    else:
        unattached_volumes , total_cost = get_unattached_volumes(args.profile)

        if unattached_volumes:
            print_volumes_table(unattached_volumes,total_cost)
        else:
            print("No unattached EBS volumes found.")