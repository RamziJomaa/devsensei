import os
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama

class CitedChunk(BaseModel):
    file_path: str = Field(description="The path of the file cited")
    start_line: int = Field(description="The starting line number of the citation")
    end_line: int = Field(description="The ending line number of the citation")

class RAGResponse(BaseModel):
    answer: str = Field(description="The detailed answer to the user's question based on the code")
    cited_chunks: List[CitedChunk] = Field(description="A list of explicit codebase chunks cited in the answer")
    confidence: float = Field(description="A score between 0.0 and 1.0 indicating confidence in the answer based on provided context")

class RAGChain:
    def __init__(self):
        provider = os.getenv("LLM_PROVIDER", "groq").lower()
        
        if provider == "ollama":
            self.llm = ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3"), format="json")
        else:
            self.llm = ChatGroq(model_name="llama3-70b-8192", temperature=0)

        self.parser = JsonOutputParser(pydantic_object=RAGResponse)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert technical architect. Answer the user's question purely based on the provided codebase context. Do not invent answers. If the answer is not in the context, explicitly state that you do not have enough information. Provide your output strictly in JSON format.\n\nInstructions:\n{format_instructions}"),
            ("user", "Question: {question}\n\nCode Context:\n{context}")
        ])

        self.chain = self.prompt | self.llm | self.parser

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Formats the retrieved dictionary payloads into a readable prompt string."""
        formatted = []
        for i, chunk in enumerate(chunks):
            file_path = chunk.get("file_path", "unknown")
            start = chunk.get("start_line", 0)
            end = chunk.get("end_line", 0)
            content = chunk.get("content", "")
            formatted.append(f"--- Document [{i+1}] File: {file_path} Lines: {start}-{end} ---\n{content}\n")
        return "\n".join(formatted)

    async def answer(self, question: str, chunks: List[Dict[str, Any]]) -> RAGResponse:
        context_str = self._format_context(chunks)
        
        response_dict = await self.chain.ainvoke({
            "question": question,
            "context": context_str,
            "format_instructions": self.parser.get_format_instructions()
        })
        
        return RAGResponse(**response_dict)
