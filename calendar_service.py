import datetime
import os, os.path
import json # <-- Added this for JSON parsing of the environment variable
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_calendar_service():
    """Handles Google login/authorization and returns the calendar API service object."""
    
    # 1. CHECK FOR DEPLOYED TOKEN (FOR RENDER DEPLOYMENT)
    if 'GOOGLE_CALENDAR_TOKEN' in os.environ:
        try:
            # Load credentials directly from the environment variable (JSON string)
            token_data = json.loads(os.environ['GOOGLE_CALENDAR_TOKEN'])
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            service = build('calendar', 'v3', credentials=creds)
            
            # CRITICAL FIX: RETURN IMMEDIATELY, STOPPING THE FUNCTION HERE
            return service 
        except Exception as e:
            # If loading fails (e.g., bad format), log the error and continue to local check
            print(f"Error loading GOOGLE_CALENDAR_TOKEN from environment: {e}")

    # 2. LOCAL LOGIC (The original flow for your development machine)
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # If expired but has a refresh token, renew it
            creds.refresh(Request())
        else:
            # If no token, or invalid, run the local server flow (triggers browser sign-in)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the new credentials for the next local run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    # 3. BUILD AND RETURN THE SERVICE (For local runs that reach this point)
    service = build('calendar', 'v3', credentials=creds)
    return service

def find_open_slots(service, calendar_id='primary'):
    """Queries the calendar API for busy slots in the next 48 hours."""
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=48)).isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        # This function is usually meant to return the events, but for simplicity,
        # we'll return a placeholder string based on results.
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found. The next 48 hours are likely open."
        else:
            busy_slots = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                busy_slots.append(f"Busy from {start} to {end} with event: {event.get('summary', 'No Title')}")
            
            return "\n".join(busy_slots)

    except HttpError as error:
        return f'An error occurred: {error}'