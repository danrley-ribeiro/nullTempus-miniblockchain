"""
Configuração global da bateria de testes.

- Força o modo LOCAL_DB (JSON em data/) antes de qualquer import do projeto.
- Para cada teste, troca o diretório de trabalho por um tmp_path isolado para
  que data/blockchain.json, data/users.json e data/security.log sejam
  totalmente independentes entre testes.
"""

import os
import sys
import pytest

os.environ["LOCAL_DB"] = "true"
os.environ.pop("MONGO_URI", None)

RAIZ_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, RAIZ_PROJETO)


@pytest.fixture(autouse=True)
def diretorio_isolado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(exist_ok=True)
    yield tmp_path


@pytest.fixture
def codigo_totp():
    import pyotp

    def _gerar(segredo: str) -> str:
        return pyotp.TOTP(segredo).now()

    return _gerar


@pytest.fixture
def usuario_registrado(codigo_totp):
    from controllers.auth_controller import registrar_usuario, logar_usuario

    nome = "alice"
    senha = "senha-forte-1"
    segredo = registrar_usuario(nome, senha)
    sessao = logar_usuario(nome, senha, codigo_totp(segredo))
    return {
        "nome": nome,
        "senha": senha,
        "segredo": segredo,
        "sessao": sessao,
    }
