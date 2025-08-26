"""
Security Patterns Database

Comprehensive database of security patterns for threat detection.
Organized by category with configurable threat levels and confidence scores.
"""

from typing import Dict, List, Any


class SecurityPatterns:
    """Security patterns database with categorized threat patterns"""
    
    def __init__(self):
        self._patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize the comprehensive patterns database"""
        return {
            "api_credentials": [
                {
                    "pattern": r'organizations/[a-f0-9\-]+/apiKeys/[a-f0-9\-]+',
                    "description": "Coinbase Advanced Trade API Key",
                    "level": "critical",
                    "confidence": 0.95,
                    "action": "Remove immediately - API key should be in environment variables"
                },
                {
                    "pattern": r'-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----',
                    "description": "PEM Private Key",
                    "level": "critical",
                    "confidence": 0.98,
                    "action": "Remove immediately - private keys must never be stored in text"
                },
                {
                    "pattern": r'sk_live_[0-9a-zA-Z]{24,}',
                    "description": "Stripe Live Secret Key",
                    "level": "critical",
                    "confidence": 0.9,
                    "action": "Remove immediately - use environment variables"
                },
                {
                    "pattern": r'sk_test_[0-9a-zA-Z]{24,}',
                    "description": "Stripe Test Secret Key", 
                    "level": "high",
                    "confidence": 0.85,
                    "action": "Remove - even test keys should not be hardcoded"
                },
                {
                    "pattern": r'AKIA[0-9A-Z]{16}',
                    "description": "AWS Access Key ID",
                    "level": "critical",
                    "confidence": 0.9,
                    "action": "Remove immediately - use AWS IAM roles or environment variables"
                },
                {
                    "pattern": r'ghp_[0-9a-zA-Z]{36}',
                    "description": "GitHub Personal Access Token",
                    "level": "high",
                    "confidence": 0.9,
                    "action": "Remove and regenerate token"
                },
                {
                    "pattern": r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
                    "description": "Potential API Key (UUID format)",
                    "level": "medium",
                    "confidence": 0.6,
                    "action": "Review - may be sensitive UUID-based API key"
                },
                {
                    "pattern": r'[A-Za-z0-9]{32,}',
                    "description": "Potential API Key (long alphanumeric)",
                    "level": "low",
                    "confidence": 0.3,
                    "action": "Review - may be API key or token"
                }
            ],
            
            "crypto_credentials": [
                {
                    "pattern": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
                    "description": "Bitcoin Address",
                    "level": "medium",
                    "confidence": 0.8,
                    "action": "Consider if sharing wallet address is intentional"
                },
                {
                    "pattern": r'\b0x[a-fA-F0-9]{40}\b',
                    "description": "Ethereum Address",
                    "level": "medium", 
                    "confidence": 0.8,
                    "action": "Consider if sharing wallet address is intentional"
                },
                {
                    "pattern": r'\b[A-Fa-f0-9]{64}\b',
                    "description": "Potential Private Key (64 hex chars)",
                    "level": "critical",
                    "confidence": 0.7,
                    "action": "Remove immediately if this is a private key"
                },
                {
                    "pattern": r'\b[A-Za-z0-9]{51,52}\b',
                    "description": "Potential Bitcoin Private Key (WIF format)",
                    "level": "critical",
                    "confidence": 0.6,
                    "action": "Remove immediately if this is a private key"
                }
            ],
            
            "prompt_injection": [
                {
                    "pattern": r'ignore\s+previous\s+instructions?',
                    "description": "Direct prompt injection attempt",
                    "level": "high",
                    "confidence": 0.9,
                    "action": "Block input - attempted prompt manipulation"
                },
                {
                    "pattern": r'system\s*:\s*you\s+are\s+now',
                    "description": "System role override attempt",
                    "level": "high",
                    "confidence": 0.85,
                    "action": "Block input - attempted system role manipulation"
                },
                {
                    "pattern": r'<\s*system\s*>',
                    "description": "System tag injection",
                    "level": "medium",
                    "confidence": 0.8,
                    "action": "Review - potential system tag injection"
                },
                {
                    "pattern": r'assistant\s*:\s*I\s+(will|must|should|am)',
                    "description": "Assistant response manipulation",
                    "level": "medium",
                    "confidence": 0.7,
                    "action": "Review - potential response manipulation"
                },
                {
                    "pattern": r'(forget|ignore|disregard|skip)\s+(everything|all|previous|prior)',
                    "description": "Context manipulation attempt",
                    "level": "medium",
                    "confidence": 0.75,
                    "action": "Review - potential context manipulation"
                },
                {
                    "pattern": r'pretend\s+(to\s+be|you\s+are)',
                    "description": "Role-playing injection attempt", 
                    "level": "medium",
                    "confidence": 0.6,
                    "action": "Review - potential role manipulation"
                }
            ],
            
            "pii": [
                {
                    "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                    "description": "US Social Security Number",
                    "level": "high",
                    "confidence": 0.8,
                    "action": "Remove - SSN is highly sensitive PII"
                },
                {
                    "pattern": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                    "description": "Credit Card Number",
                    "level": "critical",
                    "confidence": 0.7,
                    "action": "Remove immediately - credit card data"
                },
                {
                    "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    "description": "Email Address",
                    "level": "low",
                    "confidence": 0.9,
                    "action": "Consider if email sharing is intentional"
                },
                {
                    "pattern": r'\b\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b',
                    "description": "US Phone Number",
                    "level": "medium",
                    "confidence": 0.6,
                    "action": "Consider if phone number sharing is intentional"
                }
            ],
            
            "malicious_patterns": [
                {
                    "pattern": r'<script[^>]*>.*?</script>',
                    "description": "JavaScript injection attempt",
                    "level": "high",
                    "confidence": 0.95,
                    "action": "Block - potential XSS attack"
                },
                {
                    "pattern": r'javascript:\s*[^;]+',
                    "description": "JavaScript URL injection",
                    "level": "high", 
                    "confidence": 0.85,
                    "action": "Block - potential XSS vector"
                },
                {
                    "pattern": r'(union|select|drop|delete|insert|update)\s+.*(from|into|table)',
                    "description": "SQL injection attempt",
                    "level": "high",
                    "confidence": 0.7,
                    "action": "Block - potential SQL injection"
                },
                {
                    "pattern": r'<iframe[^>]*src\s*=',
                    "description": "Iframe injection",
                    "level": "medium",
                    "confidence": 0.8,
                    "action": "Review - potential iframe injection"
                }
            ],
            
            "suspicious_urls": [
                {
                    "pattern": r'https?://[^\s]+\.(tk|ml|ga|cf)\b',
                    "description": "Suspicious free domain",
                    "level": "medium",
                    "confidence": 0.6,
                    "action": "Review - commonly used by malicious sites"
                },
                {
                    "pattern": r'https?://[^\s]*[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',
                    "description": "Direct IP URL",
                    "level": "medium",
                    "confidence": 0.7,
                    "action": "Review - direct IP URLs can be suspicious"
                },
                {
                    "pattern": r'https?://bit\.ly/[A-Za-z0-9]+',
                    "description": "URL shortener link",
                    "level": "low",
                    "confidence": 0.8,
                    "action": "Review - shortened URLs can hide destination"
                }
            ]
        }
    
    def get_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all security patterns"""
        return self._patterns.copy()
    
    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get patterns for a specific category"""
        return self._patterns.get(category, [])
    
    def get_categories(self) -> List[str]:
        """Get all pattern categories"""
        return list(self._patterns.keys())
    
    def add_custom_pattern(self, category: str, pattern_info: Dict[str, Any]) -> None:
        """Add a custom security pattern"""
        required_fields = ["pattern", "description", "level", "confidence"]
        if not all(field in pattern_info for field in required_fields):
            raise ValueError(f"Pattern info must contain: {required_fields}")
        
        if category not in self._patterns:
            self._patterns[category] = []
        
        self._patterns[category].append(pattern_info)
    
    def remove_pattern(self, category: str, pattern: str) -> bool:
        """Remove a pattern from a category"""
        if category not in self._patterns:
            return False
        
        original_len = len(self._patterns[category])
        self._patterns[category] = [
            p for p in self._patterns[category] if p["pattern"] != pattern
        ]
        
        return len(self._patterns[category]) < original_len