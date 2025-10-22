import os
import logging
import random
import dns.resolver
from elbv2_client import elbv2_client
from tg_utils import get_target_group_arn, get_rds_instance_address
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configure DNS server for lookup
dns_server = os.environ.get('DNS_SERVER', '')
domainname = 'example.com'
record_type = 'A'

# Get Target Group ARN
tg_arn = get_target_group_arn()

# Retrieve registered IPs from Target Group
def get_registered_ips(tg_arn):
    registered_ip_list = []
    try:
        response = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)
        for target in response['TargetHealthDescriptions']:
            registered_ip = target['Target']['Id']
            registered_ip_list.append(registered_ip)
    except ClientError:
        logging.error("ERROR: Can't retrieve Target Group information.")
        raise
    return registered_ip_list

# Get RDS instance address
def get_rds_address():
    rds_address = get_rds_instance_address()
    return rds_address

# Update Target Group with RDS instance address
def update_target_group(tg_arn, rds_address):
    try:
        elbv2_client.register_targets(TargetGroupArn=tg_arn, Targets=[{'Id': rds_address}])
        logging.info(f"Registered {rds_address} with Target Group {tg_arn}")
    except ClientError:
        logging.error(f"Failed to register {rds_address} with Target Group {tg_arn}")
        raise

# Perform DNS lookup
def perform_dns_lookup(dns_server, domainname, record_type):
    lookup_result_list = []

    # Select DNS server to use
    myResolver = dns.resolver.Resolver()
    myResolver.domain = ''

    # Apply default DNS Server override
    if dns_server:
        name_server_ip_list = re.split(r'[,; ]+', dns_server)
        myResolver.nameservers = [random.choice(name_server_ip_list)]
    else:
        logging.info("INFO: Using default DNS resolvers: {}".format(dns.resolver.Resolver().nameservers))
        myResolver.nameservers = random.choice(dns.resolver.Resolver().nameservers)

    logging.info("INFO: Using randomly selected DNS Server: {}".format(myResolver.nameservers))

    # Resolve FQDN
    try:
        lookupAnswer = myResolver.query(domainname, record_type)
        for answer in lookupAnswer:
            lookup_result_list.append(str(answer))
    except ClientError:
        raise
    return lookup_result_list

# Main function
def main():
    # Get RDS instance address
    rds_address = get_rds_address()

    # Get registered IPs from Target Group
    registered_ips = get_registered_ips(tg_arn)

    # Check if RDS instance address is already registered
    if rds_address in registered_ips:
        logging.info(f"{rds_address} is already registered with Target Group {tg_arn}")
    else:
        # Perform DNS lookup before updating Target Group
        perform_dns_lookup(dns_server, domainname, record_type)

        # Update Target Group with RDS instance address
        update_target_group(tg_arn, rds_address)

if __name__ == '__main__':
    main()
