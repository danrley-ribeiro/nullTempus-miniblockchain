import os
from cryptography.hazmat.primitives.keywrap import aes_key_wrap, aes_key_unwrap
from cryptography.hazmat.backends import default_backend

def gerar_e_envelopar_chave_mestre(chave_derivada: bytes) -> tuple[bytes, str]:
    chave_mestre = os.urandom(32)
    envelopado = aes_key_wrap(chave_derivada, chave_mestre, default_backend())
    return chave_mestre, envelopado.hex()

def desenvelopar_chave_mestre(chave_derivada: bytes, hex_envelopado: str) -> bytes:
    try:
        bytes_envelopados = bytes.fromhex(hex_envelopado)
        return aes_key_unwrap(chave_derivada, bytes_envelopados, default_backend())
    except Exception as e:
        raise ValueError(f"Falha de Integridade: Não foi possível reabrir o cofre da Master Key com esta senha. DETALHE REAL: {str(e)}")

def criar_sessao(chave_mestre: bytes) -> dict:
    return {
        "chave_sessao": chave_mestre
    }

def destruir_sessao(sessao: dict) -> None:
    for chave in ["chave_sessao", "chave_sessao_envelopada"]:
        if sessao.get(chave) and isinstance(sessao[chave], bytearray):
            for i in range(len(sessao[chave])):
                sessao[chave][i] = 0
            
    sessao.clear()
