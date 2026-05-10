"""
Controlador de autenticação e ciclo de vida do usuário.

Funções:
- verificar_bloqueio(usuario): levanta erro se a conta ainda está dentro do período de bloqueio.
- registrar_tentativa_falha(usuario): incrementa o contador e bloqueia a conta após N falhas.
- registrar_usuario(nome_usuario, senha): cria conta nova, gera sal, deriva a chave Scrypt,
  cria o segredo TOTP cifrado e envelopa uma chave mestre aleatória.
- logar_usuario(nome_usuario, senha, codigo_totp): valida senha + TOTP, desenvelopa a chave
  mestre e devolve a sessão pronta para uso.
"""

from datetime import datetime, timezone, timedelta
from models.user import Usuario
from storage.user_store import carregar_usuarios, salvar_usuarios
from services.crypto_service import derivar_chave, verificar_senha
from services.session_service import criar_sessao, destruir_sessao, gerar_e_envelopar_chave_mestre, desenvelopar_chave_mestre
from services.totp_service import gerar_segredo_totp, obter_uri_totp, cifrar_segredo_totp, verificar_totp, gerar_qr_code, decifrar_segredo_totp
from utils.logger import registrar_evento
import os

BLOQUEAR_APOS_TENTATIVAS = 3
DURACAO_BLOQUEIO_MINUTOS = 15

def verificar_bloqueio(usuario: Usuario):
    if usuario.bloqueado_ate:
        bloqueado_ate_dt = datetime.fromisoformat(usuario.bloqueado_ate)
        if datetime.now(timezone.utc) < bloqueado_ate_dt:
            raise ValueError(f"Conta bloqueada até {usuario.bloqueado_ate}")
        else:
            usuario.tentativas_falhas = 0
            usuario.bloqueado_ate = ""

def registrar_tentativa_falha(usuario: Usuario):
    usuario.tentativas_falhas += 1
    if usuario.tentativas_falhas >= BLOQUEAR_APOS_TENTATIVAS:
        usuario.bloqueado_ate = (datetime.now(timezone.utc) + timedelta(minutes=DURACAO_BLOQUEIO_MINUTOS)).isoformat()
        registrar_evento("ACCOUNT_LOCKED", usuario.nome_usuario, "Muitas tentativas falhas. Conta travada.")

def registrar_usuario(nome_usuario: str, senha: str) -> str:
    usuarios = carregar_usuarios()
    if nome_usuario in usuarios:
        raise ValueError("Usuário já existe.")
        
    if len(senha) < 7:
        raise ValueError("A senha deve ter no mínimo 7 caracteres.")

    sal = os.urandom(32)
    chave_derivada = derivar_chave(senha, sal)
    
    segredo_totp = gerar_segredo_totp()
    chave_totp_cifrada, iv_totp = cifrar_segredo_totp(segredo_totp, chave_derivada)
    
    chave_mestre, hex_chave_mestre_envelopada = gerar_e_envelopar_chave_mestre(chave_derivada)
    
    novo_usuario = Usuario(
        nome_usuario=nome_usuario,
        sal=sal.hex(),
        verificador_senha=chave_derivada.hex(),
        chave_totp_cifrada=chave_totp_cifrada,
        iv_totp=iv_totp,
        tentativas_falhas=0,
        bloqueado_ate="",
        chave_mestre_enc=hex_chave_mestre_envelopada
    )
    usuarios[nome_usuario] = novo_usuario
    salvar_usuarios(usuarios)
    registrar_evento("REGISTER", nome_usuario, "Novo usuário registrado.")
    
    return segredo_totp

def logar_usuario(nome_usuario: str, senha: str, codigo_totp: str) -> dict:
    usuarios = carregar_usuarios()
    usuario = usuarios.get(nome_usuario)
    
    if not usuario:
        registrar_evento("LOGIN_FAILED", nome_usuario, "Usuário inexistente.")
        raise ValueError("Credenciais inválidas.")
        
    verificar_bloqueio(usuario)
    
    sal = bytes.fromhex(usuario.sal)
    chave_derivada = derivar_chave(senha, sal)
    
    if chave_derivada.hex() != usuario.verificador_senha:
        registrar_tentativa_falha(usuario)
        salvar_usuarios(usuarios)
        registrar_evento("LOGIN_FAILED", nome_usuario, "Senha incorreta.")
        raise ValueError("Credenciais inválidas.")

    segredo_totp = decifrar_segredo_totp(usuario.chave_totp_cifrada, usuario.iv_totp, chave_derivada)
    if not verificar_totp(segredo_totp, codigo_totp):
        registrar_tentativa_falha(usuario)
        salvar_usuarios(usuarios)
        registrar_evento("LOGIN_FAILED", nome_usuario, "TOTP inválido.")
        raise ValueError("Código TOTP inválido.")
        
    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate = ""
    salvar_usuarios(usuarios)
    registrar_evento("LOGIN_SUCCESS", nome_usuario, "Login efetuado com duplo fator válido")
    
    chave_mestre = desenvelopar_chave_mestre(chave_derivada, usuario.chave_mestre_enc)
    return criar_sessao(chave_mestre)
