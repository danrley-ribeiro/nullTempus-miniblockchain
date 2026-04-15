from dataclasses import dataclass

@dataclass
class Usuario:
    nome_usuario: str
    sal: str                  # hex, 32 bytes (armazenado em claro)
    verificador_senha: str    # Hash bruto gerado pelo Scrypt
    chave_totp_cifrada: str   # base64 (cifrado)
    iv_totp: str              # hex (cifrado associado)
    tentativas_falhas: int    # contador
    bloqueado_ate: str        # ISO timestamp ou string vazia
    chave_mestre_enc: str     # hex, Wrapped DEK (Master Key envelopada pela KEK)
