"""
Repositório da blockchain (collection "blockchain").

Funções:
- carregar_cadeia(): lê todos os blocos ordenados por índice e devolve lista de Bloco.
- salvar_cadeia(cadeia): faz upsert de cada bloco usando o índice como _id.
"""

import os
from models.block import Bloco
from storage.db import db, ASCENDING

chain_col = db["blockchain"]

def carregar_cadeia() -> list[Bloco]:
    # Busca ordenando por índice (ascedente: 1)
    docs = chain_col.find({}).sort("indice", ASCENDING)
    
    cadeia = []
    for doc in docs:
        dados_bloco = {k: v for k, v in doc.items() if k != "_id"}
        cadeia.append(Bloco(**dados_bloco))
        
    return cadeia

def salvar_cadeia(cadeia: list[Bloco]) -> None:
    # Insere apenas os blocos que ainda não existem ou atualiza eles via index
    for bloco in cadeia:
        doc_dados = bloco.__dict__
        # Usa o 'indice' do bloco numérico como id do documento
        chain_col.update_one(
            {"_id": bloco.indice},
            {"$set": doc_dados},
            upsert=True
        )
