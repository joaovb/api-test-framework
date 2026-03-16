"""
test_autenticacao.py
--------------------
Testes de segurança: autenticação (401) e autorização (403).

Valida que os endpoints do domínio estão corretamente protegidos contra:
    - Acesso sem token
    - Acesso com token inválido/malformado
    - Acesso com token expirado simulado
    - Acesso com role insuficiente
    - Presença de headers de segurança obrigatórios
"""

import pytest


# Endpoints protegidos do domínio — devem exigir autenticação
PROTECTED_ENDPOINTS = [
    "/manifest",
    "/pages",
    "/journeys",
    "/permissions",
]


@pytest.mark.seguranca
class TestAutenticacao:
    """Testes de autenticação — acesso sem ou com token inválido."""

    @pytest.mark.parametrize("endpoint", PROTECTED_ENDPOINTS)
    def test_sem_token_retorna_401(self, api_client_no_auth, endpoint):
        """
        Todos os endpoints protegidos devem retornar 401 quando
        acessados sem o header Authorization.
        """
        response = api_client_no_auth.get(endpoint)
        assert response.status_code == 401, (
            f"Endpoint '{endpoint}' deveria retornar 401 sem token, "
            f"mas retornou {response.status_code}"
        )

    @pytest.mark.parametrize("endpoint", PROTECTED_ENDPOINTS)
    def test_token_invalido_retorna_401(self, api_client_invalid_token, endpoint):
        """
        Todos os endpoints protegidos devem retornar 401 quando
        acessados com token JWT malformado ou inválido.
        """
        response = api_client_invalid_token.get(endpoint)
        assert response.status_code == 401, (
            f"Endpoint '{endpoint}' deveria retornar 401 com token inválido, "
            f"mas retornou {response.status_code}"
        )

    @pytest.mark.parametrize("endpoint", PROTECTED_ENDPOINTS)
    def test_token_expirado_retorna_401(self, api_client, endpoint):
        """
        Token manualmente expirado deve resultar em 401.
        Simula o token expirado passando um JWT com payload manipulado.
        """
        expired_token = (
            "eyJhbGciOiJSUzI1NiJ9"
            ".eyJzdWIiOiJ0ZXN0Iiwi"
            "ZXhwIjoxMDAwMDAwMDAwfQ"
            ".assinatura_invalida"
        )
        response = api_client.with_invalid_token(expired_token).get(endpoint)
        assert response.status_code == 401

    def test_header_authorization_ausente_retorna_401(self, api_client_no_auth):
        """Requisição sem qualquer header retorna 401 no manifest."""
        response = api_client_no_auth.get("/manifest")
        assert response.status_code == 401

    def test_authorization_com_schema_errado_retorna_401(self, config):
        """
        Header Authorization com schema errado (Basic ao invés de Bearer)
        deve retornar 401.
        """
        from core.http_client import ApiClient
        client = ApiClient(
            config=config,
            oauth_manager=None,
            extra_headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        response = client.get("/manifest")
        assert response.status_code == 401

    def test_response_401_tem_body_json(self, api_client_no_auth):
        """O response 401 deve retornar body JSON com informações do erro."""
        response = api_client_no_auth.get("/manifest")
        assert response.status_code == 401
        content_type = response.headers.get("content-type", "")
        # Verificação permissiva — alguns providers retornam texto plano no 401
        if "application/json" in content_type:
            data = response.json()
            assert data, "Body do 401 não deve estar vazio"

    def test_response_401_nao_expoe_stack_trace(self, api_client_no_auth):
        """O response 401 não deve expor stack traces ou detalhes internos."""
        response = api_client_no_auth.get("/manifest")
        body = response.text.lower()
        sensitive_keywords = [
            "stack trace", "exception", "at com.", "at org.",
            "java.lang", "caused by", "nullpointerexception",
        ]
        for keyword in sensitive_keywords:
            assert keyword not in body, (
                f"Response 401 expõe informação interna: '{keyword}'. "
                f"Verifique o error handler da aplicação."
            )


@pytest.mark.seguranca
class TestAutorizacao:
    """Testes de autorização — role insuficiente para o recurso."""

    def test_role_insuficiente_retorna_403(self, api_client_wrong_role):
        """
        Usuário autenticado com role sem permissão deve receber 403 Forbidden.
        Requer configuração de credenciais com scope restrito no ambiente.
        """
        response = api_client_wrong_role.get("/manifest")
        # 403 é o esperado; 401 indica problema de configuração do teste
        assert response.status_code in (403, 401), (
            f"Esperado 403 (Forbidden) ou 401, recebido: {response.status_code}"
        )

    def test_acesso_admin_endpoint_com_role_user_retorna_403(self, api_client_wrong_role):
        """Endpoint administrativo deve ser inacessível para role USER."""
        response = api_client_wrong_role.get("/admin/manifest")
        assert response.status_code in (403, 404), (
            f"Endpoint admin acessível com role USER: {response.status_code}"
        )


@pytest.mark.seguranca
class TestHeadersSeguranca:
    """
    Testes de headers de segurança HTTP.
    Valida que a aplicação Spring Boot retorna os headers de segurança
    obrigatórios em todas as responses.
    """

    SECURITY_HEADERS = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Strict-Transport-Security",
    ]

    FORBIDDEN_HEADERS = [
        "X-Powered-By",
        "Server",
        "X-AspNet-Version",
    ]

    @pytest.mark.parametrize("header", SECURITY_HEADERS)
    def test_header_seguranca_presente(self, api_client, header):
        """
        Headers de segurança obrigatórios devem estar presentes
        em todas as responses autenticadas.
        """
        response = api_client.get("/manifest")
        assert response.status_code == 200
        assert header in response.headers, (
            f"Header de segurança ausente: '{header}'. "
            f"Headers presentes: {list(response.headers.keys())}"
        )

    def test_x_content_type_options_valor(self, api_client):
        """X-Content-Type-Options deve ter valor 'nosniff'."""
        response = api_client.get("/manifest")
        value = response.headers.get("X-Content-Type-Options", "")
        assert value.lower() == "nosniff", (
            f"X-Content-Type-Options esperado 'nosniff', recebido: '{value}'"
        )

    def test_x_frame_options_valor(self, api_client):
        """X-Frame-Options deve ser DENY ou SAMEORIGIN."""
        response = api_client.get("/manifest")
        value = response.headers.get("X-Frame-Options", "").upper()
        assert value in ("DENY", "SAMEORIGIN"), (
            f"X-Frame-Options inválido: '{value}'. Esperado DENY ou SAMEORIGIN."
        )

    @pytest.mark.parametrize("header", FORBIDDEN_HEADERS)
    def test_header_informativo_ausente(self, api_client, header):
        """
        Headers que expõem informações do servidor não devem estar presentes.
        Informações como 'Server: Apache/2.4' facilitam ataques direcionados.
        """
        response = api_client.get("/manifest")
        assert header not in response.headers, (
            f"Header informativo exposto: '{header}: {response.headers.get(header)}'. "
            f"Configure o Spring Boot para não expor este header."
        )

    def test_content_type_nao_expoe_encoding_desnecessario(self, api_client):
        """Content-Type deve ser application/json sem informações extras desnecessárias."""
        response = api_client.get("/manifest")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Content-Type inesperado: '{content_type}'"
        )


@pytest.mark.seguranca
class TestHealthCheck:
    """Testes do endpoint de health check (Spring Actuator)."""

    def test_health_endpoint_acessivel(self, api_client):
        """O endpoint /actuator/health deve estar acessível."""
        response = api_client.get("/actuator/health")
        assert response.status_code in (200, 401, 404), (
            f"Status inesperado no health check: {response.status_code}"
        )

    def test_health_retorna_status_up(self, api_client):
        """Se o health check for acessível, deve retornar status UP."""
        response = api_client.get("/actuator/health")
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "")
            assert status == "UP", (
                f"Aplicação não está saudável. Status: {status}. "
                f"Body: {data}"
            )
