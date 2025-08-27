"""
Identity Management Module

Provides stable, email-based user identification that survives API key rotation
and works consistently across all FortunaMind services.
"""

from .email_identity import EmailIdentity

__all__ = ["EmailIdentity"]