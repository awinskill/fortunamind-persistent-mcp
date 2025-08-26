"""
Input Validators

Provides validation utilities for user inputs, configuration values,
and other data requiring security validation.
"""

import re
import logging
from typing import Any, List, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Validation strictness levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Optional[Any] = None
    confidence: float = 1.0
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class InputValidator:
    """Comprehensive input validation with security focus"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        
        # Compile common patterns for performance
        self.patterns = {
            "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            "alphanumeric": re.compile(r'^[a-zA-Z0-9]+$'),
            "safe_filename": re.compile(r'^[a-zA-Z0-9._-]+$'),
            "uuid": re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE),
            "symbol": re.compile(r'^[A-Z]{2,6}$'),  # Crypto/stock symbols
            "dangerous_chars": re.compile(r'[<>&"\'\0\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]'),
        }
    
    def validate_string(
        self,
        value: Any,
        min_length: int = 0,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        required: bool = True,
        allow_empty: bool = False
    ) -> ValidationResult:
        """Validate string input with security checks"""
        errors = []
        warnings = []
        
        # Type check
        if not isinstance(value, str):
            if value is None and not required:
                return ValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    sanitized_value=None
                )
            errors.append(f"Expected string, got {type(value).__name__}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Empty check
        if not value.strip():
            if not allow_empty:
                if required:
                    errors.append("Value cannot be empty")
                else:
                    return ValidationResult(
                        is_valid=True,
                        errors=[],
                        warnings=[],
                        sanitized_value=""
                    )
            else:
                return ValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    sanitized_value=value.strip()
                )
        
        # Length validation
        if len(value) < min_length:
            errors.append(f"Value too short (minimum {min_length} characters)")
        
        if max_length and len(value) > max_length:
            errors.append(f"Value too long (maximum {max_length} characters)")
        
        # Pattern validation
        if pattern:
            try:
                if not re.match(pattern, value):
                    errors.append(f"Value does not match required pattern")
            except re.error as e:
                errors.append(f"Invalid pattern: {e}")
        
        # Security checks
        if self.patterns["dangerous_chars"].search(value):
            if self.validation_level == ValidationLevel.STRICT:
                errors.append("Value contains potentially dangerous characters")
            else:
                warnings.append("Value contains special characters that may need escaping")
        
        # Check for excessive whitespace (potential for confusion)
        if "  " in value or value != value.strip():
            warnings.append("Value contains excessive whitespace")
        
        # Sanitize the value
        sanitized = value.strip()
        if warnings and "special characters" in warnings[0]:
            # Basic HTML entity encoding for dangerous characters
            sanitized = (sanitized
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;") 
                        .replace('"', "&quot;")
                        .replace("'", "&#x27;"))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized,
            confidence=0.9 if warnings else 1.0
        )
    
    def validate_email(self, email: Any) -> ValidationResult:
        """Validate email address"""
        result = self.validate_string(email, min_length=3, max_length=254)
        if not result.is_valid:
            return result
        
        if not self.patterns["email"].match(result.sanitized_value):
            result.errors.append("Invalid email format")
            result.is_valid = False
        
        return result
    
    def validate_symbol(self, symbol: Any) -> ValidationResult:
        """Validate cryptocurrency/stock symbol"""
        result = self.validate_string(symbol, min_length=2, max_length=6)
        if not result.is_valid:
            return result
        
        symbol_upper = result.sanitized_value.upper()
        if not self.patterns["symbol"].match(symbol_upper):
            result.errors.append("Symbol must be 2-6 uppercase letters")
            result.is_valid = False
        else:
            result.sanitized_value = symbol_upper
        
        return result
    
    def validate_amount(self, amount: Any, min_value: float = 0.0, max_value: Optional[float] = None) -> ValidationResult:
        """Validate monetary amount"""
        errors = []
        warnings = []
        
        # Type conversion
        try:
            if isinstance(amount, str):
                # Remove common formatting
                clean_amount = amount.replace(",", "").replace("$", "").strip()
                amount_float = float(clean_amount)
            else:
                amount_float = float(amount)
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Range validation
        if amount_float < min_value:
            errors.append(f"Amount cannot be less than {min_value}")
        
        if max_value is not None and amount_float > max_value:
            errors.append(f"Amount cannot be greater than {max_value}")
        
        # Precision check (crypto typically has high precision)
        if amount_float > 0 and amount_float < 0.000001:
            warnings.append("Very small amount - ensure precision is intended")
        
        # Round to reasonable precision for display
        sanitized = round(amount_float, 8)  # 8 decimal places for crypto
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized
        )
    
    def validate_json_data(self, data: Any, required_fields: Optional[List[str]] = None) -> ValidationResult:
        """Validate JSON-like data structure"""
        errors = []
        warnings = []
        
        if not isinstance(data, dict):
            errors.append("Data must be a dictionary/object")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for potentially dangerous keys
        dangerous_keys = ["__proto__", "constructor", "prototype"]
        found_dangerous = [key for key in data.keys() if key in dangerous_keys]
        if found_dangerous:
            if self.validation_level == ValidationLevel.STRICT:
                errors.append(f"Dangerous property names detected: {', '.join(found_dangerous)}")
            else:
                warnings.append(f"Potentially unsafe property names: {', '.join(found_dangerous)}")
        
        # Deep validation of string values
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                string_result = self.validate_string(value, max_length=10000)  # Reasonable limit
                if string_result.has_warnings:
                    warnings.extend([f"Field '{key}': {w}" for w in string_result.warnings])
                if string_result.has_errors:
                    errors.extend([f"Field '{key}': {e}" for e in string_result.errors])
                else:
                    sanitized_data[key] = string_result.sanitized_value
            else:
                sanitized_data[key] = value
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_data if len(errors) == 0 else None
        )
    
    def validate_list(
        self,
        data: Any,
        item_validator: Optional[callable] = None,
        min_items: int = 0,
        max_items: Optional[int] = None
    ) -> ValidationResult:
        """Validate list/array data"""
        errors = []
        warnings = []
        
        if not isinstance(data, list):
            errors.append("Data must be a list/array")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Size validation
        if len(data) < min_items:
            errors.append(f"List must contain at least {min_items} items")
        
        if max_items is not None and len(data) > max_items:
            errors.append(f"List cannot contain more than {max_items} items")
        
        # Validate individual items
        sanitized_items = []
        if item_validator and len(errors) == 0:
            for i, item in enumerate(data):
                try:
                    item_result = item_validator(item)
                    if hasattr(item_result, 'is_valid'):
                        # It's a ValidationResult
                        if item_result.has_errors:
                            errors.extend([f"Item {i}: {e}" for e in item_result.errors])
                        if item_result.has_warnings:
                            warnings.extend([f"Item {i}: {w}" for w in item_result.warnings])
                        if item_result.is_valid:
                            sanitized_items.append(item_result.sanitized_value)
                    else:
                        # Simple validator that returns True/False
                        if item_result:
                            sanitized_items.append(item)
                        else:
                            errors.append(f"Item {i}: validation failed")
                except Exception as e:
                    errors.append(f"Item {i}: validation error - {e}")
        else:
            sanitized_items = data
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_items if len(errors) == 0 else None
        )