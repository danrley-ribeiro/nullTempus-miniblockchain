"""
Logger simples de eventos de segurança em data/security.log.

Funções:
- registrar_evento(tipo_evento, nome_usuario, descricao): grava uma linha com timestamp UTC,
  tipo (LOGIN_FAILED, TAMPERING_DETECTED, BLOCK_ADDED etc.), usuário e descrição.
"""

import os
from datetime import datetime, timezone

ARQUIVO_LOG = os.path.join("data", "security.log")

def registrar_evento(tipo_evento: str, nome_usuario: str, descricao: str):
    os.makedirs("data", exist_ok=True)
    carimbo_tempo = datetime.now(timezone.utc).isoformat()
    linha_log = f"[{carimbo_tempo}] [{tipo_evento}] Usuario: {nome_usuario} - {descricao}\n"
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linha_log)
