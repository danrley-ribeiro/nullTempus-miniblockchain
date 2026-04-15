import os
import json
import base64
import hmac
import hashlib
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from services.time_bound_key_service import obter_tbk_para_cifra, obter_candidatos_tbk, derivar_tbk
from cryptography.exceptions import InvalidTag

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32

def derivar_chave(senha: str, sal: bytes) -> bytes:
    kdf = Scrypt(salt=sal, length=SCRYPT_DKLEN, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, backend=default_backend())
    return kdf.derive(senha.encode("utf-8"))

def verificar_senha(senha_entrada: str, sal: bytes, verificador_armazenado: bytes) -> bool:
    derivada = derivar_chave(senha_entrada, sal)
    return hmac.compare_digest(derivada, verificador_armazenado)

def construir_aad(indice: int, proprietario: str, carimbo_tempo: str, tipo_dado: str, expira_em: str) -> bytes:
    dict_aad = {"indice": indice, "proprietario": proprietario, "carimbo_tempo": carimbo_tempo, "tipo_dado": tipo_dado, "expira_em": expira_em}
    return json.dumps(dict_aad, sort_keys=True).encode("utf-8")

def computar_hmac_bloco(dict_bloco: dict, chave_hmac: bytes) -> str:
    carga_util = json.dumps({k: v for k, v in sorted(dict_bloco.items()) if k != "hmac_bloco"}, sort_keys=True).encode("utf-8")
    mac = hmac.new(chave_hmac, carga_util, hashlib.sha3_256)
    return mac.hexdigest()

def verificar_hmac_bloco(dict_bloco: dict, chave_hmac: bytes) -> bool:
    esperado = dict_bloco.get("hmac_bloco", "")
    computado = computar_hmac_bloco(dict_bloco, chave_hmac)
    return hmac.compare_digest(esperado, computado)

def computar_hash_bloco(dict_bloco: dict) -> str:
    carga_util = {k: v for k, v in dict_bloco.items() if k not in ("hash_bloco", "hmac_bloco")}
    serializado = json.dumps(carga_util, sort_keys=True).encode("utf-8")
    return hashlib.sha3_256(serializado).hexdigest()

def derivar_subchaves(chave_sessao: bytes, tipo_dado: str = "padrao") -> tuple[bytes, bytes]:
    def hkdf_expandir(rotulo: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA3_256(), length=32, salt=None, info=rotulo, backend=default_backend()).derive(chave_sessao)
    return hkdf_expandir(f"null-tempus-enc-{tipo_dado}".encode('utf-8')), hkdf_expandir(f"null-tempus-mac-{tipo_dado}".encode('utf-8'))

def cifrar_bloco_com_tbk(texto_claro: str, chave_sessao: bytes, nome_usuario: str, indice_bloco: int, carimbo_tempo: str, tipo_dado: str = "padrao", expira_em: str = "") -> dict:
    chave_enc, chave_mac = derivar_subchaves(chave_sessao, tipo_dado)
    tbk, slot = obter_tbk_para_cifra(chave_enc, nome_usuario)
    iv = os.urandom(12)
    aad = construir_aad(indice_bloco, nome_usuario, carimbo_tempo, tipo_dado, expira_em)
    aesgcm = AESGCM(tbk)
    texto_cifrado_tag = aesgcm.encrypt(iv, texto_claro.encode("utf-8"), aad)
    return {
        "texto_cifrado": base64.b64encode(texto_cifrado_tag).decode(),
        "iv": iv.hex(),
        "aad": base64.b64encode(aad).decode(),
        "slot_tbk": slot,
        "chave_mac": chave_mac,
        "tipo_dado": tipo_dado,
        "expira_em": expira_em
    }

def decifrar_bloco_com_tbk(bloco: dict, chave_sessao: bytes, nome_usuario: str) -> str:
    from datetime import datetime, timezone
    
    expira = bloco.get("expira_em", "")
    if expira:
        dt_expira = datetime.fromisoformat(expira)
        if datetime.now(timezone.utc) > dt_expira:
            raise ValueError("O bloco expirou e não pode mais ser lido.")
            
    tipo_dado = bloco.get("tipo_dado", "padrao")
    chave_enc, _ = derivar_subchaves(chave_sessao, tipo_dado)
    texto_cifrado_tag = base64.b64decode(bloco["texto_cifrado"])
    iv = bytes.fromhex(bloco["iv"])
    aad = base64.b64decode(bloco["aad"])
    slot_armazenado = bloco["slot_tbk"]
    
    tbk = derivar_tbk(chave_enc, slot_armazenado, nome_usuario)
    aesgcm = AESGCM(tbk)
    try:
        return aesgcm.decrypt(iv, texto_cifrado_tag, aad).decode("utf-8")
    except InvalidTag:
        pass
    
    candidatos = obter_candidatos_tbk(chave_enc, nome_usuario, bloco["carimbo_tempo"])
    for candidato_tbk in candidatos:
        try:
            aesgcm = AESGCM(candidato_tbk)
            return aesgcm.decrypt(iv, texto_cifrado_tag, aad).decode("utf-8")
        except InvalidTag:
            continue
    raise ValueError("Falha na decifragem: bloco adulterado, chave TBK errada, ou sessão inválida.")
