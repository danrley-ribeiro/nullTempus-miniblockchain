import json
import os
from models.user import Usuario

ARQUIVO_USUARIOS = os.path.join("data", "usuarios.json")

def carregar_usuarios() -> dict[str, Usuario]:
    if not os.path.exists(ARQUIVO_USUARIOS):
        return {}
    with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
            return {
                nome_usuario: Usuario(**dados_usuario) 
                for nome_usuario, dados_usuario in dados.items()
            }
        except json.JSONDecodeError:
            return {}

def salvar_usuarios(usuarios: dict[str, Usuario]) -> None:
    os.makedirs("data", exist_ok=True)
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        dados = {
            nome_usuario: usuario.__dict__
            for nome_usuario, usuario in usuarios.items()
        }
        json.dump(dados, f, indent=4)
