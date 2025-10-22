import os
import boto3

def assume_role(role_arn, session_name="LambdaSecretAccessSession"):
    sts_client = boto3.client('sts')
    assumed_role = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name
    )
    return assumed_role['Credentials']

def get_secret(credentials, secret_name):
    secrets_client = boto3.client(
        'secretsmanager',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return {"Secret": secret}
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise e

def lambda_handler(event, context):
    role_arn = os.environ['TARGET_ROLE_ARN']
    secret_name = os.environ['SECRET_NAME']
    credentials = assume_role(role_arn)
    return get_secret(credentials, secret_name)
