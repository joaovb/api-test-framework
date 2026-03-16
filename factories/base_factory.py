"""
base_factory.py
---------------
Factory base com utilitários compartilhados por todas as factories do domínio.
Fornece instância configurada do Faker e helpers reutilizáveis.

Uso:
    from factories.base_factory import BaseFactory
    class MinhaFactory(BaseFactory):
        def build(self): ...
"""

from faker import Faker

# Faker configurado para pt_BR — nomes, CPFs e dados brasileiros realistas
fake = Faker("pt_BR")
Faker.seed(0)   # Seed fixo para reprodutibilidade quando necessário


class BaseFactory:
    """
    Classe base para todas as factories de dados de teste.

    Convenção:
    - build()      → retorna dicionário com dados válidos (padrão)
    - build_list() → retorna lista de N registros
    - invalid()    → retorna dicionário com dados inválidos (para testes negativos)
    """

    @classmethod
    def build(cls) -> dict:
        raise NotImplementedError("Implemente build() na factory concreta.")

    @classmethod
    def build_list(cls, count: int = 3) -> list[dict]:
        """Retorna lista de N instâncias com dados únicos."""
        return [cls.build() for _ in range(count)]

    @classmethod
    def invalid(cls) -> dict:
        """Retorna dados inválidos para testes negativos. Sobrescreva se necessário."""
        return {}

    @staticmethod
    def random_uuid() -> str:
        return str(fake.uuid4())

    @staticmethod
    def random_string(length: int = 10) -> str:
        return fake.lexify("?" * length).lower()

    @staticmethod
    def random_slug() -> str:
        return fake.slug()
