# AWS Lambda Code
# environment variables are set in AWS and encrypted


from httplib2 import Http
from json import dumps
from os import environ


def lambda_handler(event, context):

    url = 'https://chat.googleapis.com/v1/spaces/AAAA00sTu1M/messages?key='+environ['google_key']+'&token='+environ['google_secret']

    bot_message = {
       'text' : """ TEXT or whatever """ }

    message_headers = { 'Content-Type': 'application/json; charset=UTF-8'}

    http_obj = Http()

    response = http_obj.request(
        uri=url,
        method='POST',
        headers=message_headers,
        body=dumps(bot_message),
    )

    print(response)


if __name__ == '__main__':
    main()

#http_obj.request(
#  uri=THE_SAVED_URL,
#  method='POST',
#  headers=message_headers,
#  body=dumps(bot_message),
#)
