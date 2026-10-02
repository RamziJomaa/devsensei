from pydantic import BaseModel

class CodeChunk(BaseModel):
    id: str
    repo_id: str
    file_path: str
    content: str
    chunk_type: str  # e.g., 'function', 'class', 'file', 'snippet'
    start_line: int
    end_line: int
    language: str
