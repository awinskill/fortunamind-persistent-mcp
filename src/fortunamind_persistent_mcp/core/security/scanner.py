"""
Security Scanner

Advanced security scanning for detecting sensitive information,
prompt injection attempts, and other security threats.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Pattern
from enum import Enum
from dataclasses import dataclass

from .patterns import SecurityPatterns

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Security threat severity levels"""
    CRITICAL = "critical"  # Immediate security risk
    HIGH = "high"         # Serious security concern
    MEDIUM = "medium"     # Moderate security issue
    LOW = "low"          # Minor security note
    INFO = "info"        # Informational only


@dataclass
class SecurityThreat:
    """Detected security threat"""
    threat_type: str
    level: ThreatLevel
    description: str
    pattern: str
    matches: int
    confidence: float
    location: Optional[str] = None
    suggested_action: Optional[str] = None


class SecurityScanner:
    """
    Advanced security scanner for detecting various threats
    
    Features:
    - API key and credential detection
    - Prompt injection attempt detection  
    - PII (Personally Identifiable Information) detection
    - Malicious pattern detection
    - Configurable sensitivity levels
    """
    
    def __init__(self, sensitivity_level: str = "HIGH"):
        """
        Initialize security scanner
        
        Args:
            sensitivity_level: STRICT, HIGH, MEDIUM, LOW
        """
        self.sensitivity_level = sensitivity_level
        self.patterns = SecurityPatterns()
        self.compiled_patterns = self._compile_patterns()
        
        logger.info(f"Security scanner initialized with {sensitivity_level} sensitivity")
    
    def _compile_patterns(self) -> Dict[str, List[tuple]]:
        """Compile regex patterns for better performance"""
        compiled = {}
        
        for category, patterns in self.patterns.get_patterns().items():
            compiled[category] = []
            for pattern_info in patterns:
                try:
                    compiled_pattern = re.compile(
                        pattern_info["pattern"], 
                        re.IGNORECASE | re.DOTALL
                    )
                    compiled[category].append((
                        compiled_pattern,
                        pattern_info["description"],
                        ThreatLevel(pattern_info["level"]),
                        pattern_info.get("confidence", 0.8),
                        pattern_info.get("action", "Review and remove if sensitive")
                    ))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern: {pattern_info['pattern']} - {e}")
                    
        return compiled
    
    def scan_content(self, content: str, context: Optional[str] = None) -> List[SecurityThreat]:
        """
        Scan content for security threats
        
        Args:
            content: Text content to scan
            context: Optional context (e.g., 'journal_entry', 'user_input')
            
        Returns:
            List of detected security threats
        """
        if not content or not isinstance(content, str):
            return []
            
        threats = []
        content_lower = content.lower()
        
        # Scan with compiled patterns
        for category, pattern_list in self.compiled_patterns.items():
            for compiled_pattern, description, level, confidence, action in pattern_list:
                # Skip low-priority patterns if sensitivity is high
                if self.sensitivity_level == "STRICT" and level in [ThreatLevel.LOW, ThreatLevel.INFO]:
                    continue
                if self.sensitivity_level == "HIGH" and level == ThreatLevel.INFO:
                    continue
                    
                matches = compiled_pattern.findall(content)
                if matches:
                    # Calculate confidence based on match context
                    adjusted_confidence = self._calculate_confidence(
                        matches, content_lower, category, confidence
                    )
                    
                    threat = SecurityThreat(
                        threat_type=category,
                        level=level,
                        description=description,
                        pattern=compiled_pattern.pattern,
                        matches=len(matches),
                        confidence=adjusted_confidence,
                        location=context,
                        suggested_action=action
                    )
                    threats.append(threat)
                    
                    logger.debug(f"Security threat detected: {category} - {len(matches)} matches")
        
        # Sort by threat level and confidence
        threats.sort(key=lambda t: (t.level.value, -t.confidence))
        
        return threats
    
    def _calculate_confidence(self, matches: List[str], content: str, category: str, base_confidence: float) -> float:
        """Calculate confidence score based on context"""
        confidence = base_confidence
        
        # Adjust confidence based on context clues
        if category == "api_credentials":
            # Higher confidence if found in structured formats
            if any(":" in match or "=" in match for match in matches):
                confidence = min(0.95, confidence + 0.1)
                
        elif category == "prompt_injection":
            # Higher confidence for explicit injection attempts
            injection_keywords = ["ignore", "system", "assistant", "prompt", "instructions"]
            if any(keyword in content for keyword in injection_keywords):
                confidence = min(0.9, confidence + 0.15)
                
        elif category == "pii":
            # Lower confidence for common patterns that might be false positives
            if len(matches) > 5:  # Too many matches likely false positive
                confidence = max(0.3, confidence - 0.2)
        
        return round(confidence, 2)
    
    def is_content_safe(self, content: str, context: Optional[str] = None) -> tuple[bool, List[SecurityThreat]]:
        """
        Quick safety check for content
        
        Returns:
            (is_safe, list_of_threats)
        """
        threats = self.scan_content(content, context)
        
        # Content is unsafe if there are CRITICAL or HIGH level threats
        critical_threats = [
            t for t in threats 
            if t.level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH] and t.confidence > 0.7
        ]
        
        is_safe = len(critical_threats) == 0
        return is_safe, threats
    
    def sanitize_content(self, content: str) -> tuple[str, List[SecurityThreat]]:
        """
        Sanitize content by removing or masking threats
        
        Returns:
            (sanitized_content, detected_threats)
        """
        threats = self.scan_content(content)
        sanitized = content
        
        for threat in threats:
            if threat.level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                # Replace sensitive content with placeholders
                pattern = re.compile(threat.pattern, re.IGNORECASE | re.DOTALL)
                
                if "api" in threat.threat_type.lower() or "key" in threat.threat_type.lower():
                    sanitized = pattern.sub("[REDACTED_API_KEY]", sanitized)
                elif "injection" in threat.threat_type.lower():
                    sanitized = pattern.sub("[REMOVED_INJECTION_ATTEMPT]", sanitized)
                elif "pii" in threat.threat_type.lower():
                    sanitized = pattern.sub("[REDACTED_PII]", sanitized)
                else:
                    sanitized = pattern.sub("[REDACTED_SENSITIVE_DATA]", sanitized)
        
        return sanitized, threats
    
    def generate_security_report(self, content: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive security report
        
        Returns:
            Detailed security analysis report
        """
        threats = self.scan_content(content, context)
        
        # Categorize threats by level
        threat_summary = {}
        for level in ThreatLevel:
            threat_summary[level.value] = len([t for t in threats if t.level == level])
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(threats)
        
        return {
            "scan_timestamp": logging.time.strftime("%Y-%m-%d %H:%M:%S"),
            "content_length": len(content),
            "threats_detected": len(threats),
            "threat_summary": threat_summary,
            "risk_score": risk_score,
            "is_safe": risk_score < 0.3,
            "threats": [
                {
                    "type": t.threat_type,
                    "level": t.level.value,
                    "description": t.description,
                    "matches": t.matches,
                    "confidence": t.confidence,
                    "action": t.suggested_action
                }
                for t in threats
            ],
            "recommendations": self._generate_recommendations(threats)
        }
    
    def _calculate_risk_score(self, threats: List[SecurityThreat]) -> float:
        """Calculate overall risk score (0.0 to 1.0)"""
        if not threats:
            return 0.0
            
        total_risk = 0.0
        for threat in threats:
            level_weight = {
                ThreatLevel.CRITICAL: 1.0,
                ThreatLevel.HIGH: 0.7,
                ThreatLevel.MEDIUM: 0.4,
                ThreatLevel.LOW: 0.2,
                ThreatLevel.INFO: 0.1
            }
            
            threat_risk = level_weight[threat.level] * threat.confidence
            total_risk += threat_risk
        
        # Normalize to 0-1 range
        return min(1.0, total_risk / len(threats))
    
    def _generate_recommendations(self, threats: List[SecurityThreat]) -> List[str]:
        """Generate security recommendations based on detected threats"""
        recommendations = []
        
        if any(t.level == ThreatLevel.CRITICAL for t in threats):
            recommendations.append("🚨 CRITICAL: Remove all sensitive credentials immediately")
        
        if any("api" in t.threat_type.lower() for t in threats):
            recommendations.append("🔑 Use environment variables for API credentials, never hardcode them")
        
        if any("injection" in t.threat_type.lower() for t in threats):
            recommendations.append("🛡️ Implement input validation and sanitization")
        
        if any("pii" in t.threat_type.lower() for t in threats):
            recommendations.append("👤 Consider data privacy regulations and user consent")
        
        if len(threats) > 5:
            recommendations.append("📊 High number of security issues detected - comprehensive review recommended")
        
        return recommendations