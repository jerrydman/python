import boto3
import json
import argparse
from datetime import datetime, timezone

def get_iam_users_access_keys(profile_name):
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

            user_data = {
                'UserName': user_name,
                'AccessKey': access_key_data
            }

            users_data.append(user_data)

    return users_data

def save_to_json(data, filename='iam_users_access_keys.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve IAM users and their access keys info, output to JSON.')
    parser.add_argument('--profile', required=True, help='AWS profile name from ~/.aws/credentials file')
    parser.add_argument('--output', default='iam_users_access_keys.json', help='Output file name (default: iam_users_access_keys.json)')
    args = parser.parse_args()

    users_access_keys_info = get_iam_users_access_keys(args.profile)
    save_to_json(users_access_keys_info, args.output)
    print(f"IAM users and access keys info saved to {args.output}")
