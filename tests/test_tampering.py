"""
Testes de detecção de adulteração na blockchain.

Cobre três cenários:
1. Alteração do carimbo_tempo de um bloco.
2. Alteração direta do hash_bloco.
3. Alteração de outro dado do bloco (texto_cifrado).

Em todos os casos a leitura/validação da cadeia deve falhar.
"""

import pytest

from storage.chain_store import carregar_cadeia, salvar_cadeia
from controllers.blockchain_controller import adicionar_bloco, ler_blockchain


def _preparar_cadeia(usuario_registrado, texto="dado-original"):
    sessao = usuario_registrado["sessao"]
    nome = usuario_registrado["nome"]
    adicionar_bloco(texto, sessao["chave_sessao"], nome, "padrao", 0)
    return sessao, nome


def test_alterar_timestamp_invalida_a_cadeia(usuario_registrado):
    sessao, nome = _preparar_cadeia(usuario_registrado)

    print("\n[TAMPER-TIMESTAMP] Alterando carimbo_tempo do bloco 1")
    cadeia = carregar_cadeia()
    alvo = cadeia[1]
    print(f"  -> ANTES:  carimbo_tempo = {alvo.carimbo_tempo}")
    print(f"             hash_bloco    = {alvo.hash_bloco[:32]}...")
    alvo.carimbo_tempo = "2000-01-01T00:00:00+00:00"
    salvar_cadeia(cadeia)
    print(f"  -> DEPOIS: carimbo_tempo = {alvo.carimbo_tempo}")
    print(f"             hash_bloco gravado (inalterado) = {alvo.hash_bloco[:32]}...")

    with pytest.raises(ValueError, match="hash_bloco inválido") as exc:
        ler_blockchain(sessao["chave_sessao"], nome)
    print(f"  -> leitura rejeitada: {exc.value}")


def test_alterar_hash_bloco_invalida_a_cadeia(usuario_registrado):
    sessao, nome = _preparar_cadeia(usuario_registrado)

    print("\n[TAMPER-HASH] Alterando hash_bloco diretamente")
    cadeia = carregar_cadeia()
    alvo = cadeia[1]
    original = alvo.hash_bloco
    trocado = ("0" if original[0] != "0" else "1") + original[1:]
    print(f"  -> ANTES:  hash_bloco = {original[:32]}...")
    alvo.hash_bloco = trocado
    salvar_cadeia(cadeia)
    print(f"  -> DEPOIS: hash_bloco = {trocado[:32]}...")

    with pytest.raises(ValueError, match="hash_bloco inválido|hash_anterior inválido") as exc:
        ler_blockchain(sessao["chave_sessao"], nome)
    print(f"  -> leitura rejeitada: {exc.value}")


def test_alterar_texto_cifrado_invalida_a_cadeia(usuario_registrado):
    sessao, nome = _preparar_cadeia(usuario_registrado)

    print("\n[TAMPER-CIPHERTEXT] Alterando texto_cifrado (1o byte do base64)")
    cadeia = carregar_cadeia()
    alvo = cadeia[1]
    original = alvo.texto_cifrado
    trocado = ("B" if original[0] != "B" else "C") + original[1:]
    print(f"  -> ANTES:  texto_cifrado[:32] = {original[:32]}")
    alvo.texto_cifrado = trocado
    salvar_cadeia(cadeia)
    print(f"  -> DEPOIS: texto_cifrado[:32] = {trocado[:32]}")

    with pytest.raises(ValueError, match="hash_bloco inválido") as exc:
        ler_blockchain(sessao["chave_sessao"], nome)
    print(f"  -> leitura rejeitada: {exc.value}")


def test_alteracao_em_bloco_intermediario_invalida_cadeia_seguinte(usuario_registrado):
    """Adulterar um bloco no meio quebra o encadeamento dos blocos posteriores."""
    sessao, nome = _preparar_cadeia(usuario_registrado, texto="primeiro")
    adicionar_bloco("segundo", sessao["chave_sessao"], nome)
    adicionar_bloco("terceiro", sessao["chave_sessao"], nome)

    print("\n[TAMPER-MEIO] Cadeia com 4 blocos (gen + 3). Alterando bloco do meio (indice=2)")
    cadeia = carregar_cadeia()
    print(f"  -> ANTES:  bloco[2].carimbo_tempo = {cadeia[2].carimbo_tempo}")
    cadeia[2].carimbo_tempo = "1999-12-31T23:59:59+00:00"
    salvar_cadeia(cadeia)
    print(f"  -> DEPOIS: bloco[2].carimbo_tempo = {cadeia[2].carimbo_tempo}")
    print("  -> esperado: ler_blockchain deve detectar inconsistencia no bloco 2 ou 3")

    with pytest.raises(ValueError, match="hash_bloco inválido|hash_anterior inválido") as exc:
        ler_blockchain(sessao["chave_sessao"], nome)
    print(f"  -> leitura rejeitada: {exc.value}")
