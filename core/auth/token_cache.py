"""
token_cache.py
--------------
Cache de token JWT com controle de TTL e renovação automática.
Evita múltiplas chamadas ao servidor de autenticação durante uma sessão de testes.

Uso interno — consumido pelo OAuthManager.
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CachedToken:
    """Representa um token JWT em cache com metadados de expiração."""
    access_token: str
    token_type: str
    expires_at: float          # timestamp Unix de expiração real
    scope: str = ""

    def is_expired(self, margin_seconds: int = 60) -> bool:
        """
        Verifica se o token está expirado ou prestes a expirar.

        Args:
            margin_seconds: Renova o token N segundos antes da expiração real.
                            Evita erros de race condition em execuções paralelas.
        """
        return time.time() >= (self.expires_at - margin_seconds)

    @property
    def bearer(self) -> str:
        """Retorna o token no formato Bearer para uso no header Authorization."""
        return f"Bearer {self.access_token}"


class TokenCache:
    """
    Cache thread-safe de tokens OAuth 2.0.
    Suporta múltiplos escopos — útil quando o framework precisar de tokens
    com permissões diferentes (ex: admin vs readonly).
    """

    def __init__(self, refresh_margin: int = 60):
        self._cache: dict[str, CachedToken] = {}
        self._refresh_margin = refresh_margin

    def get(self, scope: str = "default") -> Optional[CachedToken]:
        """
        Retorna token válido do cache ou None se ausente/expirado.

        Args:
            scope: Identificador do escopo para suporte a múltiplos tokens.
        """
        token = self._cache.get(scope)
        if token is None:
            logger.debug(f"Cache miss para escopo: {scope}")
            return None
        if token.is_expired(self._refresh_margin):
            logger.info(f"Token expirado/próximo do vencimento para escopo: {scope}")
            self._cache.pop(scope, None)
            return None
        logger.debug(f"Cache hit para escopo: {scope}")
        return token

    def set(self, token: CachedToken, scope: str = "default") -> None:
        """Armazena token no cache para o escopo informado."""
        logger.info(
            f"Token armazenado em cache | escopo={scope} | "
            f"expira em: {token.expires_at - time.time():.0f}s"
        )
        self._cache[scope] = token

    def invalidate(self, scope: str = "default") -> None:
        """Remove um token específico do cache (útil em testes de 401)."""
        self._cache.pop(scope, None)
        logger.debug(f"Cache invalidado para escopo: {scope}")

    def clear(self) -> None:
        """Limpa todo o cache — chamado no teardown da sessão de testes."""
        self._cache.clear()
        logger.debug("Cache de tokens completamente limpo")
