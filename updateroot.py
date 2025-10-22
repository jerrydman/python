 #Python Script to get Update from Amazon Secrets Manager
#Hashed to be used for rotatiting passwords

import boto3
import crypt
import string
import random 
from botocore.exceptions import ClientError


#Global Variables
secret_name = "root-pw-linux"
endpoint_url = "https://secretsmanager.us-east-2.amazonaws.com"
region_name = "us-east-2"

#defines new password characteristics
password_charset = string.ascii_lowercase + string.digits + string.punctuation



#defines new password randomly generated 


def new_password(char_set, length):
    if not hasattr(new_password, "rng"):
        new_password.rng = random.SystemRandom() # Create a static variable
    return ''.join([ new_password.rng.choice(char_set) for _ in xrange(length) ])
       
def update_secret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url
    )
    password = new_password(password_charset, 16)  
    client.update_secret(SecretId=secret_name,SecretString=password)
       
      
update_secret()


