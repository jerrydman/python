import os
import requests
import json
import smtplib
import textwrap
from datetime import date



fromaddr = ''
toaddr = ''
server = '
port   = 25


ghToken = ''
today   = date.today()
org     = ''
repo    = ''
ghURL   = 'https://api.github.com/orgs/sfdcit/audit-log?phrase=repo:{0}/{1}+action:protected_branch.policy_override+created:{2}'.format(org,repo,today)

def getLog():
    head ={'Authorization' : 'token {}'.format(ghToken)}
    response = requests.get(ghURL,headers=head)
    jsonresponse = response.json()
    pretty_json = json.loads(response.text)
    email_body = json.dumps(pretty_json, indent=4, sort_keys=True)
    print (email_body)

    if response.text != "[]":
        smtpObj = smtplib.SMTP(server,port)
        smtpObj.sendmail(fromaddr, toaddr, email_body)
        smtpObj.quit()
    else:
        print ("No Protected branch Policy Overrides for {0}".format(today))

getLog()
