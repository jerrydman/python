import boto3
import json
import argparse
from datetime import datetime, timezone

def get_iam_users(profile_name):
    # Initialize boto3 session with specified profile
    session = boto3.Session(profile_name=profile_name)
    iam = session.client('iam')

    # Get all IAM users
    response = iam.list_users()

    users_data = []

    for user in response['Users']:
        user_name = user['UserName']

        # Get user's access keys
        access_keys_response = iam.list_access_keys(UserName=user_name)

        access_keys_data = []
        for key in access_keys_response['AccessKeyMetadata']:
            access_key_id = key['AccessKeyId']
            create_date = key['CreateDate']
            status = key['Status']

            # Calculate age of the access key
            age_days = (datetime.now(timezone.utc) - create_date).days

            access_key_data = {
                'AccessKeyId': access_key_id,
                'AgeDays': age_days,
                'Status': status
            }

            access_keys_data.append(access_key_data)

        # Get tags associated with the user
        tags_response = iam.list_user_tags(UserName=user_name)
        tags = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}

        # Check if 'distributionlist' tag exists and add to user data
        distribution_list_tag = tags.get('DistributionList', 'N/A')

        user_data = {
            'UserName': user_name,
            'AccessKeys': access_keys_data,
            'DistributionList': distribution_list_tag
        }

        users_data.append(user_data)

    return users_data

def output(data, filename='iam_users_info.txt'):
    with open(filename, 'w') as f:
        for user in data:
            f.write(f"Username: {user['UserName']}\n")
            for access_key in user['AccessKeys']:
                f.write(f"AccessKeyID: {access_key['AccessKeyId']}\n")
                f.write(f"Age: {access_key['AgeDays']} days\n")
                f.write(f"Status: {access_key['Status']}\n")
            f.write(f"DistributionList: {user['DistributionList']}\n")
            f.write("\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve IAM users and their access keys info with tags, output to human-readable format.')
    parser.add_argument('--profile', required=True, help='AWS profile name from ~/.aws/credentials file')
    parser.add_argument('--output', default='iam_users_info.txt', help='Output file name (default: iam_users_info.txt)')
    args = parser.parse_args()

    users_info = get_iam_users(args.profile)
    output(users_info, args.output)
    print(f"IAM users info saved to {args.output}")
