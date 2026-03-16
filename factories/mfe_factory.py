"""
mfe_factory.py
--------------
Factory de dados para Micro Frontends (MFEs).
Gera payloads realistas do domínio de MFEs, rotas e recursos da Jornada do Futuro.

Uso:
    from factories.mfe_factory import MfeFactory, ManifestFactory, JourneyFactory

    mfe = MfeFactory.build()
    manifest = ManifestFactory.build()
    journey = JourneyFactory.build()
"""

import random
from factories.base_factory import BaseFactory, fake


# ── Constantes do domínio ─────────────────────────────────────────────────────

MFE_NAMES = [
    "home", "dashboard", "extrato", "investimentos",
    "seguros", "cartao", "pix", "emprestimos",
    "perfil", "notificacoes", "ajuda", "onboarding",
]

JOURNEY_NAMES = [
    "abertura-conta", "contratacao-seguro", "solicitacao-emprestimo",
    "investimento-renda-fixa", "portabilidade", "cadastro-pix",
    "desbloqueio-cartao", "ativacao-digital",
]

ROLES = ["USER", "ADMIN", "MANAGER", "READONLY", "SUPPORT"]

HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

ENVIRONMENTS = ["dev", "staging", "prod"]


# ── MfeFactory ────────────────────────────────────────────────────────────────

class MfeFactory(BaseFactory):
    """Factory para registros de Micro Frontend individual."""

    @classmethod
    def build(
        cls,
        name: str | None = None,
        active: bool = True,
        roles: list[str] | None = None,
    ) -> dict:
        """
        Constrói um MFE com dados válidos.

        Args:
            name:   Nome do MFE (aleatório se None)
            active: Status ativo/inativo
            roles:  Papéis com acesso (aleatório se None)
        """
        mfe_name = name or random.choice(MFE_NAMES)
        return {
            "id": cls.random_uuid(),
            "name": mfe_name,
            "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.0",
            "bundle_url": f"https://cdn.jornada-futuro.itau.com.br/mfes/{mfe_name}/remoteEntry.js",
            "scope": f"mfe_{mfe_name}",
            "module": f"./App",
            "active": active,
            "roles": roles or random.sample(ROLES, k=random.randint(1, 3)),
            "metadata": {
                "description": fake.sentence(nb_words=6),
                "owner_team": fake.company(),
                "updated_at": fake.iso8601(),
            },
        }

    @classmethod
    def inactive(cls, **kwargs) -> dict:
        """Constrói um MFE inativo."""
        return cls.build(active=False, **kwargs)

    @classmethod
    def invalid(cls) -> dict:
        """Dados inválidos — campos obrigatórios ausentes."""
        return {
            "name": "",           # nome vazio
            "bundle_url": "nao-e-uma-url",  # URL inválida
            "active": "sim",      # tipo errado (deveria ser bool)
        }


# ── RouteFactory ──────────────────────────────────────────────────────────────

class RouteFactory(BaseFactory):
    """Factory para rotas de página associadas a MFEs."""

    @classmethod
    def build(
        cls,
        path: str | None = None,
        mfe_name: str | None = None,
        protected: bool = True,
    ) -> dict:
        """
        Constrói uma rota com dados válidos.

        Args:
            path:      Caminho da rota (aleatório se None)
            mfe_name:  Nome do MFE associado
            protected: Se a rota requer autenticação
        """
        slug = cls.random_slug()
        mfe = mfe_name or random.choice(MFE_NAMES)
        return {
            "id": cls.random_uuid(),
            "path": path or f"/{slug}",
            "page_title": fake.catch_phrase(),
            "mfe": mfe,
            "protected": protected,
            "roles": random.sample(ROLES, k=random.randint(1, 2)),
            "breadcrumb": [
                {"label": "Início", "path": "/"},
                {"label": fake.word().capitalize(), "path": f"/{slug}"},
            ],
            "metadata": {
                "analytics_id": cls.random_string(8),
                "cache_ttl": random.choice([0, 60, 300, 3600]),
            },
        }

    @classmethod
    def public(cls, **kwargs) -> dict:
        """Constrói uma rota pública (sem proteção de auth)."""
        return cls.build(protected=False, **kwargs)

    @classmethod
    def invalid(cls) -> dict:
        return {
            "path": "sem-barra-inicial",   # path inválido
            "mfe": None,                   # campo obrigatório nulo
            "protected": "true",           # tipo errado
        }


# ── ManifestFactory ───────────────────────────────────────────────────────────

class ManifestFactory(BaseFactory):
    """Factory para o manifest completo da plataforma."""

    @classmethod
    def build(
        cls,
        mfe_count: int = 3,
        route_count: int = 5,
    ) -> dict:
        """
        Constrói um manifest completo com MFEs e rotas.

        Args:
            mfe_count:   Número de MFEs no manifest
            route_count: Número de rotas no manifest
        """
        mfes = MfeFactory.build_list(mfe_count)
        routes = RouteFactory.build_list(route_count)

        return {
            "version": f"v{random.randint(1, 3)}.{random.randint(0, 10)}.0",
            "generated_at": fake.iso8601(),
            "environment": random.choice(ENVIRONMENTS),
            "mfes": mfes,
            "routes": routes,
            "metadata": {
                "total_mfes": len(mfes),
                "total_routes": len(routes),
                "platform": "Jornada do Futuro",
            },
        }

    @classmethod
    def invalid(cls) -> dict:
        return {
            "version": None,    # obrigatório
            "mfes": "nao-e-lista",  # tipo errado
            "routes": [],
        }


# ── JourneyFactory ────────────────────────────────────────────────────────────

class JourneyFactory(BaseFactory):
    """Factory para dados de jornadas de navegação entre MFEs."""

    @classmethod
    def build(
        cls,
        name: str | None = None,
        step_count: int = 3,
    ) -> dict:
        """
        Constrói uma jornada com steps sequenciais.

        Args:
            name:       Nome da jornada (aleatório se None)
            step_count: Número de steps na jornada
        """
        journey_name = name or random.choice(JOURNEY_NAMES)
        steps = [
            {
                "order": i + 1,
                "id": cls.random_uuid(),
                "mfe": random.choice(MFE_NAMES),
                "route": f"/jornada/{journey_name}/step-{i + 1}",
                "label": fake.catch_phrase(),
                "required": random.choice([True, False]),
            }
            for i in range(step_count)
        ]
        return {
            "id": cls.random_uuid(),
            "name": journey_name,
            "display_name": journey_name.replace("-", " ").title(),
            "description": fake.sentence(nb_words=10),
            "active": True,
            "roles": random.sample(ROLES, k=random.randint(1, 3)),
            "steps": steps,
            "total_steps": step_count,
            "created_at": fake.iso8601(),
        }

    @classmethod
    def invalid(cls) -> dict:
        return {
            "name": 12345,       # tipo errado
            "steps": None,       # obrigatório
            "active": "ativo",   # tipo errado
        }


# ── PermissionFactory ─────────────────────────────────────────────────────────

class PermissionFactory(BaseFactory):
    """Factory para dados de permissões e roles de usuário."""

    @classmethod
    def build(
        cls,
        role: str | None = None,
        resource: str | None = None,
    ) -> dict:
        return {
            "id": cls.random_uuid(),
            "role": role or random.choice(ROLES),
            "resource": resource or random.choice(MFE_NAMES),
            "actions": random.sample(HTTP_METHODS, k=random.randint(1, 3)),
            "active": True,
        }
