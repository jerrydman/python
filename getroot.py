  
#Python Script to get Secret from Amazon Secrets Manager
#Hashed to be used for rotatiting root passwords

awsAccessKey= ''
awsSecretKey=  ''
awsSecretName= ''
awsRegion = 'us-east-2'
import boto3
import crypt
from botocore.exceptions import ClientError


def get_secret():
    global secret
    secret_name = (awsSecretName)
    endpoint_url = "https://secretsmanager."+(awsRegion)+".amazonaws.com"
    region_name = (awsRegion)

    session = boto3.session.Session()
    client = session.client(
          aws_access_key_id=(awsAccessKey),
          aws_secret_access_key=(awsSecretKey),
          service_name='secretsmanager',
          region_name=region_name,
          endpoint_url=endpoint_url
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", e)
    else:
        # Decrypted secret using the associated KMS CMK
        # Depending on whether the secret was a string or binary, one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            binary_secret_data = get_secret_value_response['SecretBinary']
        
       # pw = secret.split('"')[3] 
        print secret
        #pwhash = crypt.crypt(secret)
        #print "'" + pwhash + "'"
       


get_secret() 
