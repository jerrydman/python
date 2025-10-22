#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Requires Twilio Account for texting

import urllib.request
import threading
import ssl
from twilio.rest import Client

account_sid = ''
auth_token = ''
client = Client(account_sid, auth_token)

# How often to refresh the page, in seconds
UPDATE = 60.0

# Create a secure SSL context
context = ssl.create_default_context()

# This function repeatedly reads the CVS website, and if any appointments are
# available in your state, it texts you.


def sendit():

    # Initializes threading (repition / refreshing of website)
    threading.Timer(UPDATE, sendit).start()

    # Reads website into var 'html'
    html = urllib.request \
        .urlopen('https://www.cvs.com/immunizations/covid-19-vaccine').read()

    # If not all appointments are booked...
    lookforstring \
        = "At this time, all appointments in Massachusetts are booked."
    if lookforstring.encode() not in html:
        client.messages \
            .create(
             body='CVS Has appointments available',
             from_='+1555555555',
             to='+1555555555'
                   )


sendit()
