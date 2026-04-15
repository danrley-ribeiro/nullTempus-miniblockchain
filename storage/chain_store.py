import json
import os
from models.block import Bloco

ARQUIVO_CADEIA = os.path.join("data", "blockchain.json")

def carregar_cadeia() -> list[Bloco]:
    if not os.path.exists(ARQUIVO_CADEIA):
        return []
    with open(ARQUIVO_CADEIA, "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
            return [Bloco(**dados_bloco) for dados_bloco in dados]
        except json.JSONDecodeError:
            return []

def salvar_cadeia(cadeia: list[Bloco]) -> None:
    os.makedirs("data", exist_ok=True)
    with open(ARQUIVO_CADEIA, "w", encoding="utf-8") as f:
        dados = [bloco.__dict__ for bloco in cadeia]
        json.dump(dados, f, indent=4)
