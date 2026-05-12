"""
Testes de Cadastro e Login (autenticação + 2FA TOTP).
"""

import pytest


def test_cadastro_cria_usuario_e_retorna_segredo_totp(codigo_totp):
    from controllers.auth_controller import registrar_usuario
    from storage.user_store import carregar_usuarios

    print("\n[CADASTRO] Registrando usuario 'bob' com senha 'minha-senha-123'")
    segredo = registrar_usuario("bob", "minha-senha-123")
    print(f"  -> segredo TOTP retornado: {segredo}")
    print(f"  -> codigo TOTP atual gerado: {codigo_totp(segredo)}")

    usuarios = carregar_usuarios()
    print(f"  -> persistido em data/users.json: chaves = {list(usuarios.keys())}")
    print(f"  -> verificador_senha (hex, 8 primeiros): {usuarios['bob'].verificador_senha[:16]}...")
    print(f"  -> chave_totp_cifrada (hex, 8 primeiros): {usuarios['bob'].chave_totp_cifrada[:16]}...")

    assert isinstance(segredo, str) and len(segredo) > 0
    assert "bob" in usuarios
    assert usuarios["bob"].verificador_senha
    assert usuarios["bob"].chave_totp_cifrada
    assert codigo_totp(segredo).isdigit()


def test_cadastro_falha_para_usuario_duplicado():
    from controllers.auth_controller import registrar_usuario

    print("\n[CADASTRO-DUPLICADO] Registrando 'carol' duas vezes")
    registrar_usuario("carol", "abcdefg7")
    print("  -> primeira chamada: OK")
    with pytest.raises(ValueError, match="já existe") as exc:
        registrar_usuario("carol", "outra-senha")
    print(f"  -> segunda chamada levantou: {exc.value}")


def test_cadastro_falha_para_senha_curta():
    from controllers.auth_controller import registrar_usuario

    print("\n[CADASTRO-SENHA-CURTA] Tentando registrar com senha '123'")
    with pytest.raises(ValueError, match="mínimo 7") as exc:
        registrar_usuario("dave", "123")
    print(f"  -> rejeitado com: {exc.value}")


def test_login_sucesso_retorna_sessao_com_chave(codigo_totp):
    from controllers.auth_controller import registrar_usuario, logar_usuario

    print("\n[LOGIN-OK] Cadastrando 'eve' e efetuando login com TOTP correto")
    segredo = registrar_usuario("eve", "senha-forte-1")
    cod = codigo_totp(segredo)
    print(f"  -> codigo TOTP usado: {cod}")
    sessao = logar_usuario("eve", "senha-forte-1", cod)
    print(f"  -> sessao criada, chave_sessao tem {len(sessao['chave_sessao'])} bytes")
    print(f"  -> primeiros 4 bytes (hex): {sessao['chave_sessao'][:4].hex()}")

    assert "chave_sessao" in sessao
    assert isinstance(sessao["chave_sessao"], (bytes, bytearray))
    assert len(sessao["chave_sessao"]) == 32


def test_login_falha_com_senha_errada(codigo_totp):
    from controllers.auth_controller import registrar_usuario, logar_usuario

    print("\n[LOGIN-SENHA-ERRADA] Tentativa de login com senha incorreta")
    segredo = registrar_usuario("frank", "senha-forte-1")
    with pytest.raises(ValueError, match="Credenciais inválidas") as exc:
        logar_usuario("frank", "senha-errada", codigo_totp(segredo))
    print(f"  -> rejeitado com: {exc.value}")


def test_login_falha_com_totp_invalido():
    from controllers.auth_controller import registrar_usuario, logar_usuario

    print("\n[LOGIN-TOTP-INVALIDO] Login com senha correta mas TOTP '000000'")
    registrar_usuario("grace", "senha-forte-1")
    with pytest.raises(ValueError, match="TOTP") as exc:
        logar_usuario("grace", "senha-forte-1", "000000")
    print(f"  -> rejeitado com: {exc.value}")


def test_login_falha_para_usuario_inexistente():
    from controllers.auth_controller import logar_usuario

    print("\n[LOGIN-INEXISTENTE] Tentando logar como 'ninguem'")
    with pytest.raises(ValueError, match="Credenciais inválidas") as exc:
        logar_usuario("ninguem", "qualquer-coisa", "123456")
    print(f"  -> rejeitado com: {exc.value}")


def test_conta_bloqueia_apos_tres_tentativas_falhas():
    from controllers.auth_controller import registrar_usuario, logar_usuario
    from storage.user_store import carregar_usuarios

    print("\n[LOCKOUT] Registrando 'heidi' e errando senha 3 vezes")
    registrar_usuario("heidi", "senha-forte-1")
    for i in range(3):
        with pytest.raises(ValueError):
            logar_usuario("heidi", "errada", "000000")
        print(f"  -> tentativa {i+1}/3: rejeitada")

    usuarios = carregar_usuarios()
    print(f"  -> bloqueado_ate: {usuarios['heidi'].bloqueado_ate}")
    print(f"  -> tentativas_falhas: {usuarios['heidi'].tentativas_falhas}")
    assert usuarios["heidi"].bloqueado_ate != ""

    print("  -> agora tentando login com SENHA CORRETA - deve falhar por bloqueio")
    with pytest.raises(ValueError, match="bloqueada") as exc:
        logar_usuario("heidi", "senha-forte-1", "000000")
    print(f"  -> rejeitado com: {exc.value}")
