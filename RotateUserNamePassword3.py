# Password Rotation for SOX Compliance
# This keeps username the same and rotate password
# it should be in JSON format inside secrets manager
# {"username": "$username", "password": "password"}
# you can change line 39 for whatever needs to be as well
# Jerry Reid


import boto3
import string
import random
import json


#Variables
charset = string.punctuation + string.ascii_letters #Can also make a custom map if needed
passlength = 66
description = "Test Secret for SOX compliance"

secretmanager = boto3.client('secretsmanager')

def new_password(char_set, length):
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
    password = new_password(charset, passlength)  # 66 character password
    first_identifier = json.dumps(client.get_secret_value(SecretId=secretarn), default=str)
    identifier = json.loads(first_identifier)
    id1 = json.loads(identifier['SecretString'])
    data = {}
    data['username'] = id1['username']
    data['password'] = password
    #above codes creates the json with email as it was
    client.update_secret(SecretId=secretarn,Description=description,SecretString=json.dumps(data))
    
def lambda_handler(event, context):
    secretarn = event['SecretId']
    update_secret(secretarn)
