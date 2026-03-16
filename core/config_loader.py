"""
config_loader.py
----------------
Carrega e mescla configurações YAML por ambiente.
O ambiente é definido pela variável de ambiente ENV (padrão: dev).

Uso:
    from core.config_loader import get_config
    config = get_config()
    base_url = config["api"]["base_url"]
"""

import os
import re
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _resolve_env_vars(value: Any) -> Any:
    """Substitui placeholders ${VAR_NAME} pelo valor real da variável de ambiente."""
    if isinstance(value, str):
        pattern = re.compile(r"\$\{(\w+)\}")
        def replacer(match):
            env_var = match.group(1)
            resolved = os.environ.get(env_var, "")
            if not resolved:
                logger.warning(f"Variável de ambiente não definida: {env_var}")
            return resolved
        return pattern.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(i) for i in value]
    return value


def _deep_merge(base: dict, override: dict) -> dict:
    """Mescla dois dicionários recursivamente. Override tem prioridade."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict:
    """Carrega um arquivo YAML e retorna como dicionário."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_config() -> dict:
    """
    Retorna configuração completa para o ambiente ativo.
    Mescla base.yaml com o YAML do ambiente, depois resolve variáveis de ambiente.

    A configuração é cacheada após a primeira chamada — use reset_config() em testes
    que precisem de ambientes diferentes.
    """
    env = os.environ.get("ENV", "dev").lower()
    logger.info(f"Carregando configuração para ambiente: {env}")

    base_config = _load_yaml(CONFIG_DIR / "base.yaml")
    env_config = _load_yaml(CONFIG_DIR / f"{env}.yaml")

    merged = _deep_merge(base_config, env_config)
    resolved = _resolve_env_vars(merged)

    resolved["_env"] = env
    return resolved


def reset_config() -> None:
    """Limpa o cache da configuração. Útil em testes de múltiplos ambientes."""
    get_config.cache_clear()
