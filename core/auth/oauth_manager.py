"""
oauth_manager.py
----------------
Gerenciador de autenticação OAuth 2.0 com fluxo Client Credentials.
Responsável por obter, cachear e renovar tokens JWT automaticamente.

Uso:
    from core.auth.oauth_manager import OAuthManager
    manager = OAuthManager(config)
    headers = manager.get_auth_headers()   # {"Authorization": "Bearer eyJ..."}
"""

import time
from typing import Optional

import httpx

from core.auth.token_cache import CachedToken, TokenCache
from core.logger import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Erro de autenticação OAuth 2.0 — falha ao obter token."""
    pass


class OAuthManager:
    """
    Gerencia o ciclo de vida de tokens OAuth 2.0 (Client Credentials).

    Fluxo:
        1. Verifica cache — retorna token válido se existir
        2. Se cache vazio ou token expirado → solicita novo token
        3. Armazena novo token no cache com TTL
        4. Em caso de 401 nas requests — invalida cache e tenta uma renovação
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Dicionário de configuração completo (saída do get_config()).
        """
        auth_cfg = config.get("auth", {})
        self._token_url: str = auth_cfg.get("token_url", "")
        self._client_id: str = auth_cfg.get("client_id", "")
        self._client_secret: str = auth_cfg.get("client_secret", "")
        self._scope: str = auth_cfg.get("scope", "")
        self._grant_type: str = auth_cfg.get("grant_type", "client_credentials")
        refresh_margin: int = auth_cfg.get("token_refresh_margin", 60)

        self._cache = TokenCache(refresh_margin=refresh_margin)
        self._timeout = config.get("api", {}).get("timeout", 30)

    def _fetch_token(self) -> CachedToken:
        """
        Realiza a chamada ao servidor de autenticação e retorna o token.
        Lança AuthenticationError em caso de falha.
        """
        logger.info(f"Solicitando novo token OAuth | url={self._token_url}")

        if not self._client_id or not self._client_secret:
            raise AuthenticationError(
                "OAUTH_CLIENT_ID e OAUTH_CLIENT_SECRET não configurados. "
                "Verifique o arquivo .env ou as variáveis de ambiente."
            )

        payload = {
            "grant_type": self._grant_type,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        if self._scope:
            payload["scope"] = self._scope

        try:
            response = httpx.post(
                self._token_url,
                data=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(
                f"Falha ao obter token OAuth | status={e.response.status_code} | "
                f"body={e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(
                f"Erro de conexão com servidor de autenticação: {e}"
            ) from e

        data = response.json()
        expires_in = data.get("expires_in", 3600)

        token = CachedToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            scope=data.get("scope", self._scope),
        )
        logger.info(f"Token obtido com sucesso | expira em {expires_in}s")
        return token

    def get_token(self, force_refresh: bool = False) -> CachedToken:
        """
        Retorna token válido (do cache ou renovado).

        Args:
            force_refresh: Ignora o cache e força nova autenticação.
                           Útil após receber 401 inesperado.
        """
        if force_refresh:
            self._cache.invalidate()

        cached = self._cache.get()
        if cached:
            return cached

        token = self._fetch_token()
        self._cache.set(token)
        return token

    def get_auth_headers(self, force_refresh: bool = False) -> dict[str, str]:
        """
        Retorna dicionário com header Authorization pronto para injeção.

        Returns:
            {"Authorization": "Bearer eyJ..."}
        """
        token = self.get_token(force_refresh=force_refresh)
        return {"Authorization": token.bearer}

    def invalidate_cache(self) -> None:
        """Invalida o cache de token — útil em testes de segurança."""
        self._cache.invalidate()

    def clear_cache(self) -> None:
        """Limpa todo o cache — chamado no teardown."""
        self._cache.clear()
