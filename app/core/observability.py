"""Core utilities for logging and observability."""
import logging
import time
from typing import Any, Dict
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class ChainStep:
    """Observability tracker for chain steps."""
    
    def __init__(self, name: str, logger: logging.Logger = None):
        self.name = name
        self.logger = logger or get_logger(__name__)
        self.start_time = None
        self.end_time = None
        self.metadata: Dict[str, Any] = {}
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"[CHAIN_STEP] Starting: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if exc_type:
            self.logger.error(
                f"[CHAIN_STEP] Failed: {self.name} after {duration:.2f}s",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            self.logger.info(f"[CHAIN_STEP] Completed: {self.name} in {duration:.2f}s")
            if self.metadata:
                self.logger.info(f"[METADATA] {self.metadata}")
    
    def log_metadata(self, **kwargs):
        """Log metadata for observability."""
        self.metadata.update(kwargs)
        self.logger.info(f"[METADATA] {self.metadata}")


class QueryMetrics:
    """Query metrics and observability."""
    
    def __init__(self):
        self.start_time = time.time()
        self.steps: Dict[str, Any] = {}
        self.total_tokens = 0
        self.embedding_calls = 0
        self.retrieval_time = 0.0

    def log_metadata(self, **kwargs):
        self.steps.update(kwargs)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_latency_ms": (time.time() - self.start_time) * 1000,
            "total_tokens": self.total_tokens,
            "embedding_calls": self.embedding_calls,
            "retrieval_time_ms": self.retrieval_time * 1000,
            "steps": self.steps
        }
