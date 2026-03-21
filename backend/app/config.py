from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://shipflow:shipflow_dev@localhost:5432/shipflow"
    database_url_sync: str = "postgresql://shipflow:shipflow_dev@localhost:5432/shipflow"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_expiry_minutes: int = 15
    jwt_refresh_expiry_minutes: int = 10080

    mfa_encryption_key: str = "change-me"

    environment: str = "development"
    platform_admin_emails: str = ""  # Comma-separated; users with these emails can manage tenants
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"
    rate_limit_per_minute: int = 100
    rate_limit_auth_per_minute: int = 20

    # LLM / AI parsing
    llm_api_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_key_encryption_key: str = Field(
        default="",
        description="Fernet key (base64) for tenant API key encryption",
        validation_alias=AliasChoices("LLM_KEY_ENCRYPTION_KEY", "ENCRYPTION_KEY"),
    )
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3
    llm_max_input_chars: int = 24000  # ~6k tokens; keeps under Groq free tier 12k TPM
    llm_parse_single_attempt_on_ingest: bool = True  # No retries on initial ingest
    llm_vessel_only_sync: bool = True  # Only ingest vessel-related emails; set False to sync all

    # IMAP email ingest
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_use_ssl: bool = True
    imap_poll_interval_seconds: int = 60
    imap_default_tenant_id: str = ""

    # OAuth 2.0 – Google (Gmail)
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    # OAuth 2.0 – Microsoft (Outlook / Microsoft 365)
    microsoft_oauth_client_id: str = ""
    microsoft_oauth_client_secret: str = ""
    microsoft_oauth_tenant: str = "common"

    # OAuth shared
    oauth_redirect_base_url: str = "http://localhost:8000"
    oauth_frontend_success_url: str = "http://localhost:5173/settings/integrations"
    oauth_state_encryption_key: str = ""

    # Webhook secret for inbound email verification
    webhook_inbound_secret: str = ""

    # myPOS billing (Task 8.6: migrated from Stripe)
    mypos_sid: str = ""
    mypos_wallet_number: str = ""
    mypos_key_index: int = 1
    mypos_private_key: str = ""  # PEM-encoded RSA private key for signing
    mypos_public_cert: str = ""  # PEM-encoded myPOS public cert for verifying notify
    mypos_skip_cancel_verify: bool = False  # Skip cancel signature verify if prod cert unavailable
    mypos_base_url: str = "https://www.mypos.com/vmp/checkout-test"  # sandbox default
    mypos_currency: str = "EUR"
    mypos_amount_starter_monthly: float = 0.0
    mypos_amount_professional_monthly: float = 0.0
    api_public_base_url: str = ""  # e.g. https://api.portnomic.com — for URL_Notify

    # Object storage (S3-compatible / local)
    storage_backend: str = "local"
    storage_local_path: str = "./storage"
    storage_s3_bucket: str = ""
    storage_s3_region: str = ""
    storage_s3_access_key: str = ""
    storage_s3_secret_key: str = ""
    storage_s3_endpoint_url: str = ""

    # SMTP / email dispatch
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_address: str = "noreply@portnomic.ai"
    smtp_from_name: str = "Portnomic"

    # OpenTelemetry
    otel_enabled: bool = False
    otel_service_name: str = "shipflow-backend"
    otel_exporter_endpoint: str = "http://localhost:4317"
    otel_exporter_insecure: bool = True

    # Circuit breaker
    cb_failure_threshold: int = 5
    cb_recovery_timeout: int = 30
    cb_half_open_max_calls: int = 3

    # AIS (aisstream.io) — berth arrival/departure for Sentinel Rule S-002
    aisstream_api_key: str = ""
    aisstream_url: str = "wss://stream.aisstream.io/v0/stream"
    aisstream_collect_timeout_seconds: int = 60
    aisstream_cache_ttl_seconds: int = 300  # 5 min cache per vessel+port
    aisstream_berth_speed_threshold_knots: float = 0.5  # Sog < this = at berth

    # Carbon price (EUA) for C-Engine EU ETS cost projection
    carbon_price_api_url: str = ""
    carbon_price_api_key: str = ""
    carbon_price_api_header: str = "Authorization"  # "Authorization" (Bearer) or "X-API-Key"
    carbon_price_json_path: str = "price"  # JSON path, e.g. "price" or "contracts.0.last_price"
    fallback_carbon_price_eur: float = 80.0
    carbon_price_cache_ttl_seconds: int = 3600  # 1 hour

    # Timeouts (seconds)
    db_pool_timeout: int = 30
    db_connect_timeout: int = 10
    redis_socket_timeout: float = 15.0  # must be > blpop timeout (5s) in worker
    redis_socket_connect_timeout: float = 5.0
    smtp_timeout: int = 30

    model_config = {
        "env_file": ["../.env", ".env"],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Fail fast if production uses default/insecure secrets."""
        if self.environment != "production":
            if self.jwt_secret == "change-me" or self.mfa_encryption_key == "change-me":
                import logging

                logging.getLogger("shipflow.config").warning(
                    "SECURITY: Using default JWT_SECRET or MFA_ENCRYPTION_KEY in non-production. "
                    "Set JWT_SECRET and MFA_ENCRYPTION_KEY in all environments."
                )
            return self
        if self.jwt_secret == "change-me" or self.mfa_encryption_key == "change-me":
            raise ValueError(
                "Production requires JWT_SECRET and MFA_ENCRYPTION_KEY from environment; "
                "never use default 'change-me' in production"
            )
        if len(self.jwt_secret.encode()) < 32:
            raise ValueError(
                "Production JWT_SECRET must be at least 32 bytes for HS256. "
                "Use a cryptographically secure random value."
            )
        return self


settings = Settings()

# Plan limits for feature gating (None = unlimited)
# See docs/monetization-plan.md for full plan details
# Restructured (Task 8.10): Starter limits → Professional; Professional → Enterprise; new lower Starter
PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "demo": {
        "users": 1,
        "vessels": 2,
        "das_per_month": 5,
        "ai_parses_per_month": 10,
    },
    "starter": {
        "users": 2,
        "vessels": 5,
        "das_per_month": 25,
        "ai_parses_per_month": 50,
    },
    "professional": {
        "users": 3,
        "vessels": 10,
        "das_per_month": 50,
        "ai_parses_per_month": 100,
    },
    "enterprise": {
        "users": None,
        "vessels": None,
        "das_per_month": None,
        "ai_parses_per_month": None,
    },
}
