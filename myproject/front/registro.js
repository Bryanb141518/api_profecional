// ============================================
// registro.js — Conectado a la API real
// ============================================

document.addEventListener('DOMContentLoaded', () => {

    const form       = document.getElementById('form-registro');
    const btnRegistro= document.getElementById('btn-registro');
    const btnTexto   = btnRegistro?.querySelector('.btn-text');
    const btnSpinner = btnRegistro?.querySelector('.btn-spinner');
    const inputPass  = document.getElementById('password');

    // ── Fortaleza de contraseña ───────────────
    if (inputPass) {
        inputPass.addEventListener('input', () => {
            const val    = inputPass.value;
            const fill   = document.getElementById('strength-fill');
            const label  = document.getElementById('strength-label');
            if (!fill || !label) return;

            let puntos = 0;
            if (val.length >= 8)                             puntos++;
            if (/[A-Z]/.test(val))                           puntos++;
            if (/[0-9]/.test(val))                           puntos++;
            if (/[!@#$%^&*(),.?":{}|<>]/.test(val))         puntos++;

            const niveles = ['', 'Débil', 'Regular', 'Buena', 'Fuerte'];
            const colores = ['', '#ef4444', '#f59e0b', '#3b82f6', '#22c55e'];
            fill.style.width      = `${puntos * 25}%`;
            fill.style.background = colores[puntos] || '#e5e7eb';
            label.textContent     = niveles[puntos] || '';
            label.style.color     = colores[puntos] || '';
        });
    }

    // ── Helpers ───────────────────────────────
    function setError(id, msg) {
        const el = document.getElementById('error-' + id);
        if (el) el.textContent = msg;
    }
    function clearErrors() {
        ['nombre','email','password','confirm','fecha'].forEach(id => setError(id, ''));
    }

    function calcularEdad(fechaNac) {
        const hoy  = new Date();
        const nac  = new Date(fechaNac);
        let edad   = hoy.getFullYear() - nac.getFullYear();
        const m    = hoy.getMonth() - nac.getMonth();
        if (m < 0 || (m === 0 && hoy.getDate() < nac.getDate())) edad--;
        return edad;
    }

    function setBtnCargando(cargando) {
        if (!btnRegistro) return;
        btnRegistro.disabled = cargando;
        if (btnTexto)   btnTexto.style.display   = cargando ? 'none'   : '';
        if (btnSpinner) btnSpinner.style.display  = cargando ? 'inline' : 'none';
    }

    // ── Submit ────────────────────────────────
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearErrors();

            const nombre   = document.getElementById('nombre')?.value.trim();
            const email    = document.getElementById('email')?.value.trim();
            const password = document.getElementById('password')?.value;
            const confirm  = document.getElementById('confirm')?.value;
            const fecha    = document.getElementById('fecha')?.value;

            // Validaciones locales
            let ok = true;
            if (!nombre)  { setError('nombre', 'El nombre es obligatorio'); ok = false; }
            if (!email)   { setError('email',  'El correo es obligatorio');  ok = false; }
            if (!password){ setError('password','La contraseña es obligatoria'); ok = false; }
            if (password !== confirm) { setError('confirm', 'Las contraseñas no coinciden'); ok = false; }
            if (!fecha)   { setError('fecha',  'La fecha de nacimiento es obligatoria'); ok = false; }

            if (!ok) return;

            const edad = calcularEdad(fecha);
            if (edad < 14) { setError('fecha', 'Debes tener al menos 14 años'); return; }
            if (edad > 120){ setError('fecha', 'Fecha inválida'); return; }

            // Separar nombre y apellido
            const partes   = nombre.split(' ');
            const nombreVal= partes[0];
            const apellido = partes.slice(1).join(' ') || nombreVal;

            setBtnCargando(true);

            try {
                const res  = await storage.fetchPublic('/registro/', {
                    method: 'POST',
                    body: JSON.stringify({
                        nombre:   nombreVal,
                        apellido: apellido,
                        email,
                        password,
                        edad,
                        genero:   'P',
                    }),
                });

                const data = await res.json();

                if (res.ok) {
                    storage.setTokens(data.access, data.refresh);
                    storage.set('usuario_actual', data.usuario);
                    toast('¡Cuenta creada! Redirigiendo...', 'exito');
                    setTimeout(() => {
                        window.location.href = '/front/seleccion.html';
                    }, 1200);
                } else {
                    const errores = Object.values(data).flat().join(' | ');
                    toast(errores || 'Error al registrar', 'error');
                }

            } catch (err) {
                toast('No se pudo conectar al servidor. ¿Está corriendo Django?', 'error');
                console.error(err);
            } finally {
                setBtnCargando(false);
            }
        });
    }
});

// ── Toggle mostrar/ocultar password ──────────
function togglePass(id, btn) {
    const input = document.getElementById(id);
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.textContent = input.type === 'password' ? '👁' : '🙈';
}