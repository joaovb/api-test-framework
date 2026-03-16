"""
http_client.py
--------------
Wrapper do httpx com autenticação automática, retry, logging e timeout configurável.
É a camada central de comunicação HTTP do framework — todos os testes usam este client.

Uso:
    # Via fixture (recomendado):
    def test_example(api_client):
        response = api_client.get("/manifest")
        assert response.status_code == 200

    # Manual:
    from core.http_client import ApiClient
    client = ApiClient(config, oauth_manager)
    response = client.get("/manifest")
"""

import time
from typing import Any, Optional

import httpx

from core.auth.oauth_manager import OAuthManager
from core.logger import get_logger

logger = get_logger(__name__)


class ApiClient:
    """
    HTTP Client configurado para testes de API REST.

    Funcionalidades:
    - Injeção automática de token Bearer em todos os requests
    - Retry automático com backoff exponencial em erros 5xx e de rede
    - Logging estruturado de todas as requests/responses
    - Renovação automática de token em respostas 401
    - Timeout configurável por ambiente
    """

    def __init__(
        self,
        config: dict,
        oauth_manager: Optional[OAuthManager] = None,
        extra_headers: Optional[dict] = None,
    ):
        """
        Args:
            config:        Configuração completa do ambiente.
            oauth_manager: Gerenciador OAuth. Se None, requests sem autenticação.
            extra_headers: Headers adicionais fixos para todas as requests.
        """
        api_cfg = config.get("api", {})
        self._base_url: str = api_cfg.get("base_url", "").rstrip("/")
        self._timeout: int = api_cfg.get("timeout", 30)
        self._oauth = oauth_manager

        retry_cfg = api_cfg.get("retry", {})
        self._retry_enabled: bool = retry_cfg.get("enabled", True)
        self._max_attempts: int = retry_cfg.get("max_attempts", 3)
        self._backoff_factor: float = retry_cfg.get("backoff_factor", 0.5)

        default_headers = config.get("headers", {}).get("default", {})
        self._base_headers: dict = {**default_headers, **(extra_headers or {})}

    def _build_headers(self, extra: Optional[dict] = None) -> dict:
        """Monta headers finais: base + auth + extras da request."""
        headers = {**self._base_headers}
        if self._oauth:
            headers.update(self._oauth.get_auth_headers())
        if extra:
            headers.update(extra)
        return headers

    def _log_request(self, method: str, url: str, **kwargs) -> None:
        logger.info(f"→ {method.upper()} {url}")
        if kwargs.get("json"):
            logger.debug(f"  Body: {kwargs['json']}")
        if kwargs.get("params"):
            logger.debug(f"  Params: {kwargs['params']}")

    def _log_response(self, response: httpx.Response, elapsed: float) -> None:
        status = response.status_code
        level = logger.info if status < 400 else logger.warning
        level(f"← {status} ({elapsed:.0f}ms) {response.url}")
        if status >= 400:
            logger.debug(f"  Response body: {response.text[:500]}")

    def _should_retry(self, response: Optional[httpx.Response], attempt: int) -> bool:
        """Determina se deve tentar novamente com base no status e tentativa atual."""
        if not self._retry_enabled or attempt >= self._max_attempts:
            return False
        if response is None:
            return True   # erro de rede — sempre tenta de novo
        return response.status_code in (429, 500, 502, 503, 504)

    def _request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Executa uma requisição HTTP com retry automático.

        Args:
            method:   Método HTTP (GET, POST, PUT, PATCH, DELETE)
            endpoint: Path relativo ao base_url (ex: "/manifest")
            headers:  Headers adicionais específicos desta request
            **kwargs: Parâmetros extras do httpx (json, params, data, etc.)
        """
        url = f"{self._base_url}{endpoint}"
        final_headers = self._build_headers(headers)

        for attempt in range(1, self._max_attempts + 1):
            response = None
            start = time.monotonic()

            try:
                self._log_request(method, url, **kwargs)
                response = httpx.request(
                    method=method,
                    url=url,
                    headers=final_headers,
                    timeout=self._timeout,
                    **kwargs,
                )
                elapsed = (time.monotonic() - start) * 1000
                self._log_response(response, elapsed)

                # Renovação automática em 401
                if response.status_code == 401 and self._oauth and attempt == 1:
                    logger.warning("401 recebido — renovando token e tentando novamente")
                    final_headers.update(
                        self._oauth.get_auth_headers(force_refresh=True)
                    )
                    continue

                if self._should_retry(response, attempt):
                    wait = self._backoff_factor * (2 ** (attempt - 1))
                    logger.warning(
                        f"Tentativa {attempt}/{self._max_attempts} falhou "
                        f"(status={response.status_code}) — aguardando {wait:.1f}s"
                    )
                    time.sleep(wait)
                    continue

                return response

            except httpx.RequestError as e:
                elapsed = (time.monotonic() - start) * 1000
                logger.error(f"Erro de rede na tentativa {attempt}: {e}")
                if not self._should_retry(None, attempt):
                    raise
                wait = self._backoff_factor * (2 ** (attempt - 1))
                time.sleep(wait)

        # Retorna o último response mesmo em falha (para assertions nos testes)
        return response  # type: ignore

    # ── Métodos públicos HTTP ──────────────────────────────────────────────────

    def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> httpx.Response:
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json: Optional[Any] = None, **kwargs) -> httpx.Response:
        return self._request("POST", endpoint, json=json, **kwargs)

    def put(self, endpoint: str, json: Optional[Any] = None, **kwargs) -> httpx.Response:
        return self._request("PUT", endpoint, json=json, **kwargs)

    def patch(self, endpoint: str, json: Optional[Any] = None, **kwargs) -> httpx.Response:
        return self._request("PATCH", endpoint, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        return self._request("DELETE", endpoint, **kwargs)

    def without_auth(self) -> "ApiClient":
        """
        Retorna novo client sem autenticação — para testes de segurança.

        Uso:
            def test_sem_token(api_client):
                response = api_client.without_auth().get("/manifest")
                assert response.status_code == 401
        """
        return ApiClient(
            config={"api": {"base_url": self._base_url, "timeout": self._timeout}},
            oauth_manager=None,
            extra_headers=self._base_headers,
        )

    def with_invalid_token(self, token: str = "invalid.token.here") -> "ApiClient":
        """
        Retorna novo client com token inválido — para testes de segurança.

        Uso:
            def test_token_invalido(api_client):
                response = api_client.with_invalid_token().get("/manifest")
                assert response.status_code == 401
        """
        client = ApiClient(
            config={"api": {"base_url": self._base_url, "timeout": self._timeout}},
            oauth_manager=None,
            extra_headers={**self._base_headers, "Authorization": f"Bearer {token}"},
        )
        return client
