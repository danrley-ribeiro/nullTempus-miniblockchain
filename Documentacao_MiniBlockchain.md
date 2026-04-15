# Documentação: nullTempus (nullTempus)

Este documento acompanha a entrega do trabalho prático de Segurança da Informação e Redes (INE5680), preenchendo todos os requisitos estabelecidos no documento oficial para execução, arquitetura criptográfica e justificativas.

## 1. Tutorial de Execução

O projeto **nullTempus** está modularizado, mas conta com uma interface amigável centralizada em um menu (CLI). Para executá-lo, o avaliador deve garantir que os módulos base do python estejam instalados.

### Passos:
1. **(Caso não exista na pasta) Crie o Ambiente Virtual (Virtualenv):**
   ```bash
   # Windows, Linux ou macOS
   python -m venv venv
   # Obs: No Linux ou Mac, você pode precisar usar "python3 -m venv venv"
   ```
2. **Ative a Virtualenv** recém criada:
   ```bash
   # Em Windows PowerShell
   .\venv\Scripts\Activate.ps1

   # Em Linux ou macOS
   source venv/bin/activate
   ```
3. **Instale as dependências** do projeto presentes no arquivo de submissão (necessário após criar o venv do zero):
   ```bash
   pip install -r requirements.txt
   # Obs: No Linux ou Mac, você pode precisar usar "pip3"
   ```
4. **Execute o construtor do console**:
   ```bash
   python main.py
   # Obs: No Linux ou Mac, você pode precisar usar "python3 main.py"
   ```
5. Navegue pelo menu seguindo os passos de testes exigidos pela avaliação:
    * Na opção **[1]**, Cadastre os Usuários "A" e "B". (Na criação, o sistema apresentará um QRCode em interface ASCII e em `.png` na pasta `data/qrs/`).
    * Faça a leitura via aplicativo mobile (Google Authenticator / Authy) e extraia os 6 dígitos temporais de 2FA.
    * Use a opção **[2]** fazendo o Login injetando a mesclagem da Senha + Novo código gerado pelo aplicativo na hora.
    * Preencha dados simulando requisições, leia a blockchain, e por fim utilize a opção **[4]** do menu interno para acionar uma flagrância corrompendo ativamente o JSON.

---

## 2. Abordagem de Autenticação Duplo Fator (TOTP)
O sistema exige segurança de 2 camadas contra interceptações:
* **Fator de Possessão (TOTP):** Implementamos integralmente o algoritmo de *Time-Based One-Time Password* regulamentado pela **RFC 6238**.
* A geração de senhas gira em torno de uma `secret base32`. Para impedir o vazamento dessas secrets se o JSON de usuários for furtado, o lado do servidor aplica criptografia **AES-GCM** envelopada ao guardar esse token localmente (`totp_key_enc`). A chave que encripta seu TOTP é instanciada apenas com sua senha derivada (KDF), unindo o fator de "conhecimento" à preservação do fator de "possessão".

## 3. Derivação de Chave Simétrica e Session Wrap (Duplo Envelope)
A restrição absoluta aos padrões Pós-Quânticos / Imutabilidade e hardcoding foi seguida com rigor cirúrgico:
* Quando o usuário faz login, usamos o `Scrypt` (configurado com custo massivo `N=2^14, r=8, p=1`, blindando contra ataques de força-bruta físicos ou GPUs) mesclado ao `Salt` de 32 bytes de alto nível de entropia computacional (`os.urandom`) do usuário armazenado em claro.
* **Double-Wrap Architecture (Proteção Extra)**: Ao invés de usar a cifra de Scrypt pura para acessar a blockchain (o que colocaria as transações em risco num vazamento de hash), o log-in bem-sucedido cria magicamente uma **Session-Key de uso único**. Essa *Session* encripta a operação atual usando KDF dinâmicos, ou seja... toda seção é desmaterializada após o script ser encerrado.

## 4. Criptografia por Bloco Encadeado na nullTempus
A rede tem uma base descentralizada nos dados de blocos contendo os atributos primários (`data`, `timestamp`, `owner`).
* **Segurança e Detecção AES-GCM:** Todos os blocos são encriptados usando *Modo Galois Counter* em AES-256 bits, e um *IV (Initialization Vector)* descartável pseudoaleatório. Como o GCM embute a "Autenticidade" em sua Tag, dados como o Timestamp e o Tipo são passados não-criptografados na flag `AAD (Authenticated Additional Data)`. Isso significa que se um cibercriminoso conseguir escanear o JSON principal e apenas alterar o `timestamp` de um bloco público, o AAD barrará a decifragem do AES!
* Se o `hash_prev` (hash linkante do status do bloco de trás) for tocado por 1 único bit em edição indevida computacional (Simulada no Teste 4), a chain desmorona detectando adulteração massiva e abortando qualquer vazamento!

---

## 5. Casos de Teste e Validação (Roteiro de Avaliação)

Durante a apresentação ou avaliação do projeto, os seguintes cenários estruturados podem ser conferidos provando a blindagem criptográfica da aplicação através do Menu Principal do console:

### Autenticação
1. **Login correto + TOTP válido** → Acesso garantido ao "Menu do Usuário".
2. **Login com TOTP inválido** → Ação bloqueada. É lançada *PermissionError ("TOTP inválido")* e a tentativa falha é registrada. Após 5 falhas, bloqueio temporário (lockout).
3. **Login com senha incorreta** → Ação bloqueada. Identificada na falha do Scrypt / HMAC e registrada.

### Blockchain Multiusuário e Acesso
1. **Usuário A adiciona bloco** → Bloco devidamente criptografado com a junção de *AES-GCM* e anexado na chain.
2. **Usuário B adiciona bloco** → ID do owner "User B" carimbado matematicamente.
3. **Usuário A lê sua blockchain** → Visualiza publicamente *Timestamps* e *Hashes* de toda a rede, mas apenas descriptografa e acessa seus próprios blocos. Em blocos do Usuário B, constará a restrição: `[dados privados - acesso negado]`.

### Imutabilidade e Integridade
1. **Tentativa de modificar ciphertext / owner** → Através do atalho `[4]` do Menu, corrompe-se diretamente as chaves salvas do `.json`. O resultado imediato na hora da leitura é uma falha de integridade barrando a rede *(Ex: block_hash inválido)*.
2. **Alterar hash_prev** → Assim que um hash linkante é alterado para tentar quebrar a corrente, a leitura da chain acusa a divergência entre estado atual do bloco de trás e a ancoragem gravada ativando o modo de defesa.

### KDF (Key Derivation Function)
1. **Mesma senha + mesmo salt** → A geração de `pyotp` validará de forma consistente e a *Session Key* será idêntica para poder decifrar o Banco de Dados gerando o acesso.
2. **Salt diferente / Pimenta violada** → Derivará uma matriz HMAC completamente diferente, trancando permanentemente toda a visualização do usuário com aquela database falsa.
