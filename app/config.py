"""Configuração da aplicação lida de variáveis de ambiente."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"
    http_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "10")),
        )
