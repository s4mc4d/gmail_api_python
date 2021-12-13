"""Testing gmail api 
Steps can be found on https://towardsdatascience.com/extracting-metadata-from-medium-daily-digest-newsletters-via-gmail-api-97eee890a439
Objects documentation can be found here : https://developers.google.com/gmail/api/reference/rest
The goal is to retrieve all senders emails in order to make statistics

NB : Gmail API must be activated and a project should be defined in Google Cloud Platform
See API & Services
"""

from __future__ import print_function
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool
from functools import partial

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
    while True: #len(messages_list) % 500 == 0:
        print(f"Next page : {nextPageToken}")
        messages_request_response_2 = service.users().messages().list(userId='me', maxResults=500, pageToken=nextPageToken).execute()
        new_messages = messages_request_response_2["messages"]
        messages_list.extend(new_messages)
        try:
            nextPageToken = messages_request_response_2['nextPageToken']
        except KeyError:
            print(f"No more page token")
            break

    return messages_list



def process_all_messages_id_parallel(messages_dict):
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
    
    pool = Pool(processes=os.cpu_count())

    # messages_ids_only = [item["id"] for item in messages_dict]

    # Processing all messages content in parallel to retrieve email addresses
    emails = pool.map(func=extract_senders_from_single_id,iterable=messages_dict)
    pool.close()
    pool.join()

    return emails

def extract_senders_from_single_id(message_id):
    """Finds email addresses from a single mail id

    Parameters
    ----------
    service_users_messages_obj : object
        result of service.users().messages()
    message_id : string
        unique id of mail

    Returns
    -------
    output : list
       list of emails
    """
    service = build('gmail', 'v1', credentials=get_credentials())
    service_users_messages_obj = service.users().messages()

    # service_users_messages_obj is the result of build('gmail', 'v1', credentials=get_credentials()).users().messages()
    message_obj = service_users_messages_obj.get(id=message_id["id"],userId="me").execute()
        # source  : https://developersclear.google.com/gmail/api/reference/rest/v1/users.messages/get
    
    data = message_obj["payload"]["headers"]  # this is a list of dict {"name":...,"value":...}
    output = []
    for item in data:
        if item["name"].lower().strip() in ["from","to"]:
            res = re.findall(EMAIL_REGEX,item["value"])
            output.extend(res)
    print("Extracted %s " % (output))
    
    return output


    


if __name__ == '__main__':

    message_dict_results = get_all_messages_id()

    emails_output = process_all_messages_id_parallel(message_dict_results)

    with open(os.path.join("data","emails_list.txt", "w")) as target:
        target.write("\n".join([item for sublist in emails_output for item in sublist]))
