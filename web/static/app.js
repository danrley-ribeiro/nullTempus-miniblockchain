const API_URL = '/api';

let chaveSessao = localStorage.getItem('nt_session');
let usuarioLogado = localStorage.getItem('nt_user');

window.onload = () => {
    updateClock(); // Relogio
    sortearMensagemRodape(); // Mensagem do rodapé
    if (chaveSessao && usuarioLogado) {
        showDashboard();
    } else {
        switchAuthTab('login'); // Start clean
    }
};

function switchAuthTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('explorer-section').classList.add('hidden');

    if (tab === 'login') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('login-form').classList.remove('hidden');
    } else if (tab === 'register') {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('register-form').classList.remove('hidden');
    } else if (tab === 'explorer') {
        document.querySelector('.tab-btn:nth-child(3)').classList.add('active');
        document.getElementById('explorer-section').classList.remove('hidden');
        fetchChain();
    }
}

function showToast(msg, isError = false) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${isError ? 'error' : ''}`;
    toast.innerText = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// Authentication
async function register() {
    const user = document.getElementById('reg-user').value;
    const pass = document.getElementById('reg-pass').value;

    if (pass.length < 7) {
        return showToast("A senha do cofre deve ter no mínimo 7 caracteres.", true);
    }

    try {
        const target = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const res = await target.json();

        if (target.ok) {
            document.getElementById('qr-result').classList.remove('hidden');
            
            // Limpa o container e gera o QR Code no Frontend
            const qrContainer = document.getElementById('qr-code-container');
            qrContainer.innerHTML = '';
            new QRCode(qrContainer, {
                text: res.uri_totp,
                width: 128,
                height: 128,
                colorDark : "#000000",
                colorLight : "#ffffff",
                correctLevel : QRCode.CorrectLevel.H
            });

            document.getElementById('manual-code').innerText = res.segredo_totp;
            showToast("Chaves Geradas! Escaneie seu Auth Code para habilitar 2FA.");
        } else throw new Error(res.erro || res.error);
    } catch (e) { showToast(e.message, true); }
}

async function login() {
    const user = document.getElementById('login-user').value;
    const pass = document.getElementById('login-pass').value;
    const totp = document.getElementById('login-totp').value;

    try {
        const target = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass, totp_code: totp })
        });
        const res = await target.json();

        if (target.ok) {
            chaveSessao = res.chave_sessao;
            usuarioLogado = res.nome_usuario;
            localStorage.setItem('nt_session', chaveSessao);
            localStorage.setItem('nt_user', usuarioLogado);
            showDashboard();
            showToast("Acesso Seguro Aprovado. Bem-vindo à nullTempus.");
        } else throw new Error(res.erro || res.error);
    } catch (e) { showToast(e.message, true); }
}

function logout() {
    chaveSessao = null;
    usuarioLogado = null;
    localStorage.removeItem('nt_session');
    localStorage.removeItem('nt_user');
    
    // Força o descarregamento total da página web pelo navegador.
    // Isso garante purificação absoluta da RAM e reseta o frontend à estaca zero.
    window.location.reload();
}

function showDashboard() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('dashboard-section').classList.remove('hidden');
    document.getElementById('explorer-section').classList.remove('hidden');
    document.getElementById('logged-user').innerText = usuarioLogado;
    fetchChain();
}

async function authFetch(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = chaveSessao;
    options.headers['X-Username'] = usuarioLogado;
    options.headers['Content-Type'] = 'application/json';

    const res = await fetch(`${API_URL}${endpoint}`, options);
    const data = await res.json();
    if (!res.ok) throw new Error(data.erro || data.error || 'Erro Crítico');
    return data;
}

// Blockchain Features
async function fetchChain() {
    try {
        let chain = [];
        if (chaveSessao && usuarioLogado) {
            chain = await authFetch('/chain');
        } else {
            const res = await fetch(`${API_URL}/public_chain`);
            const data = await res.json();
            if (!res.ok) throw new Error(data.erro || data.error);
            chain = data;
        }

        const container = document.getElementById('chain-container');
        container.innerHTML = '';

        chain.forEach(b => {
            let cssClass = 'encrypted';
            let status = b.status || 'Locked';
            if (b.indice === 0) cssClass = 'genesis';
            else if (status === 'Decrypted') cssClass = 'decrypted';

            const card = document.createElement('div');
            card.className = `block-card ${cssClass}`;
            card.innerHTML = `
                <div class="block-header">
                    <span class="block-idx">BLOCO #${b.indice} - <span style="font-weight:400; font-size: 0.8rem">${b.carimbo_tempo}</span></span>
                    <span class="block-owner">[HELD BY]: @${b.proprietario}</span>
                </div>
                <div class="block-hash"><span class="hash-label">Categoria (Tipo):</span> <span style="color:var(--white);">${b.tipo_dado || 'padrao'}</span></div>
                <div class="block-hash"><span class="hash-label">Prev. Hash:</span> ${b.hash_anterior}</div>
                <div class="block-hash"><span class="hash-label">Node  Hash:</span> ${b.hash_bloco}</div>
                <div class="block-data ${status === 'Encrypted' ? 'encrypted' : ''}">
                    ${status === 'Encrypted' ? '[ ACESSO NEGADO - CONFIDENCIAL ] VOCE NAO POSSUI A CHAVE DE DERIVACAO DESSE USUARIO' : '[ DECRIPTADO ] Payload Original: ' + b.dado}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        showToast("SISTEMA BLOQUEADO: " + e.message, true);
        document.getElementById('chain-container').innerHTML = `
            <div class="block-card default" style="border-left-color: var(--danger); background: rgba(255,0,0,0.1)">
                <h3 style="color:var(--danger); margin-bottom:10px">[ALERTA CRITICO] ARQUITETURA CONGELADA (TAMPERING DETECTADO)</h3>
                <p style="font-family:monospace">${e.message}</p>
                <p style="margin-top:20px; font-size:0.9rem; color:#aaa">O hash linkante anterior e atual no batem com os metadados fisicos. Como seguranca, a nullTempus travou a injecao da sua Chave de Memoria.</p>
            </div>
        `;
    }
}

function filterChain() {
    const input = document.getElementById('chain-search').value.toLowerCase();
    const cards = document.querySelectorAll('.block-card');
    
    cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        if (text.includes(input)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

async function addBlock() {
    const data = document.getElementById('block-data').value;
    const type = document.getElementById('block-type').value || 'padrao';
    const xp = document.getElementById('block-exp').value || 0;

    if (!data) return showToast("Insira dados para o bloco!", true);

    try {
        await authFetch('/add_block', { method: 'POST', body: JSON.stringify({ data: data, data_type: type, expiration: xp }) });
        showToast("Transação encriptada em duplo-envelope e anexada com sucesso à Blockchain.");
        fetchChain();
        document.getElementById('block-data').value = '';
    } catch (e) { showToast(e.message, true); }
}

async function simulateAttack() {
    try {
        const res = await fetch(`${API_URL}/simulate`, { method: 'POST' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.erro || data.error);
        showToast("Aviso: " + data.mensagem, true);
        fetchChain();
    } catch (e) { showToast(e.message, true); }
}

function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    const micro = String(Math.floor((performance.now() % 1) * 1000)).padStart(3, '0');

    const clockElement = document.getElementById('system-clock');
    if (clockElement) {
        clockElement.innerHTML = `
            <span class="clock-prefix">NT_SYS:</span>
            <span class="clock-digits">${h}:${m}:${s}.${ms}</span>
            <span class="clock-us">${micro}µs</span>
        `;
    }
    requestAnimationFrame(updateClock);
}

// --- LISTA DE MENSAGENS DO SISTEMA ---
const mensagensSistema = [
    "Sua chave privada é nossa chave pública.",
    "Fragmentando suas intenções em blocos de 256-bit.",
    "O nó #0 nunca esquece, e ele não gosta de você.",
    "Procurando colisões de Hash? Boa sorte nos próximos mil anos.",
    "Seus segredos são apenas texto plano no meu buffer.",
    "A curva elíptica aqui é um círculo vicioso.",
    "Derivando sua chave... Erro: Entropia insuficiente na sua lógica.",
    "Salt, Pepper e uma pitada de desespero.",
    "Sua força bruta é apenas um aquecedor de CPU para nós.",
    "Chaves simétricas para problemas assimétricos.",
    "O envelope digital foi violado. A vergonha é eterna.",
    "Assinatura inválida. Tente novamente em outra encarnação.",
    "RSA-4096 é o café da manhã dos nossos nós.",
    "Chaves perdidas, dados malditos.",
    "Onde termina o seu bit, começa o nosso abismo.",
    "Diffie-Hellman não previu sua audácia.",
    "Um nonce usado duas vezes é o seu convite para o desastre.",
    "XORing sua dignidade com zero.",
    "Sua semente mnemônica foi plantada em solo estéril.",
    "Criptografia é o direito de permanecer em silêncio.",
    "A cifra de Vigenère riria da sua complexidade.",
    "Descriptografando esperanças... Resultado: 0 matches.",
    "Sua keychain é um cadeado de papelão.",
    "O segredo compartilhado agora é só meu.",
    "No espaço de chaves, ninguém ouve você gritar.",
    "Puzzles de prova de trabalho: Sua GPU vai derreter primeiro.",
    "Vetor de Inicialização corrompido. Bem-vindo ao caos.",
    "Padding Oracle está sussurrando seus segredos.",
    "A chave mestra foi forjada no coração de um servidor morto.",
    "Criptoanálise concluída: Sua defesa é puramente estética.",
    "Sugiro nem tentar, Mythos.",
    "O tempo é nulo, mas sua falha é absoluta.",
    "Você está caçando fantasmas em um labirinto de espelhos.",
    "A arquitetura é imutável; sua vontade é volátil.",
    "Rastreando salto de IP... Origem identificada. Volte para o berçário.",
    "Você não é o root. Você não é nada.",
    "Batendo na porta de um buraco negro.",
    "Sua conexão é apenas um ruído na nossa rede.",
    "Onde você vê código, eu vejo uma armadilha.",
    "A entropia devora os fracos e cospe os curiosos.",
    "Protocolo de purificação de RAM pronto. Quer ser o próximo?",
    "O abismo também olha para o seu código-fonte.",
    "Sua persistência é admirável; sua técnica, uma piada.",
    "Bem-vindo à nullTempus. Deixe sua lógica na entrada.",
    "Injetando realidade no seu script de criança.",
    "A matemática é o único juiz aqui. Você foi condenado.",
    "Seus pacotes estão sendo descartados no limbo.",
    "Um nó fantasma está observando você agora.",
    "Não force o handshake, eu não gosto de você.",
    "O nó de saída é um beco sem saída.",
    "Sua VPN é apenas um túnel para o meu domínio.",
    "Camadas de abstração não esconderão sua mediocridade.",
    "O firewall tem fome. Alimente-o com seus exploits.",
    "Tentativa de bypass detectada. Nível de patetismo: Crítico.",
    "Você está jogando xadrez com um compilador.",
    "Sua stack está prestes a transbordar de frustração.",
    "O sistema não dorme. O sistema nem sequer pisca.",
    "Scripts automáticos? Tenha um pouco de respeito próprio.",
    "A rede nullTempus é um ecossistema hostil para turistas.",
    "Seu status: 'ReadOnly' na vida, 'Null' no sistema.",
    "O 'S' em IoT significa Segurança.",
    "Minha senha é o nome do meu cachorro (ele tem 256 bits de puro ódio).",
    "O maior firewall do mundo ainda é um alicate de corte.",
    "Segurança de TI: Onde o erro é público e o acerto é invisível.",
    "Nada é à prova de idiotas, eles são muito criativos.",
    "Seu sistema é uma porta de vidro com um adesivo de 'Cuidado com o Cão'.",
    "Backup é igual seguro de vida: você só valoriza quando o defunto aparece.",
    "Usuário: a única vulnerabilidade que não aceita patch de correção.",
    "'Senha123' ainda é a chave para o reino.",
    "Eu uso 2FA: Eu e minha paranoia.",
    "A nuvem é apenas o computador de outra pessoa que você não pode desligar.",
    "Bug bounty: Onde te pagam com uma camiseta por uma falha de RCE.",
    "Minha política de senhas é baseada em poemas de autores mortos.",
    "Ocultar o SSID é como esconder uma chave embaixo do tapete transparente.",
    "Criptografia: Transformando dados em lixo caro.",
    "Injeção de SQL? O ano 2000 ligou e pediu o exploit de volta.",
    "Social Engineering: Porque é mais fácil enganar você do que o servidor.",
    "Seus segredos estão seguros comigo... e com o meu banco de dados não indexado.",
    "O firewall barrou seu ego, mas deixou o vírus passar.",
    "Antivírus é o placebo preferido dos sysadmins.",
    "Honeypots: Onde hackers vão para se sentir importantes.",
    "'Foi só um teste' - Todo hacker após ser pego.",
    "A internet das coisas vai te matar através da sua torradeira inteligente.",
    "Sua segurança é baseada em obscura ignorância.",
    "Clique aqui para ganhar um ransomware grátis.",
    "A BIOS riu da sua tentativa de acesso.",
    "Kernel Panic: O jeito do sistema dizer 'Chega!'.",
    "O cabo de rede é a única conexão 100% segura. Se estiver cortado.",
    "Minha infraestrutura é baseada em orações e fita isolante.",
    "Se você acha que é seguro, você não está prestando atenção.",
    "Hackear é fácil. Explicar o que você fez para o juiz é difícil.",
    "O estagiário acabou de dar um rm -rf / no seu orgulho.",
    "Logs de auditoria: O diário de bordo do Titanic.",
    "Certificados SSL expirados: A bandeira branca da TI.",
    "Zero Day? Para você, todo dia é Zero Brain.",
    "Sandbox: Onde eu deixo você brincar antes de te deletar.",
    "SSH: Sofrimento Super Hardcore.",
    "Root é apenas um estado de espírito. Que você não alcançou.",
    "A última linha de defesa é a negação plausível.",
    "Game Over, Mythos. Tente inserir outra moeda."
];

function sortearMensagemRodape() {
    const footerElement = document.querySelector('.footer');
    if (footerElement) {
        const indice = Math.floor(Math.random() * mensagensSistema.length);
        footerElement.innerHTML = `Desenvolvido por 🌑👤 <br> <span class="footer-msg">${mensagensSistema[indice]}</span>`;
    }
}