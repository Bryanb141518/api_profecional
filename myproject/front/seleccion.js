// ============================================
// seleccion.js — Conectado a la API real
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    if (!storage.hasValidSession()) {
        window.location.href = '/front/login.html';
        return;
    }

    // Mostrar nombre de usuario
    const usuario = storage.get('usuario_actual');
    if (usuario) {
        const avatarEl = document.getElementById('user-avatar');
        const nombreEl = document.getElementById('user-nombre');
        if (avatarEl) avatarEl.textContent = (usuario.nombre || 'U').charAt(0).toUpperCase();
        if (nombreEl) nombreEl.textContent = usuario.nombre || 'Usuario';
    }
});

// Función global llamada desde el HTML
async function seleccionar(tipo) {
    const esUniversidad = tipo === 'universidad';
    const tipoAPI       = esUniversidad ? 'U' : 'C';

    if (!esUniversidad) {
        toast('La modalidad colegio estará disponible pronto', 'info');
        return;
    }

    const card = document.getElementById(`card-${tipo}`);
    if (card) card.style.opacity = '0.6';

    try {
        const res  = await storage.fetchAuth('/tipo-estudiante/', {
            method: 'POST',
            body:   JSON.stringify({ tipo_estudiante: tipoAPI }),
        });
        const data = await res.json();

        if (res.ok) {
            const usuario = storage.get('usuario_actual') || {};
            usuario.tipo_estudiante = tipoAPI;
            storage.set('usuario_actual', usuario);
            toast('Tipo guardado correctamente', 'exito');
            setTimeout(() => {
                window.location.href = '/front/configuracion.html';
            }, 800);
        } else {
            toast(data.error || 'Error al guardar tipo', 'error');
            if (card) card.style.opacity = '1';
        }

    } catch (err) {
        toast('No se pudo conectar al servidor', 'error');
        console.error(err);
        if (card) card.style.opacity = '1';
    }
}

function cerrarSesion() {
    if (confirm('¿Cerrar sesión?')) {
        storage.logout();
        window.location.href = '/front/login.html';
    }
}