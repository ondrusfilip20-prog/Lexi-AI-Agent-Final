import datetime
import os, os.path
import json # Essential for reading the token from the environment variable
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    Handles Google authorization. 
    This version is designed specifically for Render and relies ONLY on 
    the GOOGLE_CALENDAR_TOKEN environment variable.
    """
    
    # Check for the deployed token
    if 'GOOGLE_CALENDAR_TOKEN' in os.environ:
        try:
            # Load credentials directly from the environment variable (JSON string)
            token_data = json.loads(os.environ['GOOGLE_CALENDAR_TOKEN'])
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            service = build('calendar', 'v3', credentials=creds)
            
            # CRITICAL: Returns immediately for the successful deployment
            return service 
        except Exception as e:
            # If loading fails, something is wrong with the JSON string itself
            print(f"FATAL ERROR: GOOGLE_CALENDAR_TOKEN environment variable is invalid: {e}")
            raise e 

    # If the environment variable is not set (should not happen on Render)
    print("FATAL ERROR: GOOGLE_CALENDAR_TOKEN environment variable not found. Calendar tool is disabled.")
    raise EnvironmentError("Calendar token not found. Cannot initialize Google Calendar.")

def find_open_slots(service, calendar_id='primary'):
    """Queries the calendar API for busy slots in the next 48 hours."""
    # Ensure local machine runs in UTC for compatibility with the API
    now = datetime.datetime.utcnow().isoformat() + 'Z' 
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=48)).isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found. The next 48 hours are likely open."
        else:
            busy_slots = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                busy_slots.append(f"Busy from {event.get('summary', 'No Title')}: {start} to {end}")
            
            return "\n".join(busy_slots)

    except HttpError as error:
        return f'An error occurred while fetching calendar data: {error}'