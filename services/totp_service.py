"""
Serviço TOTP (RFC-6238) e proteção do segredo TOTP em repouso.

Funções:
- gerar_segredo_totp(): cria um segredo Base32 aleatório.
- obter_uri_totp(segredo, nome_usuario, nome_emissor): monta a URI otpauth:// padrão.
- gerar_qr_code(uri, nome_arquivo): salva a URI como imagem PNG.
- imprimir_qr_code_no_console(uri): renderiza o QR Code em ASCII no terminal.
- verificar_totp(segredo, codigo): valida o código de 6 dígitos contra o slot atual.
- cifrar_segredo_totp(segredo, chave_derivada) / decifrar_segredo_totp(...): protege o
  segredo TOTP em repouso usando AES-GCM com a chave derivada da senha.
"""

import pyotp
import qrcode
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Tuple

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

def cifrar_segredo_totp(segredo: str, chave_derivada: bytes) -> Tuple[str, str]:
    aesgcm = AESGCM(chave_derivada)
    iv = os.urandom(12)
    texto_cifrado = aesgcm.encrypt(iv, segredo.encode('utf-8'), None)
    return base64.b64encode(texto_cifrado).decode('utf-8'), iv.hex()

def decifrar_segredo_totp(segredo_cifrado: str, iv_hex: str, chave_derivada: bytes) -> str:
    aesgcm = AESGCM(chave_derivada)
    iv = bytes.fromhex(iv_hex)
    texto_cifrado = base64.b64decode(segredo_cifrado)
    return aesgcm.decrypt(iv, texto_cifrado, None).decode('utf-8')
