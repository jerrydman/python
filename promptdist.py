##Python Script to scan all IAM users for tag distribution list
##If it does not have the tag it prompts the user to add in a value
##python3 promptdist.py --profile <profile>


import boto3
import argparse

def get_iam_users_without_distribution_list(profile_name):
    # Initialize boto3 session with specified profile
    session = boto3.Session(profile_name=profile_name)
    iam = session.client('iam')

    # Get all IAM users
    response = iam.list_users()
    users = response['Users']

    users_without_distribution_list = []

    for user in users:
        user_name = user['UserName']

        # Check if user has 'DistributionList' tag
        tags_response = iam.list_user_tags(UserName=user_name)
        tags = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}

        if 'DistributionList' not in tags:
            users_without_distribution_list.append(user_name)

    return users_without_distribution_list

def prompt_user_for_distribution_list(username):
    distribution_list_value = input(f"Enter the value for 'DistributionList' tag for user '{username}': ")
    return distribution_list_value

def add_distribution_list_tag(profile_name, username, distribution_list_value):
    # Initialize boto3 session with specified profile
    session = boto3.Session(profile_name=profile_name)
    iam = session.client('iam')

    # Add or update 'DistributionList' tag for the specified user
    response = iam.tag_user(
        UserName=username,
        Tags=[
            {
                'Key': 'DistributionList',
                'Value': distribution_list_value
            }
        ]
    )

    print(f"Tag 'DistributionList' added for IAM user '{username}'.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan IAM users without DistributionList tag and prompt to add it.')
    parser.add_argument('--profile', required=True, help='AWS profile name from ~/.aws/credentials file')
    args = parser.parse_args()

    users_without_distribution_list = get_iam_users_without_distribution_list(args.profile)

    if users_without_distribution_list:
        print("The following IAM users do not have a 'DistributionList' tag:")
        for user in users_without_distribution_list:
            print(f"- {user}")
            distribution_list_value = prompt_user_for_distribution_list(user)
            add_distribution_list_tag(args.profile, user, distribution_list_value)
    else:
        print("All IAM users have a 'DistributionList' tag.")
