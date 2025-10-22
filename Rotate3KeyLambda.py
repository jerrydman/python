# Lambda to rotate credentials
# Gets Username and SNS topic from tags
# This will disable and delete and put new one in secrets manager

import boto3
from botocore.exceptions import ClientError
import datetime
import json
import sys

iam_client = boto3.client('iam')
secretmanager = boto3.client('secretsmanager')
session = boto3.session.Session()
AWS_REGION_NAME = session.region_name
sns = boto3.client('sns', region_name=AWS_REGION_NAME)



def list_access_key(user, days_filter, status_filter):
    keydetails=iam_client.list_access_keys(UserName=user)
    key_details={}
    user_iam_details=[]
    
    # Some user may have 2 access keys.
    for keys in keydetails['AccessKeyMetadata']:
        if (days:=time_diff(keys['CreateDate'])) >= days_filter and keys['Status']==status_filter:
            key_details['UserName']=keys['UserName']
            key_details['AccessKeyId']=keys['AccessKeyId']
            key_details['days']=days
            key_details['status']=keys['Status']
            user_iam_details.append(key_details)
            key_details={}
    
    return user_iam_details

def time_diff(keycreatedtime):
    now=datetime.datetime.now(datetime.timezone.utc)
    diff=now-keycreatedtime
    return diff.days
    
    
def get_username(secret):
        get_secret_value_response = secretmanager.describe_secret(
            SecretId=secret
        )
        secret = get_secret_value_response['Tags']
        data = json.dumps(secret)
        pretty_data = json.loads(data)
        names = [dict['Value'] for dict in pretty_data if dict['Key'] == 'Name']
        aws_user_name = " ".join(names)
        return (aws_user_name)

def get_snstopicarn(secret):
        get_secret_value_response = secretmanager.describe_secret(
            SecretId=secret
        )
        secret = get_secret_value_response['Tags']
        data = json.dumps(secret)
        pretty_data = json.loads(data)
        snstopics = [dict['Value'] for dict in pretty_data if dict['Key'] == 'snstopic']
        snstopicarn = " ".join(snstopics)
        return (snstopicarn)
        
def create_key(username,secret):
    access_key_metadata = iam_client.create_access_key(UserName=username)
    access_key = access_key_metadata['AccessKey']['AccessKeyId']
    secret_key = access_key_metadata['AccessKey']['SecretAccessKey']
    snstopic = get_snstopicarn(secret)
    try:
        json_data = json.dumps(
        {'AccessKey': access_key, 'SecretKey': secret_key})
        secretmanager.put_secret_value(
        SecretId=secret, SecretString=json_data)
        emailmsg = 'Hello,\n\n' \
        'A new access key has been created for key rotation. \n\n' \
        f'Access Key Id: {access_key}\n' \
        f'Access Key Secret: {secret_key}\n' \
        f'Secrets Manager Secret Id: {username}'

        emailmsg = f'{emailmsg}\n\n' \
        f'Please obtain the new access key information from ' \
        'secrets manager using the secret Id provided above in ' \
        f'{AWS_REGION_NAME} and update your application within 7 days ' \
        'to avoid interruption.\n'

        sns.publish(TopicArn=snstopic, Message=emailmsg,
        Subject=f'AWS Access Key Rotation: New key is available for '
        f'{username}')
    except ClientError as e:
        print(e)

def disable_key(access_key, username):
    try:
        iam_client.update_access_key(UserName=username, AccessKeyId=access_key, Status="Inactive")
        print(access_key + " has been disabled.")
    except ClientError as e:
        print("The access key with id %s cannot be found" % access_key)

def delete_key(access_key, username):
    try:
        iam_client.delete_access_key(UserName=username, AccessKeyId=access_key)
        print (access_key + " has been deleted.")
    except ClientError as e:
        print("The access key with id %s cannot be found" % access_key)

def lambda_handler(event, context):
    secretarn = event['SecretId']
    user = get_username(secret=secretarn)
    user_iam_details=list_access_key(user=user,days_filter=0,status_filter='Active')
    for _ in user_iam_details:
        disable_key(access_key=_['AccessKeyId'], username=_['UserName'])
        delete_key(access_key=_['AccessKeyId'], username=_['UserName'])
        create_key(username=_['UserName'],secret=secretarn)
    
    return {
        'statusCode': 200,
        'body': list_access_key(user=user,days_filter=0,status_filter='Active')
    }
