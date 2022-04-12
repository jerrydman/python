# Script to check the sfdcit github audit log
# Currently on checking for protected_branch_override
# v1.0 - Jerry Reid Initial Build
# ghtoken currently stored in secrets manager
# script will take document id and put it in dynamo db table so no duplicates

import requests
import os
import json
import boto3
import base64
from botocore.exceptions import ClientError
from datetime import date


ghToken = os.environ['ghtoken']
region = os.environ['region']
topicArn = os.environ['topicArn']
tableName = os.environ['tableName']
today = date.today()
org = os.environ['ghorg'].strip()
repo = os.environ['ghrepo']
ghURL = 'https://api.github.com/orgs/{0}/audit-log?phrase=\
        repo:{0}/{1}+action:protected_branch.policy_override+created:{2}' \
         .format(org, repo, today).replace(" ", "")
value = '[{"org": "'+org+'", "_document_id": "logempty"}]'


def get_secret():
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=ghToken)
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
        else:
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return base64.b64decode(get_secret_value_response['SecretBinary'])


def additemtodb():
    ghsecret = get_secret()
    head = {'Authorization': 'token {}'.format(ghsecret)}
    response = requests.get(ghURL, headers=head)
    pretty_json = json.loads(response.text) or json.loads(value)
    docid = pretty_json[0]['_document_id']
    dynamodb = boto3.client('dynamodb')
    try:
        dynamodb.put_item(TableName=tableName,
                          Item={'document_id': {'S': docid}},
                          ConditionExpression="attribute_not_exists \
                          (document_id)",)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(" Item Already Exists No new Protected branch Policy " +
                  "Overrides for {0}".format(today))
        elif e.response['Error']['Code'] == 'list index out of range':
            print("Index out of range")

    else:
        getuiplog(ghsecret)


def getuiplog(ghsecret):
    head = {'Authorization': 'token {}'.format(ghsecret)}
    response = requests.get(ghURL, headers=head)
    pretty_json = json.loads(response.text)
    email_body = (json.dumps(pretty_json, indent=4, sort_keys=True) +
                  "\n Please Visit https://whateverwebsite")
    client = boto3.client('sns')
    response = client.publish(
        TargetArn=topicArn,
        Message=email_body
        )


def lambda_handler(event, context):
    additemtodb()
