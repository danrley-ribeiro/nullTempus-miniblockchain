const API_URL = '/api';

let chaveSessao = localStorage.getItem('nt_session');
let usuarioLogado = localStorage.getItem('nt_user');

window.onload = () => {
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
