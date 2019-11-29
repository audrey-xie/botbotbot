from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
import os
import requests
from flask import Flask, request, jsonify, json
from threading import Thread

import sheet

app = Flask(__name__)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_client = SlackClient(slack_bot_token)

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
range_ = '!A:C'

reacts = {}
toMake = []

commands = ["hi", "hello", "rr", "joke", "help"]

@slack_events_adapter.on("app_mention")
def app_mention(event_data):
    message = event_data["event"]
    return_message = None
    if message.get("subtype") is None:
        text = message.get('text')
        channel = message["channel"]
        if "hi" in text or "hello" in text:
            return_message = "Hello <@%s>! :tada:" % message["user"]
        elif "rr" in text:
            return_message = "follow this link --> https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        elif "joke" in text:
            return_message = str(requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}).json()["joke"])
        elif "help" in text:
            return_message = "Commands for botbotbot:\n    - hi/hello\n    - joke\n    - rr"
        
        if return_message != None:
            slack_client.api_call("chat.postMessage", channel=channel, text=return_message)

@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    event = event_data["event"]
    channel = requests.get('https://slack.com/api/groups.info', params={'token': slack_bot_token, 'channel': event["item"]["channel"]}).json()['group']['name']
    user = requests.get('https://slack.com/api/users.info', params={'token': slack_bot_token, 'user': event["user"]}).json()['user']['real_name']
    key = event_data["event"]["item"]["ts"]
    if not checkKey(reacts, key):
        reacts[key] = []
        toMake.append(key)
    reacts[key].append([channel, user])

def checkKey(dict, key): 
    if key in dict.keys(): 
        return True
    else: 
        return False

def addToSheet(response_url):
    for name in toMake:
        sheet.add_sheets(SPREADSHEET_ID, name)
    del toMake[:]
    for key in reacts:
        new_range = key + range_
        resource = {
            "majorDimension": "ROWS",
            "values": reacts[key]
        }
        sheet.append(SPREADSHEET_ID, new_range, resource)
        del reacts[key][:]
    payload = {"text":"The spreadsheet has been updated.\n Here\'s the link! --> https://tinyurl.com/grtbot2020",
                "username": "bot"}
    requests.post(response_url, data=json.dumps(payload))

@app.route('/dump', methods=['POST'])
def dump():
    response_url = request.form.get("response_url")
    thr = Thread(target=addToSheet, args=[response_url])
    thr.start()
    return {"text": "Working on it..."}

if __name__ == "__main__":
  app.run(port=3000)