"""
conftest.py (raiz)
------------------
Fixtures globais do framework — disponíveis em todos os módulos de teste.
Este arquivo é carregado automaticamente pelo pytest antes de qualquer teste.

Hierarquia de fixtures:
    session scope  → config, oauth_manager (criados uma vez por execução)
    function scope → api_client (recriado por teste para isolamento)
"""

import os
import pytest
from dotenv import load_dotenv

from core.config_loader import get_config, reset_config
from core.auth.oauth_manager import OAuthManager
from core.http_client import ApiClient
from core.logger import setup_logging
from core.schema_validator import SchemaValidator

# Carrega .env antes de qualquer coisa
load_dotenv()


# ── Setup global de logging ───────────────────────────────────────────────────

def pytest_configure(config):
    """Hook do pytest — executado antes de qualquer fixture ou teste."""
    env = os.environ.get("ENV", "dev")
    log_level = "DEBUG" if env == "dev" else "INFO"
    log_format = "json" if env in ("staging", "prod") else "text"
    setup_logging(level=log_level, fmt=log_format)


# ── Fixtures de configuração ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def config() -> dict:
    """
    Configuração completa do ambiente ativo.
    Criada uma única vez por sessão de testes.

    Uso:
        def test_algo(config):
            assert config["api"]["base_url"] != ""
    """
    return get_config()


# ── Fixtures de autenticação ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def oauth_manager(config) -> OAuthManager:
    """
    Gerenciador OAuth configurado para o ambiente ativo.
    Sessão única — token é cacheado e reutilizado entre testes.

    Uso:
        def test_algo(oauth_manager):
            headers = oauth_manager.get_auth_headers()
    """
    manager = OAuthManager(config)
    yield manager
    manager.clear_cache()


@pytest.fixture(scope="session")
def auth_token(oauth_manager) -> str:
    """
    Token JWT válido para uso direto em testes.

    Uso:
        def test_algo(auth_token):
            assert auth_token.startswith("Bearer ")
    """
    return oauth_manager.get_token().bearer


# ── Fixtures de HTTP client ───────────────────────────────────────────────────

@pytest.fixture(scope="function")
def api_client(config, oauth_manager) -> ApiClient:
    """
    Client HTTP autenticado — recriado a cada teste para isolamento.
    Injeta token Bearer automaticamente em todas as requests.

    Uso:
        def test_manifest(api_client):
            response = api_client.get("/manifest")
            assert response.status_code == 200
    """
    return ApiClient(config=config, oauth_manager=oauth_manager)


@pytest.fixture(scope="function")
def api_client_no_auth(config) -> ApiClient:
    """
    Client HTTP SEM autenticação — para testes de segurança (401).

    Uso:
        def test_sem_token(api_client_no_auth):
            response = api_client_no_auth.get("/manifest")
            assert response.status_code == 401
    """
    return ApiClient(config=config, oauth_manager=None)


@pytest.fixture(scope="function")
def api_client_invalid_token(config) -> ApiClient:
    """
    Client HTTP com token inválido — para testes de segurança (401).

    Uso:
        def test_token_invalido(api_client_invalid_token):
            response = api_client_invalid_token.get("/manifest")
            assert response.status_code == 401
    """
    return ApiClient(
        config=config,
        oauth_manager=None,
        extra_headers={"Authorization": "Bearer token.invalido.aqui"},
    )


@pytest.fixture(scope="function")
def api_client_wrong_role(config) -> ApiClient:
    """
    Client HTTP com token de role insuficiente — para testes de autorização (403).
    Requer que o ambiente tenha credenciais de role limitada configuradas.
    """
    from core.auth.oauth_manager import OAuthManager
    import copy

    restricted_config = copy.deepcopy(config)
    restricted_config["auth"]["scope"] = "jornada:readonly"
    manager = OAuthManager(restricted_config)
    return ApiClient(config=config, oauth_manager=manager)


# ── Fixture de validação de schema ────────────────────────────────────────────

@pytest.fixture(scope="session")
def schema_validator() -> SchemaValidator:
    """
    Validador de schema JSON — reutilizado em toda a sessão.

    Uso:
        def test_schema(api_client, schema_validator):
            response = api_client.get("/manifest")
            schema_validator.validate(response.json(), "manifest/manifest_response")
    """
    return SchemaValidator()


# ── Fixtures de dados ─────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def manifest_payload():
    """Payload válido de manifest para uso em testes."""
    from factories.mfe_factory import ManifestFactory
    return ManifestFactory.build()


@pytest.fixture(scope="function")
def mfe_payload():
    """Payload válido de MFE para uso em testes."""
    from factories.mfe_factory import MfeFactory
    return MfeFactory.build()


@pytest.fixture(scope="function")
def route_payload():
    """Payload válido de rota para uso em testes."""
    from factories.mfe_factory import RouteFactory
    return RouteFactory.build()


@pytest.fixture(scope="function")
def journey_payload():
    """Payload válido de jornada para uso em testes."""
    from factories.mfe_factory import JourneyFactory
    return JourneyFactory.build()


# ── Helpers de asserção ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def assert_response():
    """
    Helper de asserções comuns de response HTTP.
    Elimina boilerplate repetitivo nos testes.

    Uso:
        def test_algo(api_client, assert_response):
            response = api_client.get("/manifest")
            assert_response.ok(response)
            assert_response.has_json(response)
    """
    class ResponseAssertions:
        @staticmethod
        def ok(response, expected_status: int = 200):
            assert response.status_code == expected_status, (
                f"Status esperado {expected_status}, recebido {response.status_code}. "
                f"Body: {response.text[:300]}"
            )

        @staticmethod
        def has_json(response):
            assert response.headers.get("content-type", "").startswith("application/json"), (
                f"Content-Type esperado application/json, "
                f"recebido: {response.headers.get('content-type')}"
            )
            try:
                response.json()
            except Exception as e:
                raise AssertionError(f"Response não é JSON válido: {e}")

        @staticmethod
        def has_field(response, field: str):
            data = response.json()
            assert field in data, (
                f"Campo '{field}' ausente no response. "
                f"Campos presentes: {list(data.keys())}"
            )

        @staticmethod
        def is_list(response, field: str | None = None):
            data = response.json()
            target = data.get(field, data) if field else data
            assert isinstance(target, list), (
                f"Esperava lista em '{field}', recebido: {type(target).__name__}"
            )

        @staticmethod
        def not_empty(response, field: str | None = None):
            data = response.json()
            target = data.get(field, data) if field else data
            assert target, f"Campo '{field}' está vazio ou nulo no response."

    return ResponseAssertions()
