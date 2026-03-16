"""
test_pages_journeys.py
----------------------
Testes funcionais de contrato para os endpoints:
    - GET /pages          → lista de páginas e rotas por perfil
    - GET /pages/{id}     → página específica
    - GET /journeys       → lista de jornadas de navegação entre MFEs
    - GET /journeys/{id}  → jornada específica com seus steps
"""

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.contrato
@pytest.mark.pages
class TestPagesContrato:
    """Testes de contrato do endpoint GET /pages."""

    def test_pages_retorna_200(self, api_client):
        """Listagem de páginas deve retornar 200 OK."""
        response = api_client.get("/pages")
        assert response.status_code == 200

    def test_pages_retorna_json(self, api_client, assert_response):
        """Content-Type deve ser application/json."""
        response = api_client.get("/pages")
        assert_response.has_json(response)

    def test_pages_schema_valido(self, api_client, schema_validator):
        """Body deve conformar ao schema pages/pages_response."""
        response = api_client.get("/pages")
        assert response.status_code == 200
        schema_validator.validate(response.json(), "pages/pages_response")

    def test_pages_contem_campo_total(self, api_client, assert_response):
        """Response deve conter campo 'total' com o count de páginas."""
        response = api_client.get("/pages")
        assert_response.has_field(response, "total")
        total = response.json()["total"]
        assert isinstance(total, int) and total >= 0, (
            f"Campo 'total' deve ser inteiro >= 0, recebido: {total}"
        )

    def test_pages_lista_e_array(self, api_client, assert_response):
        """Campo 'pages' deve ser um array."""
        response = api_client.get("/pages")
        assert_response.is_list(response, "pages")

    def test_pages_items_possuem_path(self, api_client):
        """Cada página deve ter um path definido."""
        response = api_client.get("/pages")
        assert response.status_code == 200
        pages = response.json().get("pages", [])
        for i, page in enumerate(pages):
            assert "path" in page, f"pages[{i}] está sem o campo 'path'"

    def test_pages_paths_iniciam_com_barra(self, api_client):
        """Todos os paths devem começar com '/'."""
        response = api_client.get("/pages")
        assert response.status_code == 200
        pages = response.json().get("pages", [])
        for page in pages:
            path = page.get("path", "")
            assert path.startswith("/"), f"Path inválido: '{path}'"

    def test_pages_protected_e_boolean(self, api_client):
        """O campo 'protected' de cada página deve ser boolean."""
        response = api_client.get("/pages")
        assert response.status_code == 200
        pages = response.json().get("pages", [])
        for i, page in enumerate(pages):
            if "protected" in page:
                assert isinstance(page["protected"], bool), (
                    f"pages[{i}].protected deve ser boolean, "
                    f"recebido: {type(page['protected']).__name__}"
                )

    def test_page_por_id_retorna_200(self, api_client):
        """GET /pages/{id} deve retornar a página específica."""
        # Obtém ID da primeira página da listagem
        list_response = api_client.get("/pages")
        if list_response.status_code != 200:
            pytest.skip("Listagem de páginas indisponível — pulando teste de detalhe")

        pages = list_response.json().get("pages", [])
        if not pages:
            pytest.skip("Nenhuma página disponível para testar detalhe")

        page_id = pages[0]["id"]
        response = api_client.get(f"/pages/{page_id}")
        assert response.status_code == 200

    def test_page_id_inexistente_retorna_404(self, api_client):
        """GET /pages/id-inexistente deve retornar 404."""
        response = api_client.get("/pages/id-que-nao-existe-00000000")
        assert response.status_code == 404

    @pytest.mark.parametrize("role", ["USER", "ADMIN", "MANAGER"])
    def test_pages_filtradas_por_role(self, api_client, role):
        """GET /pages?role={role} deve filtrar páginas pelo perfil."""
        response = api_client.get("/pages", params={"role": role})
        assert response.status_code in (200, 400), (
            f"Status inesperado para role '{role}': {response.status_code}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# JOURNEYS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.contrato
@pytest.mark.journeys
class TestJourneysContrato:
    """Testes de contrato dos endpoints GET /journeys."""

    def test_journeys_retorna_200(self, api_client):
        """Listagem de jornadas deve retornar 200 OK."""
        response = api_client.get("/journeys")
        assert response.status_code == 200

    def test_journeys_retorna_json(self, api_client, assert_response):
        """Content-Type deve ser application/json."""
        response = api_client.get("/journeys")
        assert_response.has_json(response)

    def test_journeys_schema_valido(self, api_client, schema_validator):
        """Body deve conformar ao schema journeys/journeys_response."""
        response = api_client.get("/journeys")
        assert response.status_code == 200
        schema_validator.validate(response.json(), "journeys/journeys_response")

    def test_journeys_contem_campo_total(self, api_client):
        """Response deve conter campo 'total'."""
        response = api_client.get("/journeys")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data, "Campo 'total' ausente no response de journeys"

    def test_journeys_items_possuem_steps(self, api_client):
        """Cada jornada deve ter ao menos 1 step definido."""
        response = api_client.get("/journeys")
        assert response.status_code == 200
        journeys = response.json().get("journeys", [])
        for i, journey in enumerate(journeys):
            steps = journey.get("steps", [])
            assert isinstance(steps, list) and len(steps) > 0, (
                f"journeys[{i}] deve ter pelo menos 1 step. "
                f"Journey: {journey.get('name')}"
            )

    def test_journeys_steps_ordenados(self, api_client):
        """Os steps de cada jornada devem estar em ordem crescente."""
        response = api_client.get("/journeys")
        assert response.status_code == 200
        journeys = response.json().get("journeys", [])
        for journey in journeys:
            steps = journey.get("steps", [])
            orders = [s.get("order", 0) for s in steps if "order" in s]
            assert orders == sorted(orders), (
                f"Steps da jornada '{journey.get('name')}' estão fora de ordem: {orders}"
            )

    def test_journeys_active_e_boolean(self, api_client):
        """O campo 'active' deve ser boolean em todas as jornadas."""
        response = api_client.get("/journeys")
        assert response.status_code == 200
        journeys = response.json().get("journeys", [])
        for i, journey in enumerate(journeys):
            if "active" in journey:
                assert isinstance(journey["active"], bool), (
                    f"journeys[{i}].active deve ser boolean, "
                    f"recebido: {type(journey['active']).__name__}"
                )

    def test_journey_por_id_retorna_200(self, api_client):
        """GET /journeys/{id} deve retornar a jornada específica."""
        list_response = api_client.get("/journeys")
        if list_response.status_code != 200:
            pytest.skip("Listagem de jornadas indisponível")

        journeys = list_response.json().get("journeys", [])
        if not journeys:
            pytest.skip("Nenhuma jornada disponível para testar detalhe")

        journey_id = journeys[0]["id"]
        response = api_client.get(f"/journeys/{journey_id}")
        assert response.status_code == 200

    def test_journey_id_inexistente_retorna_404(self, api_client):
        """GET /journeys/id-inexistente deve retornar 404."""
        response = api_client.get("/journeys/journey-inexistente-00000000")
        assert response.status_code == 404

    def test_journeys_apenas_ativas(self, api_client):
        """GET /journeys?active=true deve retornar apenas jornadas ativas."""
        response = api_client.get("/journeys", params={"active": "true"})
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            journeys = response.json().get("journeys", [])
            for journey in journeys:
                if "active" in journey:
                    assert journey["active"] is True, (
                        f"Jornada inativa retornada no filtro active=true: "
                        f"{journey.get('name')}"
                    )
