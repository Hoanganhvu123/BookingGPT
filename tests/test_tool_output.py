import json
from json import JSONDecodeError
from typing import List, Union, Dict
from pydantic import BaseModel

from langchain_core.agents import AgentAction, AgentActionMessageLog, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, BaseMessage, ToolCall
from langchain_core.memory import BaseMemory
from langchain_core.language_models import BaseLanguageModel
from langchain_core.outputs import Generation, ChatGeneration
from langchain.agents.agent import MultiActionAgentOutputParser

class Query(BaseModel):
    ai_message: AIMessage
    chat_history: List[BaseMessage]

class ToolAgentAction(AgentActionMessageLog):
    tool_call_id: str
    """Tool call that this message is responding to."""

def parse_ai_message_and_memory_to_tool_action(
    query: Query,
    llm: BaseLanguageModel
) -> Union[List[AgentAction], AgentFinish]:
    """Parse an AI message and memory, potentially containing tool_calls."""
    message = query.ai_message
    chat_history = query.chat_history

    if not isinstance(message, AIMessage):
        raise TypeError(f"Expected an AI message got {type(message)}")

    actions: List = []
    
    if message.tool_calls:
        tool_calls = message.tool_calls
    else:
        if not message.additional_kwargs.get("tool_calls"):
            return AgentFinish(
                return_values={
                    "output": message.content,
                    "chat_history": chat_history
                }, 
                log=str(message.content)
            )
        
        # Best-effort parsing
        tool_calls = []
        for tool_call in message.additional_kwargs["tool_calls"]:
            function = tool_call["function"]
            function_name = function["name"]
            try:
                args = json.loads(function["arguments"] or "{}")
                tool_calls.append(
                    ToolCall(name=function_name, args=args, id=tool_call["id"])
                )
            except JSONDecodeError:
                raise OutputParserException(
                    f"Could not parse tool input: {function} because "
                    f"the `arguments` is not valid JSON."
                )

    for tool_call in tool_calls:
        function_name = tool_call["name"]
        tool_input = tool_call["args"]

        # Use LLM to process the tool input
        processed_input = llm.predict(f"Process this tool input: {tool_input}")
        
        # Add chat history to processed input
        query = Query(ai_message=AIMessage(content=processed_input), chat_history=chat_history)

        content_msg = f"responded: {message.content}\n" if message.content else "\n"
        log = f"\nInvoking: `{function_name}` with `{query}`\n{content_msg}\n"
        actions.append(
            ToolAgentAction(
                tool=function_name,
                tool_input=query,
                log=log,
                message_log=[message],
                tool_call_id=tool_call["id"],
            )
        )

    return actions if actions else AgentFinish(
        return_values={"output": message.content, "chat_history": chat_history},
        log=str(message.content)
    )

class ToolsAgentOutputParser(MultiActionAgentOutputParser):
    """Parses a message into agent actions/finish."""

    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm

    @property
    def _type(self) -> str:
        return "tools-agent-output-parser"

    def parse_result(
        self, result: List[Generation], *, partial: bool = False
    ) -> Union[List[AgentAction], AgentFinish]:
        if not isinstance(result[0], ChatGeneration):
            raise ValueError("This output parser only works on ChatGeneration output")
        message = result[0].message
        query = Query(ai_message=message, chat_history=[])  # Assuming empty chat history for now
        return parse_ai_message_and_memory_to_tool_action(query, self.llm)

    def parse(self, text: str) -> Union[List[AgentAction], AgentFinish]:
        raise ValueError("Can only parse messages")

def main():
    # Example usage
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    parser = ToolsAgentOutputParser(llm)
    
    # Simulating an AI message with tool calls
    ai_message = AIMessage(
        content="Let's schedule an appointment",
        additional_kwargs={
            "tool_calls": [
                {
                    "function": {
                        "name": "calendar_tool",
                        "arguments": '{"event_name": "Haircut", "customer_name": "John Doe", "start_time": "2024-03-15T14:00:00"}'
                    },
                    "id": "call_123"
                }
            ]
        }
    )
    
    query = Query(ai_message=ai_message, chat_history=[])
    result = parse_ai_message_and_memory_to_tool_action(query, llm)
    
    if isinstance(result, list):
        for action in result:
            print(f"Tool: {action.tool}")
            print(f"Input: {action.tool_input}")
            print(f"Log: {action.log}")
    else:
        print(f"Finish: {result.return_values}")

if __name__ == "__main__":
    main()