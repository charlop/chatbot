"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    app_name: str = Field(default="Contract Refund Eligibility System")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    # API
    api_v1_prefix: str = Field(default="/api/v1")
    cors_origins: str | List[str] = Field(default="http://localhost:3000")

    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)
    database_pool_timeout: int = Field(default=30)
    database_pool_recycle: int = Field(default=3600)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_ttl_default: int = Field(default=3600)
    cache_ttl_contract: int = Field(default=900)
    cache_ttl_extraction: int = Field(default=3600)
    cache_ttl_document: int = Field(default=1800)
    cache_ttl_session: int = Field(default=14400)

    # LLM Providers
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")
    openai_max_tokens: int = Field(default=4000)
    openai_temperature: float = Field(default=0.1)

    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")
    anthropic_max_tokens: int = Field(default=4000)
    anthropic_temperature: float = Field(default=0.1)

    aws_bedrock_region: str | None = Field(default=None)
    aws_access_key_id: str | None = Field(default=None)
    aws_secret_access_key: str | None = Field(default=None)
    aws_bedrock_model_id: str | None = Field(default=None)

    llm_provider: str = Field(
        default="anthropic", description="LLM provider: openai, anthropic, bedrock"
    )
    llm_timeout: int = Field(default=30)
    llm_max_retries: int = Field(default=3)
    llm_circuit_breaker_threshold: int = Field(default=5)

    # External Services
    external_rdb_api_url: str = Field(default="http://localhost:8001/api/contracts")
    external_rdb_api_key: str = Field(default="mock-key")
    external_rdb_timeout: int = Field(
        default=5, description="External RDB request timeout in seconds"
    )
    external_rdb_retry_attempts: int = Field(
        default=3, description="Number of retry attempts for External RDB"
    )
    external_rdb_cache_ttl: int = Field(
        default=3600, description="External RDB mapping cache TTL in seconds (1 hour)"
    )
    external_rdb_mock_mode: bool = Field(
        default=True,
        description="Use mock mode for External RDB (simulates with local DB)",
    )
    enable_external_rdb: bool = Field(default=True, description="Enable External RDB integration")
    enable_hybrid_cache: bool = Field(
        default=True, description="Enable hybrid cache strategy (Redis + DB + External)"
    )

    document_repo_api_url: str = Field(default="http://localhost:8002/api/documents")
    document_repo_api_key: str = Field(default="mock-key")

    # S3 Storage
    s3_bucket_name: str = Field(
        default="contract-templates-dev", description="S3 bucket for contract template PDFs"
    )
    s3_region: str = Field(default="us-east-1", description="AWS region for S3")
    s3_endpoint_url: str | None = Field(
        default=None, description="S3 endpoint URL (for LocalStack/MinIO)"
    )
    s3_use_localstack: bool = Field(
        default=True, description="Use LocalStack for local S3 development"
    )

    # Testing
    test_database_url: str | None = Field(default=None)
    test_redis_url: str | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is one of the supported options."""
        valid_providers = {"openai", "anthropic", "bedrock"}
        if v.lower() not in valid_providers:
            raise ValueError(f"LLM provider must be one of {valid_providers}")
        return v.lower()

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate environment is one of the supported options."""
        valid_envs = {"development", "staging", "production"}
        if v.lower() not in valid_envs:
            raise ValueError(f"App environment must be one of {valid_envs}")
        return v.lower()

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    def get_database_url(self, for_test: bool = False) -> str:
        """Get the appropriate database URL."""
        if for_test and self.test_database_url:
            return self.test_database_url
        return self.database_url

    def get_redis_url(self, for_test: bool = False) -> str:
        """Get the appropriate Redis URL."""
        if for_test and self.test_redis_url:
            return self.test_redis_url
        return self.redis_url


# Global settings instance
settings = Settings()
