#!/usr/bin/env python3

import smtplib
import textwrap
import datetime

now = datetime.datetime.now()
server = ""
port = 25

fromaddr = "From: "
toaddr = "To: "

message = now.strftime("%Y-%m-%d %H:%M:%S")

smtpObj = smtplib.SMTP(server,port)
smtpObj.set_debuglevel(1)
smtpObj.sendmail(fromaddr, toaddr, message)
smtpObj.quit()
print("Successfully sent email")
