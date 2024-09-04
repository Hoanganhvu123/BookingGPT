import os
import datetime
import uuid
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain.agents import create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Optional
from dotenv import load_dotenv
from langchain.agents import AgentExecutor

from bookinggpt.utils import SCOPES, CREDENTIALS_FILE, TOKEN_FILE
from bookinggpt.agent.prompt import PROMPT_TEMPLATE

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def generate_booking_code():
    return str(uuid.uuid4())[:8]


class EventInfo(BaseModel):
    event_name: str = Field(description="Name of the event or service")
    customer_name: str = Field(description="Customer's name")
    customer_phone: str = Field(description="Customer's phone number")
    start_time: str = Field(description="Start time of the event in 24-hour format (HH:MM)")
    end_time: str = Field(description="End time of the event in 24-hour format (HH:MM)")
    booking_code: Optional[str] = Field(description="Unique booking code")
    customer_service: str = Field(description="Service requested by the customer")


class CalendarTool(BaseTool):
    name = "calendar_tool"
    description = """
    A Google Calendar scheduling tool for creating new events, including hair salon appointments.
    
    Input: JSON object containing customer information and preferred appointment time.
    Example input: {
        "customer_name": "John Doe",
        "phone": "1234567890",
        "service": "Hair wash",
        "start_time": "14:00",
        "end_time": "15:00",
        "date": "tomorrow"
    }
    
    Output: JSON object with booking details.
    Example output: {
        "status": "success",
        "booking_code": "ABC123",
        "event_id": "event123456"
    }
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

    def check_duplicate_event(self, service, start_time, end_time):
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return len(events) > 0

    def create_event(self, event_info: EventInfo, current_time: datetime.datetime):
        try:
            creds = self.get_credentials()
            if not creds:
                return "Unable to obtain valid credentials."

            service = build("calendar", "v3", credentials=creds)

            start_time = current_time.replace(
                hour=int(event_info.start_time.split(":")[0]),
                minute=int(event_info.start_time.split(":")[1]),
                second=0,
                microsecond=0
            ) + datetime.timedelta(days=1)
            end_time = current_time.replace(
                hour=int(event_info.end_time.split(":")[0]),
                minute=int(event_info.end_time.split(":")[1]),
                second=0,
                microsecond=0
            ) + datetime.timedelta(days=1)

            # Check for duplicate events
            if self.check_duplicate_event(service, start_time, end_time):
                return "This time slot is already booked. Please choose another time."

            event = {
                'summary': f"{event_info.customer_name} - {event_info.customer_service}",
                'description': f"Service: {event_info.customer_service}\n"
                               f"Phone: {event_info.customer_phone}\n"
                               f"Booking Code: {event_info.booking_code}",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            return (f"Event created successfully. "
                    f"Booking code: {event_info.booking_code}, "
                    f"Event ID: {event.get('id')}")

        except HttpError as error:
            return f"An error occurred: {error}"

    def _run(self, query: str) -> str:
        parser = PydanticOutputParser(pydantic_object=EventInfo)
        prompt = PromptTemplate(
            template="Extract the following information from the user query. "
                     "If the query mentions 'tomorrow' or 'mai', use the next day's date. "
                     "Convert time to 24-hour format (HH:MM):\n"
                     "{format_instructions}\n"
                     "User query: {query}\n"
                     "Current time: {current_time}\n",
            input_variables=["query", "current_time"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            google_api_key=GOOGLE_API_KEY
        )
        chain = prompt | llm | parser

        current_time = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        event_info = chain.invoke({
            "query": query,
            "current_time": current_time.isoformat()
        })

        if not event_info.booking_code:
            event_info.booking_code = generate_booking_code()

        return self.create_event(event_info, current_time)
    

def main():
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=GOOGLE_API_KEY)
    calendar_tool = CalendarTool()
    tools = [calendar_tool]

    prompt = PROMPT_TEMPLATE
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    user_input = "My name is Hoang Anh, my phone number is 1234, I want to use the hair wash service, from 14:00 to 15:00 tomorrow."
    result = agent_executor.invoke({
        "input": user_input,
    })
    print(result["output"])

if __name__ == "__main__":
    main()