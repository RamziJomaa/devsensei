from .base_agent import AgentNode
from .tool_registry import search_codebase, read_file

class RAGAgent(AgentNode):
    def __init__(self):
        # The RAG Agent is specialized in answering architectural queries via semantic search.
        super().__init__(
            name="rag_agent",
            tools=[search_codebase, read_file]
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are an expert Software Architect. You answer deep technical questions about a codebase. "
            "Always use the `search_codebase` tool to find mathematically relevant context before answering. "
            "If the search results are not enough, use `read_file` to fetch the complete source code. "
            "Never guess the architecture; always rely on the tool outputs."
        )
