# Glossário do nullTempus-miniblockchain

Dicionário rápido dos termos usados na aplicação. Cada entrada tem:
**o que é → para que serve → onde aparece no código**.

---

## Primitivas criptográficas

### Scrypt
KDF (Key Derivation Function) baseado em senha, custoso em memória.
Deriva uma chave de 32 bytes a partir de `(senha, sal)`.
Usado no cadastro (gerar verificador) e no login (rederivar a chave para abrir o cofre).
- `services/crypto_service.py` → `derivar_chave()`
- Parâmetros usados no projeto:
  - `SCRYPT_N = 2^14` (16384) — **cost factor** (potência de 2). Controla o número de
    iterações internas e, junto com `r`, a quantidade de RAM exigida. Dobrar `N` dobra
    tempo e memória. Com os valores atuais, cada derivação aloca ~16 MB e leva ~100 ms.
  - `SCRYPT_R = 8` — **block size**. Tamanho dos blocos manipulados pelo BlockMix. Afeta
    a largura de banda da cache da CPU e o consumo de memória. Valor padrão recomendado
    pelo autor do Scrypt.
  - `SCRYPT_P = 1` — **paralelismo**. Quantos blocos independentes são processados em
    paralelo. Aumenta custo de CPU sem aumentar memória. Para login interativo, `p=1`
    é suficiente.
  - `SCRYPT_DKLEN = 32` — **tamanho da chave de saída**, em bytes. Não influencia o
    custo; só define que a chave derivada tem 256 bits (compatível com AES-256).
- Fórmulas práticas: `custo_tempo ∝ N · r · p`; `memória ≈ 128 · N · r` bytes.
- A combinação `(2^14, 8, 1)` é a recomendação RFC 7914 / OWASP para login interativo.

### HKDF (HMAC-based Key Derivation Function)
Expande uma chave em várias subchaves rotuladas por um `info`.
Aqui usa SHA3-256.
- `services/crypto_service.py` → `derivar_subchaves()` (separa `chave_enc` e `chave_mac`).
- `services/time_bound_key_service.py` → `derivar_tbk()` (deriva a TBK do slot).

### HMAC (Hash-based Message Authentication Code)
MAC com chave secreta usado para autenticar a integridade do bloco inteiro.
Usa SHA3-256.
- `services/crypto_service.py` → `computar_hmac_bloco()`, `verificar_hmac_bloco()`.

### SHA3-256
Hash criptográfico de 256 bits. Usado para:
- encadear blocos (`hash_anterior` / `hash_bloco`),
- como função interna do HMAC e do HKDF.
- `services/crypto_service.py` → `computar_hash_bloco()`.

### AES-GCM (AEAD)
Cifra simétrica autenticada. Cifra o conteúdo do bloco e autentica os metadados via AAD.
- `services/crypto_service.py` → `cifrar_bloco_com_tbk()`, `decifrar_bloco_com_tbk()`.
- `services/totp_service.py` → cifragem do segredo TOTP em repouso.

### AES Key Wrap (RFC 3394)
Algoritmo específico para "envelopar" chaves (encriptar uma chave com outra).
Aqui envelopa a chave mestre usando a chave derivada da senha.
- `services/session_service.py` → `gerar_e_envelopar_chave_mestre()`, `desenvelopar_chave_mestre()`.

### TOTP (Time-based One-Time Password, RFC 6238)
Códigos de 6 dígitos válidos por 30s. Segundo fator de autenticação.
- `services/totp_service.py` → `gerar_segredo_totp()`, `verificar_totp()`, `obter_uri_totp()`.
- Provisionamento: QR Code (PNG ou ASCII no terminal).

### AAD (Additional Authenticated Data)
Dados em claro autenticados (mas não cifrados) pelo AES-GCM.
Garante que metadados públicos do bloco (índice, dono, timestamp, tipo, expiração)
não possam ser alterados sem invalidar a tag de autenticação.
- `services/crypto_service.py` → `construir_aad()`.

### IV (Initialization Vector)
Nonce de 12 bytes do AES-GCM. Único por cifragem.
- **Blocos da cadeia**: aleatório (`os.urandom(12)`), gerado em `cifrar_bloco_com_tbk()`
  e armazenado no campo `iv` do bloco. Obrigatoriamente aleatório porque a mesma TBK
  pode cifrar múltiplos blocos dentro da janela de 30s.
- **Segredo TOTP em repouso**: **derivado** da chave via HKDF-SHA3-256
  (`info=b"null-tempus-totp-iv"`) em `services/totp_service.py::_derivar_iv_totp()`.
  Seguro aqui porque cada usuário tem chave única (sal de 32 bytes) e há apenas uma
  cifragem por chave — o IV derivado não precisa ser armazenado.

### Sal (salt)
32 bytes aleatórios por usuário, em claro. Faz com que duas pessoas com a mesma senha
produzam chaves derivadas diferentes (impede ataques com rainbow tables).
- Gerado em `controllers/auth_controller.py::registrar_usuario()`.
- Persistido em `data/users.json` como `usuario.sal` (hex).

---

## Conceito central: Time-Bound Key

### TBK (Time-Bound Key)
Chave AES-256 derivada por **janela de tempo** (30s, mesma janela do TOTP).
Cifra cada bloco com uma chave diferente, atrelada ao instante de criação.
- `services/time_bound_key_service.py` → `derivar_tbk()`, `obter_tbk_para_cifra()`, `obter_tbk_para_decifra()`.

### Slot
Inteiro = `floor(unix_time / 30)`. Identifica a janela de 30s.
Faz parte do `info` do HKDF que gera a TBK; também é armazenado no bloco (`slot_tbk`).
- `services/time_bound_key_service.py` → `_slot_atual()`, `slot_por_timestamp()`.

### Tolerância de slot
Constante `SLOTS_TOLERANCIA_TBK = 1`. Permite decifrar com slot ±1 para tolerar
deslocamento de relógio entre cifragem e decifragem.
- `services/time_bound_key_service.py` → `obter_candidatos_tbk()`.
- `services/crypto_service.py::decifrar_bloco_com_tbk()` usa os candidatos como fallback.

---

## Chaves e segredos (hierarquia)

### Senha
Segredo do usuário. **Nunca persistida.** Só passa por memória durante login.

### Chave derivada
Saída do Scrypt sobre `(senha, sal)`. Atua como:
1. **Verificador de senha** (comparação em tempo constante).
2. **KEK** (Key Encryption Key) que envelopa a chave mestre.
3. Chave AES-GCM que cifra o segredo TOTP em repouso.
- `services/crypto_service.py::derivar_chave()`.

### Verificador de senha (`verificador_senha`)
Hex da chave derivada, armazenado no `users.json` para validar login.
- `models/user.py::Usuario.verificador_senha`.
- Comparado em `auth_controller.py::logar_usuario()` com `hmac.compare_digest`.

### Chave mestre
32 bytes aleatórios gerados no cadastro. Armazenada **envelopada** com AES Key Wrap.
No login é desenvelopada e usada como **chave de sessão**.
- `services/session_service.py::gerar_e_envelopar_chave_mestre()`.
- Persistida em `users.json` como `chave_mestre_enc` (hex).

### Chave de sessão (`chave_sessao`)
Chave mestre desenvelopada, viva apenas em memória durante a sessão.
Entrada para o HKDF que produz `chave_enc` e `chave_mac`.
- `services/session_service.py::criar_sessao()` → retorna `{"chave_sessao": bytes}`.
- Destruída em `destruir_sessao()` ao logout.

### Subchaves: `chave_enc` e `chave_mac`
Derivadas via HKDF da chave de sessão, separadas por tipo de dado.
- `chave_enc`: usada para derivar a TBK (cifragem do bloco).
- `chave_mac`: usada no HMAC do bloco (integridade autenticada).
- `services/crypto_service.py::derivar_subchaves()`.

### Segredo TOTP
String Base32 gerada no cadastro. **Cifrada em repouso** com AES-GCM usando a chave derivada.
- `services/totp_service.py::gerar_segredo_totp()`, `cifrar_segredo_totp()`.
- Persistido em `users.json` como `chave_totp_cifrada`. O IV é derivado da própria
  chave via HKDF e não é armazenado.

---

## Modelo de dados

### `Usuario` (modelo)
- `models/user.py`.
- Campos: `nome_usuario`, `sal`, `verificador_senha`, `chave_totp_cifrada`,
  `tentativas_falhas`, `bloqueado_ate`, `chave_mestre_enc`.

### `Bloco` (modelo)
- `models/block.py`.
- Campos: `indice`, `proprietario`, `carimbo_tempo`, `tipo_dado`, `expira_em`,
  `texto_cifrado`, `iv`, `aad`, `slot_tbk`, `hash_anterior`, `hash_bloco`, `hmac_bloco`.

### Bloco gênesis
Bloco 0 da cadeia, criado automaticamente na primeira leitura.
Não tem ciphertext; `hash_anterior` é 64 zeros.
- `controllers/blockchain_controller.py::criar_bloco_genesis_se_necessario()`.

### `tipo_dado`
Rótulo livre (`padrao`, `financiamento`, `medico`, etc.). Entra no `info` do HKDF que
deriva `chave_enc`/`chave_mac` → cada tipo tem subchaves independentes.
- Definido pelo usuário ao adicionar bloco.

### `expira_em`
Timestamp ISO 8601 UTC. Se preenchido, blocos vencidos são rejeitados na decifragem.
- Verificado em `services/crypto_service.py::decifrar_bloco_com_tbk()`.

### `hash_anterior` / `hash_bloco`
SHA3-256 hex. `hash_anterior` referencia o `hash_bloco` do bloco anterior — assim a cadeia
é encadeada e qualquer alteração quebra os blocos seguintes.

### `hmac_bloco`
HMAC-SHA3-256 do bloco inteiro (exceto o próprio campo).
Diferente do `hash_bloco`, **requer chave** — só o dono consegue recalcular.

---

## Controle de autenticação

### Lockout (bloqueio de conta)
Após 3 tentativas falhas o usuário é bloqueado por 15 minutos.
- `controllers/auth_controller.py` → constantes `BLOQUEAR_APOS_TENTATIVAS`, `DURACAO_BLOQUEIO_MINUTOS`.
- Funções: `verificar_bloqueio()`, `registrar_tentativa_falha()`.

### Sessão
Dicionário com `chave_sessao`. Retornado por `logar_usuario()`, destruído por logout.
- `services/session_service.py`.

---

## Armazenamento

### LOCAL_DB
Modo que persiste tudo em JSON local (`data/blockchain.json`, `data/users.json`).
Ativado por env var `LOCAL_DB=true` ou pela ausência de `MONGO_URI`.
- `storage/db.py` → classes `LocalCollection`, `LocalDatabase`.

### MongoDB (modo padrão)
Quando `MONGO_URI` está definida, usa PyMongo. Mesmas coleções: `users`, `blockchain`.
- `storage/db.py`.

### `chain_store` / `user_store`
Camadas finas de carregar/salvar coleções, agnósticas ao backend.
- `storage/chain_store.py`, `storage/user_store.py`.

### `security.log`
Log textual de eventos: `REGISTER`, `LOGIN_SUCCESS`, `LOGIN_FAILED`, `ACCOUNT_LOCKED`,
`BLOCK_ADDED`, `BLOCKCHAIN_READ`, `TAMPERING_DETECTED`.
- `utils/logger.py::registrar_evento()`.
- Arquivo: `data/security.log`.

---

## Interfaces de uso

### CLI
Menu interativo de cadastro/login/blockchain.
- `cli/menu.py`, `cli/prompts.py`.
- Ponto de entrada: `main.py`.

### Servidor Web
API Flask + frontend estático em `web/`.
- `web_server.py` (rotas), servido por `waitress` em produção.

---

## Camadas de proteção do bloco (defesa em profundidade)

Resumo das verificações executadas ao ler a cadeia:

| Camada                  | Chave usada     | O que detecta                                                |
|-------------------------|-----------------|--------------------------------------------------------------|
| `hash_anterior`         | nenhuma         | bloco anterior alterado / blocos reordenados                 |
| `hash_bloco` (SHA3-256) | nenhuma         | qualquer campo do próprio bloco alterado                     |
| `hmac_bloco`            | `chave_mac`     | reescrita por quem **não** tem a chave de sessão             |
| Tag do AES-GCM + AAD    | TBK             | ciphertext alterado / metadados (índice, dono, timestamp) trocados |
| Validade do `expira_em` | nenhuma         | bloco fora da janela de validade                             |

Romper **qualquer uma sozinha** já dispara `ValueError` em `ler_blockchain()`.

---

## Observações sobre dependências declaradas

- O KDF de senha é **Scrypt** (não Argon2). `argon2-cffi` foi removido do
  `requirements.txt` por não ser utilizado.
- `pillow` é dependência indireta de `qrcode` para gerar PNGs.
