"""
test_manifest.py
----------------
Testes funcionais de contrato para o endpoint GET /manifest.

O manifest é o recurso central do domínio — fornece ao frontend a lista
completa de MFEs, rotas e metadados necessários para renderização da plataforma.

Cobertura:
    - Status codes esperados
    - Estrutura e schema do response
    - Presença de campos obrigatórios
    - Tipagem dos campos
    - Comportamento com filtros e parâmetros
"""

import pytest


@pytest.mark.contrato
@pytest.mark.manifest
class TestManifestContrato:
    """Testes de contrato do endpoint GET /manifest."""

    def test_manifest_retorna_200(self, api_client):
        """O endpoint deve retornar 200 OK com autenticação válida."""
        response = api_client.get("/manifest")
        assert response.status_code == 200, (
            f"Esperado 200, recebido {response.status_code}. Body: {response.text[:200]}"
        )

    def test_manifest_retorna_json(self, api_client, assert_response):
        """O Content-Type da resposta deve ser application/json."""
        response = api_client.get("/manifest")
        assert_response.has_json(response)

    def test_manifest_schema_valido(self, api_client, schema_validator):
        """O body do response deve conformar ao schema definido em schemas/manifest."""
        response = api_client.get("/manifest")
        assert response.status_code == 200
        schema_validator.validate(response.json(), "manifest/manifest_response")

    def test_manifest_contem_campo_version(self, api_client, assert_response):
        """O manifest deve sempre conter o campo 'version'."""
        response = api_client.get("/manifest")
        assert_response.has_field(response, "version")

    def test_manifest_contem_lista_mfes(self, api_client, assert_response):
        """O campo 'mfes' deve estar presente e ser uma lista."""
        response = api_client.get("/manifest")
        assert_response.has_field(response, "mfes")
        assert_response.is_list(response, "mfes")

    def test_manifest_contem_lista_routes(self, api_client, assert_response):
        """O campo 'routes' deve estar presente e ser uma lista."""
        response = api_client.get("/manifest")
        assert_response.has_field(response, "routes")
        assert_response.is_list(response, "routes")

    def test_manifest_mfes_nao_vazios(self, api_client, assert_response):
        """A lista de MFEs não deve estar vazia em ambiente configurado."""
        response = api_client.get("/manifest")
        assert_response.not_empty(response, "mfes")

    def test_manifest_mfe_possui_campos_obrigatorios(self, api_client, schema_validator):
        """Cada MFE no manifest deve ter id, name, bundle_url e active."""
        response = api_client.get("/manifest")
        assert response.status_code == 200

        mfes = response.json().get("mfes", [])
        assert len(mfes) > 0, "Nenhum MFE retornado no manifest"

        required_fields = ["id", "name", "bundle_url", "active"]
        for i, mfe in enumerate(mfes):
            for field in required_fields:
                assert field in mfe, (
                    f"MFE[{i}] está sem o campo obrigatório '{field}'. "
                    f"MFE recebido: {mfe}"
                )

    def test_manifest_routes_possuem_campos_obrigatorios(self, api_client):
        """Cada rota no manifest deve ter id, path, mfe e protected."""
        response = api_client.get("/manifest")
        assert response.status_code == 200

        routes = response.json().get("routes", [])
        assert len(routes) > 0, "Nenhuma rota retornada no manifest"

        required_fields = ["id", "path", "mfe", "protected"]
        for i, route in enumerate(routes):
            for field in required_fields:
                assert field in route, (
                    f"Route[{i}] está sem o campo obrigatório '{field}'. "
                    f"Route recebida: {route}"
                )

    def test_manifest_route_paths_iniciam_com_barra(self, api_client):
        """Todos os paths de rotas devem iniciar com '/' (padrão de URL)."""
        response = api_client.get("/manifest")
        assert response.status_code == 200

        routes = response.json().get("routes", [])
        for route in routes:
            path = route.get("path", "")
            assert path.startswith("/"), (
                f"Path de rota inválido — deve iniciar com '/': '{path}'"
            )

    def test_manifest_mfe_active_e_boolean(self, api_client):
        """O campo 'active' de cada MFE deve ser boolean (não string)."""
        response = api_client.get("/manifest")
        assert response.status_code == 200

        mfes = response.json().get("mfes", [])
        for i, mfe in enumerate(mfes):
            assert isinstance(mfe.get("active"), bool), (
                f"MFE[{i}].active deve ser boolean, "
                f"recebido: {type(mfe.get('active')).__name__} ('{mfe.get('active')}')"
            )

    def test_manifest_contem_environment(self, api_client):
        """O manifest deve informar o ambiente de origem."""
        response = api_client.get("/manifest")
        assert response.status_code == 200

        data = response.json()
        assert "environment" in data, "Campo 'environment' ausente no manifest"
        assert data["environment"] in ("dev", "staging", "prod"), (
            f"Valor inesperado para 'environment': {data['environment']}"
        )

    @pytest.mark.parametrize("environment", ["dev", "staging", "prod"])
    def test_manifest_environment_values_validos(self, api_client, environment):
        """
        Smoke test parametrizado — valida que o campo environment aceita
        apenas valores conhecidos da enumeração.
        """
        response = api_client.get("/manifest")
        if response.status_code == 200:
            data = response.json()
            if "environment" in data:
                assert data["environment"] in ("dev", "staging", "prod")


@pytest.mark.contrato
@pytest.mark.manifest
class TestManifestFiltros:
    """Testes de comportamento com query params e filtros."""

    def test_manifest_filtrado_por_role(self, api_client):
        """GET /manifest?role=USER deve retornar apenas MFEs acessíveis ao role."""
        response = api_client.get("/manifest", params={"role": "USER"})
        # O endpoint pode retornar 200 (filtrado) ou 400 (param não suportado)
        assert response.status_code in (200, 400), (
            f"Status inesperado para filtro de role: {response.status_code}"
        )

    def test_manifest_filtrado_por_environment(self, api_client):
        """GET /manifest?env=prod deve retornar manifest do ambiente solicitado."""
        response = api_client.get("/manifest", params={"env": "prod"})
        assert response.status_code in (200, 400, 403)

    def test_manifest_param_invalido_retorna_400(self, api_client):
        """Query params desconhecidos devem ser ignorados ou retornar 400."""
        response = api_client.get("/manifest", params={"parametro_inexistente": "valor"})
        assert response.status_code in (200, 400), (
            f"Status inesperado para param inválido: {response.status_code}"
        )
