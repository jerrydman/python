##Output to look like this
##
##EC2 Instance and vCPU Count by TechnologyCode (Grouped by Region + Totals):
##+----------------+----------------------+-----------------+-----------------+
##|     Region     | TechnologyCode Value |  Instance Count |    Total vCPU   |
##+----------------+----------------------+-----------------+-----------------+

##AWS Account Details:
##+----------------+-------------------+-----------------+------------+
##| AWS Account ID |   Account Alias   | Total Instances | Total vCPU |
##+----------------+-------------------+-----------------+------------+

##Jerry Reid



import boto3
import csv
from collections import defaultdict
from prettytable import PrettyTable



# Define the tag key to be used 
TAG_KEY = ""

def normalize_tag_value(tag_value):
    """Normalize the tag value to ensure consistent casing."""
    return tag_value.lower().title() if tag_value else "Unknown"

def get_ec2_vcpu_and_instance_count():
    session = boto3.Session()
    ec2_client = session.client('ec2')
    iam_client = session.client('iam')
    sts_client = session.client('sts')

    # Get AWS account details
    account_id = sts_client.get_caller_identity()["Account"]
    aliases = iam_client.list_account_aliases().get("AccountAliases", ["Unknown"])
    account_alias = aliases[0] if aliases else "Unknown"

    # Get all available regions
    regions = [r['RegionName'] for r in ec2_client.describe_regions()['Regions']]

    # Ensure we start with us-west-2
    if "us-west-2" in regions:
        regions.remove("us-west-2")
        regions.insert(0, "us-west-2")

    total_vcpu = 0
    total_instance_count = 0
    total_counts = defaultdict(lambda: {"instances": 0, "vcpu": 0})
    region_counts_list = []

    for region in regions:
        ec2 = session.resource('ec2', region_name=region)
        instances = ec2.instances.all()

        region_vcpu = 0
        region_instance_count = 0
        region_counts = defaultdict(lambda: {"instances": 0, "vcpu": 0})

        for instance in instances:
            tag_value = "Unknown"  # Default if no relevant tag is present
            for tag in instance.tags or []:
                if tag['Key'].lower() == TAG_KEY.lower():
                    tag_value = normalize_tag_value(tag['Value'])
                    break

            # Fetch instance type details
            instance_type = instance.instance_type
            instance_details = ec2_client.describe_instance_types(InstanceTypes=[instance_type])
            vcpu_count = instance_details['InstanceTypes'][0]['VCpuInfo']['DefaultVCpus']

            region_counts[tag_value]["instances"] += 1
            region_counts[tag_value]["vcpu"] += vcpu_count
            total_counts[tag_value]["instances"] += 1
            total_counts[tag_value]["vcpu"] += vcpu_count

            region_vcpu += vcpu_count
            region_instance_count += 1

        total_vcpu += region_vcpu
        total_instance_count += region_instance_count

        for tag, values in region_counts.items():
            region_counts_list.append((region, tag, values["instances"], values["vcpu"]))

    # Create a combined table
    table = PrettyTable()
    table.field_names = ["Region", f"{TAG_KEY} Value", "Instance Count", "Total vCPU"]

    for region, tag, instance_count, vcpu in region_counts_list:
        table.add_row([region, tag, instance_count, vcpu])

    table.add_row(["-" * 10, "-" * 20, "-" * 15, "-" * 15])  # Separator row

    for tag, values in total_counts.items():
        table.add_row(["TOTAL", tag, values["instances"], values["vcpu"]])


    print(f"\nEC2 Instance and vCPU Count by {TAG_KEY} (Grouped by Region + Totals):")
    print(table)


    account_table = PrettyTable()
    account_table.field_names = ["AWS Account ID", "Account Alias", "Total Instances", "Total vCPU"]
    account_table.add_row([account_id, account_alias, total_instance_count, total_vcpu])

    print("\nAWS Account Details:")
    print(account_table)

    # Export to CSV as acctnumber.csv
    csv_filename = f"{account_id}.csv"
    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Region", f"{TAG_KEY} Value", "Instance Count", "Total vCPU"])  # Header

        for region, tag, instance_count, vcpu in region_counts_list:
            writer.writerow([region, tag, instance_count, vcpu])

        writer.writerow(["TOTAL", "", "", ""])  # Empty row for separation
        for tag, values in total_counts.items():
            writer.writerow(["TOTAL", tag, values["instances"], values["vcpu"]])

        writer.writerow([])  # Blank row
        writer.writerow(["AWS Account ID", "Account Alias", "Total Instances", "Total vCPU"])  # Account details header
        writer.writerow([account_id, account_alias, total_instance_count, total_vcpu])

    print(f"\nCSV file saved: {csv_filename}")

    return total_instance_count, total_vcpu

if __name__ == "__main__":
    total_instance_count, total_vcpu = get_ec2_vcpu_and_instance_count()
