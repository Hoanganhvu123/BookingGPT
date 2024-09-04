import os
import datetime
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import Field
from langchain.tools import BaseTool

from bookinggpt.utils import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


class AvailableSlotsTool(BaseTool):
    name = "available_slots_tool"
    description = """
    A tool for showing available slots on Google Calendar for the current week, excluding Sundays.
    
    Input: No input required. The tool will automatically use the current time and date.
    
    Output: A string listing available time slots for each day of the current week (excluding Sunday),
    starting from the current day until Saturday.
    
    Note: This tool checks for available slots between 9:00 AM and 6:00 PM on weekdays and Saturdays.
    """

    slot_duration: int = 60  # Set slot duration as a class attribute

    def get_credentials(self):
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

    def get_busy_slots(self, service, start_time, end_time):
        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            busy_slots = [(datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))),
                           datetime.datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))))
                          for event in events]
            return busy_slots
        except HttpError as error:
            print(f"An error occurred while fetching events: {error}")
            return []

    def get_available_slots(self, current_time):
        try:
            creds = self.get_credentials()
            if not creds:
                return "Failed to obtain valid credentials."
            
            service = build("calendar", "v3", credentials=creds)
            
            start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + datetime.timedelta(days=(6 - start_time.weekday()))
            
            busy_slots = self.get_busy_slots(service, start_time, end_time)
            
            available_slots = {}
            current_date = start_time.date()
            while current_date <= end_time.date():
                if current_date.weekday() != 6:  # Skip Sunday
                    day_start = datetime.datetime.combine(current_date, datetime.time(9, 0)).replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
                    day_end = datetime.datetime.combine(current_date, datetime.time(18, 0)).replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
                    
                    if current_date == current_time.date():
                        day_start = max(day_start, current_time)
                    
                    available_slots[current_date] = []
                    current_slot = day_start
                    while current_slot < day_end:
                        slot_end = current_slot + datetime.timedelta(minutes=self.slot_duration)
                        if all(slot_end <= busy_start or current_slot >= busy_end for busy_start, busy_end in busy_slots):
                            available_slots[current_date].append(current_slot)
                        current_slot += datetime.timedelta(minutes=self.slot_duration)
                
                current_date += datetime.timedelta(days=1)
            
            return available_slots

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self, *args, **kwargs) -> str:
        current_time = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        available_slots = self.get_available_slots(current_time)
        
        if isinstance(available_slots, dict):
            result = "Available slots for the current week:\n"
            for date, slots in available_slots.items():
                result += f"\n{date.strftime('%A, %B %d')}: "
                if slots:
                    result += ", ".join([slot.strftime('%I:%M %p') for slot in slots])
                else:
                    result += "No available slots"
                result += "\n"
            return result.strip()  # Remove trailing newline
        else:
            return available_slots
