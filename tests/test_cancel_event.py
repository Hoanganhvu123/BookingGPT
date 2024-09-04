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


class CancelEventTool(BaseTool):
    """
    A tool for canceling events on Google Calendar
    """
    name = "cancel_event_tool"
    description = "A tool for canceling events on Google Calendar"

    booking_code: str = Field(description='Unique booking code for the event')
    customer_phone: str = Field(description='Phone number of the customer who booked the event')

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

    def find_event_by_booking_code(self, service):
        try:
            events_result = service.events().list(calendarId='primary', q=self.booking_code).execute()
            events = events_result.get('items', [])
            for event in events:
                if self.verify_booking(service, event['id'], self.booking_code, self.customer_phone):
                    return event['id']
            return None
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def verify_booking(self, service, event_id, booking_code, customer_phone):
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            description = event.get('description', '')
            return f"Booking Code: {booking_code}" in description and f"Phone: {customer_phone}" in description
        except HttpError:
            return False

    def cancel_event(self):
        """
        Cancels an event on Google Calendar
        """
        try:
            creds = self.get_credentials()
            if not creds:
                return "Failed to obtain valid credentials."
            
            service = build("calendar", "v3", credentials=creds)
            
            event_id = self.find_event_by_booking_code(service)
            if not event_id:
                return "No event found with the given booking code and customer phone."

            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            
            return f"Event '{event['summary']}' has been successfully canceled."

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self):
        return self.cancel_event()

def main():
    cancel_event_tool = CancelEventTool(
        booking_code="51a264e4",  # Giả sử đây là mã đặt chỗ được tạo khi tạo sự kiện
        customer_phone="0123456789"  # Số điện thoại khách hàng từ ví dụ trước
    )

    # Chạy tool để hủy sự kiện
    result = cancel_event_tool._run()
    print(result)

if __name__ == "__main__":
    main()