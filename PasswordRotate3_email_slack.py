# Password Rotation Compliance
# This keeps username the same and rotate password
# it should be in JSON format inside secrets manager
# {"$whatever": "$username", "$whatever": "password"}
# SNS topic is taken from environment variables
# slack webhook is taken from environment variables

import boto3
import os
import string
import random
import json
import urllib3

# sns topic for notification and slack url if needed
sns_topic = os.environ['sns_topic']
url = os.environ['slack_url']
http = urllib3.PoolManager()

#Variables
charset = string.punctuation + string.ascii_letters #Can also make a custom map if needed
description = "Test Secret for compliance"
passwordlength = 64 #Default is no length tag is created


#get region
region_session = boto3.session.Session()
current_region = region_session.region_name
secretmanager = boto3.client('secretsmanager')
sns = boto3.client('sns', region_name=current_region)

def new_password(char_set,secretarn):
    gettags = secretmanager.describe_secret(
            SecretId=secretarn)['Tags'] 
    jsonlength = [dict['Value'] for dict in gettags if dict['Key'] == 'length']
    if len(jsonlength) != 0:
        length = int(" ".join(jsonlength)) 
    else:
        length = passwordlength
    if not hasattr(new_password, "rng"):
        new_password.rng = random.SystemRandom()
    return ''.join([new_password.rng.choice(char_set) for _ in range(length)]) 

def update_secret(secretarn):
    session = boto3.session.Session()
    current_region = session.region_name
    client = session.client(
        service_name='secretsmanager',
        region_name=current_region,
    )
    password = new_password(charset,secretarn)  # 16 character password
    first_identifier = json.dumps(client.get_secret_value(SecretId=secretarn), default=str)
    identifier = json.loads(first_identifier)
    id1 = json.loads(identifier['SecretString'])
    firstvalue = list(id1.keys())[0]
    secondvalue = list(id1.keys())[1]
    data = {}
    data[firstvalue] = id1[firstvalue]
    data[secondvalue] = password
    #above codes creates the json with keys as it was
    client.update_secret(SecretId=secretarn,Description=description,SecretString=json.dumps(data))
    emailmsg = 'Hello,\n\n' \
        'A new password has been created for key rotation for' + secretarn
    slack_message = {
      "blocks": [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "Password updated for:  "+ "```" + secretarn + "```"
                    },
                    {
                        "type": "mrkdwn",
                        "text": firstvalue + ":" + " "+  id1[firstvalue] + "\n" + secondvalue + " " + "```" + password + "```"
                    },
                ]
            }
        ]
    }
    #Send to slack
    slack = http.request('POST',url,body=json.dumps(slack_message))
    #Send to email
    sns.publish(TopicArn=sns_topic,Message=emailmsg)
    
def lambda_handler(event, context):
    secretarn = event['SecretId']
    update_secret(secretarn)
