# DevSensei Architecture & LangGraph State Machine

## GraphState (Shared Memory)
The entire multi-agent system revolves around a shared memory object, strictly typed using Python's `TypedDict`. This ensures type safety as data flows asynchronously between nodes and agents.

```python
class GraphState(TypedDict):
    analysis_id: str            # UUID for database relational tracking
    repo_url: str               # Target repository URL
    repo_id: str                # owner/repo format for API calls
    file_tree: List[str]        # Cached repository structure to prevent redundant API calls
    messages: List[BaseMessage] # Conversation and tool execution history
    findings: List[Dict]        # Unstructured agent discoveries and vulnerabilities
    report_draft: str           # Aggregated Markdown text
    eval_scores: Dict           # Output from the LLM-as-a-judge evaluation
    status: str                 # running, failed, done
    error: Optional[str]        # System-level error capture
```

## Nodes (The Agents)
1. **CodeReviewAgent:** A general-purpose reviewer. It uses the `get_file_list` tool to explore the repo and the `read_file` tool to inspect specific implementations for bugs and anti-patterns.
2. **RAGAgent:** An architectural specialist. It embeds natural language queries to search the Qdrant database using the `search_codebase` tool, retrieving mathematically relevant function boundaries.
3. **DevOpsAgent:** A CI/CD and Docker specialist. It executes `analyze_dockerfile` and `analyze_github_actions_yaml` to find missing quality gates, hardcoded secrets, and root-user vulnerabilities.
4. **AggregatorAgent:** A deterministic node (no LLM) that loops over the `findings` array and groups them by severity.
5. **EvalAgent:** An LLM-as-a-judge. It takes the output of the Aggregator, applies a strict scoring rubric, and generates `relevance`, `actionability`, and `faithfulness` scores.
6. **ReportGenerator:** Deduplicates findings by file/line and generates the final user-facing Markdown document, persisting it to PostgreSQL.

## Tool Registry
Tools are deterministic Python functions annotated with `@tool`. Their docstrings are injected directly into the LLM system prompt.
- `@tool read_file`: Fetches raw file content via the GitHub API.
- `@tool search_codebase`: Performs semantic similarity search against the Qdrant vector database.
- `@tool get_file_list`: Retrieves the flat file hierarchy of the repository.
- `@tool analyze_dockerfile`: Applies heuristic parsing to flag security anti-patterns in Docker containers.
- `@tool analyze_github_actions_yaml`: Checks for unpinned action versions and missing testing steps.
- `@tool fetch_workflow_runs`: Checks the GitHub API to see if the CI/CD pipeline is currently failing.
