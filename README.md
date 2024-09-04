# Daisy Hair Salon Booking System 🌼💇‍♀️

Welcome to the Daisy Hair Salon booking system! This is a smart application using AI to help customers easily book and manage appointments at our salon.

## 🌟 Key Features

- 🤖 Intelligent AI assistant to interact with customers
- 📅 Integration with Google Calendar for appointment management
- ⏰ Check and display available time slots
- 📝 Create, view, and cancel appointments easily
- 🗣️ Support for English communication
- 😊 Friendly and natural communication with customers

## 🛠️ Technologies Used

- Python 3.11
- LangChain for creating AI agent
- Google Generative AI (Gemini 1.5 Flash model)
- Google Calendar API for appointment management
- Poetry for dependency management
- Docker for containerization (if deployment is needed)

## 🏗️ Project Structure

```
bookinggpt/
├── agent/
│   ├── __init__.py
│   ├── booking_agent.py (Implements the main BookingAgent class for handling customer interactions)
│   └── prompt.py (Contains the prompt template for the AI assistant)
├── tool/
│   ├── __init__.py
│   ├── available_event.py (Tool for checking available time slots)
│   ├── cancel_event.py (Tool for canceling appointments)
│   └── create_event.py (Tool for creating new appointments)
├── __init__.py
└── utils.py (Contains utility functions used across the project)
tests/
├── __init__.py
├── test_available_event.py (Unit tests for available_event.py)
├── test_cancel_event.py (Unit tests for cancel_event.py)
├── test_create_event.py (Unit tests for create_event.py)
├── test_output_parser.py (Tests for parsing AI output)
└── test_tool_output.py (Tests for tool output formatting)
main.py (Entry point of the application, initializes and runs the BookingAgent)
README.md (Project documentation and usage instructions)
.env (Contains environment variables like API keys)
.gitignore (Specifies files to be ignored by Git)
Dockerfile (Instructions for building a Docker container for the application)
pyproject.toml (Poetry configuration file for dependency management)
requirements.txt (List of Python package dependencies)
```

## 🚀 Installation and Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/daisy-hair-salon-booking.git
   cd daisy-hair-salon-booking
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in the `.env` file:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. Run the application:
   ```bash
   python main.py
   ```

5. Interact with the AI assistant to book appointments, check available time slots, or cancel appointments.

## 📝 Usage Instructions

- To book an appointment: "I want to book a haircut tomorrow at 2 PM"
- To check available time slots: "Show me the available slots for this week"
- To cancel an appointment: "I want to cancel the appointment with booking code ABC123"

## 💈 Our Services

1. Hair wash (20 minutes)
2. Haircut (30 minutes)
3. Hair styling (30 minutes)
4. Beard trim (15 minutes)
5. Hair coloring (60 minutes)
6. Hair treatment (45 minutes)
7. Scalp massage (15 minutes)
8. Eyebrow shaping (10 minutes)
9. Facial care (45 minutes)
10. Manicure (30 minutes)

## 🤝 Contributions

We welcome all contributions to improve this project. Please create a pull request or report issues if you have any ideas or encounter any problems.

## 📄 License

This project is distributed under the MIT License. See the `LICENSE` file for more details.

## 📞 Contact

If you have any questions or suggestions, please contact us via email: hoanganvu933@gmail.com

---

Thank you for your interest in the Daisy Hair Salon Booking System! We hope this application will provide you with a wonderful booking experience. 💖✨