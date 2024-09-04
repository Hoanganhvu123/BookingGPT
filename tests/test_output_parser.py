from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Define the Pydantic model for event details
class EventDetails(BaseModel):
    event_name: str = Field(description="The name of the event or service being booked")
    customer_name: str = Field(description="The name of the customer making the booking")
    customer_phone: Optional[str] = Field(description="The customer's phone number for contact")
    start_time: datetime = Field(description="The starting time of the event")
    end_time: datetime = Field(description="The ending time of the event")
    booking_code: Optional[str] = Field(description="A unique code for this booking, if applicable")
    additional_requests: Optional[str] = Field(description="Any additional requests or preferences from the customer")

# Initialize the Pydantic output parser
parser = PydanticOutputParser(pydantic_object=EventDetails)

# Create a prompt template
prompt = PromptTemplate(
    template="""
            Based on the user input, chat history, and current time, extract the following event details:
            User Input: {input}
            
            {format_instructions}
            
            Ensure all fields are filled appropriately based on the available information.
            If any information is not provided or unclear, leave the field empty or null.
            For the start_time and end_time, use the current time as reference if needed.
            """,
    input_variables=["input"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Initialize the language model
model = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7, google_api_key=GOOGLE_API_KEY)

# Create the chain
chain = prompt | model | parser

# Run the chain
result = chain.invoke({
    "input": "I am hoàng anh. I want to book a haircut for tomorrow at 3 PM. i want to book for my girlfriend",
})

# Print the result
print(result)
