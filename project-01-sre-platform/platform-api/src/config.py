"""Runtime configuration, driven by environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PLATFORM_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Observability.
    service_name: str = "platform-api"
    log_level: str = "INFO"
    otlp_endpoint: str = "http://signoz-otel-collector.signoz.svc.cluster.local:4317"

    # Vault.
    vault_addr: str = "http://vault.vault.svc.cluster.local:8200"
    vault_role: str = "platform-api"
    vault_k8s_mount: str = "kubernetes"
    vault_token_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"

    # Platform behaviour.
    workload_namespace: str = "sre-platform"
    receipt_key_path: str = "platform-api/receipt-key"

    # LLM feature.
    enable_llm_explain: bool = False

    # LLM backend selection — overrides live on the LLMBackend module.
    # Read directly from env because LLM_BACKEND / GOOGLE_API_KEY are
    # process-global, not prefixed.


def get_settings() -> Settings:
    return Settings()
