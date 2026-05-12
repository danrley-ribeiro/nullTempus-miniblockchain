"""
Testes do Explorador da Blockchain e do fluxo de registro de valores em blocos.
"""

import pytest


def test_genesis_e_criado_automaticamente_na_primeira_leitura(usuario_registrado):
    from controllers.blockchain_controller import ler_blockchain

    sessao = usuario_registrado["sessao"]
    print("\n[GENESIS] Lendo blockchain recem criada")
    resultado = ler_blockchain(sessao["chave_sessao"], usuario_registrado["nome"])
    print(f"  -> blocos retornados: {len(resultado)}")
    print(f"  -> bloco[0]: indice={resultado[0]['indice']} status={resultado[0]['status']}")
    print(f"  -> hash_anterior do genesis: {resultado[0]['hash_anterior']}")
    print(f"  -> hash_bloco do genesis: {resultado[0]['hash_bloco'][:32]}...")

    assert len(resultado) == 1
    assert resultado[0]["indice"] == 0
    assert resultado[0]["status"] == "Genesis"
    assert resultado[0]["hash_anterior"] == "0" * 64


def test_adicionar_bloco_e_recuperar_conteudo(usuario_registrado):
    from controllers.blockchain_controller import adicionar_bloco, ler_blockchain

    sessao = usuario_registrado["sessao"]
    nome = usuario_registrado["nome"]
    conteudo = "transacao-1: pagamento aprovado"

    print(f"\n[ADD-BLOCO] Adicionando bloco com conteudo: '{conteudo}'")
    adicionar_bloco(conteudo, sessao["chave_sessao"], nome, "financeiro", 0)

    resultado = ler_blockchain(sessao["chave_sessao"], nome)
    print(f"  -> blocos na cadeia: {len(resultado)} (genesis + 1)")
    b = resultado[1]
    print(f"  -> bloco[1]: indice={b['indice']} proprietario={b['proprietario']}")
    print(f"               tipo_dado={b['tipo_dado']} status={b['status']}")
    print(f"               dado decifrado: '{b['dado']}'")
    print(f"               hash_anterior == hash_bloco do genesis: {b['hash_anterior'] == resultado[0]['hash_bloco']}")

    assert len(resultado) == 2
    assert b["indice"] == 1
    assert b["proprietario"] == nome
    assert b["status"] == "Decrypted"
    assert b["dado"] == conteudo
    assert b["tipo_dado"] == "financeiro"


def test_adicionar_varios_blocos_mantem_encadeamento(usuario_registrado):
    from controllers.blockchain_controller import adicionar_bloco, ler_blockchain

    sessao = usuario_registrado["sessao"]
    nome = usuario_registrado["nome"]
    valores = ["bloco-A", "bloco-B", "bloco-C"]

    print(f"\n[ENCADEAMENTO] Adicionando {len(valores)} blocos em sequencia")
    for v in valores:
        adicionar_bloco(v, sessao["chave_sessao"], nome, "padrao", 0)
        print(f"  -> adicionado: '{v}'")

    resultado = ler_blockchain(sessao["chave_sessao"], nome)
    print(f"  -> total na cadeia: {len(resultado)}")
    for i, b in enumerate(resultado):
        ha = b["hash_anterior"][:12]
        hb = b["hash_bloco"][:12]
        dado = b["dado"] if b["status"] == "Decrypted" else b["status"]
        print(f"     bloco[{i}] hash_ant={ha}... hash={hb}... dado='{dado}'")

    assert len(resultado) == 1 + len(valores)
    for i in range(1, len(resultado)):
        assert resultado[i]["hash_anterior"] == resultado[i - 1]["hash_bloco"]
        assert resultado[i]["dado"] == valores[i - 1]


def test_explorador_oculta_dados_de_outros_usuarios(codigo_totp):
    from controllers.auth_controller import registrar_usuario, logar_usuario
    from controllers.blockchain_controller import adicionar_bloco, ler_blockchain

    print("\n[PRIVACIDADE] Registrando 'alice' e 'bob', cada um adiciona 1 bloco")
    seg_a = registrar_usuario("alice", "senha-forte-1")
    seg_b = registrar_usuario("bob", "senha-forte-2")
    s_alice = logar_usuario("alice", "senha-forte-1", codigo_totp(seg_a))
    s_bob = logar_usuario("bob", "senha-forte-2", codigo_totp(seg_b))

    adicionar_bloco("segredo-da-alice", s_alice["chave_sessao"], "alice")
    adicionar_bloco("segredo-do-bob", s_bob["chave_sessao"], "bob")

    print("  -> visao do BOB sobre a cadeia:")
    visao_bob = ler_blockchain(s_bob["chave_sessao"], "bob")
    for b in visao_bob:
        print(f"     indice={b['indice']} dono={b['proprietario']} status={b['status']} dado='{b['dado']}'")

    proprios = [b for b in visao_bob if b.get("proprietario") == "bob"]
    alheios = [b for b in visao_bob if b.get("proprietario") == "alice"]

    assert any(b["status"] == "Decrypted" and b["dado"] == "segredo-do-bob" for b in proprios)
    assert all(b["status"] == "Encrypted" for b in alheios)
    assert all("[dados privados" in b["dado"] for b in alheios)
