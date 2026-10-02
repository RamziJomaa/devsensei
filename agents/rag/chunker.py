import ast
import re
import uuid
from typing import List
from .models import CodeChunk

class CodeChunker:
    def __init__(self, repo_id: str):
        self.repo_id = repo_id

    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        if file_path.endswith('.py'):
            return self._chunk_python(file_path, content)
        elif file_path.endswith('.java'):
            return self._chunk_java(file_path, content)
        else:
            return self._chunk_text(file_path, content)

    def _chunk_python(self, file_path: str, content: str) -> List[CodeChunk]:
        chunks = []
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                    
                    chunk_content = '\n'.join(lines[start_line-1:end_line])
                    chunk_type = 'class' if isinstance(node, ast.ClassDef) else 'function'
                    
                    chunks.append(CodeChunk(
                        id=str(uuid.uuid4()),
                        repo_id=self.repo_id,
                        file_path=file_path,
                        content=chunk_content,
                        chunk_type=chunk_type,
                        start_line=start_line,
                        end_line=end_line,
                        language='python'
                    ))
        except SyntaxError:
            # Fallback to text chunking if the python file has syntax errors
            return self._chunk_text(file_path, content, language='python')
        
        # If the file had no functions or classes, just chunk as text
        if not chunks:
            return self._chunk_text(file_path, content, language='python')
            
        return chunks

    def _chunk_java(self, file_path: str, content: str) -> List[CodeChunk]:
        chunks = []
        # A basic regex to identify Java method and class boundaries. 
        # For production with deep Java integration, a library like TreeSitter or javalang is preferred.
        pattern = re.compile(
            r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+(?:<[^>]+>)?\s+\w+\s*\([^)]*\)\s*\{', 
            re.MULTILINE
        )
        
        matches = list(pattern.finditer(content))
        if not matches:
            return self._chunk_text(file_path, content, language='java')
            
        lines = content.split('\n')
        
        for i, match in enumerate(matches):
            start_idx = match.start()
            start_line = content.count('\n', 0, start_idx) + 1
            
            # Simple assumption: the chunk lasts until the start of the next method/class
            if i + 1 < len(matches):
                end_idx = matches[i+1].start()
                end_line = content.count('\n', 0, end_idx)
            else:
                end_line = len(lines)
                
            chunk_content = '\n'.join(lines[start_line-1:end_line])
            
            chunks.append(CodeChunk(
                id=str(uuid.uuid4()),
                repo_id=self.repo_id,
                file_path=file_path,
                content=chunk_content,
                chunk_type='function',
                start_line=start_line,
                end_line=end_line,
                language='java'
            ))
            
        return chunks

    def _chunk_text(self, file_path: str, content: str, language: str = 'text', chunk_size: int = 500) -> List[CodeChunk]:
        chunks = []
        lines = content.split('\n')
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            chunks.append(CodeChunk(
                id=str(uuid.uuid4()),
                repo_id=self.repo_id,
                file_path=file_path,
                content=chunk_content,
                chunk_type='snippet' if len(lines) > chunk_size else 'file',
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                language=language
            ))
        return chunks
