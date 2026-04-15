import time
import math
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

JANELAS_TBK_SEGUNDOS = 30
SLOTS_TOLERANCIA_TBK = 1

def _slot_atual(janela: int = JANELAS_TBK_SEGUNDOS) -> int:
    return math.floor(time.time() / janela)

def slot_por_timestamp(iso_timestamp: str, janela: int = JANELAS_TBK_SEGUNDOS) -> int:
    from datetime import datetime, timezone
    dt = datetime.fromisoformat(iso_timestamp)
    unix = dt.replace(tzinfo=timezone.utc).timestamp()
    return math.floor(unix / janela)

def derivar_tbk(chave_sessao: bytes, slot: int, nome_usuario: str, janela: int = JANELAS_TBK_SEGUNDOS) -> bytes:
    info = f"tbk:v1:{janela}:{slot}".encode("utf-8")
    sal = nome_usuario.encode("utf-8")
    tbk = HKDF(
        algorithm=hashes.SHA3_256(),
        length=32,
        salt=sal,
        info=info,
        backend=default_backend()
    ).derive(chave_sessao)
    return tbk

def obter_tbk_para_cifra(chave_sessao: bytes, nome_usuario: str) -> tuple[bytes, int]:
    slot = _slot_atual()
    tbk = derivar_tbk(chave_sessao, slot, nome_usuario)
    return tbk, slot

def obter_tbk_para_decifra(chave_sessao: bytes, nome_usuario: str, carimbo_tempo_bloco: str) -> bytes:
    slot_alvo = slot_por_timestamp(carimbo_tempo_bloco)
    return derivar_tbk(chave_sessao, slot_alvo, nome_usuario)

def obter_candidatos_tbk(chave_sessao: bytes, nome_usuario: str, carimbo_tempo_bloco: str) -> list[bytes]:
    slot_alvo = slot_por_timestamp(carimbo_tempo_bloco)
    candidatos = []
    for delta in range(-SLOTS_TOLERANCIA_TBK, SLOTS_TOLERANCIA_TBK + 1):
        candidatos.append(derivar_tbk(chave_sessao, slot_alvo + delta, nome_usuario))
    return candidatos
