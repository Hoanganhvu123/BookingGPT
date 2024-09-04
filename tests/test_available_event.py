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


class AvailableSlotsTool(BaseTool):
    """
    A tool for showing available slots on Google Calendar
    """
    name = "available_slots_tool"
    description = "A tool for showing available slots on Google Calendar for the next 7 days"

    slot_duration: int = 60  # Set slot duration as a class attribute
    request_time: datetime.datetime = Field(description='Time when the user requests available slots')

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

    def get_busy_slots(self, service, start_time, end_time):
        """
        Get busy time slots from Google Calendar
        """
        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            busy_slots = [(datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).replace(tzinfo=None),
                           datetime.datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))).replace(tzinfo=None))
                          for event in events]
            return busy_slots
        except HttpError as error:
            print(f"An error occurred while fetching events: {error}")
            return []

    def get_available_slots(self):
        """
        Get available slots for the next 7 days
        """
        try:
            creds = self.get_credentials()
            if not creds:
                return "Failed to obtain valid credentials."
            
            service = build("calendar", "v3", credentials=creds)
            
            start_time = self.request_time
            end_time = start_time + datetime.timedelta(days=7)
            
            busy_slots = self.get_busy_slots(service, start_time, end_time)
            
            available_slots = []
            current_time = start_time
            while current_time < end_time:
                if 9 <= current_time.hour < 18:
                    slot_end = current_time + datetime.timedelta(minutes=self.slot_duration)
                    if all(slot_end <= busy_start or current_time >= busy_end for busy_start, busy_end in busy_slots):
                        available_slots.append(current_time)
                
                current_time += datetime.timedelta(minutes=self.slot_duration)
                
                # Nếu đã qua 18:00, chuyển sang 9:00 ngày hôm sau
                if current_time.hour >= 18:
                    current_time = current_time.replace(hour=9, minute=0) + datetime.timedelta(days=1)
            
            return available_slots

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self):
        available_slots = self.get_available_slots()
        if isinstance(available_slots, list):
            result = "Available slots for the next 7 days:\n"
            current_date = None
            for slot in available_slots:
                if current_date != slot.date():
                    if current_date:
                        result += "\n"
                    current_date = slot.date()
                    result += f"{slot.strftime('%Y-%m-%d (%A)')}\n"
                result += f"  {slot.strftime('%H:%M')}\n"
            return result
        else:
            return available_slots

def main():
    # Lấy thời gian hiện tại khi người dùng yêu cầu
    current_time = datetime.datetime.now()

    # Tạo một instance của AvailableSlotsTool với thời gian yêu cầu
    available_slots_tool = AvailableSlotsTool(request_time=current_time)

    # Chạy tool để lấy các slot trống
    result = available_slots_tool._run()
    print(result)

if __name__ == "__main__":
    main()