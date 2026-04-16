import os
import sys
from cli.prompts import prompt_string, prompt_password
from controllers.auth_controller import registrar_usuario, logar_usuario
from controllers.blockchain_controller import adicionar_bloco, ler_blockchain
from services.totp_service import obter_uri_totp, gerar_qr_code, imprimir_qr_code_no_console

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_menu():
    print("=" * 55)
    print("  _  _       _  _  _____                              ")
    print(" | \\| |_  _ | || ||_   _|___ _ __  _ __  _  _  ___    ")
    print(" | .` | || || || |  | | / -_) '  \\| '_ \\| || |(_-<    ")
    print(" |_|\\_|\\_,_||_||_|  |_| \\___|_|_|_| .__/ \\_,_|/__/    ")
    print("                                  |_|                 ")
    print("=" * 55)
    print("1. Cadastrar Usuário")
    print("2. Fazer Login (Senha + TOTP)")
    print("3. Sair")
    print("=" * 55)

def fluxo_registro():
    print("\n--- CADASTRO ---")
    nome_usuario = prompt_string("Username")
    senha = prompt_password("Senha")
    try:
        segredo_totp = registrar_usuario(nome_usuario, senha)
        print("\n[SUCESSO] Usuário cadastrado!")
        print(f"Sua chave TOTP manual é: {segredo_totp}")
        uri = obter_uri_totp(segredo_totp, nome_usuario)
        dir_qr = os.path.join("data", "qrs")
        os.makedirs(dir_qr, exist_ok=True)
        caminho_img = os.path.join(dir_qr, f"{nome_usuario}_qrcode.png")
        
        gerar_qr_code(uri, caminho_img)
        print("\nEscaneie o QR Code abaixo com seu aplicativo Authenticator:")
        imprimir_qr_code_no_console(uri)
        print(f"Se preferir, a imagem original foi salva como '{caminho_img}'.")
    except Exception as e:
        print(f"\n[ERRO] {e}")

def fluxo_login():
    print("\n--- LOGIN ---")
    nome_usuario = prompt_string("Username")
    senha = prompt_password("Senha")
    codigo_totp = prompt_string("Código TOTP")
    try:
        sessao = logar_usuario(nome_usuario, senha, codigo_totp)
        print("\n[SUCESSO] Login realizado com sucesso!")
        menu_usuario(nome_usuario, sessao)
    except Exception as e:
        print(f"\n[ERRO] {e}")

def menu_usuario(nome_usuario: str, sessao: dict):
    from services.session_service import destruir_sessao
    while True:
        print(f"\n--- MENU DO USUÁRIO ({nome_usuario}) ---")
        print("1. Adicionar Bloco (Transação)")
        print("2. Ler Blockchain")
        print("3. Realizar Logout")

        escolha = prompt_string("Escolha uma opção")
        
        if escolha == "1":
            dado = prompt_string("Dados do bloco")
            tipo_dado = prompt_string("Tipo de dado (ex: padrao, financiamento, medico)")
            if not tipo_dado: tipo_dado = "padrao"
            str_exp = prompt_string("Expira em (minutos, 0 para nunca)")
            try:
                minutos_exp = int(str_exp) if str_exp.isdigit() else 0
                from controllers.blockchain_controller import adicionar_bloco
                adicionar_bloco(dado, sessao["chave_sessao"], nome_usuario, tipo_dado, minutos_exp)
                print("[SUCESSO] Bloco adicionado com segurança!")
            except Exception as e:
                print(f"[ERRO] {e}")
                
        elif escolha == "2":
            print("\n--- STATUS DA BLOCKCHAIN ---")
            try:
                from controllers.blockchain_controller import ler_blockchain
                info_cadeia = ler_blockchain(sessao["chave_sessao"], nome_usuario)
                for bloco in info_cadeia:
                    print("-" * 30)
                    print(f"Índice: {bloco['indice']}")
                    print(f"Proprietário: {bloco['proprietario']}")
                    print(f"Data/Hora UTC: {bloco.get('carimbo_tempo', 'N/A')}")
                    print(f"Hash Anterior: {bloco.get('hash_anterior', 'N/A')}")
                    print(f"Hash Atual: {bloco.get('hash_bloco', 'N/A')}")
                    print(f"Status: {bloco['status']}")
                    print(f"Dados: {bloco['dado']}")
                print("-" * 30)
            except Exception as e:
                print(f"[ALERTA DE SEGURANÇA] {e}")
                
        elif escolha == "3":
            destruir_sessao(sessao)
            print("Sessão finalizada com segurança. Voltando ao menu principal...")
            break

                
        else:
            print("Opção inválida.")

def main_cli():
    while True:
        mostrar_menu()
        escolha = prompt_string("Escolha")
        if escolha == "1":
            fluxo_registro()
        elif escolha == "2":
            fluxo_login()
        elif escolha == "3":
            print("Saindo do sistema...")
            sys.exit(0)
        else:
            print("Opção inválida.")
