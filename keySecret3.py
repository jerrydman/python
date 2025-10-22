# Script to rotate keys for aws and store in secrets manager
# Some arguments are required others are optional
# 

import argparse
import boto3
from botocore.exceptions import ClientError, ParamValidationError
iam_client = boto3.client('iam')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username",
                        help="An IAM username, --username <username>",
                        required=True)
    parser.add_argument("-k", "--key",
                        help="An AWS access key,")
    parser.add_argument("-d", "--delete",
                        help="Deletes an access key", action="store_true")
    parser.add_argument("-r", "--rotate",
                        help="rotates current key", action="store_true")
    parser.add_argument("-p", "--profile",
                        help="Choose the profile from aws config file ",
                        nargs='?', const="default", type=str, required=True)
    parser.add_argument("-g", "--get", nargs='?')
    parser.add_argument("-z", "--region", nargs='?')
    args = parser.parse_args()
    username = args.username
    profile = args.profile
    region = args.region
    aws_profile = boto3.session.Session(profile_name=profile)
    aws_access_key = get_key(username, aws_profile)
    try:
        if args.delete:
            delete_key(aws_access_key, username, aws_profile)
        elif args.rotate:
            rotate_key(username, aws_profile, region)
        elif args.get:
            get_key(username, aws_profile)
        else:
            print("You must choose to either (r)otate or (d)elete your key.")
    except ClientError as e:
        raise e
    except ParamValidationError as e:
        print("you need to use the proper arguments i.e python3 rotateKeys3.py\
               -u username@salesforce.com -p profile ")
        return e
    return (username, profile, aws_access_key)


def get_key(username, aws_profile):
    session = aws_profile
    credentials = session.get_credentials()
    current_credentials = credentials.get_frozen_credentials()
    return (current_credentials.access_key)


def create_key(username, aws_access_key, aws_profile, region):
    keys = iam_client.list_access_keys()
    print(keys)
    inactive_keys = 0
    active_keys = 0
    for key in keys['AccessKeyMetadata']:
        if key['Status'] == 'Inactive':
            inactive_keys = inactive_keys + 1
        elif key['Status'] == 'Active':
            active_keys = active_keys + 1
    if inactive_keys + active_keys >= 2:
        print(("%s already has 1 keys. As a best practice \
                you are only allowed 1 keys.") % username)
        print(("%s is your key to refresh your memory ") % aws_access_key)
        exit()
    aws_access_key = get_key(username, aws_profile)
    access_key_metadata = iam_client.create_access_key(
                           UserName=username)['AccessKey']
    access_key = access_key_metadata['AccessKeyId']
    secret_key = access_key_metadata['SecretAccessKey']
    print(("your new access key is %s and your new secret key is %s")
          % (access_key, secret_key))
    access_key = ''
    secret_key = ''
    sm_access_key = access_key
    sm_secret_key = secret_key
    update_secrets_manager(region, aws_profile, sm_access_key, sm_secret_key)
    return sm_access_key, sm_secret_key


def delete_key(access_key, username, aws_profile):
    i = ""
    old_access_key = get_key(username, aws_profile)
    try:
        while i != 'y' or 'n':
            i = input("Do you want to delete the access key " + " "
                      + old_access_key + " y/n" + " ")
            if i == 'y':
                iam_client.delete_access_key(UserName=username,
                                             AccessKeyId=old_access_key)
                print((old_access_key + " has been deleted."))
                return old_access_key
            elif i == 'n':
                exit()
    except ClientError as e:
        print(("The access key with id %s cannot be found" % old_access_key))
        return e


def get_secret(secret, region, profile):
    secret_name = secret
    session = boto3.session.Session(profile_name=profile)
    client = session.client(
        service_name='secretsmanager',
        region_name=region,
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            print("secrets manager cannot decrypt using provided KMS")
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            print("Error on Server side, try again later")
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("Cannot find secret; please check secret name and region")
    else:
        secret = get_secret_value_response['SecretString']
        print(secret)


def update_secrets_manager(region, profile, sm_access_key, sm_secret_key):
    session = boto3.session.Session(profile_name=profile)
    client = session.client(
        service_name='secretsmanager',
        region_name=region,
    )
    client.update_secret(SecretId=sm_access_key, SecretString=sm_secret_key)


def rotate_key(username, aws_profile, region):
    aws_access_key = get_key(username, aws_profile)
    print("Removing Old Key")
    delete_key(aws_access_key, username, aws_profile)
    print("creating new key")
    create_key(username, aws_access_key, aws_profile, region)


if __name__ == "__main__":
    main()
