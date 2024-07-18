import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def connect_to_google_account():
    creds = None
    token_path = 'token.json'
    creds_path = 'credentials.json'

    try:
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        logging.info("Google account connected successfully.")
        return "Google account connected successfully."
    except Exception as e:
        logging.error(f"Error obtaining credentials: {e}")
        return f"Error obtaining credentials: {e}"
