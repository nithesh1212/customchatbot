import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()
from flask import Flask
from flask import request

from flask import Blueprint, request
import requests

import requests
import json
from datetime import datetime

############# How to set a webhook for Cisco Spark
# Use ngrok for making localhost:port to public safely (Install ngrok free )
# use command 'ngrok http <port>'
# Now Register a webhook at cisco spark using https://developer.ciscospark.com/endpoint-webhooks-post.html#
# in this link use
# authorization: Bot access token
# targetUrl: <ngrok link>/
# resource: messages
# event : create
# filter: roomId=room_id (as below)
# This will register ngrok link to webhook
# now run this file using python starterbotCiscoSpark.py
#############
## Supporting links
# 1 - http://madumal.piyasundara.org/2017/02/python-chat-bot-integration-with-cisco.html
# 2 - https://communities.cisco.com/community/developer/spark/blog/2016/07/18/spark-bot-demo
# 3 - https://developer.ciscospark.com/endpoint-rooms-get.html to get room ids
# 4 - https://developer.ciscospark.com  to create a new bot
# 5 - https://learninglabs.cisco.com/lab/collab-spark-chatops-bot-itp/step/1  Lab for many bots ay cisco spark
# 6 - https://learninglabs.cisco.com/lab/collab-sparkwebhook/step/1  webhook understanding good one

# Access token can be generated using the CISCO BOT account and Bot Email also can find in there
botEmail = "custombot@sparkbot.io"  # bot's email address
accessToken = "ZjJjMjc4ZjItN2U1Ni00NjdmLWFmNzMtOTFhZjJlM2Q1ZjRiYmMyYzI0MzUtOTcx"  # Bot's access token
host = "https://api.ciscospark.com/v1/"  # end point provided by the CISCO Spark to communicate between their services
#server = "localhost"  # Web hook won't work until the server sets up
#port = 8001
headers = {"Authorization": "Bearer %s" % accessToken, "Content-Type": "application/json"}
room_id = "Y2lzY29zcGFyazovL3VzL1JPT00vNDYzM2FlN2ItODQyOC0zOTdlLWFlYTQtMGQyY2MxNjc1NjI3"  ## Room id where bot is added@app.route('/webhook', methods=['POST'])

SparkTest = Blueprint('SparkTest_blueprint', __name__, url_prefix='/spark')


@SparkTest.route('/integration', methods=['POST'])
def get_tasks():
    messageId = request.json.get('data').get('id')
    print(messageId);
    messageDetails = requests.get(host + "messages/" + messageId, headers=headers)
    print(messageDetails)
    replyForMessages(messageDetails)
    return ""


# A function to send the message by particular email of the receiver
def sendMessage(message, toPersonEmail):
    payload = {"roomId": room_id, "text": message}
    response = requests.request("POST", "https://api.ciscospark.com/v1/messages/", data=json.dumps(payload),
                                headers=headers)
    return response.status_code


# A function to get the reply and generate the response of from the bot's side
## Add Bot logic for complicated bots
def replyForMessages(response):
    responseMessage = response.json().get('text')
    print("response message", responseMessage)
    toPersonEmail = response.json().get('personEmail')
    print(responseMessage)
    if toPersonEmail != botEmail:
        if 'hello' in responseMessage:
            messageString = 'Hello! What can i do for you?'
            sendMessage(messageString, toPersonEmail)
        elif "What is the date today?".lower() in responseMessage.lower():
            messageString = "it is " + datetime.now().strftime('%A %d %B %Y') + " today."
            sendMessage(messageString, toPersonEmail)
        else:
            messageString = 'Sorry! I was not programmed to answer this question!'
            sendMessage(messageString, toPersonEmail)



