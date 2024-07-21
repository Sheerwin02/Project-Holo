from email.mime.application import MIMEApplication
import os
import logging
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import mimetypes
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the scope
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

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

# Email functions

def get_gmail_service():
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        service = build('gmail', 'v1', credentials=creds)
        logging.info("Gmail service built successfully.")
        return service
    except Exception as e:
        logging.error(f"Error building Gmail service: {e}")
        return None

def fetch_emails(max_results=10):
    service = get_gmail_service()
    if service:
        try:
            results = service.users().messages().list(userId='me', maxResults=max_results).execute()
            messages = results.get('messages', [])
            email_list = []

            logging.info(f"Fetched {len(messages)} messages.")

            for msg in messages:
                try:
                    msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
                    headers = msg_detail.get('payload', {}).get('headers', [])
                    subject = next(header['value'] for header in headers if header['name'] == 'Subject')

                    email_list.append({
                        'id': msg['id'],
                        'snippet': msg_detail.get('snippet', 'No snippet available'),
                        'subject': subject if subject else 'No subject'
                    })
                except StopIteration:
                    logging.warning(f"Message with ID {msg['id']} does not have a subject.")
                    email_list.append({
                        'id': msg['id'],
                        'snippet': msg_detail.get('snippet', 'No snippet available'),
                        'subject': 'No subject'
                    })
                except Exception as e:
                    logging.error(f"Error retrieving details for message ID {msg['id']}: {e}")

            logging.info("Emails retrieved successfully.")
            return email_list

        except Exception as e:
            logging.error(f"Error retrieving emails: {e}")
            return [f"Error retrieving emails: {e}"]
    else:
        logging.error("Failed to build Gmail service.")
        return ["Failed to build Gmail service."]


def quick_reply(message_id, reply_text):
    service = get_gmail_service()
    if service:
        try:
            message = service.users().messages().get(userId='me', id=message_id).execute()
            thread_id = message['threadId']
            reply = {
                'raw': base64.urlsafe_b64encode(reply_text.encode("utf-8")).decode("utf-8"),
                'threadId': thread_id
            }
            service.users().messages().send(userId='me', body=reply).execute()
            logging.info(f"Reply sent successfully to thread: {thread_id}")
            return f"Reply sent successfully to thread: {thread_id}"
        except Exception as e:
            logging.error(f"Error sending reply: {e}")
            return f"Error sending reply: {e}"
    return "Failed to build Gmail service."

def send_email(to, subject, body):
    service = get_gmail_service()
    if service:
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            message = {'raw': raw}
            service.users().messages().send(userId='me', body=message).execute()
            logging.info(f"Email sent successfully to: {to}")
            return f"Email sent successfully to: {to}"
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return f"Error sending email: {e}"
    return "Failed to build Gmail service."

def get_email_details(email_id):
    service = get_gmail_service()
    if service:
        try:
            message = service.users().messages().get(userId='me', id=email_id, format='full').execute()
            payload = message['payload']
            headers = payload['headers']
            subject = next(header['value'] for header in headers if header['name'] == 'Subject')
            from_ = next(header['value'] for header in headers if header['name'] == 'From')
            date = next(header['value'] for header in headers if header['name'] == 'Date')
            body = ''
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        body += part['body']['data']
            else:
                body = payload['body']['data']
            body = base64.urlsafe_b64decode(body.encode('UTF-8')).decode('utf-8')
            return {'subject': subject, 'from': from_, 'date': date, 'body': body}
        except Exception as e:
            logging.error(f"Error getting email details: {e}")
            return None
    return None

def delete_email(email_id):
    service = get_gmail_service()
    if service:
        try:
            service.users().messages().delete(userId='me', id=email_id).execute()
            logging.info(f"Email deleted successfully: {email_id}")
            return f"Email deleted successfully: {email_id}"
        except Exception as e:
            logging.error(f"Error deleting email: {e}")
            return f"Error deleting email: {e}"
    return "Failed to build Gmail service."