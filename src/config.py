"""
Configuration management for FortunaMind Persistent MCP Server.

Handles all environment variables, settings, and configuration validation.
"""

import os
from enum import Enum
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityProfile(str, Enum):
    """Security scanner profiles"""
    STRICT = "STRICT"
    MODERATE = "MODERATE"
    LENIENT = "LENIENT"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log output formats"""
    JSON = "json"
    TEXT = "text"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings for validation and type conversion.
    """
    
    # ===== DATABASE CONFIGURATION =====
    database_url: str = Field(
        default="postgresql://mock:mock@mock:5432/mock",
        description="PostgreSQL database connection URL"
    )
    
    supabase_url: str = Field(
        default="https://mock.supabase.co",
        description="Supabase project URL"
    )
    
    supabase_anon_key: str = Field(
        default="mock-anon-key-replace-in-dashboard",
        description="Supabase anonymous key"
    )
    
    supabase_service_role_key: str = Field(
        default="mock-service-key-replace-in-dashboard",
        description="Supabase service role key"
    )
    
    # ===== SERVER CONFIGURATION =====
    mcp_server_name: str = Field(
        default="FortunaMind-Persistent-MCP",
        description="MCP server identification name"
    )
    
    server_host: str = Field(
        default="0.0.0.0",
        description="Server bind host"
    )
    
    server_mode: str = Field(
        default="stdio",
        description="Server mode - 'stdio' or 'http'"
    )
    
    server_port: int = Field(
        default_factory=lambda: int(os.environ.get("PORT", "8080")),
        ge=1,
        le=65535,
        description="Server bind port (reads from PORT env var for Render)"
    )
    
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Runtime environment"
    )
    
    # ===== SECURITY CONFIGURATION =====
    jwt_secret_key: str = Field(
        default="mock-jwt-secret-key-at-least-32-chars-long-for-production-use",
        min_length=32,
        description="JWT signing secret key"
    )
    
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiration in minutes"
    )
    
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        description="Refresh token expiration in days"
    )
    
    security_profile: SecurityProfile = Field(
        default=SecurityProfile.STRICT,
        description="Security scanner sensitivity profile"
    )
    
    api_rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="API requests per minute limit"
    )
    
    max_journal_entry_length: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Maximum journal entry length"
    )
    
    # ===== SUBSCRIPTION INTEGRATION =====
    subscription_api_url: str = Field(
        default="https://api.fortunamind.com/v1/subscriptions",
        description="FortunaMind subscription API URL"
    )
    
    subscription_api_key: Optional[str] = Field(
        default=None,
        description="Subscription API authentication key"
    )
    
    subscription_cache_ttl_minutes: int = Field(
        default=5,
        ge=1,
        description="Subscription status cache TTL"
    )
    
    subscription_grace_period_days: int = Field(
        default=7,
        ge=0,
        description="Grace period after subscription expires"
    )
    
    # ===== TECHNICAL INDICATORS =====
    technical_indicators_cache_ttl_minutes: int = Field(
        default=5,
        ge=1,
        description="Technical indicators cache TTL"
    )
    
    supported_symbols: List[str] = Field(
        default=["BTC", "ETH", "LTC", "BCH", "ADA", "SOL", "MATIC", "DOT", "AVAX", "UNI"],
        description="Supported cryptocurrency symbols"
    )
    
    default_rsi_period: int = Field(
        default=14,
        ge=2,
        le=100,
        description="Default RSI calculation period"
    )
    
    default_sma_periods: List[int] = Field(
        default=[20, 50, 200],
        description="Default SMA periods"
    )
    
    default_ema_periods: List[int] = Field(
        default=[12, 26],
        description="Default EMA periods"  
    )
    
    default_macd_fast: int = Field(
        default=12,
        ge=1,
        description="MACD fast period"
    )
    
    default_macd_slow: int = Field(
        default=26,
        ge=1,
        description="MACD slow period"
    )
    
    default_macd_signal: int = Field(
        default=9,
        ge=1,
        description="MACD signal period"
    )
    
    # ===== LOGGING CONFIGURATION =====
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="Log output format"
    )
    
    log_file_path: Optional[str] = Field(
        default="logs/persistent-mcp.log",
        description="Log file path (None for stdout only)"
    )
    
    log_max_size_mb: int = Field(
        default=100,
        ge=1,
        description="Maximum log file size in MB"
    )
    
    log_backup_count: int = Field(
        default=5,
        ge=0,
        description="Number of log backup files to keep"
    )
    
    # ===== MONITORING =====
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics"
    )
    
    metrics_port: int = Field(
        default=9090,
        ge=1,
        le=65535,
        description="Metrics server port"
    )
    
    health_check_path: str = Field(
        default="/health",
        description="Health check endpoint path"
    )
    
    # ===== DEVELOPMENT SETTINGS =====
    development_mode: bool = Field(
        default=False,
        description="Enable development mode features"
    )
    
    enable_debug_endpoints: bool = Field(
        default=False,
        description="Enable debug endpoints (development only)"
    )
    
    mock_subscription_check: bool = Field(
        default=False,
        description="Mock subscription verification (testing only)"
    )
    
    mock_technical_data: bool = Field(
        default=False,
        description="Use mock technical indicator data (testing only)"
    )
    
    # ===== FEATURE FLAGS =====
    enable_trading_journal: bool = Field(
        default=True,
        description="Enable trading journal features"
    )
    
    enable_technical_indicators: bool = Field(
        default=True,
        description="Enable technical indicators"
    )
    
    enable_portfolio_integration: bool = Field(
        default=True,
        description="Enable portfolio integration"
    )
    
    enable_pre_trade_analysis: bool = Field(
        default=True,
        description="Enable pre-trade analysis warnings"
    )
    
    # Beta features (disabled by default)
    enable_advanced_analytics: bool = Field(
        default=False,
        description="Enable advanced analytics (beta)"
    )
    
    enable_predictive_insights: bool = Field(
        default=False,
        description="Enable predictive insights (beta)"
    )
    
    # ===== PERFORMANCE CONFIGURATION =====
    db_pool_size: int = Field(
        default=10,
        ge=1,
        description="Database connection pool size"
    )
    
    db_max_overflow: int = Field(
        default=20,
        ge=0,
        description="Database connection pool overflow"
    )
    
    db_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Database connection timeout seconds"
    )
    
    http_timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="HTTP client timeout"
    )
    
    http_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="HTTP client retry attempts"
    )
    
    http_retry_backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        description="HTTP retry backoff multiplier"
    )
    
    cache_default_ttl_seconds: int = Field(
        default=300,
        ge=1,
        description="Default cache TTL in seconds"
    )
    
    # Optional Redis for advanced caching
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (optional)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == Environment.PRODUCTION

    def get_db_config(self) -> dict:
        """Get database configuration for SQLAlchemy"""
        return {
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
        }

    def get_security_config(self) -> dict:
        """Get security scanner configuration"""
        profiles = {
            SecurityProfile.STRICT: {
                "enable_api_detection": True,
                "enable_injection_detection": True,
                "enable_pii_detection": True,
                "sensitivity": "high",
                "auto_sanitize": True,
                "block_on_medium": True,
                "log_all_attempts": True
            },
            SecurityProfile.MODERATE: {
                "enable_api_detection": True,
                "enable_injection_detection": True,
                "enable_pii_detection": False,
                "sensitivity": "medium",
                "auto_sanitize": True,
                "block_on_high": True,
                "log_critical_only": True
            },
            SecurityProfile.LENIENT: {
                "enable_api_detection": True,
                "enable_injection_detection": False,
                "enable_pii_detection": False,
                "sensitivity": "low",
                "auto_sanitize": False,
                "block_on_critical": True,
                "log_critical_only": True
            }
        }
        return profiles[self.security_profile]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings