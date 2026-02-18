"""Environment-based configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/defi_agent"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Chain
    eth_rpc_url: str = ""
    eth_rpc_fallback_1: str = ""
    eth_rpc_fallback_2: str = ""
    chain_id: int = 1

    # MEV Protection
    flashbots_rpc: str = "https://rpc.flashbots.net"

    # Safe
    safe_address: str = ""

    # API Security
    api_secret_key: str = ""

    # Monitoring
    prometheus_port: int = 9090
    grafana_port: int = 3000
    alert_slack_webhook: str = ""

    # AI
    model_registry_path: str = "./mlflow"
    decision_log_path: str = "./logs/decisions/"

    model_config = {"env_file": ".env", "case_sensitive": False}
