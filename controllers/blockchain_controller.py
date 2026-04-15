from datetime import datetime, timezone
from models.block import Bloco
from storage.chain_store import carregar_cadeia, salvar_cadeia
from services.crypto_service import (
    cifrar_bloco_com_tbk,
    decifrar_bloco_com_tbk,
    computar_hash_bloco,
    computar_hmac_bloco,
    verificar_hmac_bloco,
    derivar_subchaves
)
from utils.logger import registrar_evento

def criar_bloco_genesis_se_necessario() -> list[Bloco]:
    cadeia = carregar_cadeia()
    if not cadeia:
        bloco_gen = Bloco(
            indice=0, proprietario="system", carimbo_tempo=datetime.now(timezone.utc).isoformat(),
            tipo_dado="padrao", expira_em="",
            texto_cifrado="", iv="", aad="", slot_tbk=0,
            hash_anterior="0"*64, hash_bloco="", hmac_bloco=""
        )
        bloco_gen.hash_bloco = computar_hash_bloco(bloco_gen.__dict__)
        cadeia.append(bloco_gen)
        salvar_cadeia(cadeia)
    return cadeia

def adicionar_bloco(texto_claro: str, chave_sessao: bytes, nome_usuario: str, tipo_dado: str = "padrao", minutos_expiracao: int = 0) -> None:
    cadeia = criar_bloco_genesis_se_necessario()
    
    try:
        ler_blockchain(chave_sessao, nome_usuario, validar_apenas=True)
    except Exception as e:
        registrar_evento("TAMPERING_DETECTED", nome_usuario, f"Cadeia corrompida na validação: {e}")
        raise ValueError("Blockchain base corrompida. Não é possível adicionar blocos.")
    
    ultimo_bloco = cadeia[-1]
    novo_indice = ultimo_bloco.indice + 1
    carimbo_tempo = datetime.now(timezone.utc).isoformat()
    
    expira_em = ""
    if minutos_expiracao > 0:
        from datetime import timedelta
        expira_em = (datetime.now(timezone.utc) + timedelta(minutes=minutos_expiracao)).isoformat()
    
    res_cripto = cifrar_bloco_com_tbk(texto_claro, chave_sessao, nome_usuario, novo_indice, carimbo_tempo, tipo_dado, expira_em)
    
    novo_bloco = Bloco(
        indice=novo_indice,
        proprietario=nome_usuario,
        carimbo_tempo=carimbo_tempo,
        tipo_dado=res_cripto["tipo_dado"],
        expira_em=res_cripto["expira_em"],
        texto_cifrado=res_cripto["texto_cifrado"],
        iv=res_cripto["iv"],
        aad=res_cripto["aad"],
        slot_tbk=res_cripto["slot_tbk"],
        hash_anterior=ultimo_bloco.hash_bloco,
        hash_bloco="",
        hmac_bloco=""
    )
    
    novo_bloco.hash_bloco = computar_hash_bloco(novo_bloco.__dict__)
    chave_mac = res_cripto["chave_mac"]
    novo_bloco.hmac_bloco = computar_hmac_bloco(novo_bloco.__dict__, chave_mac)
    
    cadeia.append(novo_bloco)
    salvar_cadeia(cadeia)
    registrar_evento("BLOCK_ADDED", nome_usuario, f"Adicionado bloco indice {novo_indice}")

def ler_blockchain(chave_sessao: bytes, nome_usuario: str, validar_apenas: bool = False) -> list[dict]:
    cadeia = criar_bloco_genesis_se_necessario()
    resultado = []
    
    for i, bloco in enumerate(cadeia):
        if i == 0:
            if not validar_apenas:
                resultado.append({
                    "indice": 0, "proprietario": "system", "carimbo_tempo": bloco.carimbo_tempo,
                    "hash_anterior": bloco.hash_anterior, "hash_bloco": bloco.hash_bloco,
                    "tipo_dado": bloco.tipo_dado,
                    "status": "Genesis", "dado": "Genesis Block"
                })
            continue
            
        bloco_previo = cadeia[i-1]
        if bloco.hash_anterior != bloco_previo.hash_bloco:
            registrar_evento("TAMPERING_DETECTED", nome_usuario, f"Hash_anterior inválido no bloco {bloco.indice}")
            raise ValueError(f"Blockchain adulterada! hash_anterior inválido no bloco {bloco.indice}")
            
        if computar_hash_bloco(bloco.__dict__) != bloco.hash_bloco:
            registrar_evento("TAMPERING_DETECTED", nome_usuario, f"Hash_bloco inválido no bloco {bloco.indice}")
            raise ValueError(f"Blockchain adulterada! hash_bloco inválido no bloco {bloco.indice}")
            
        chave_mac_alvo = derivar_subchaves(chave_sessao, bloco.tipo_dado)[1]
            
        if bloco.proprietario == nome_usuario:
            if not verificar_hmac_bloco(bloco.__dict__, chave_mac_alvo):
                registrar_evento("TAMPERING_DETECTED", nome_usuario, f"MAC inválido no bloco {bloco.indice}")
                raise ValueError(f"Blockchain adulterada! MAC inválido no bloco {bloco.indice}")
            
            if not validar_apenas:
                try:
                    decifrado = decifrar_bloco_com_tbk(bloco.__dict__, chave_sessao, nome_usuario)
                    resultado.append({
                        "indice": bloco.indice, "proprietario": bloco.proprietario, "carimbo_tempo": bloco.carimbo_tempo,
                        "hash_anterior": bloco.hash_anterior, "hash_bloco": bloco.hash_bloco,
                        "tipo_dado": bloco.tipo_dado,
                        "status": "Decrypted", "dado": decifrado
                    })
                except Exception as e:
                    resultado.append({
                        "indice": bloco.indice, "proprietario": bloco.proprietario, "carimbo_tempo": bloco.carimbo_tempo,
                        "hash_anterior": bloco.hash_anterior, "hash_bloco": bloco.hash_bloco,
                        "tipo_dado": bloco.tipo_dado,
                        "status": "Error", "dado": str(e)
                    })
        else:
            if not validar_apenas:
                resultado.append({
                    "indice": bloco.indice, "proprietario": bloco.proprietario, "carimbo_tempo": bloco.carimbo_tempo,
                    "hash_anterior": bloco.hash_anterior, "hash_bloco": bloco.hash_bloco,
                    "tipo_dado": bloco.tipo_dado,
                    "status": "Encrypted", "dado": "[dados privados - acesso negado]"
                })
                
    if not validar_apenas:
        registrar_evento("BLOCKCHAIN_READ", nome_usuario, "Leitura completa da blockchain realizada.")
    return resultado
