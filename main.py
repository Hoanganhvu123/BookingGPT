import os
from dotenv import load_dotenv
from bookinggpt.agent.booking_agent import BookingAgent
from langchain_core.language_models.base import BaseLanguageModel
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def main():
    # Initialize language model
    llm: BaseLanguageModel = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3
    )
    
    # Create BookingAgent instance
    booking_agent = BookingAgent(llm)

    while True:
        user_input = input("Bạn: ")
        if user_input.lower() == 'thoát':
            print("Trợ lý: Cảm ơn bạn đã sử dụng dịch vụ. Tạm biệt!")
            break
        response = booking_agent.call_agent(user_input)
        print(f"Trợ lý: {response}")

if __name__ == "__main__":
    main()
