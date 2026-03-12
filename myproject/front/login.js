// ============================================
// login.js — Conectado a la API real
// ============================================

// Si ya tiene sesión activa, redirigir
if (storage.hasValidSession()) {
    const usuario = storage.get('usuario_actual');
    if (usuario && usuario.tiene_perfil) {
        window.location.href = '/front/dashboard.html';
    } else {
        window.location.href = '/front/seleccion.html';
    }
}

const _form       = document.getElementById('form-login');
const _btnLogin   = document.getElementById('btn-login');
const _btnTexto   = _btnLogin ? _btnLogin.querySelector('.btn-text') : null;
const _btnSpinner = _btnLogin ? _btnLogin.querySelector('.btn-spinner') : null;

function setError(id, msg) {
    const el = document.getElementById('error-' + id);
    if (el) el.textContent = msg;
}

function mostrarAlerta(msg) {
    const el = document.getElementById('alert-error');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}

function ocultarAlerta() {
    const el = document.getElementById('alert-error');
    if (el) el.style.display = 'none';
}

function setBtnCargando(cargando) {
    if (!_btnLogin) return;
    _btnLogin.disabled = cargando;
    if (_btnTexto)   _btnTexto.style.display  = cargando ? 'none'   : '';
    if (_btnSpinner) _btnSpinner.style.display = cargando ? 'inline' : 'none';
}

if (_form) {
    _form.addEventListener('submit', async function(e) {
        e.preventDefault();
        ocultarAlerta();
        setError('email', '');
        setError('password', '');

        const email    = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        if (!email)    { setError('email',    'El correo es obligatorio');     return; }
        if (!password) { setError('password', 'La contraseña es obligatoria'); return; }

        setBtnCargando(true);

        try {
            const res  = await storage.fetchPublic('/login/', {
                method: 'POST',
                body:   JSON.stringify({ email, password }),
            });
            const data = await res.json();

            if (res.ok) {
                storage.setTokens(data.access, data.refresh);
                storage.set('usuario_actual', data.usuario);
                toast('¡Bienvenido!', 'exito');
                setTimeout(function() {
                    if (data.usuario.tiene_perfil) {
                        window.location.href = '/front/dashboard.html';
                    } else {
                        window.location.href = '/front/seleccion.html';
                    }
                }, 800);
            } else if (res.status === 403) {
                mostrarAlerta(data.error || 'Cuenta bloqueada temporalmente');
            } else if (res.status === 401) {
                mostrarAlerta('Email o contraseña incorrectos');
            } else {
                mostrarAlerta(data.error || 'Error al iniciar sesión');
            }

        } catch (err) {
            mostrarAlerta('No se pudo conectar al servidor');
            console.error(err);
        } finally {
            setBtnCargando(false);
        }
    });
}

function togglePass(id, btn) {
    const input = document.getElementById(id);
    if (!input) return;
    input.type      = input.type === 'password' ? 'text' : 'password';
    btn.textContent = input.type === 'password' ? '👁' : '🙈';
}