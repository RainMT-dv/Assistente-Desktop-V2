"""Utilitario de logging padronizado com timestamp para Assistente V2."""

import logging
import sys
from datetime import datetime


class TimestampFormatter(logging.Formatter):
    """Formatter que adiciona timestamp em todos os logs."""

    def format(self, record):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.') + f'{datetime.now().microsecond // 1000:03d}'

        # Manter o level name se existir (INFO, WARNING, ERROR)
        if hasattr(record, 'levelname'):
            prefix = f'[{timestamp}] [{record.levelname}]'
        else:
            prefix = f'[{timestamp}]'

        # Se a mensagem ja tiver proprio tag como [PATIENCE], [SKILL], etc, preservar
        message = record.getMessage()

        return f'{prefix} {message}'


def setup_logger(name: str = 'Assistente') -> logging.Logger:
    """Cria logger com timestamp padrao."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(TimestampFormatter())

    # Evitar duplicados
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


def log(tag: str, message: str):
    """Funcao rapida para log customizado com tag."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.') + f'{datetime.now().microsecond // 1000:03d}'
    print(f'[{timestamp}] [{tag}] {message}')
