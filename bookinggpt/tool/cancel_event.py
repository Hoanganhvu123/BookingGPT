import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.tools import BaseTool

from bookinggpt.utils import SCOPES, CREDENTIALS_FILE, TOKEN_FILE

class CancelEventTool(BaseTool):
    name = "cancel_event_tool"
    description = """
    A Google Calendar tool for canceling existing events.
    
    Input: JSON object containing booking code and customer phone number.
    Example input: {
        "booking_code": "ABC123",
        "customer_phone": "1234567890"
    }
    
    Output: String confirming cancellation, error message, or request for missing information.
    
    Note: Both booking code and customer phone number are required. If either is missing, 
    the tool will request the customer to provide the missing information. 
    Do not proceed with cancellation unless both pieces of information are provided.
    """

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

    def cancel_event(self, booking_code: str, customer_phone: str):
        try:
            creds = self.get_credentials()
            if not creds:
                return "Unable to obtain valid credentials."

            service = build("calendar", "v3", credentials=creds)

            # Search for the event
            events_result = service.events().list(calendarId='primary', q=booking_code).execute()
            events = events_result.get('items', [])

            for event in events:
                description = event.get('description', '')
                if (f"Booking Code: {booking_code}" in description and
                    f"Phone: {customer_phone}" in description):
                    # Cancel the event
                    service.events().delete(calendarId='primary', eventId=event['id']).execute()
                    return f"Event with booking code {booking_code} has been successfully canceled."

            return f"No event found with booking code {booking_code} and phone number {customer_phone}. lets try again or check the booking code again"

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self, query: str) -> str:
        try:
            # Parse the input JSON string
            data = json.loads(query)
            booking_code = data.get('booking_code')
            customer_phone = data.get('customer_phone')

            # Check if both booking_code and customer_phone are provided
            if not booking_code or not customer_phone:
                return "Please provide both booking code and customer phone number."

            return self.cancel_event(booking_code, customer_phone)
        except json.JSONDecodeError:
            return "Invalid input format. Please provide a valid JSON object."
        except Exception as e:
            return f"An error occurred: {str(e)}"
