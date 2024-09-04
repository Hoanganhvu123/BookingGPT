import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import Field
from langchain.tools import BaseTool

# Định nghĩa các hằng số
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'E:\\chatbot\\SaleGPT\\security\\credentials.json'
TOKEN_FILE = 'token.json'


class DuplicateEventCheckerTool(BaseTool):
    """
    A tool for checking duplicate events on Google Calendar
    """
    name = "duplicate_event_checker_tool"
    description = "A tool for checking duplicate events on Google Calendar"

    event_name: str = Field(description='Name of the event to check for duplicates')
    event_datetime: str = Field(
        description='Date and time of the event. This must be converted into a Python datetime.datetime object before use.'
    )
    event_duration: int = Field(description='Duration of the event in minutes')

    def get_credentials(self):
        """
        Get and refresh Google Calendar API credentials
        """
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        return creds

    def check_duplicate_events(self, service, start_time, end_time):
        """
        Check for duplicate events in the given time range
        """
        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',  # 'Z' indicates UTC time
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            duplicate_events = [event for event in events if event['summary'].lower() == self.event_name.lower()]
            return duplicate_events
        except HttpError as error:
            print(f"An error occurred while checking for duplicate events: {error}")
            return []

    def check_for_duplicates(self):
        """
        Checks for duplicate events on Google Calendar
        """
        try:
            creds = self.get_credentials()
            if not creds:
                return "Failed to obtain valid credentials."
            
            service = build("calendar", "v3", credentials=creds)
            
            # Convert the string to a datetime object
            event_start_time = datetime.datetime.fromisoformat(self.event_datetime)
            event_end_time = event_start_time + datetime.timedelta(minutes=self.event_duration)

            duplicate_events = self.check_duplicate_events(service, event_start_time, event_end_time)

            if duplicate_events:
                return f"Found {len(duplicate_events)} duplicate event(s) with the name '{self.event_name}' in the specified time range."
            else:
                return f"No duplicate events found for '{self.event_name}' in the specified time range."

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self):
        return self.check_for_duplicates()

def main():
    # Tạo một instance của DuplicateEventCheckerTool
    duplicate_checker_tool = DuplicateEventCheckerTool(
        event_name="play football",
        event_datetime="2024-09-04T10:11:00",
        event_duration=60
    )

    # Chạy tool để kiểm tra sự kiện trùng lặp
    result = duplicate_checker_tool._run()
    print(result)

if __name__ == "__main__":
    main()