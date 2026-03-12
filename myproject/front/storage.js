// ============================================
// storage.js — Gestor con API real
// ============================================

const API_URL = 'http://127.0.0.1:8000/api';

class StorageManager {
    constructor() {
        this.prefix = 'app_';
    }

    // ── localStorage para datos no sensibles ──
    set(key, value) {
        try {
            localStorage.setItem(this.prefix + key, JSON.stringify(value));
            return true;
        } catch (e) { console.error('Error al guardar:', e); return false; }
    }

    get(key) {
        try {
            const item = localStorage.getItem(this.prefix + key);
            return item ? JSON.parse(item) : null;
        } catch (e) { return null; }
    }

    remove(key) {
        localStorage.removeItem(this.prefix + key);
        sessionStorage.removeItem(this.prefix + key);
    }

    clear() {
        ['localStorage', 'sessionStorage'].forEach(store => {
            const s    = window[store];
            const keys = Object.keys(s).filter(k => k.startsWith(this.prefix));
            keys.forEach(k => s.removeItem(k));
        });
    }

    has(key) {
        return localStorage.getItem(this.prefix + key) !== null;
    }

    // ── Tokens JWT en sessionStorage ──────────
    setTokens(access, refresh) {
        sessionStorage.setItem(this.prefix + 'access',  access);
        sessionStorage.setItem(this.prefix + 'refresh', refresh);
    }

    getAccess() {
        return sessionStorage.getItem(this.prefix + 'access') || null;
    }

    getRefresh() {
        return sessionStorage.getItem(this.prefix + 'refresh') || null;
    }

    clearTokens() {
        sessionStorage.removeItem(this.prefix + 'access');
        sessionStorage.removeItem(this.prefix + 'refresh');
    }

    hasValidSession() {
        return !!this.getAccess();
    }

    logout() {
        this.clearTokens();
        this.clear();
    }

    // ── Fetch autenticado con auto-refresh ────
    async fetchAuth(endpoint, options = {}) {
        let access = this.getAccess();
        if (!access) throw new Error('No autenticado');

        const hacer = async (token) => {
            return fetch(`${API_URL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    ...(options.headers || {}),
                },
            });
        };

        let res = await hacer(access);

        // Si el token expiró, intentar refresh automático
        if (res.status === 401) {
            const refreshToken = this.getRefresh();
            if (!refreshToken) {
                this.logout();
                window.location.href = '/front/login.html';
                return;
            }

            const refreshRes = await fetch(`${API_URL}/token/refresh/`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ refresh: refreshToken }),
            });

            if (!refreshRes.ok) {
                this.logout();
                window.location.href = '/front/login.html';
                return;
            }

            const data = await refreshRes.json();
            this.setTokens(data.access, data.refresh || refreshToken);
            res = await hacer(data.access);
        }

        return res;
    }

    // ── Fetch público (sin token) ─────────────
    async fetchPublic(endpoint, options = {}) {
        return fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {}),
            },
        });
    }
}

// ── Helpers globales ──────────────────────────────

function sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function toast(mensaje, tipo = 'exito', duracion = 3000) {
    document.querySelectorAll('.toast').forEach(t => t.remove());
    const el = document.createElement('div');
    el.className = `toast toast-${tipo}`;
    el.innerHTML = `
        <span class="toast-icon">${tipo === 'exito' ? '✅' : tipo === 'error' ? '❌' : 'ℹ️'}</span>
        <span class="toast-texto">${sanitizeHTML(mensaje)}</span>`;
    document.body.appendChild(el);
    requestAnimationFrame(() => el.classList.add('toast-visible'));
    setTimeout(() => {
        el.classList.remove('toast-visible');
        setTimeout(() => el.remove(), 400);
    }, duracion);
}

const storage = new StorageManager();
window.storage      = storage;
window.sanitizeHTML = sanitizeHTML;
window.escapeAttr   = escapeAttr;
window.toast        = toast;
window.API_URL      = API_URL;