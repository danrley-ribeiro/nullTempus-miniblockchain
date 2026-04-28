# nullTempus - Mini-Blockchain Segura (Web & Cloud Ready)

> Trabalho Prático de Segurança da Informação e Redes (INE5680). Este projeto preenche os requisitos oficiais de execução, arquitetura criptográfica e imutabilidade, provendo uma blockchain completa com chaves de sessão efêmeras protegidas e registradas em um Banco de Dados em Nuvem (MongoDB).

---

## 1. Visão Geral

O **nullTempus** evoluiu de uma simples plataforma por comando de terminal (CLI) para uma Aplicação Web de Interface rica desenvolvida em **Python (Flask + Servidor Waitress)** no backend. 

Diferente de escopos rasos, a aplicação abandona o uso de arquivos estáticos `.json` salvos localmente, transformando a arquitetura em um sistema "Stateless" (sem disco) totalmente pronto e validado para rodar sob instâncias efêmeras (como o Google Cloud Run) ao utilizar um Cluster **MongoDB** para o armazenamento encadeado.

---

## 2. Como Executar (Localmente)

1. **Crie e Ative um Ambiente Virtual (venv)**:
   ```bash
   python -m venv venv

   # No Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # No Mac/Linux:
   source venv/bin/activate
   ```

2. **Instale as Dependências do Projeto**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o Banco de Dados (.env)**:
   A integração remota utiliza o MongoDB como repositório padrão. No entanto, o projeto suporta execução **Local Offline**:
   - **Modo Nuvem**: Preencha `MONGO_URI` no seu arquivo `.env`.
   - **Modo Local (JSON)**: Deixe a `MONGO_URI` vazia ou defina `LOCAL_DB=true` no `.env`. Os dados serão salvos automaticamente na pasta `data/`.

4. **Inicialize o Servidor Web de Produção**:
   ```bash
   python web_server.py
   ```

5. **Acesse a Aplicação**:
   Abra seu navegador em: **`http://127.0.0.1:5001`**

### Validando os Testes Acadêmicos:
Ao invés de menus em preto e branco no console, todo o fluxo está imerso na web:
- Acesse a aba "Criar Cofre" e gere um novo usuário adicionando um nome de usuário e uma senha (Mínimo de 7 caracteres). A interface apresentará um QR Code para ser escaneado via *Google Authenticator* / *Authy*.
- Troque para a aba de "Painel de Acesso", realize o login usando a mesclagem da Senha em texto com o código OTP gerado no autenticador do seu smartphone.
- Insira blocos de dados. Digite qualquer texto no campo "Carga Secreta", escreva uma categoria e digite o tempo de expiração em minutos (Se deixar 0, o tempo será "infinito").  O servidor construirá os enlaces criptográficos AES de forma transparente usando envolórios de chaves, mandando para o MongoDB.
- Qualquer pessoa na rede pode enxergar publicamente as Metadata (Timestamp, index, etc) de toda a BlockChain. No entanto, o `Payload` permanece cifrado na tela (`[ACESSO NEGADO]`) ao menos que o dono correto possua uma "Session_Key" correspondente injetada pelo KDF no login validado para desencriptar!

---

## 3. Publicação e Nuvem (Cloud Run)

O projeto anula os riscos de perda por conta das máquinas dinâmicas e está 100% conteinerizado e com porta atizada.

1. Instale e autentique a Google Cloud SDK (`gcloud`).
2. Digite no terminal da raiz apontando para o Docker:
   ```bash
   gcloud run deploy nulltempus --source .
   ```
O servidor *Waitress* resgatará silenciosamente via `os.environ` a Porta do Data Center do Google provendo um escalonamento linear.

---

## 4. Arquitetura Criptográfica e Segurança

O projeto segue restrições rígidas seguindo recomendações da OWASP, sem hardcoding:

* **Possessão Temporal (Algorítmo OTP 2FA):** Implementação regida rigorosamente pela RFC-6238 Base32.
* **Scrypt e Double-Wrap:** A senha nunca é misturada ao Payload. Utiliza-se o derivador com força bruta assíncrona blindada (`n=2^{14}`). O script backend então "enrola" (Wrap) uma Chave de Sessão Aleatória efêmera usando a masterkey do Banco de Dados para que nenhuma chave física possa ser capturada na RAM durante os loops operacionais de AES-256. 
* **Time-Bound Key (Criptografia Temporal):** Implementa-se uma chave efêmera transversal utilizando HKDF, que combina a `session_key` a um slot de tempo do momento da criação da transação (intervalos do TOTP). Esse mecanismo garante a propriedade de *Forward Secrecy Temporal*: mesmo em caso de comprometimento da sessão principal no futuro, o bloco restringe sua decifragem cirurgicamente à janela temporal em que foi cifrado originariamente.
* **Impeditivo de Extensão e Manipulação (AAD GCM):** Para que um hacker não manipule um bloco "clonando" o pacote de GCM e invertendo seus donos e datas, todas as variáveis de leitura pública são acorrentadas aos bytes da variável `AAD (Authenticated Additional Data)`. Qualquer bit alterado no Documento Database fará a validação GCM da integridade despencar para "Falha" (crashing imediato da leitura pelo AES ao invés de falso-positivo).
* **Hashes Unilaterais:** Cada instância da cadeia amarra seu encadeamento SHA3 com hash_anterior do último objeto salvo no MongoDB preenchendo as premissas da Blockchain.
