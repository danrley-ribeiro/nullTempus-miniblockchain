import os
from models.user import Usuario
from storage.db import db

# Conexão com a collection de usuarios no Mongo
users_col = db["users"]

def carregar_usuarios() -> dict[str, Usuario]:
    usuarios_dict = {}
    
    # Busca todos os documentos na coleção
    docs = users_col.find({})
    
    for doc in docs:
        # Pega a chave principal que inserimos manualmente
        nome_usuario = doc.get("_id")
        
        # Removemos o _id para não conflitar com a desestruturação do modelo Usuario
        dados_usuario = {k: v for k, v in doc.items() if k != "_id"}
        
        # O modelo já tem um atributo username, garantindo as devidas passagens
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
