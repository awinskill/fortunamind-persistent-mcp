"""
Simplified Storage Utilities

Provides common utilities for storage implementations without the complex
template pattern that was identified as over-engineering.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StorageMetrics:
    """Simple storage metrics tracking"""
    operations: int = 0
    errors: int = 0
    avg_duration: float = 0.0
    
    def update(self, duration: float, success: bool = True):
        """Update metrics with new operation"""
        self.operations += 1
        if not success:
            self.errors += 1
        
        # Update rolling average
        if self.operations == 1:
            self.avg_duration = duration
        else:
            total_time = self.avg_duration * (self.operations - 1) + duration
            self.avg_duration = total_time / self.operations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "operations": self.operations,
            "errors": self.errors, 
            "success_rate": (self.operations - self.errors) / max(self.operations, 1),
            "avg_duration_ms": self.avg_duration * 1000,
        }


def generate_record_id() -> str:
    """Generate unique record ID"""
    return str(uuid.uuid4())


def validate_user_id_hash(user_id_hash: str) -> None:
    """Validate user ID hash format"""
    if not user_id_hash:
        raise ValueError("user_id_hash is required")
    
    if not isinstance(user_id_hash, str):
        raise ValueError("user_id_hash must be a string")
    
    if len(user_id_hash) < 8:
        raise ValueError("user_id_hash too short")


def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Basic data sanitization to prevent common issues"""
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        # Skip potentially dangerous keys
        if isinstance(key, str) and (key.startswith('__') or key in ['constructor', 'prototype']):
            logger.warning(f"Skipping potentially dangerous key: {key}")
            continue
        
        sanitized[key] = value
    
    return sanitized


def create_health_check_result(
    backend_name: str, 
    status: str = "unknown",
    details: Optional[str] = None,
    metrics: Optional[StorageMetrics] = None
) -> Dict[str, Any]:
    """Create standardized health check result"""
    result = {
        "backend": backend_name,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if details:
        result["details"] = details
    
    if metrics:
        result["metrics"] = metrics.to_dict()
    
    return result