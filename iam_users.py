#!/usr/bin/env python
# Get IAM Users and Access Key Info
# Author: Jerry Reid

# This script will get ALL IAM users from selected AWS account and send it to cloudwatch
# This will allow grafana to graph it so we can get a dashboard

##ToDo
# create log group using pipeline for proper encryption; add username string via script


import boto3
import datetime
import json
import os
import datetime
import time
from datetime import date

#Variables
session = boto3.Session()
os.environ['AWS_PROFILE'] = "<profile>"
os.environ['AWS_DEFAULT_REGION'] = "us-west-2"
tag_created_by = 'CreatedBy'
tag_owner = 'Service' #Service for now
tag_purpose = 'Service' #Service for now

# Initialize the Boto3 IAM client
iam = session.client('iam')

# Initialize the CloudWatch Logs client
cloudwatchlogs = boto3.client('logs')

# List all IAM users
response = iam.list_users()

# Create a log group name for CloudWatch Logs
log_group_name = 'IAMUserLogGroup-test'

# Create the log group if it doesn't exist
try:
    cloudwatchlogs.create_log_group(logGroupName=log_group_name)
except:
    print("Log group already exists")


def get_specific_iam_user_tag(user_name, tag_key):
    iam_client = boto3.client('iam')
    try:
        response = iam_client.list_user_tags(UserName=user_name)
        # Extract and search for the specific tag by its key
        tags = response['Tags']
        desired_tag = tag_key
        for tag in tags:
            if tag['Key'] == tag_key:
                desired_tag = tag
                break
        # Check if the tag was found and return its value
        if desired_tag:
            return desired_tag['Value']
        else:
            return None  # Tag not found
    except Exception as e:
        print(f"Error: {str(e)}")
        return None  # Error occurred

# Iterate through the list of IAM users
for user in response['Users']:
    user_name = user['UserName']

    # List access keys for the user
    access_keys = iam.list_access_keys(UserName=user_name)

    # Iterate through the user's access keys
    for access_key in access_keys['AccessKeyMetadata']:
        access_key_id = access_key['AccessKeyId']
        status = access_key['Status']

        # Get the access key last used information
        last_used = iam.get_access_key_last_used(AccessKeyId=access_key_id)
        last_used_date = last_used['AccessKeyLastUsed'].get('LastUsedDate')

        # Calculate expiration date (e.g., 90 days)
        create_date = access_key['CreateDate']
        expiration_date = create_date + datetime.timedelta(days=90)

        #Calculate days till expiration
        accesskeydate = access_keys['AccessKeyMetadata'][0]['CreateDate'].date()
        currentdate = date.today()
        age_of_key = str((currentdate - accesskeydate).days) + " days"

        # get tags
        created_by_tag = get_specific_iam_user_tag(user_name, tag_created_by)
        purpose_tag = get_specific_iam_user_tag(user_name, tag_purpose)
        owner_tag = get_specific_iam_user_tag(user_name, tag_owner)

        # Prepare IAM user data as a dictionary
        user_data = {
            'UserName': user_name,
            'AccessKeyId': access_key_id,
            'Status': status,
            'LastUsedDate': last_used_date.strftime('%Y-%m-%d')if last_used_date else 'N/A',
            'ExpirationDate': expiration_date.strftime('%Y-%m-%d'),
            'Age of Key' : age_of_key,
            'Owner' : owner_tag,
            'Purpose': purpose_tag,
            'github link' : created_by_tag
        }

        # Send IAM user data to CloudWatch Logs
        # create loggroup once
        # if logstream exist update else create new and put into function
        print(user_data)
        log_message = json.dumps(user_data)
       # this will be created via argo
        try:
            cloudwatchlogs.create_log_stream(logGroupName=log_group_name,logStreamName=user_name)
        except:
            print("Log Stream Already Created ignoring create")
        cloudwatchlogs.put_log_events(
            logGroupName=log_group_name,
            logStreamName=user_name,
            logEvents=[
                {
                    'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                    'message': log_message
                }
            ]
        )

# Sample Output
# {
#     "UserName": "$username",
#     "AccessKeyId": "$accesskey",
#     "Status": "Active",
#     "LastUsedDate": "N/A",
#     "ExpirationDate": "2021-10-18",
#     "Age of Key": "813 days",
#     "Owner" : "owner_tag",
#     "Purpose": "purpose_tag",
#     "github link" : "created_by_tag"
# }

