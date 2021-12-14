# gmail API - Extract all senders emails

## Prerequisites

Detailed procedure can be found [here](https://towardsdatascience.com/extracting-metadata-from-medium-daily-digest-newsletters-via-gmail-api-97eee890a439)

1. Create a new project in the Google Cloud Console
1.  Enable the Gmail API
1. Create Credentials
1. OAuth Consent Screen
1. Scopes

### Summary 

- Access [Google Cloud Platform](console.cloud.google.com)
- Create project
- Add credentials in API & Sercices and download as json file. Put this file next to the script.
- Add personal email address as a test user for application consent screen.
- Activate Gmail API. Go to Gmail API Quickstart code to have the snippet which manages credentials.


## Run code

```shell
python3 quickstart.py
```