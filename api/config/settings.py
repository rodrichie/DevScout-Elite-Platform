"""
Centralized Settings Management with Validation
Replaces scattered os.getenv() calls with type-safe configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator, PostgresDsn
from typing import Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with validation.
    Uses Pydantic for type checking and validation.
    """
    
    # ============ Environment ============
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # ============ Database ============
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(..., env="POSTGRES_DB")
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # ============ MinIO/S3 ============
    aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    minio_endpoint: str = Field(default="http://minio:9000", env="MINIO_ENDPOINT")
    
    # ============ Security ============
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # ============ CORS ============
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # ============ Kafka ============
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_topic: str = Field(default="coding-events", env="KAFKA_TOPIC")
    
    # ============ Weaviate ============
    weaviate_url: str = Field(
        default="http://weaviate:8080",
        env="WEAVIATE_URL"
    )
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # ============ GitHub ============
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # ============ Airflow ============
    airflow_fernet_key: Optional[str] = Field(default=None, env="AIRFLOW__CORE__FERNET_KEY")
    airflow_webserver_secret_key: Optional[str] = Field(
        default=None,
        env="AIRFLOW__WEBSERVER__SECRET_KEY"
    )
    
    # ============ Spark ============
    spark_master_url: str = Field(
        default="spark://spark-master:7077",
        env="SPARK_MASTER_URL"
    )
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v, values):
        """Validate JWT secret key strength in production."""
        environment = values.get("environment", "development")
        if environment == "production":
            if len(v) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            if v in ["your-secret-key-change-in-production", "secret", "changeme"]:
                raise ValueError("JWT_SECRET_KEY contains insecure default value")
        return v
    
    @validator("postgres_password")
    def validate_postgres_password(cls, v, values):
        """Validate database password strength in production."""
        environment = values.get("environment", "development")
        if environment == "production":
            if len(v) < 16:
                raise ValueError("POSTGRES_PASSWORD must be at least 16 characters in production")
            if v in ["password", "admin", "postgres", "airflow"]:
                raise ValueError("POSTGRES_PASSWORD is too weak for production")
        return v
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v, values):
        """Ensure CORS is restricted in production."""
        environment = values.get("environment", "development")
        if environment == "production":
            if "*" in v or "http://localhost" in str(v):
                raise ValueError("CORS cannot allow all origins or localhost in production")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development-specific settings with relaxed validation."""
    environment: str = "development"
    debug: bool = True
    
    # Allow weaker credentials in development
    jwt_secret_key: str = "dev-secret-key-not-for-production"
    postgres_password: str = "devscout_pass"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"


class ProductionSettings(Settings):
    """Production settings with strict validation."""
    environment: str = "production"
    debug: bool = False
    
    # All fields required and validated
    # No defaults allowed for sensitive values


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Determines environment and returns appropriate settings.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "development":
        # Allow fallbacks in development
        try:
            return Settings()
        except Exception:
            return DevelopmentSettings()
    else:
        return Settings()


# Convenience instance
settings = get_settings()


# Validation on import
def validate_settings_on_startup():
    """
    Validate settings when application starts.
    Call this in main.py startup event.
    """
    try:
        settings = get_settings()
        
        # Log configuration (redact sensitive values)
        print(f"[OK] Environment: {settings.environment}")
        print(f"[OK] Database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        print(f"[OK] CORS Origins: {settings.cors_origins}")
        print(f"[OK] JWT Algorithm: {settings.jwt_algorithm}")
        
        # Production-specific checks
        if settings.environment == "production":
            assert len(settings.jwt_secret_key) >= 32, "JWT secret too short"
            assert "*" not in settings.cors_origins, "CORS not restricted"
            print("[OK] Production security checks passed")
        
        return True
    except Exception as e:
        print(f"[FAIL] Configuration validation failed: {e}")
        raise


if __name__ == "__main__":
    """Test settings validation."""
    print("Testing settings validation...\n")
    validate_settings_on_startup()
    
    print("\nCurrent settings:")
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.database_url}")
    print(f"JWT Secret: {'*' * len(settings.jwt_secret_key)}")
