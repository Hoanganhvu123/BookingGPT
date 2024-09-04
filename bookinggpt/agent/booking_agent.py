import os
from dotenv import load_dotenv
from langchain_core.language_models.base import BaseLanguageModel
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from bookinggpt.tool.create_event import CalendarTool
from bookinggpt.tool.available_event import AvailableSlotsTool
from bookinggpt.tool.cancel_event import CancelEventTool
from bookinggpt.agent.prompt import PROMPT_TEMPLATE


class BookingAgent:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.verbose = True
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.tools = [
            CalendarTool(),
            AvailableSlotsTool(),
            CancelEventTool()
        ]
        self.prompt = PROMPT_TEMPLATE

    def call_agent(self, query: str) -> str:
        inputs = {
            "input": query,
            "chat_history": self.memory.load_memory_variables({})["chat_history"],
        }
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            handle_parsing_errors=True,
        )
        ai_message = agent_executor.invoke(inputs)
        agent_output = ai_message['output']
        self.memory.save_context({"input": query}, {"output": agent_output})
        return agent_output
