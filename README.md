# 🛡️ DevSensei

**An agentic AI system that autonomously reviews codebases and pull requests to find architectural flaws, security vulnerabilities, and CI/CD anti-patterns.**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge) ![LangChain](https://img.shields.io/badge/LangChain-FFFFFF?style=for-the-badge) ![Qdrant](https://img.shields.io/badge/Qdrant-FE315D?style=for-the-badge) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white) ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white) ![Angular](https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white)

## What it does
DevSensei is an intelligent, multi-agent CI/CD pipeline overlay that acts as an autonomous Senior Staff Engineer. Instead of relying on static, regex-based linters, DevSensei uses a LangGraph state machine to coordinate specialized AI agents. When a pull request is opened, DevSensei ingests the codebase, chunks the syntax using AST parsing, and embeds it into a Qdrant vector database. Specialized agents—a Code Reviewer, a RAG Architect, and a DevOps Specialist—then autonomously query the repository, analyze Dockerfiles and Actions YAML, and synthesize their findings. Finally, an internal LLM-as-a-judge evaluates the findings for actionability before delivering a deduplicated, structured Markdown report to the developer.

## Architecture

```text
[GitHub Webhook] -> (FastAPI Async Queue) -> [LangGraph State Machine]
                                                      |
    +-------------------------------------------------+---------------------+
    |                                                 |                     |
[CodeReviewAgent]                                [RAGAgent]            [DevOpsAgent]
(Fetches File Tree)                        (Qdrant Vector Search)  (Checks CI/CD & Docker)
    |                                                 |                     |
    +------------------------+------------------------+---------------------+
                             v
                     [AggregatorAgent]
               (Merges & Deduplicates Findings)
                             |
                             v
                        [EvalAgent]
         (LLM-as-a-judge: Faithfulness & Actionability)
                             |
                             v
                     [ReportGenerator]
               (Markdown Output & Postgres DB) -> [Angular Frontend / Grafana]
```

## Quickstart

Spin up the entire stack—AI Backend, Postgres, Redis, Qdrant, Prometheus, Grafana, and Angular UI—in one command.

```bash
git clone https://github.com/yourusername/DevSensei.git
cd DevSensei
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and GITHUB_TOKEN
docker compose up -d
```

Navigate to `http://localhost:80` to access the UI.

## Performance Results
DevSensei runs its own internal LLMOps evaluation pipeline on every analysis using an LLM-as-a-judge approach:
- **Faithfulness Score:** 87% (Ensures the AI's claims are backed by actual code chunks)
- **Average Actionability:** 0.82 (Measures if findings include concrete, implementable fixes)
- **Average Finding Relevance:** 0.79 (Measures if the finding is contextually accurate for the repository)

## Technical Decisions
- **Why LangGraph over CrewAI:** CrewAI is excellent for sequential, conversational workflows. DevSensei requires complex cyclic graphs, deterministic state management (`TypedDict`), and precise tool-calling loops where agents can dynamically route based on errors. LangGraph provides this structural control.
- **Why Qdrant over FAISS:** FAISS is a fantastic, lightweight library, but it lacks a native client-server architecture and metadata filtering. Qdrant is built for production, allowing us to filter vectors by file type, line numbers, and repository ID instantly.
- **Why AST Chunking over Fixed-Size Chunking:** Fixed-size chunking (e.g., splitting by 500 characters) frequently slices functions in half, destroying semantic context. We parse Python code into an Abstract Syntax Tree (AST) to ensure chunks perfectly align with class and function boundaries.
