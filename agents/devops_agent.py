from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, ToolMessage
from .base_agent import AgentNode
from agents.tool_registry import read_file, get_file_list
from .devops.devops_tools import analyze_github_actions_yaml, analyze_dockerfile, fetch_workflow_runs
from .state import GraphState

class DevOpsFinding(BaseModel):
    type: str = Field(description="The category of the finding (e.g., security, performance, reliability)")
    severity: str = Field(description="critical, high, medium, or low")
    file: str = Field(description="The file path where the issue was found")
    line: int = Field(description="The line number (0 if general to the file)")
    message: str = Field(description="Description of the issue")
    suggestion: str = Field(description="Actionable suggestion to fix the issue")

class DevOpsFindingsOutput(BaseModel):
    findings: List[DevOpsFinding]

class DevOpsAgent(AgentNode):
    def __init__(self):
        super().__init__(
            name="devops_agent",
            tools=[get_file_list, read_file, analyze_github_actions_yaml, analyze_dockerfile, fetch_workflow_runs]
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Senior DevOps Engineer. Your goal is to find infrastructure vulnerabilities, "
            "missing CI/CD quality gates, and Docker anti-patterns.\n"
            "Steps:\n"
            "1. Use get_file_list to find Dockerfiles and GitHub Actions (.github/workflows/*.yml).\n"
            "2. Use read_file to read their contents.\n"
            "3. Use analyze_github_actions_yaml and analyze_dockerfile on the contents.\n"
            "4. Use fetch_workflow_runs to check if pipelines are currently failing.\n"
            "5. Consolidate the tool outputs and your own observations into a final structured response.\n"
            "IMPORTANT: Do not guess. Only report findings derived from the actual code or tool outputs."
        )

    async def run(self, state: GraphState) -> GraphState:
        messages = state.get("messages", [])
        if not any(isinstance(m, SystemMessage) for m in messages):
             messages.insert(0, SystemMessage(content=self.system_prompt))
             
        # Basic ReAct Tool Calling Loop
        for _ in range(4):
            response = await self.llm.ainvoke(messages)
            messages.append(response)
            
            if not response.tool_calls:
                break
                
            for tool_call in response.tool_calls:
                tool_obj = next((t for t in self.tools if t.name == tool_call["name"]), None)
                if tool_obj:
                    try:
                        result = await tool_obj.ainvoke(tool_call["args"])
                    except Exception as e:
                        result = str(e)
                    messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

        # Force the final output into a strict structured JSON representation
        structured_llm = self.llm.with_structured_output(DevOpsFindingsOutput)
        structured_res = await structured_llm.ainvoke(
            messages + [SystemMessage(content="Return the final consolidated DevOps findings in the requested JSON schema.")]
        )
        
        # Merge structured LLM findings back into the GraphState
        current_findings = state.get("findings", [])
        if structured_res and structured_res.findings:
            for f in structured_res.findings:
                current_findings.append({
                    "title": f.type,
                    "severity": f.severity,
                    "file": f.file,
                    "line": f.line,
                    "description": f.message,
                    "suggestion": f.suggestion
                })
            
        new_state = {**state, "messages": messages, "findings": current_findings}
        return new_state
