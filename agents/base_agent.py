from abc import ABC, abstractmethod
from typing import List
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
import time
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import GraphState
from backend.database import AsyncSessionLocal
from backend.models import AgentLog

class AgentNode(ABC):
    def __init__(self, name: str, tools: List[BaseTool]):
        self.name = name
        self.tools = tools
        
        # We use a tool-calling capable model
        self.llm = ChatGroq(model_name="llama3-70b-8192", temperature=0)
        
        # Bind the tools to the LLM so it knows they exist
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Define the agent's persona and objective."""
        pass

    async def _log_execution(self, analysis_id: str, input_state: GraphState, output_state: GraphState, duration_ms: int):
        """Asynchronously log agent execution to the database."""
        try:
            async with AsyncSessionLocal() as db:
                log = AgentLog(
                    analysis_id=uuid.UUID(analysis_id) if analysis_id else None,
                    agent_name=self.name,
                    # We just log the string representation of the last few messages for brevity
                    input_summary=str(input_state.get("messages", [])[-1:]) if input_state.get("messages") else "",
                    output_summary=str(output_state.get("messages", [])[-1:]) if output_state.get("messages") else "",
                    tokens_used=0, # Token usage extraction depends on specific LLM provider's AIMessage structure
                    duration_ms=duration_ms
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            print(f"Failed to log agent execution: {e}")

    async def run(self, state: GraphState) -> GraphState:
        """The core execution method for the LangGraph node."""
        start_time = time.time()
        
        # Ensure system prompt is the first message
        messages = state.get("messages", [])
        if not messages:
             messages = [SystemMessage(content=self.system_prompt)]
        elif not any(isinstance(m, SystemMessage) for m in messages):
             messages.insert(0, SystemMessage(content=self.system_prompt))

        # Invoke the LLM
        response = await self.llm.ainvoke(messages)
        
        # Update State
        new_messages = messages + [response]
        new_state = {**state, "messages": new_messages}
        
        # Log to DB
        duration_ms = int((time.time() - start_time) * 1000)
        await self._log_execution(state.get("analysis_id", ""), state, new_state, duration_ms)
        
        return new_state
