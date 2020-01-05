# coding: utf-8
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
import os
import requests
from flask import Flask, request, jsonify, json
from threading import Thread
from random import seed, randint

import sheet

app = Flask(__name__)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_client = SlackClient(slack_bot_token)

SPREADSHEET_ID_REACT = os.environ["SPREADSHEET_ID"]
range_react = '!A:C'

SPREADSHEET_ID_EXCUSE = os.environ["SPREADSHEET_ID_EXCUSE"]
range_excuse = 'Sheet1!A:A'

port = int(os.environ["PORT"])

reacts = {}
toMake = []
leaderboard = []
people_who_have_reacted = {}

ricebowl = [
    "Research shows that Ricebowl is the best club at Gunn High School.",
    "Ricebowl of course!",
    "Ricebowl is objectively the best club at Gunn.",
    "Sources tell me that it's Ricebowl."
]

seed(1)

members = requests.get('https://slack.com/api/users.list', params={'token': slack_bot_token}).json()

for member in members:
    people_who_have_reacted[member['real_name']] = 0

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
        elif "best club" in text:
            return_message = ricebowl[randint(0, len(ricebowl) - 1)]
        if return_message != None:
            slack_client.api_call("chat.postMessage", channel=channel, text=return_message)

@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    event = event_data["event"]
    channel = requests.get('https://slack.com/api/channels.info', params={'token': slack_bot_token, 'channel': event["item"]["channel"]}).json()['channel']['name']
    if channel == "announcements":
        user = requests.get('https://slack.com/api/users.info', params={'token': slack_bot_token, 'user': event["user"]}).json()['user']['real_name']
        emoji = event["reaction"]
        key = event_data["event"]["item"]["ts"]
        people_who_have_reacted[user] += 1
        if not checkKey(reacts, key):
            reacts[key] = []
            toMake.append(key)
        reacts[key].append([user, emoji])

def checkKey(dict, key): 
    if key in dict.keys(): 
        return True
    else: 
        return False

def addToSheet(response_url):
    for name in toMake:
        sheet.add_sheets(SPREADSHEET_ID_REACT, name)
    del toMake[:]
    for key in reacts:
        new_range = key + range_react
        resource = {
            "majorDimension": "ROWS",
            "values": reacts[key]
        }
        sheet.append(SPREADSHEET_ID_REACT, new_range, resource)
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

def addExcuseToSheet(response_url, text):
    list_ = [[text]]
    resource = {
        "majorDimension": "ROWS",
        "values": list_
    }
    sheet.append(SPREADSHEET_ID_EXCUSE, range_excuse, resource)
    payload = {"text":"The spreadsheet has been updated.\n Here\'s the link! --> https://tinyurl.com/grtexcuses2020",
                "username": "bot"}
    requests.post(response_url, data=json.dumps(payload))

@app.route('/add_excuse', methods=['POST'])
def add_excuse():
    response_url = request.form.get("response_url")
    text = request.form.get("text")
    thr = Thread(target=addExcuseToSheet, args=[response_url, text])
    thr.start()
    return {"text": "Working on it..."}

@app.route('/helpme', methods=['POST'])
def helpme():
    return {
        "response_type": "in_channel",
        "text": "@ commands for botbotbot:\n    - hi/hello\n    - rr\n\n/ commands for botbotbot:\n    - /helpme\n    - /dump (should only be used by admin)\n    - /tf [text]\n    - /uf [text]\n    - /joke\n    - /add_excuse [text]\n    - /make_excuse"
        }

@app.route('/tf', methods=['POST'])
def tf():
    to_send = request.form.get("text") + " (╯°□°）╯︵ ┻━┻".decode('utf-8')
    payload = {
        "response_type": "in_channel",
        "text": to_send
        }
    return jsonify(payload)

@app.route('/uf', methods=['POST'])
def uf():
    to_send = request.form.get("text") + " ┬─┬ ノ( ゜-゜ノ)".decode('utf-8')
    payload = {
        "response_type": "in_channel",
        "text": to_send
        }
    return jsonify(payload)

@app.route('/joke', methods=['POST'])
def joke():
    joke = str(requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}).json()["joke"])
    payload = {
        "response_type": "in_channel",
        "text": joke
    }
    return jsonify(payload)

def getExcuseFromSheet(response_url):
    val = sheet.get_value(SPREADSHEET_ID_EXCUSE, 'Sheet1!A1:A')
    index = randint(0, len(val) - 1)
    text = val[index][0]
    payload = {
        "response_type": "in_channel",
        "text":text
        }
    requests.post(response_url, data=json.dumps(payload))

@app.route('/make_excuse', methods=['POST'])
def excuses():
    response_url = request.form.get("response_url")
    thr = Thread(target=getExcuseFromSheet, args=[response_url])
    thr.start()
    payload = {
        "text": "Generating excuse..."
    }
    return jsonify(payload)

@app.route('/leaderboard', methods=['POST'])
def leaderboard():
    min_val = min(people_who_have_reacted.itervalues())
    leaderboard = [for key, value in people_who_have_reacted.itervalues() == min_val]
    to_send = requests.form.get("text")
    for person in leaderboard:
        to_send += person + "\n"
    payload = {
        "response_type": "in_channel"
        "text": to_send
    }

app.run(port=port, host="0.0.0.0")