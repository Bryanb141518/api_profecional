// ============================================
// configuracion.js — Conectado a la API real
// ============================================

let pasoActual = 1;
const totalPasos = 4;

// ── Navegación ────────────────────────────

function siguiente() {
    if (!validarPaso(pasoActual)) return;
    if (pasoActual < totalPasos) {
        mostrarPaso(pasoActual + 1);
    }
}

function anterior() {
    if (pasoActual > 1) {
        mostrarPaso(pasoActual - 1);
    }
}

function mostrarPaso(paso) {
    document.querySelectorAll('.form-step').forEach(p => p.classList.remove('active'));
    const el = document.getElementById('form-step-' + paso);
    if (el) el.classList.add('active');

    document.querySelectorAll('.step').forEach(function(s, i) {
        s.classList.remove('active', 'completado');
        if (i + 1 === paso) s.classList.add('active');
        if (i + 1 < paso)   s.classList.add('completado');
    });

    pasoActual = paso;
}

function validarPaso(paso) {
    var ok = true;

    if (paso === 1) {
        var universidad = document.getElementById('universidad').value.trim();
        var carrera     = document.getElementById('carrera').value.trim();
        var errU = document.getElementById('error-universidad');
        var errC = document.getElementById('error-carrera');
        if (!universidad) { if (errU) errU.textContent = 'Obligatorio'; ok = false; }
        else               { if (errU) errU.textContent = ''; }
        if (!carrera)      { if (errC) errC.textContent = 'Obligatorio'; ok = false; }
        else               { if (errC) errC.textContent = ''; }
    }

    if (paso === 2) {
        var total  = parseInt(document.getElementById('total-creditos').value);
        var min    = parseInt(document.getElementById('min-creditos').value);
        var max    = parseInt(document.getElementById('max-creditos').value);
        var errT   = document.getElementById('error-total-creditos');
        var errMin = document.getElementById('error-min-creditos');
        var errMax = document.getElementById('error-max-creditos');

        if (!total || total < 120 || total > 300) {
            if (errT) errT.textContent = 'Entre 120 y 300'; ok = false;
        } else { if (errT) errT.textContent = ''; }

        if (!min || min < 6) {
            if (errMin) errMin.textContent = 'Mínimo 6'; ok = false;
        } else { if (errMin) errMin.textContent = ''; }

        if (!max || max < min) {
            if (errMax) errMax.textContent = 'Debe ser mayor al mínimo'; ok = false;
        } else { if (errMax) errMax.textContent = ''; }
    }

    if (paso === 3) {
        var semestre = parseInt(document.getElementById('semestre-actual').value);
        var errS     = document.getElementById('error-semestre-actual');
        if (!semestre || semestre < 1) {
            if (errS) errS.textContent = 'Mínimo 1'; ok = false;
        } else { if (errS) errS.textContent = ''; }
    }

    if (paso === 4) {
        var nota   = parseFloat(document.getElementById('nota-minima').value);
        var escala = parseFloat(document.getElementById('escala').value);
        var errN   = document.getElementById('error-nota-minima');
        if (!nota || nota <= 0 || nota >= escala) {
            if (errN) errN.textContent = 'Entre 0 y ' + escala; ok = false;
        } else { if (errN) errN.textContent = ''; }
    }

    return ok;
}

function calcularSemestres() {
    var total = parseInt(document.getElementById('total-creditos').value) || 0;
    var min   = parseInt(document.getElementById('min-creditos').value)   || 0;
    var box   = document.getElementById('box-semestres');
    var est   = document.getElementById('semestres-estimados');
    if (total > 0 && min > 0) {
        var semestres = Math.ceil(total / min);
        if (est) est.textContent = semestres;
        if (box) box.style.display = 'block';
    }
}

function actualizarNotaMinima() {
    var escala   = parseFloat(document.getElementById('escala').value) || 5.0;
    var input    = document.getElementById('nota-minima');
    var sugerida = document.getElementById('nota-sugerida');
    var sugerido = escala === 5.0 ? 3.0 : escala === 10.0 ? 6.0 : 60;
    if (input && !input.value) input.value = sugerido;
    if (sugerida) sugerida.textContent = 'Sugerida: ' + sugerido;
}

function volverSeleccion() {
    window.location.href = '/front/seleccion.html';
}

async function crear() {
    if (!validarPaso(4)) return;

    var getData  = function(id) { var el = document.getElementById(id); return el ? el.value.trim() : ''; };
    var getInt   = function(id) { var el = document.getElementById(id); return el ? (parseInt(el.value) || 0) : 0; };
    var getFloat = function(id) { var el = document.getElementById(id); return el ? (parseFloat(el.value) || 0) : 0; };

    var totalCreditos = getInt('total-creditos');
    var minCreditos   = getInt('min-creditos');
    var totalSems     = minCreditos > 0 ? Math.ceil(totalCreditos / minCreditos) : 10;

    var payload = {
        universidad:                   getData('universidad'),
        carrera:                       getData('carrera'),
        facultad:                      getData('facultad'),
        modalidad:                     getData('modalidad'),
        creditos_para_graduarse:       totalCreditos,
        creditos_minimos_por_semestre: minCreditos,
        creditos_maximos_por_semestre: getInt('max-creditos'),
        semestre_actual:               getInt('semestre-actual'),
        total_semestres:               totalSems,
        creditos_aprobados:            getInt('creditos-aprobados'),
        promedio_minimo_carrera:       getFloat('promedio-actual') || 3.0,
        escala_notas:                  getData('escala') || '5.0',
        nota_minima_global:            getFloat('nota-minima'),
        anno_ingreso:                  getInt('año-ingreso') || new Date().getFullYear(),
    };

    var btnCrear   = document.getElementById('btn-crear');
    var btnTexto   = btnCrear ? btnCrear.querySelector('.btn-text')   : null;
    var btnSpinner = btnCrear ? btnCrear.querySelector('.btn-spinner') : null;

    if (btnCrear)   btnCrear.disabled = true;
    if (btnTexto)   btnTexto.style.display   = 'none';
    if (btnSpinner) btnSpinner.style.display  = 'inline';

    try {
        var res  = await storage.fetchAuth('/perfil-universitario/', {
            method: 'POST',
            body:   JSON.stringify(payload),
        });
        var data = await res.json();

        if (res.ok) {
            var usuario = storage.get('usuario_actual') || {};
            usuario.tiene_perfil = true;
            storage.set('usuario_actual', usuario);
            toast('¡Perfil configurado correctamente!', 'exito');
            setTimeout(function() {
                window.location.href = '/front/dashboard.html';
            }, 1200);
        } else {
            var errores = Object.values(data).flat().join(' | ');
            toast(errores || 'Error al guardar perfil', 'error');
        }

    } catch (err) {
        toast('No se pudo conectar al servidor', 'error');
        console.error(err);
    } finally {
        if (btnCrear)   btnCrear.disabled = false;
        if (btnTexto)   btnTexto.style.display   = '';
        if (btnSpinner) btnSpinner.style.display  = 'none';
    }
}

// ── Inicializar ──────────────────────────
if (false) {
    window.location.href = '/front/login.html';
} else {
    mostrarPaso(1);
    actualizarNotaMinima();
}
