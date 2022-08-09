# This keeps username the same and rotate password
# it should be in JSON format inside secrets manager
# {"$whatever": "$username", "$whatever": "password"}
# length is given in aws tags or defaulted to 64 on line 27

import boto3
import os
import string
import random
import json


#Variables
charset = string.punctuation + string.ascii_letters #Can also make a custom map if needed
description = "Test Secret for SOX compliance"

secretmanager = boto3.client('secretsmanager')

def new_password(char_set,secretarn):
    gettags = secretmanager.describe_secret(
            SecretId=secretarn)['Tags'] 
    jsonlength = [dict['Value'] for dict in gettags if dict['Key'] == 'length']
    if len(jsonlength) != 0:
        length = int(" ".join(jsonlength)) 
    else:
        length = 64
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
    #above codes creates the json with email as it was
    client.update_secret(SecretId=secretarn,Description=description,SecretString=json.dumps(data))
    
def lambda_handler(event, context):
    secretarn = event['SecretId']
    #new_password(charset,secretarn)
    update_secret(secretarn)
