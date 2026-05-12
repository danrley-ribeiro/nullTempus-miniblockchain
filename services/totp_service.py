"""
Serviço TOTP (RFC-6238) e proteção do segredo TOTP em repouso.

Funções:
- gerar_segredo_totp(): cria um segredo Base32 aleatório.
- obter_uri_totp(segredo, nome_usuario, nome_emissor): monta a URI otpauth:// padrão.
- gerar_qr_code(uri, nome_arquivo): salva a URI como imagem PNG.
- imprimir_qr_code_no_console(uri): renderiza o QR Code em ASCII no terminal.
- verificar_totp(segredo, codigo): valida o código de 6 dígitos contra o slot atual.
- cifrar_segredo_totp(segredo, chave_derivada) / decifrar_segredo_totp(...): protege o
  segredo TOTP em repouso usando AES-GCM com a chave derivada da senha. O IV é
  derivado deterministicamente da própria chave via HKDF-SHA3-256, evitando armazenar
  um nonce separado (seguro aqui porque cada usuário tem sal único → chave única e
  apenas um segredo TOTP é cifrado por chave).
"""

import pyotp
import qrcode
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def gerar_segredo_totp() -> str:
    return pyotp.random_base32()

def obter_uri_totp(segredo: str, nome_usuario: str, nome_emissor: str = "nullTempus") -> str:
    return pyotp.totp.TOTP(segredo).provisioning_uri(name=nome_usuario, issuer_name=nome_emissor)

def gerar_qr_code(uri: str, nome_arquivo: str) -> None:
    img = qrcode.make(uri)
    img.save(nome_arquivo)

def imprimir_qr_code_no_console(uri: str) -> None:
    qr = qrcode.QRCode()
    qr.add_data(uri)
    qr.make(fit=True)
    print("")
    qr.print_ascii(invert=True)
    print("")

def verificar_totp(segredo: str, codigo: str) -> bool:
    totp = pyotp.TOTP(segredo)
    return totp.verify(codigo)

def _derivar_iv_totp(chave_derivada: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA3_256(),
        length=12,
        salt=None,
        info=b"null-tempus-totp-iv",
        backend=default_backend(),
    ).derive(chave_derivada)

def cifrar_segredo_totp(segredo: str, chave_derivada: bytes) -> str:
    aesgcm = AESGCM(chave_derivada)
    iv = _derivar_iv_totp(chave_derivada)
    texto_cifrado = aesgcm.encrypt(iv, segredo.encode('utf-8'), None)
    return base64.b64encode(texto_cifrado).decode('utf-8')

def decifrar_segredo_totp(segredo_cifrado: str, chave_derivada: bytes) -> str:
    aesgcm = AESGCM(chave_derivada)
    iv = _derivar_iv_totp(chave_derivada)
    texto_cifrado = base64.b64decode(segredo_cifrado)
    return aesgcm.decrypt(iv, texto_cifrado, None).decode('utf-8')
