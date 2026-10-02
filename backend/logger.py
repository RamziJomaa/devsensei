import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Formats log records into structured JSON suitable for Datadog, ELK, or CloudWatch."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        
        # Extract custom LLMOps fields passed via the 'extra' parameter
        if hasattr(record, "analysis_id"):
            log_obj["analysis_id"] = record.analysis_id
        if hasattr(record, "agent_name"):
            log_obj["agent_name"] = record.agent_name
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "token_count"):
            log_obj["token_count"] = record.token_count
            
        return json.dumps(log_obj)

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("devsensei")
    logger.setLevel(logging.INFO)
    
    # Ensure handlers aren't duplicated if this is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
