"""
Modelo de Usuário persistido no banco.

Classe:
- Usuario: dataclass com sal, verificador de senha (Scrypt), segredo TOTP cifrado,
  controle de tentativas/bloqueio e a chave mestre envelopada (AES Key Wrap).
"""

from dataclasses import dataclass

@dataclass
class Usuario:
    nome_usuario: str
    sal: str                  # hex, 32 bytes (armazenado em claro)
    verificador_senha: str    # Hash bruto gerado pelo Scrypt
    chave_totp_cifrada: str   # base64 (cifrado; IV derivado da chave via HKDF)
    tentativas_falhas: int    # contador
    bloqueado_ate: str        # ISO timestamp ou string vazia
    chave_mestre_enc: str     # hex, Wrapped DEK (Master Key envelopada pela KEK)
