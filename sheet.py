from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build

def append(id, range_, resource):
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    service = build('sheets', 'v4', credentials=creds)
    spreadsheets = service.spreadsheets()
    request = spreadsheets.values().append(spreadsheetId=id, range=range_, valueInputOption="USER_ENTERED", body=resource)
    response = request.execute()

def get_value(id, range_):
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    service = build('sheets', 'v4', credentials=creds)
    spreadsheets = service.spreadsheets()
    request = spreadsheets.values().get(spreadsheetId=id, range=range_)
    response = request.execute()
    return response.get('values', [])

def add_sheets(gsheet_id, sheet_name):
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    service = build('sheets', 'v4', credentials=creds)
    spreadsheets = service.spreadsheets()
    try:
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'tabColor': {
                            'red': 0.44,
                            'green': 0.99,
                            'blue': 0.50
                        }
                    }
                }
            }]
        }
        response = spreadsheets.batchUpdate(
            spreadsheetId=gsheet_id,
            body=request_body
        ).execute()
        return response
    except Exception as e:
        print(e)