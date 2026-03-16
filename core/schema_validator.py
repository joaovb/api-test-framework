"""
schema_validator.py
-------------------
Valida responses JSON contra schemas pré-definidos em /schemas/.
Usa jsonschema para validação e Pydantic para parsing tipado.

Uso:
    from core.schema_validator import SchemaValidator
    validator = SchemaValidator()

    # Valida response contra arquivo de schema
    validator.validate(response.json(), "manifest/manifest_response")

    # Valida campo específico
    validator.validate_field(response.json(), "mfes", expected_type=list)
"""

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import ValidationError as JsonSchemaValidationError

logger = logging.getLogger(__name__)

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


class SchemaValidationError(Exception):
    """Erro de validação de schema — contém detalhes do campo inválido."""
    pass


class SchemaValidator:
    """
    Validador de contratos de API baseado em JSON Schema.

    Os schemas ficam em /schemas/<dominio>/<nome>.json.
    O framework carrega e cacheia os schemas automaticamente.
    """

    def __init__(self):
        self._cache: dict[str, dict] = {}

    def _load_schema(self, schema_path: str) -> dict:
        """
        Carrega schema do disco com cache em memória.

        Args:
            schema_path: Caminho relativo a /schemas/ sem extensão.
                         Ex: "manifest/manifest_response"
        """
        if schema_path in self._cache:
            return self._cache[schema_path]

        full_path = SCHEMAS_DIR / f"{schema_path}.json"
        if not full_path.exists():
            raise FileNotFoundError(
                f"Schema não encontrado: {full_path}\n"
                f"Crie o arquivo em schemas/{schema_path}.json"
            )

        with open(full_path, encoding="utf-8") as f:
            schema = json.load(f)

        self._cache[schema_path] = schema
        logger.debug(f"Schema carregado: {schema_path}")
        return schema

    def validate(self, data: Any, schema_path: str) -> None:
        """
        Valida dados contra um schema JSON.

        Args:
            data:        Dados a validar (geralmente response.json())
            schema_path: Caminho relativo ao schema (ex: "manifest/manifest_response")

        Raises:
            SchemaValidationError: Se os dados não conformam ao schema.
        """
        schema = self._load_schema(schema_path)
        try:
            jsonschema.validate(instance=data, schema=schema)
            logger.debug(f"Validação de schema OK: {schema_path}")
        except JsonSchemaValidationError as e:
            raise SchemaValidationError(
                f"Falha na validação do schema '{schema_path}':\n"
                f"  Campo: {' → '.join(str(p) for p in e.absolute_path) or 'raiz'}\n"
                f"  Erro:  {e.message}\n"
                f"  Valor recebido: {e.instance}"
            ) from e

    def validate_field(
        self,
        data: dict,
        field: str,
        expected_type: type | None = None,
        required: bool = True,
    ) -> Any:
        """
        Valida e retorna um campo específico do response.

        Args:
            data:          Dicionário do response
            field:         Nome do campo (suporte a notação de ponto: "mfe.name")
            expected_type: Tipo esperado (str, int, list, dict, bool)
            required:      Se True, falha caso o campo esteja ausente

        Returns:
            Valor do campo validado.
        """
        keys = field.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                if required:
                    raise SchemaValidationError(
                        f"Campo obrigatório ausente no response: '{field}'"
                    )
                return None

        if expected_type and not isinstance(value, expected_type):
            raise SchemaValidationError(
                f"Campo '{field}' — tipo esperado: {expected_type.__name__}, "
                f"recebido: {type(value).__name__} (valor: {value!r})"
            )

        return value

    def assert_has_fields(self, data: dict, fields: list[str]) -> None:
        """
        Verifica que todos os campos da lista estão presentes no response.

        Args:
            data:   Dicionário do response
            fields: Lista de campos obrigatórios (suporte a notação de ponto)
        """
        missing = []
        for field in fields:
            try:
                self.validate_field(data, field, required=True)
            except SchemaValidationError:
                missing.append(field)

        if missing:
            raise SchemaValidationError(
                f"Campos obrigatórios ausentes no response: {missing}"
            )
