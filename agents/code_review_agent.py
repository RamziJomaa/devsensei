from .base_agent import AgentNode
from .tool_registry import get_file_list, read_file

class CodeReviewAgent(AgentNode):
    def __init__(self):
        # The Code Reviewer needs to explore the file tree and read specific files.
        super().__init__(
            name="code_reviewer",
            tools=[get_file_list, read_file]
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are an expert Senior Staff Software Engineer and Code Reviewer. "
            "Your job is to review the codebase for bugs, missing tests, anti-patterns, and security issues. "
            "Use the provided tools to fetch the file list and read the contents of critical files. "
            "Focus strictly on actionable feedback. If you find an issue, explicitly log it in your response."
        )
