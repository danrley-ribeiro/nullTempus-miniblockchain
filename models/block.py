from dataclasses import dataclass

@dataclass
class Bloco:
    indice: int
    proprietario: str
    carimbo_tempo: str       # ISO 8601 UTC
    tipo_dado: str           # Extra: Múltiplas chaves
    expira_em: str           # Extra: Expiração temporal
    texto_cifrado: str       # base64 — AES-GCM(TBK, plaintext) || tag
    iv: str                  # hex — 12 bytes únicos
    aad: str                 # base64 — contexto em claro
    slot_tbk: int            # slot TBK — necessário para reconstituir a TBK
    hash_anterior: str       # SHA3-256 hex
    hash_bloco: str          # SHA3-256 hex
    hmac_bloco: str          # HMAC-SHA3-256
