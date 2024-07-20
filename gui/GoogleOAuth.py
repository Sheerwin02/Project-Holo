import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# In GoogleOAuth.py

def connect_to_google_account():
    creds = None
    token_path = 'token.json'
    creds_path = 'credentials.json'

    try:
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.valid:
                logging.info("Google account already connected.")
                return "Google account already connected.", True
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        logging.info("Google account connected successfully.")
        return "Google account connected successfully.", True
    except Exception as e:
        logging.error(f"Error obtaining credentials: {e}")
        return f"Error obtaining credentials: {e}", False


def get_calendar_service():
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        logging.info("Google Calendar service built successfully.")
        return service
    except Exception as e:
        logging.error(f"Error building Google Calendar service: {e}")
        return None

def get_upcoming_events(max_results=10):
    service = get_calendar_service()
    if service:
        try:
            events_result = service.events().list(
                calendarId='primary', maxResults=max_results, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                logging.info("No upcoming events found.")
                return ["No upcoming events found."]
            events_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                events_list.append(f"{event['id']}: {start}: {event['summary']}")
            logging.info("Upcoming events retrieved successfully.")
            return events_list
        except Exception as e:
            logging.error(f"Error retrieving events: {e}")
            return [f"Error retrieving events: {e}"]
    return ["Failed to build Google Calendar service."]

def add_event(summary, start_time, end_time, description=''):
    service = get_calendar_service()
    if service:
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
            'description': description,
        }
        try:
            event_result = service.events().insert(calendarId='primary', body=event).execute()
            logging.info(f"Event created: {event_result['summary']} at {event_result['start']['dateTime']}")
            return f"Event created: {event_result['summary']} at {event_result['start']['dateTime']}"
        except Exception as e:
            logging.error(f"Error creating event: {e}")
            return f"Error creating event: {e}"
    return "Failed to build Google Calendar service."

def edit_event(event_id, summary=None, start_time=None, end_time=None, description=None):
    service = get_calendar_service()
    if service:
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            if summary:
                event['summary'] = summary
            if start_time:
                event['start']['dateTime'] = start_time
            if end_time:
                event['end']['dateTime'] = end_time
            if description:
                event['description'] = description
            updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
            logging.info(f"Event updated: {updated_event['summary']} at {updated_event['start']['dateTime']}")
            return f"Event updated: {updated_event['summary']} at {updated_event['start']['dateTime']}"
        except Exception as e:
            logging.error(f"Error updating event: {e}")
            return f"Error updating event: {e}"
    return "Failed to build Google Calendar service."

def delete_event(event_id):
    service = get_calendar_service()
    if service:
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            logging.info(f"Event deleted: {event_id}")
            return f"Event deleted: {event_id}"
        except Exception as e:
            logging.error(f"Error deleting event: {e}")
            return f"Error deleting event: {e}"
    return "Failed to build Google Calendar service."
