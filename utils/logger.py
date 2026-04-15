import os
from datetime import datetime, timezone

ARQUIVO_LOG = os.path.join("data", "security.log")

def registrar_evento(tipo_evento: str, nome_usuario: str, descricao: str):
    os.makedirs("data", exist_ok=True)
    carimbo_tempo = datetime.now(timezone.utc).isoformat()
    linha_log = f"[{carimbo_tempo}] [{tipo_evento}] Usuario: {nome_usuario} - {descricao}\n"
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linha_log)
