"""
logger.py
---------
Logger estruturado do framework. Suporta formato JSON (pipeline) e texto (dev).
Configurado uma única vez via setup_logging() — chamado automaticamente pelo conftest.

Uso:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Enviando request", extra={"url": url, "method": "GET"})
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formata log entries como JSON — ideal para pipelines e observabilidade."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Inclui campos extras passados via extra={}
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "id", "levelname", "levelno",
                "lineno", "module", "msecs", "message", "msg", "name",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName",
            ):
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Formata log entries como texto legível — ideal para desenvolvimento local."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Verde
        "WARNING": "\033[33m",  # Amarelo
        "ERROR": "\033[31m",    # Vermelho
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{color}[{timestamp}] [{record.levelname:<8}] "
            f"{record.name} — {record.getMessage()}{reset}"
        )


def setup_logging(level: str = "INFO", fmt: str = "text") -> None:
    """
    Configura o sistema de logging do framework.
    Chamado uma vez no conftest.py raiz.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        fmt:   Formato de saída — "json" para pipelines, "text" para dev
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove handlers existentes para evitar duplicação
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    if fmt.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger nomeado para o módulo.

    Uso:
        logger = get_logger(__name__)
        logger.info("Mensagem")
    """
    return logging.getLogger(name)
