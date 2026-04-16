import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from controllers.auth_controller import registrar_usuario, logar_usuario
from controllers.blockchain_controller import adicionar_bloco, ler_blockchain
from services.totp_service import obter_uri_totp
from utils.logger import registrar_evento
import base64
import json

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    dados = request.json
    nome_usuario = dados.get('username')
    senha = dados.get('password')
    
    if not nome_usuario or not senha:
        return jsonify({"erro": "Username e senha são obrigatórios"}), 400
        
    try:
        segredo_totp = registrar_usuario(nome_usuario, senha)
        uri = obter_uri_totp(segredo_totp, nome_usuario)
        
        return jsonify({
            "mensagem": "Usuário registrado",
            "segredo_totp": segredo_totp,
            "uri_totp": uri
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    nome_usuario = dados.get('username')
    senha = dados.get('password')
    codigo_totp = dados.get('totp_code')
    
    try:
        sessao = logar_usuario(nome_usuario, senha, codigo_totp)
        return jsonify({
            "mensagem": "Login realizado com sucesso",
            "chave_sessao": sessao["chave_sessao"].hex(),
            "nome_usuario": nome_usuario
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 401

@app.route('/api/public_chain', methods=['GET'])
def get_public_chain():
    try:
        cadeia = ler_blockchain(b'\x00'*32, "anonymous_explorer")
        return jsonify(cadeia)
    except Exception as e:
        return jsonify({"erro": str(e)}), 403

@app.route('/api/chain', methods=['GET'])
def get_chain():
    hex_sessao = request.headers.get("Authorization")
    nome_usuario = request.headers.get("X-Username")
    
    if not hex_sessao or not nome_usuario:
        return jsonify({"erro": "Não autenticado"}), 401
    
    try:
        chave_sessao = bytes.fromhex(hex_sessao)
        cadeia = ler_blockchain(chave_sessao, nome_usuario)
        return jsonify(cadeia)
    except Exception as e:
        return jsonify({"erro": str(e)}), 403

@app.route('/api/add_block', methods=['POST'])
def create_block():
    hex_sessao = request.headers.get("Authorization")
    nome_usuario = request.headers.get("X-Username")
    
    if not hex_sessao or not nome_usuario:
        return jsonify({"erro": "Não autenticado"}), 401
        
    dados = request.json
    conteudo = dados.get('data')
    tipo_dado = dados.get('data_type', 'padrao')
    expiracao = int(dados.get('expiration', 0))
    
    try:
        chave_sessao = bytes.fromhex(hex_sessao)
        adicionar_bloco(conteudo, chave_sessao, nome_usuario, tipo_dado, expiracao)
        return jsonify({"mensagem": "Bloco adicionado com segurança na nullTempus!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400



if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('web/templates', exist_ok=True)
    os.makedirs('web/static', exist_ok=True)
    
    app.debug = False
    
    print("=========================================================")
    print(" [SERVICO] Servidor nullTempus em Execucao")
    print(" [REDE] Porta Dinamica (Cloud Run)")
    print("=========================================================")
    
    from waitress import serve
    porta_servidor = int(os.environ.get('PORT', 5000))
    serve(app, host='0.0.0.0', port=porta_servidor)
