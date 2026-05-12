"""
Repositório de usuários (collection "users").

Funções:
- carregar_usuarios(): lê todos os documentos e devolve dict {nome_usuario: Usuario}.
- salvar_usuarios(usuarios): upsert de cada usuário usando nome_usuario como _id.
"""

import os
from dataclasses import fields
from models.user import Usuario
from storage.db import db

# Conexão com a collection de usuarios no Mongo
users_col = db["users"]

_CAMPOS_USUARIO = {f.name for f in fields(Usuario)}

def carregar_usuarios() -> dict[str, Usuario]:
    usuarios_dict = {}
    
    # Busca todos os documentos na coleção
    docs = users_col.find({})
    
    for doc in docs:
        # Pega a chave principal que inserimos manualmente
        nome_usuario = doc.get("_id")
        
        # Removemos o _id e ignoramos campos legados que não fazem mais parte do modelo
        dados_usuario = {k: v for k, v in doc.items() if k != "_id" and k in _CAMPOS_USUARIO}

        usuarios_dict[nome_usuario] = Usuario(**dados_usuario)

    return usuarios_dict

def salvar_usuarios(usuarios: dict[str, Usuario]) -> None:
    # Pra não precisar fazer uma exclusão e reinclusão ou loop pesado:
    # Iteramos cada usuário fazendo upsert no documento cujo _id igual ao username.
    for nome_usuario, usuario_obj in usuarios.items():
        doc_dados = usuario_obj.__dict__
        users_col.update_one(
            {"_id": nome_usuario},
            {"$set": doc_dados},
            upsert=True
        )
