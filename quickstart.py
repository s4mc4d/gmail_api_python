"""Testing gmail api 
Steps can be found on https://towardsdatascience.com/extracting-metadata-from-medium-daily-digest-newsletters-via-gmail-api-97eee890a439

The goal is to retrieve all senders emails in order to make statistics
"""

from __future__ import print_function

import os
import pprint
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import threading

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

EMAIL_REGEX = r"[\w\.-]+@[\w\.-]+"

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def get_all_messages_id():
    """
    Lists the user's Gmail senders emails.
    """

    service = build('gmail', 'v1', credentials=get_credentials())

    # Call the Gmail API
    # results = service.users().labels().list(userId='me').execute()
    message_objects = service.users().messages()
    messages_request_response = message_objects.list(userId='me',maxResults=500).execute()
    messages_list = messages_request_response["messages"]  # contains list of ids
    nextPageToken = messages_request_response["nextPageToken"]
    print(f"First page token {nextPageToken}")

    # retrieve all other pages of messages ids
    while len(messages_list) % 500 == 0:
        print(f"Next page : {nextPageToken}")
        messages_request_response_2 = service.users().messages().list(userId='me', maxResults=500, pageToken=nextPageToken).execute()
        new_messages = messages_request_response_2["messages"]
        nextPageToken = messages_request_response_2['nextPageToken']
        messages_list.extend(new_messages)

    return messages_list


def extract_senders_from_message_id(messages_dict):
    """Extracts sender email from Messages

    Parameters
    ----------
    messages_dict : list of dict 
        [{"id":...,threadId:...}, ...]

    Returns
    -------
    emails : list
        list of emails
    """
    service = build('gmail', 'v1', credentials=get_credentials())
    message_objects = service.users().messages()
    
    emails = []
    # Browsing through messages content to retrieve email addresses
    for i,message_id in enumerate(messages_dict):
        print(i)
        message_obj = message_objects.get(id=message_id["id"],userId="me").execute()
        # source  : https://developersclear.google.com/gmail/api/reference/rest/v1/users.messages/get
        
        data = message_obj["payload"]["headers"]  # this is a list of dict {"name":...,"value":...}
        for item in data:
            if item["name"].lower().strip() in ["from","to"]:
                res = re.findall(EMAIL_REGEX,item["value"])
                emails.extend(res)
        # pprint.pprint(res)

    return emails
    


if __name__ == '__main__':

    message_dict_results = get_all_messages_id()
    emails_output = extract_senders_from_message_id(message_dict_results)
    with open("emails.txt", "w") as target:
        target.write("\n".join(emails_output))
