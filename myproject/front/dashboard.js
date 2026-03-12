// ============================================
// dashboard.js — v5 conectado a API real
// ============================================

class Dashboard {
    constructor() {
        this.perfil          = null;
        this.perfilId        = null;  // ID del perfil en BD
        this.semestresCache  = {};    // { numeroSemestre: { id, materias[] } }
        this.materiaActualId = null;
        this.semestreModalId = null;
        this._semActividadId = null;
        this._modoEdicion    = false;
        this._materiaEditId  = null;
        this.grafica         = null;
        this.init();
    }

    // ══════════════════════════════════════════
    // INIT
    // ══════════════════════════════════════════

    async init() {
        if (!storage.hasValidSession()) {
            window.location.href = 'login.html';
            return;
        }

        this.mostrarCargando(true);

        try {
            // Cargar perfil desde la API
            const res  = await storage.fetchAuth('/perfil-universitario/detalle/');
            const data = await res.json();

            if (!res.ok) {
                window.location.href = 'seleccion.html';
                return;
            }

            // Normalizar nombres del perfil (API → estructura local)
            this.perfil = {
                universidad:         data.universidad,
                carrera:             data.carrera,
                facultad:            data.facultad || '',
                modalidad:           data.modalidad || '',
                nombreUsuario:       data.nombre_usuario || storage.get('usuario_actual')?.nombre || '',
                totalCreditos:       data.creditos_para_graduarse,
                minCreditosSemestre: data.creditos_minimos_por_semestre,
                maxCreditosSemestre: data.creditos_maximos_por_semestre,
                semestreActual:      data.semestre_actual,
                totalSemestres:      data.total_semestres,
                creditosAprobados:   data.creditos_aprobados,
                escalaNotas:         data.escala_notas || '5.0',
                notaMinima:          data.nota_minima_global,
                añoIngreso:          data.anno_ingreso,
            };

            // Cargar semestres desde la API
            await this.cargarSemestres();

        } catch (err) {
            console.error('Error cargando perfil:', err);
            // Intentar usar caché local como fallback
            this.perfil = storage.get('perfil_universitario');
            if (!this.perfil) {
                window.location.href = 'seleccion.html';
                return;
            }
        }

        this.mostrarCargando(false);
        this.aplicarTemaGuardado();
        this.actualizarTituloPagina();
        this.iniciarParticulas();
        this.renderizarPerfil();
        this.renderizarResumen();
        this.renderizarBloques();
        this.renderizarMaterias();
        this.verificarAlertas();
        this.configurarEventos();
        this.programarAlertas();
    }

    mostrarCargando(mostrar) {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay && mostrar) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.style.cssText = `
                position:fixed;inset:0;background:rgba(8,14,26,0.85);
                display:flex;align-items:center;justify-content:center;
                z-index:9999;font-size:1.1rem;color:#06b6d4;
                flex-direction:column;gap:16px;`;
            overlay.innerHTML = `
                <div style="width:40px;height:40px;border:3px solid rgba(6,182,212,0.2);
                    border-top-color:#06b6d4;border-radius:50%;animation:spin 0.8s linear infinite"></div>
                <span>Cargando tu perfil...</span>`;
            const style = document.createElement('style');
            style.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
            document.head.appendChild(style);
            document.body.appendChild(overlay);
        }
        if (overlay) overlay.style.display = mostrar ? 'flex' : 'none';
    }

    // ══════════════════════════════════════════
    // CARGA DE DATOS DESDE API
    // ══════════════════════════════════════════

    async cargarSemestres() {
        try {
            const res  = await storage.fetchAuth('/semestres/');
            const data = await res.json();
            if (!res.ok) return;

            // Construir cache de semestres con materias y notas
            for (const sem of data) {
                const materiasRes  = await storage.fetchAuth(`/semestres/${sem.id}/materias/`);
                const materiasData = await materiasRes.json();

                const materias = materiasData.map(m => ({
                    id:          String(m.id),
                    _apiId:      m.id,
                    nombre:      m.nombre,
                    creditos:    m.creditos,
                    totalNotas:  m.total_notas,
                    escala:      m.escala_notas,
                    notaMinima:  parseFloat(m.nota_minima_aprobacion),
                    color:       m.color || '#2563eb',
                    estado:      m.estado,
                    actividades: (m.notas || []).map(n => ({
                        id:          String(n.id),
                        _apiId:      n.id,
                        titulo:      n.titulo,
                        tipo:        n.tipo,
                        porcentaje:  parseFloat(n.porcentaje),
                        nota:        n.valor_obtenido !== null ? parseFloat(n.valor_obtenido) : null,
                        fechaLimite: n.fecha_limite,
                        prioridad:   n.prioridad,
                        descripcion: n.descripcion || '',
                        recordatorio:n.recordatorio || '',
                    })),
                }));

                this.semestresCache[sem.numero] = {
                    id:      sem.id,
                    numero:  sem.numero,
                    estado:  sem.estado,
                    materias,
                };
            }
        } catch (err) {
            console.error('Error cargando semestres:', err);
        }
    }

    async cargarHorario() {
        try {
            const res  = await storage.fetchAuth('/horario/');
            const data = await res.json();
            if (!res.ok) return [];
            return data.map(c => ({
                id:           String(c.id),
                _apiId:       c.id,
                materiaId:    c.materia ? String(c.materia) : null,
                nombreMateria:c.nombre_materia,
                color:        c.color,
                dia:          c.dia,
                horaInicio:   c.hora_inicio,
                duracion:     c.duracion,
                salon:        c.salon || '',
            }));
        } catch (err) {
            console.error('Error cargando horario:', err);
            return [];
        }
    }

    // ══════════════════════════════════════════
    // TEMA
    // ══════════════════════════════════════════

    aplicarTemaGuardado() {
        const temaClaro = storage.get('tema_claro');
        if (temaClaro) {
            document.body.classList.add('tema-claro');
            const cb = document.getElementById('theme-checkbox');
            const lb = document.getElementById('theme-label');
            if (cb) cb.checked = true;
            if (lb) lb.textContent = 'Claro';
        }
    }

    toggleTema(esClaro) {
        if (esClaro) {
            document.body.classList.add('tema-claro');
            const lb = document.getElementById('theme-label');
            if (lb) lb.textContent = 'Claro';
            storage.set('tema_claro', true);
        } else {
            document.body.classList.remove('tema-claro');
            const lb = document.getElementById('theme-label');
            if (lb) lb.textContent = 'Oscuro';
            storage.remove('tema_claro');
        }
    }

    actualizarTituloPagina() {
        document.title = `Semestre ${this.perfil.semestreActual} — ${this.perfil.carrera}`;
    }

    // ══════════════════════════════════════════
    // PARTÍCULAS
    // ══════════════════════════════════════════

    iniciarParticulas() {
        const canvas = document.getElementById('particles-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const resize = () => {
            canvas.width  = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        class Particula {
            constructor() { this.reset(); }
            reset() {
                this.x     = Math.random() * canvas.width;
                this.y     = Math.random() * canvas.height;
                this.vx    = (Math.random() - 0.5) * 0.4;
                this.vy    = (Math.random() - 0.5) * 0.4;
                this.alpha = Math.random() * 0.35 + 0.08;
                this.r     = Math.random() * 1.5 + 0.5;
                this.color = Math.random() > 0.5 ? '37,99,235' : '6,182,212';
            }
            update() {
                this.x += this.vx; this.y += this.vy;
                if (this.x < 0 || this.x > canvas.width ||
                    this.y < 0 || this.y > canvas.height) this.reset();
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${this.color},${this.alpha})`;
                ctx.fill();
            }
        }

        const particulas = Array.from({ length: 80 }, () => new Particula());
        const loop = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < particulas.length; i++) {
                for (let j = i + 1; j < particulas.length; j++) {
                    const dx = particulas[i].x - particulas[j].x;
                    const dy = particulas[i].y - particulas[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 100) {
                        ctx.beginPath();
                        ctx.moveTo(particulas[i].x, particulas[i].y);
                        ctx.lineTo(particulas[j].x, particulas[j].y);
                        ctx.strokeStyle = `rgba(37,99,235,${0.08 * (1 - dist / 100)})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
            particulas.forEach(p => { p.update(); p.draw(); });
            requestAnimationFrame(loop);
        };
        loop();
    }

    // ══════════════════════════════════════════
    // PERFIL HEADER
    // ══════════════════════════════════════════

    renderizarPerfil() {
        const p      = this.perfil;
        const titulo = this.calcularTitulo(p.carrera);
        const nombre = titulo ? `${titulo} ${p.nombreUsuario}` : p.nombreUsuario;

        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('header-universidad',   p.universidad);
        set('header-carrera',       p.carrera);
        set('header-nombre',        p.nombreUsuario);
        set('perfil-nombre',        nombre);
        set('perfil-universidad',   p.universidad);
        set('perfil-carrera',       p.carrera);
        set('num-semestre-actual',  p.semestreActual);
        set('min-sem',              p.minCreditosSemestre);
        set('max-sem',              p.maxCreditosSemestre);

        const avatar = document.getElementById('header-avatar');
        if (avatar) avatar.textContent = (p.nombreUsuario || '?').charAt(0).toUpperCase();

        this.actualizarBarraCreditos();
    }

    calcularTitulo(carrera) {
        const c = (carrera || '').toLowerCase();
        if (c.includes('ingeniería') || c.includes('ingenieria')) return 'Ing.';
        if (c.includes('medicina')   || c.includes('médico'))     return 'Dr.';
        if (c.includes('derecho')    || c.includes('abogacía'))   return 'Abg.';
        if (c.includes('arquitectura'))                            return 'Arq.';
        if (c.includes('psicología') || c.includes('psicologia')) return 'Psic.';
        if (c.includes('administración') || c.includes('administracion')) return 'Adm.';
        if (c.includes('contaduría') || c.includes('contaduria')) return 'Cont.';
        return '';
    }

    actualizarBarraCreditos() {
        const p   = this.perfil;
        const pct = Math.min((p.creditosAprobados / p.totalCreditos) * 100, 100);
        const bar = document.getElementById('barra-creditos');
        const txt = document.getElementById('creditos-texto');
        if (bar) bar.style.width = pct + '%';
        if (txt) txt.textContent = `${p.creditosAprobados} / ${p.totalCreditos} créditos`;
    }

    // ══════════════════════════════════════════
    // RESUMEN
    // ══════════════════════════════════════════

    renderizarResumen() {
        const semestre = this.getSemestreActual();
        const materias = semestre.materias || [];
        const enRiesgo = materias.filter(m => {
            const p = this.calcularPromedioMateria(m);
            return this.calcularEstadoMateria(m, p) === 'riesgo';
        }).length;

        const hoy    = new Date().toISOString().split('T')[0];
        const manana = new Date(Date.now() + 86400000).toISOString().split('T')[0];
        let pendientesHoy = 0;
        materias.forEach(m => {
            m.actividades.forEach(a => {
                if (!a.nota && (a.fechaLimite === hoy || a.fechaLimite === manana))
                    pendientesHoy++;
            });
        });

        const pct = ((this.perfil.creditosAprobados / this.perfil.totalCreditos) * 100).toFixed(1);
        const tarjetas = [
            { valor: materias.length, label: 'Materias',         color: 'azul',     icon: '📚' },
            { valor: enRiesgo,        label: 'En riesgo',        color: 'rojo',     icon: '⚠️' },
            { valor: pendientesHoy,   label: 'Vencen pronto',    color: 'amarillo', icon: '📅' },
            { valor: `${pct}%`,       label: 'Progreso carrera', color: 'verde',    icon: '🎯' },
        ];

        const grid = document.getElementById('resumen-grid');
        if (grid) grid.innerHTML = tarjetas.map((t, i) => `
            <div class="resumen-card ${t.color}" style="animation-delay:${i * 0.07}s">
                <div class="resumen-valor">${t.valor}</div>
                <div class="resumen-label">${t.label}</div>
                <div class="resumen-icon">${t.icon}</div>
            </div>`).join('');
    }

    // ══════════════════════════════════════════
    // BLOQUES
    // ══════════════════════════════════════════

    renderizarBloques() {
        const grid = document.getElementById('bloques-grid');
        if (!grid) return;
        grid.innerHTML = '';
        const p = this.perfil;

        for (let i = 1; i <= p.totalSemestres; i++) {
            const bloque = document.createElement('div');
            bloque.className = 'bloque';
            bloque.style.animationDelay = `${(i - 1) * 0.04}s`;

            if (i < p.semestreActual) {
                bloque.classList.add('completado');
                bloque.textContent = '✓';
                bloque.title   = `Semestre ${i} — Click para ver materias`;
                bloque.onclick = () => this.abrirModalSemestreAnt(i);
            } else if (i === p.semestreActual) {
                bloque.classList.add('actual');
                bloque.textContent = i;
                bloque.title = `Semestre ${i} — En curso`;
            } else {
                bloque.classList.add('futuro');
                bloque.textContent = i;
                bloque.title   = `Semestre ${i} — Pendiente`;
                bloque.onclick = () => toast(`El semestre ${i} aún no ha comenzado`, 'info');
            }
            grid.appendChild(bloque);
        }
    }

    // ══════════════════════════════════════════
    // SEMESTRE HELPERS
    // ══════════════════════════════════════════

    getSemestre(numero) {
        if (!this.semestresCache[numero]) {
            this.semestresCache[numero] = { numero, materias: [], estado: 'pendiente', id: null };
        }
        return this.semestresCache[numero];
    }

    getSemestreActual() {
        return this.getSemestre(this.perfil.semestreActual);
    }

    async _asegurarSemestreEnAPI(numero) {
        let sem = this.semestresCache[numero];
        if (sem && sem.id) return sem;

        // Crear semestre en la API
        const res  = await storage.fetchAuth('/semestres/', {
            method: 'POST',
            body:   JSON.stringify({ numero, estado: 'en_curso' }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error creando semestre');

        if (!this.semestresCache[numero]) this.semestresCache[numero] = { numero, materias: [] };
        this.semestresCache[numero].id     = data.semestre.id;
        this.semestresCache[numero].estado = data.semestre.estado;
        return this.semestresCache[numero];
    }

    // ══════════════════════════════════════════
    // CERRAR SEMESTRE
    // ══════════════════════════════════════════

    confirmarCerrarSemestre() {
        const semestre = this.getSemestreActual();
        const materias = semestre.materias;

        if (materias.length === 0) {
            toast('Agrega al menos una materia antes de cerrar el semestre', 'error');
            return;
        }
        if (this.perfil.semestreActual >= this.perfil.totalSemestres) {
            toast('¡Ya estás en el último semestre!', 'info');
            return;
        }

        const aprobadas = materias.filter(m => this.calcularEstadoMateria(m, this.calcularPromedioMateria(m)) === 'aprobada');
        const perdidas  = materias.filter(m => this.calcularEstadoMateria(m, this.calcularPromedioMateria(m)) === 'perdida');
        const enCurso   = materias.filter(m => {
            const e = this.calcularEstadoMateria(m, this.calcularPromedioMateria(m));
            return e === 'curso' || e === 'riesgo';
        });
        const creditosSem = aprobadas.reduce((s, m) => s + m.creditos, 0);

        const resumenEl = document.getElementById('resumen-cierre');
        if (resumenEl) resumenEl.innerHTML = `
            <div class="resumen-cierre-grid">
                <div class="cierre-item"><span class="cierre-label">Semestre actual</span><span class="cierre-valor">${this.perfil.semestreActual}</span></div>
                <div class="cierre-item"><span class="cierre-label">Aprobadas</span><span class="cierre-valor" style="color:var(--success)">✅ ${aprobadas.length}</span></div>
                <div class="cierre-item"><span class="cierre-label">Perdidas</span><span class="cierre-valor" style="color:var(--danger)">❌ ${perdidas.length}</span></div>
                ${enCurso.length > 0 ? `<div class="cierre-item"><span class="cierre-label">Sin nota final</span><span class="cierre-valor" style="color:var(--warning)">⚠️ ${enCurso.length}</span></div>` : ''}
                <div class="cierre-item"><span class="cierre-label">Créditos ganados</span><span class="cierre-valor">${creditosSem} cr</span></div>
                <div class="cierre-item"><span class="cierre-label">Próximo semestre</span><span class="cierre-valor" style="color:var(--cyan)">${this.perfil.semestreActual + 1}</span></div>
            </div>`;

        document.getElementById('modal-cerrar-sem').classList.add('open');
    }

    async cerrarSemestre() {
        const semestre = this.getSemestreActual();

        try {
            // Marcar semestre como completado en la API
            if (semestre.id) {
                await storage.fetchAuth(`/semestres/${semestre.id}/`, {
                    method: 'PUT',
                    body:   JSON.stringify({ estado: 'completado' }),
                });
            }

            // Actualizar perfil — avanzar semestre_actual
            await storage.fetchAuth('/perfil-universitario/detalle/', {
                method: 'PUT',
                body:   JSON.stringify({ semestre_actual: this.perfil.semestreActual + 1 }),
            });

            this.perfil.semestreActual++;
            cerrarModal('modal-cerrar-sem');
            this.actualizarTituloPagina();
            this.renderizarPerfil();
            this.renderizarResumen();
            this.renderizarBloques();
            this.renderizarMaterias();
            this.verificarAlertas();
            toast(`¡Semestre ${this.perfil.semestreActual - 1} cerrado! Ahora vas en semestre ${this.perfil.semestreActual} 🎓`, 'exito', 4000);

        } catch (err) {
            toast('Error al cerrar el semestre', 'error');
            console.error(err);
        }
    }

    // ══════════════════════════════════════════
    // MODAL SEMESTRE ANTERIOR
    // ══════════════════════════════════════════

    abrirModalSemestreAnt(numeroSemestre) {
        this.semestreModalId = numeroSemestre;
        const semestre = this.getSemestre(numeroSemestre);
        const tituloEl = document.getElementById('modal-sem-titulo');
        if (tituloEl) tituloEl.textContent = `Semestre ${numeroSemestre}`;
        this.renderizarModalSemestreAnt(semestre);
        document.getElementById('modal-semestre-ant').classList.add('open');
    }

    renderizarModalSemestreAnt(semestre) {
        const body = document.getElementById('modal-sem-body');
        if (!body) return;
        const creditosUsados = semestre.materias.reduce((s, m) => s + m.creditos, 0);

        body.innerHTML = `
            <div class="sem-ant-header">
                <span style="color:var(--gray-500);font-size:0.83rem">
                    ${semestre.materias.length} materias · ${creditosUsados} créditos
                </span>
                <button class="btn-agregar-sem-ant"
                    onclick="dashboard.abrirModalMateria(${semestre.numero})">
                    + Agregar materia
                </button>
            </div>
            <div id="materias-sem-ant">
                ${semestre.materias.length === 0
                    ? `<div class="empty-state"><span class="empty-icon">📂</span><p>Sin materias registradas.</p></div>`
                    : semestre.materias.map(m => this.htmlTarjetaMateriaAnt(m, semestre.numero)).join('')
                }
            </div>`;
    }

    htmlTarjetaMateriaAnt(materia, numeroSemestre) {
        const promedio = this.calcularPromedioMateria(materia);
        const estado   = this.calcularEstadoMateria(materia, promedio);
        const pctUsado = materia.actividades.reduce((s, a) => s + a.porcentaje, 0);

        return `
            <div class="materia-card ${estado}" style="margin-bottom:12px">
                <div class="materia-top">
                    <div class="materia-color" style="background:${materia.color}"></div>
                    <div class="materia-info">
                        <div class="materia-nombre">${sanitizeHTML(materia.nombre)}</div>
                        <div class="materia-meta">${materia.creditos} cr · Escala ${materia.escala} · Mín. ${materia.notaMinima}</div>
                    </div>
                    <div class="materia-acciones-top">
                        <button class="btn-icon editar" title="Editar"
                            onclick="dashboard.abrirModalEditarMateria('${materia.id}', ${numeroSemestre})">✏️</button>
                        <button class="btn-icon eliminar" title="Eliminar"
                            onclick="dashboard.eliminarMateria('${materia.id}', ${numeroSemestre})">🗑️</button>
                    </div>
                    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;margin-left:10px">
                        <div class="materia-promedio ${estado}">${promedio !== null ? promedio.toFixed(2) : '—'}</div>
                        <span class="materia-estado-badge badge-${estado}">${this.etiquetaEstado(estado)}</span>
                    </div>
                </div>
                <div class="materia-barra-wrap">
                    <div class="materia-barra">
                        <div class="materia-barra-fill" style="width:${pctUsado}%"></div>
                    </div>
                    <span class="materia-barra-label">${pctUsado}% ingresado</span>
                </div>
                <div class="actividades-wrap">
                    <div class="actividades-titulo">Actividades (${materia.actividades.length}/${materia.totalNotas})</div>
                    <div class="actividades-lista">${this.renderizarActividades(materia, numeroSemestre)}</div>
                    ${materia.actividades.length < materia.totalNotas
                        ? `<button class="btn-agregar-actividad"
                                onclick="dashboard.abrirModalActividadEn('${materia.id}', ${numeroSemestre})">
                                + Agregar actividad
                           </button>` : ''}
                </div>
            </div>`;
    }

    cerrarModalSemestreAnt() {
        document.getElementById('modal-semestre-ant').classList.remove('open');
        this.semestreModalId = null;
    }

    // ══════════════════════════════════════════
    // MATERIAS SEMESTRE ACTUAL
    // ══════════════════════════════════════════

    renderizarMaterias() {
        const grid     = document.getElementById('materias-grid');
        if (!grid) return;
        const semestre = this.getSemestreActual();

        if (!semestre.materias || semestre.materias.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">🎒</span>
                    <p>Aún no hay materias. ¡Agrega tu primera materia!</p>
                </div>`;
            return;
        }

        grid.innerHTML = '';
        semestre.materias.forEach((materia, idx) => {
            const card = this.crearTarjetaMateria(materia);
            card.style.animationDelay = `${idx * 0.07}s`;
            grid.appendChild(card);
        });
    }

    crearTarjetaMateria(materia) {
        const promedio       = this.calcularPromedioMateria(materia);
        const estado         = this.calcularEstadoMateria(materia, promedio);
        const notasFaltantes = materia.totalNotas - materia.actividades.length;
        const pctUsado       = materia.actividades.reduce((s, a) => s + a.porcentaje, 0);
        const numSem         = this.perfil.semestreActual;

        const card = document.createElement('div');
        card.className  = `materia-card ${estado}`;
        card.dataset.id = materia.id;

        card.innerHTML = `
            <div class="materia-top">
                <div class="materia-color" style="background:${materia.color}"></div>
                <div class="materia-info">
                    <div class="materia-nombre">${sanitizeHTML(materia.nombre)}</div>
                    <div class="materia-meta">${materia.creditos} cr · Escala ${materia.escala} · Mín. ${materia.notaMinima}</div>
                </div>
                <div class="materia-acciones-top">
                    <button class="btn-icon editar" title="Editar materia"
                        onclick="dashboard.abrirModalEditarMateria('${materia.id}', ${numSem})">✏️</button>
                    <button class="btn-icon eliminar" title="Eliminar materia"
                        onclick="dashboard.eliminarMateria('${materia.id}', ${numSem})">🗑️</button>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;margin-left:10px">
                    <div class="materia-promedio ${estado}">
                        ${promedio !== null ? promedio.toFixed(2) : '—'}
                    </div>
                    <span class="materia-estado-badge badge-${estado}">${this.etiquetaEstado(estado)}</span>
                </div>
            </div>
            <div class="materia-barra-wrap">
                <div class="materia-barra">
                    <div class="materia-barra-fill" style="width:${pctUsado}%"></div>
                </div>
                <span class="materia-barra-label">${pctUsado}% ingresado</span>
            </div>
            <div class="actividades-wrap">
                <div class="actividades-titulo">
                    Actividades (${materia.actividades.length}/${materia.totalNotas})
                    ${notasFaltantes > 0
                        ? `· <span style="color:var(--warning)">${notasFaltantes} pendientes</span>` : ''}
                </div>
                <div class="actividades-lista">
                    ${this.renderizarActividades(materia, numSem)}
                </div>
                ${materia.actividades.length < materia.totalNotas
                    ? `<button class="btn-agregar-actividad"
                            onclick="dashboard.abrirModalActividad('${materia.id}')">
                            + Agregar actividad
                       </button>` : ''}
            </div>`;
        return card;
    }

    renderizarActividades(materia, numeroSemestre) {
        if (materia.actividades.length === 0) {
            return `<div style="color:var(--gray-500);font-size:0.8rem;padding:6px 0">Sin actividades aún.</div>`;
        }

        const hoy    = new Date().toISOString().split('T')[0];
        const manana = new Date(Date.now() + 86400000).toISOString().split('T')[0];

        return materia.actividades.map(act => {
            const tieneNota = act.nota !== null && act.nota !== undefined && act.nota !== '';
            const notaNum   = parseFloat(act.nota);
            const aprobada  = tieneNota && notaNum >= materia.notaMinima;

            let claseItem = tieneNota ? 'con-nota' : 'sin-nota';
            if (act.fechaLimite === hoy)    claseItem = 'vence-hoy';
            else if (act.fechaLimite === manana) claseItem = 'vence-pronto';

            const claseBadge = tieneNota ? (aprobada ? 'aprobada' : 'perdida') : '';
            const textoFecha = act.fechaLimite ? `· 📅 ${act.fechaLimite}` : '';
            const prioridad  = act.prioridad === 'alta' ? '🔴' : act.prioridad === 'media' ? '🟡' : '🟢';

            return `
                <div class="actividad-item ${claseItem}">
                    <div class="actividad-info">
                        <div class="actividad-titulo">${prioridad} ${sanitizeHTML(act.titulo)}</div>
                        <div class="actividad-detalles">${act.tipo} · ${act.porcentaje}% ${textoFecha}</div>
                    </div>
                    <div class="actividad-acciones">
                        <div class="actividad-nota-badge ${claseBadge}"
                            onclick="dashboard.editarNota('${materia.id}','${act.id}')"
                            title="Click para editar nota">
                            ${tieneNota ? notaNum.toFixed(2) : 'Sin nota'}
                        </div>
                        <button class="btn-eliminar-act" title="Eliminar"
                            onclick="dashboard.eliminarActividad('${materia.id}','${act.id}',${numeroSemestre})">✕</button>
                    </div>
                </div>`;
        }).join('');
    }

    // ══════════════════════════════════════════
    // CÁLCULOS
    // ══════════════════════════════════════════

    calcularPromedioMateria(materia) {
        const conNota = materia.actividades.filter(
            a => a.nota !== null && a.nota !== '' && a.nota !== undefined
        );
        if (conNota.length === 0) return null;
        const totalPct = conNota.reduce((s, a) => s + a.porcentaje, 0);
        if (totalPct === 0) return null;
        return conNota.reduce((s, a) => s + parseFloat(a.nota) * a.porcentaje, 0) / totalPct;
    }

    calcularEstadoMateria(materia, promedio) {
        const todas = materia.actividades.length === materia.totalNotas;
        if (todas && promedio !== null)
            return promedio >= materia.notaMinima ? 'aprobada' : 'perdida';
        if (promedio !== null) {
            const pctUsado    = materia.actividades
                .filter(a => a.nota !== null && a.nota !== '')
                .reduce((s, a) => s + a.porcentaje, 0);
            const pctRestante = 100 - pctUsado;
            const maxAlcanzable = promedio + (parseFloat(materia.escala) * pctRestante / 100);
            if (maxAlcanzable < materia.notaMinima) return 'riesgo';
        }
        return 'curso';
    }

    etiquetaEstado(estado) {
        return { aprobada: '✅ Aprobada', perdida: '❌ Perdida',
                 riesgo: '⚠️ En riesgo', curso: '📖 En curso' }[estado] || 'En curso';
    }

    recalcularTotalCreditos() {
        return Object.values(this.semestresCache).reduce((total, sem) => {
            return total + (sem.materias || [])
                .filter(m => this.calcularEstadoMateria(m, this.calcularPromedioMateria(m)) === 'aprobada')
                .reduce((s, m) => s + m.creditos, 0);
        }, 0);
    }

    // ══════════════════════════════════════════
    // MODAL MATERIA — AGREGAR
    // ══════════════════════════════════════════

    abrirModalMateria(numeroSemestre) {
        const numSem         = numeroSemestre !== null ? numeroSemestre : this.perfil.semestreActual;
        this.semestreModalId = numSem;
        this._modoEdicion    = false;
        this._materiaEditId  = null;

        const tituloEl = document.getElementById('modal-materia-titulo');
        const btnEl    = document.getElementById('btn-guardar-materia');
        const grupoEl  = document.getElementById('grupo-total-notas');
        if (tituloEl) tituloEl.textContent = 'Agregar Materia';
        if (btnEl)    btnEl.textContent    = 'Agregar materia';
        if (grupoEl)  grupoEl.style.display = 'block';
        document.getElementById('form-materia').reset();
        this.limpiarErroresMateria();

        if (numSem === this.perfil.semestreActual) {
            const semestre         = this.getSemestre(numSem);
            const creditosActuales = (semestre.materias || []).reduce((s, m) => s + m.creditos, 0);
            if (creditosActuales >= this.perfil.maxCreditosSemestre) {
                toast(`Máximo de ${this.perfil.maxCreditosSemestre} créditos alcanzado`, 'error');
                return;
            }
        }

        document.getElementById('modal-materia').classList.add('open');
        document.getElementById('form-materia').onsubmit = (e) => {
            e.preventDefault();
            this.guardarMateria(numSem);
        };
    }

    abrirModalEditarMateria(materiaId, numeroSemestre) {
        const semestre = this.getSemestre(numeroSemestre);
        const materia  = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;

        this._modoEdicion    = true;
        this._materiaEditId  = materiaId;
        this.semestreModalId = numeroSemestre;

        const tituloEl = document.getElementById('modal-materia-titulo');
        const btnEl    = document.getElementById('btn-guardar-materia');
        const grupoEl  = document.getElementById('grupo-total-notas');
        if (tituloEl) tituloEl.textContent = 'Editar Materia';
        if (btnEl)    btnEl.textContent    = 'Guardar cambios';
        if (grupoEl)  grupoEl.style.display = 'none';
        this.limpiarErroresMateria();

        document.getElementById('m-nombre').value      = materia.nombre;
        document.getElementById('m-creditos').value    = materia.creditos;
        document.getElementById('m-color').value       = materia.color;
        document.getElementById('m-escala').value      = materia.escala;
        document.getElementById('m-nota-minima').value = materia.notaMinima;

        document.getElementById('modal-materia').classList.add('open');
        document.getElementById('form-materia').onsubmit = (e) => {
            e.preventDefault();
            this.guardarEdicionMateria(materiaId, numeroSemestre);
        };
    }

    async guardarMateria(numeroSemestre) {
        const nombre     = document.getElementById('m-nombre').value.trim();
        const creditos   = parseInt(document.getElementById('m-creditos').value);
        const color      = document.getElementById('m-color').value;
        const escala     = document.getElementById('m-escala').value;
        const notaMinima = parseFloat(document.getElementById('m-nota-minima').value);
        const totalNotas = parseInt(document.getElementById('m-total-notas').value);

        let ok = true;
        if (!nombre)   { this.setModalError('m-nombre', 'Obligatorio'); ok = false; }
        else             this.clearModalError('m-nombre');
        if (!creditos || creditos < 1) { this.setModalError('m-creditos', 'Mínimo 1'); ok = false; }
        else             this.clearModalError('m-creditos');
        if (!notaMinima || notaMinima <= 0 || notaMinima >= parseFloat(escala)) {
            this.setModalError('m-nota-minima', `Entre 0 y ${escala}`); ok = false;
        } else           this.clearModalError('m-nota-minima');
        if (!totalNotas || totalNotas < 1) { this.setModalError('m-total-notas', 'Mínimo 1'); ok = false; }
        else             this.clearModalError('m-total-notas');
        if (!ok) return;

        try {
            const sem = await this._asegurarSemestreEnAPI(numeroSemestre);

            const res  = await storage.fetchAuth(`/semestres/${sem.id}/materias/`, {
                method: 'POST',
                body:   JSON.stringify({
                    nombre, creditos, color,
                    escala_notas:           escala,
                    nota_minima_aprobacion: notaMinima,
                    total_notas:            totalNotas,
                }),
            });
            const data = await res.json();

            if (!res.ok) {
                toast(Object.values(data).flat().join(' | ') || 'Error al guardar', 'error');
                return;
            }

            const nuevaMateria = {
                id:          String(data.materia.id),
                _apiId:      data.materia.id,
                nombre, creditos, color,
                escala, notaMinima, totalNotas,
                actividades: [],
            };

            if (!this.semestresCache[numeroSemestre]) this.semestresCache[numeroSemestre] = { numero: numeroSemestre, materias: [] };
            this.semestresCache[numeroSemestre].materias.push(nuevaMateria);

            this.cerrarModalMateria();
            if (numeroSemestre === this.perfil.semestreActual) {
                this.renderizarMaterias();
                this.renderizarResumen();
                this.verificarAlertas();
            } else {
                this.renderizarModalSemestreAnt(this.getSemestre(numeroSemestre));
            }
            toast(`Materia "${nombre}" agregada`, 'exito');

        } catch (err) {
            toast('Error al guardar la materia', 'error');
            console.error(err);
        }
    }

    async guardarEdicionMateria(materiaId, numeroSemestre) {
        const nombre     = document.getElementById('m-nombre').value.trim();
        const creditos   = parseInt(document.getElementById('m-creditos').value);
        const color      = document.getElementById('m-color').value;
        const escala     = document.getElementById('m-escala').value;
        const notaMinima = parseFloat(document.getElementById('m-nota-minima').value);

        let ok = true;
        if (!nombre)   { this.setModalError('m-nombre', 'Obligatorio'); ok = false; }
        else             this.clearModalError('m-nombre');
        if (!creditos || creditos < 1) { this.setModalError('m-creditos', 'Mínimo 1'); ok = false; }
        else             this.clearModalError('m-creditos');
        if (!notaMinima || notaMinima <= 0 || notaMinima >= parseFloat(escala)) {
            this.setModalError('m-nota-minima', `Entre 0 y ${escala}`); ok = false;
        } else           this.clearModalError('m-nota-minima');
        if (!ok) return;

        const semestre = this.getSemestre(numeroSemestre);
        const materia  = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;

        try {
            const res  = await storage.fetchAuth(`/materias/${materia._apiId}/`, {
                method: 'PUT',
                body:   JSON.stringify({
                    nombre, creditos, color,
                    escala_notas:           escala,
                    nota_minima_aprobacion: notaMinima,
                }),
            });
            if (!res.ok) { toast('Error al actualizar', 'error'); return; }

            materia.nombre = nombre; materia.creditos = creditos;
            materia.color  = color;  materia.escala   = escala;
            materia.notaMinima = notaMinima;
            this.perfil.creditosAprobados = this.recalcularTotalCreditos();
            this.cerrarModalMateria();

            if (numeroSemestre === this.perfil.semestreActual) {
                this.renderizarMaterias();
                this.renderizarResumen();
                this.actualizarBarraCreditos();
            } else {
                this.renderizarModalSemestreAnt(this.getSemestre(numeroSemestre));
            }
            toast(`Materia "${nombre}" actualizada`, 'exito');

        } catch (err) {
            toast('Error al actualizar la materia', 'error');
            console.error(err);
        }
    }

    cerrarModalMateria() {
        document.getElementById('modal-materia').classList.remove('open');
        this._modoEdicion   = false;
        this._materiaEditId = null;
    }

    async eliminarMateria(materiaId, numeroSemestre) {
        const semestre = this.getSemestre(numeroSemestre);
        const materia  = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;
        if (!confirm(`¿Eliminar "${materia.nombre}"? Se borrarán todas sus actividades.`)) return;

        try {
            await storage.fetchAuth(`/materias/${materia._apiId}/`, { method: 'DELETE' });

            semestre.materias = semestre.materias.filter(m => m.id !== materiaId);
            this.perfil.creditosAprobados = this.recalcularTotalCreditos();

            if (numeroSemestre === this.perfil.semestreActual) {
                this.renderizarMaterias();
                this.renderizarResumen();
                this.actualizarBarraCreditos();
                this.verificarAlertas();
            } else {
                this.renderizarModalSemestreAnt(semestre);
                this.actualizarBarraCreditos();
            }
            toast(`Materia "${materia.nombre}" eliminada`, 'info');

        } catch (err) {
            toast('Error al eliminar la materia', 'error');
            console.error(err);
        }
    }

    // ══════════════════════════════════════════
    // MODAL ACTIVIDAD
    // ══════════════════════════════════════════

    abrirModalActividad(materiaId) {
        this.materiaActualId = materiaId;
        this._semActividadId = this.perfil.semestreActual;
        document.getElementById('form-actividad').reset();
        document.getElementById('modal-actividad').classList.add('open');
        document.getElementById('form-actividad').onsubmit = (e) => {
            e.preventDefault(); this.guardarActividad();
        };
    }

    abrirModalActividadEn(materiaId, numeroSemestre) {
        this.materiaActualId = materiaId;
        this._semActividadId = numeroSemestre;
        document.getElementById('form-actividad').reset();
        document.getElementById('modal-actividad').classList.add('open');
        document.getElementById('form-actividad').onsubmit = (e) => {
            e.preventDefault(); this.guardarActividad();
        };
    }

    cerrarModalActividad() {
        document.getElementById('modal-actividad').classList.remove('open');
        this.materiaActualId = null;
    }

    async guardarActividad() {
        const titulo       = document.getElementById('a-titulo').value.trim();
        const tipo         = document.getElementById('a-tipo').value;
        const porcentaje   = parseInt(document.getElementById('a-porcentaje').value);
        const nota         = document.getElementById('a-nota').value;
        const fecha        = document.getElementById('a-fecha').value;
        const prioridad    = document.getElementById('a-prioridad').value;
        const descripcion  = document.getElementById('a-descripcion').value.trim();
        const recordatorio = document.getElementById('a-recordatorio').value.trim();

        let ok = true;
        if (!titulo) { this.setModalError('a-titulo', 'Obligatorio'); ok = false; }
        else           this.clearModalError('a-titulo');
        if (!porcentaje || porcentaje < 1 || porcentaje > 100) {
            this.setModalError('a-porcentaje', 'Entre 1 y 100'); ok = false;
        } else         this.clearModalError('a-porcentaje');
        if (!ok) return;

        const numSem   = this._semActividadId || this.perfil.semestreActual;
        const semestre = this.getSemestre(numSem);
        const materia  = semestre.materias.find(m => m.id === this.materiaActualId);
        if (!materia) return;

        const pctUsado = materia.actividades.reduce((s, a) => s + a.porcentaje, 0);
        if (pctUsado + porcentaje > 100) {
            this.setModalError('a-porcentaje', `Solo quedan ${100 - pctUsado}%`);
            return;
        }

        try {
            const res  = await storage.fetchAuth(`/materias/${materia._apiId}/notas/`, {
                method: 'POST',
                body:   JSON.stringify({
                    titulo, tipo, porcentaje,
                    valor_obtenido: nota !== '' ? parseFloat(nota) : null,
                    fecha_limite:   fecha || null,
                    prioridad, descripcion,
                    recordatorio,
                }),
            });
            const data = await res.json();

            if (!res.ok) {
                toast(Object.values(data).flat().join(' | ') || 'Error al guardar', 'error');
                return;
            }

            const nuevaAct = {
                id:          String(data.nota.id),
                _apiId:      data.nota.id,
                titulo, tipo, porcentaje,
                nota:        nota !== '' ? parseFloat(nota) : null,
                fechaLimite: fecha || null,
                prioridad, descripcion, recordatorio,
            };

            materia.actividades.push(nuevaAct);
            this.perfil.creditosAprobados = this.recalcularTotalCreditos();
            this.cerrarModalActividad();

            if (numSem === this.perfil.semestreActual) {
                this.renderizarMaterias();
                this.renderizarResumen();
                this.actualizarBarraCreditos();
                this.verificarAlertas();
            } else {
                this.renderizarModalSemestreAnt(this.getSemestre(numSem));
                this.actualizarBarraCreditos();
            }
            toast(`Actividad "${titulo}" guardada`, 'exito');

        } catch (err) {
            toast('Error al guardar la actividad', 'error');
            console.error(err);
        }
    }

    async eliminarActividad(materiaId, actividadId, numeroSemestre) {
        const semestre  = this.getSemestre(numeroSemestre);
        const materia   = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;
        const actividad = materia.actividades.find(a => a.id === actividadId);
        if (!actividad) return;
        if (!confirm(`¿Eliminar "${actividad.titulo}"?`)) return;

        try {
            await storage.fetchAuth(`/notas/${actividad._apiId}/`, { method: 'DELETE' });

            materia.actividades = materia.actividades.filter(a => a.id !== actividadId);
            this.perfil.creditosAprobados = this.recalcularTotalCreditos();

            if (numeroSemestre === this.perfil.semestreActual) {
                this.renderizarMaterias();
                this.renderizarResumen();
                this.actualizarBarraCreditos();
                this.verificarAlertas();
            } else {
                this.renderizarModalSemestreAnt(this.getSemestre(numeroSemestre));
                this.actualizarBarraCreditos();
            }
            toast('Actividad eliminada', 'info');

        } catch (err) {
            toast('Error al eliminar la actividad', 'error');
            console.error(err);
        }
    }

    async editarNota(materiaId, actividadId) {
        let materia = null;
        let numSem  = null;

        for (const [num, sem] of Object.entries(this.semestresCache)) {
            const m = (sem.materias || []).find(m => m.id === materiaId);
            if (m) { materia = m; numSem = parseInt(num); break; }
        }
        if (!materia) return;

        const actividad = materia.actividades.find(a => a.id === actividadId);
        if (!actividad) return;

        const nueva = prompt(
            `Nota para "${actividad.titulo}"\nEscala: ${materia.escala} · Mínimo: ${materia.notaMinima}`,
            actividad.nota !== null ? actividad.nota : ''
        );
        if (nueva === null) return;

        const notaNum = parseFloat(nueva);
        if (nueva !== '' && (isNaN(notaNum) || notaNum < 0 || notaNum > parseFloat(materia.escala))) {
            toast(`La nota debe estar entre 0 y ${materia.escala}`, 'error');
            return;
        }

        try {
            await storage.fetchAuth(`/notas/${actividad._apiId}/`, {
                method: 'PUT',
                body:   JSON.stringify({ valor_obtenido: nueva !== '' ? notaNum : null }),
            });

            actividad.nota = nueva !== '' ? notaNum : null;
            this.perfil.creditosAprobados = this.recalcularTotalCreditos();

            if (numSem === this.perfil.semestreActual) {
                this.renderizarMaterias();
                this.renderizarResumen();
            } else {
                this.renderizarModalSemestreAnt(this.getSemestre(numSem));
            }
            this.actualizarBarraCreditos();
            this.verificarAlertas();
            toast('Nota actualizada', 'exito');

        } catch (err) {
            toast('Error al actualizar la nota', 'error');
            console.error(err);
        }
    }

    // ══════════════════════════════════════════
    // HISTORIAL
    // ══════════════════════════════════════════

    renderizarHistorial() {
        const lista   = document.getElementById('historial-lista');
        const statsEl = document.getElementById('historial-stats');
        if (!lista) return;

        const historial = [];
        Object.values(this.semestresCache).forEach(sem => {
            (sem.materias || []).forEach(m => {
                const promedio = this.calcularPromedioMateria(m);
                const estado   = this.calcularEstadoMateria(m, promedio);
                if (estado === 'aprobada' || estado === 'perdida') {
                    historial.push({
                        materiaId: m.id, semestre: sem.numero,
                        nombre: m.nombre, creditos: m.creditos,
                        promedio, estado,
                    });
                }
            });
        });

        if (historial.length === 0) {
            lista.innerHTML   = `<div class="empty-state"><span class="empty-icon">📋</span><p>Aún no hay materias en el historial.</p></div>`;
            if (statsEl) statsEl.innerHTML = '';
            return;
        }

        const aprobadas = historial.filter(h => h.estado === 'aprobada');
        const perdidas  = historial.filter(h => h.estado === 'perdida');
        const promGen   = aprobadas.length > 0
            ? (aprobadas.reduce((s, h) => s + h.promedio, 0) / aprobadas.length).toFixed(2) : '—';
        const mejor = historial.reduce((a, b) => (!a || b.promedio > a.promedio ? b : a), null);
        const peor  = historial.reduce((a, b) => (!a || b.promedio < a.promedio ? b : a), null);

        if (statsEl) statsEl.innerHTML = `
            <div class="stat-card"><div class="stat-valor">${promGen}</div><div class="stat-label">Promedio general</div></div>
            <div class="stat-card"><div class="stat-valor" style="color:var(--success)">${aprobadas.length}</div><div class="stat-label">Aprobadas</div></div>
            <div class="stat-card"><div class="stat-valor" style="color:var(--danger)">${perdidas.length}</div><div class="stat-label">Perdidas</div></div>
            <div class="stat-card"><div class="stat-valor">${this.perfil.creditosAprobados}</div><div class="stat-label">Créditos aprobados</div></div>
            ${mejor ? `<div class="stat-card"><div class="stat-valor" style="color:var(--success);font-size:1rem">${sanitizeHTML(mejor.nombre)}</div><div class="stat-label">Mejor (${mejor.promedio.toFixed(2)})</div></div>` : ''}
            ${peor  ? `<div class="stat-card"><div class="stat-valor" style="color:var(--danger);font-size:1rem">${sanitizeHTML(peor.nombre)}</div><div class="stat-label">Más baja (${peor.promedio.toFixed(2)})</div></div>` : ''}`;

        const porSemestre = {};
        historial.forEach(h => {
            if (!porSemestre[h.semestre]) porSemestre[h.semestre] = [];
            porSemestre[h.semestre].push(h);
        });

        lista.innerHTML = Object.keys(porSemestre).sort((a, b) => a - b).map(sem => `
            <div class="historial-semestre">
                <div class="historial-sem-titulo">📚 Semestre ${sem}</div>
                ${porSemestre[sem].map(h => `
                    <div class="historial-materia">
                        <div>
                            <span class="hm-nombre">${h.estado === 'aprobada' ? '✅' : '❌'} ${sanitizeHTML(h.nombre)}</span>
                            <span class="hm-creditos"> · ${h.creditos} cr</span>
                        </div>
                        <span class="hm-nota ${h.estado}">${h.promedio.toFixed(2)}</span>
                    </div>`).join('')}
            </div>`).join('');
    }

    // ══════════════════════════════════════════
    // ESTADÍSTICAS
    // ══════════════════════════════════════════

    renderizarEstadisticas() {
        const p   = this.perfil;
        const pct = ((p.creditosAprobados / p.totalCreditos) * 100).toFixed(1);

        const statsGrid = document.getElementById('stats-grid');
        if (statsGrid) statsGrid.innerHTML = `
            <div class="stat-card"><div class="stat-valor">${pct}%</div><div class="stat-label">Progreso carrera</div></div>
            <div class="stat-card"><div class="stat-valor">${p.semestreActual}</div><div class="stat-label">Semestre actual</div></div>
            <div class="stat-card"><div class="stat-valor">${p.totalSemestres - p.semestreActual}</div><div class="stat-label">Semestres restantes</div></div>
            <div class="stat-card"><div class="stat-valor">${p.totalCreditos - p.creditosAprobados}</div><div class="stat-label">Créditos faltantes</div></div>`;
        this.renderizarGrafica();
    }

    renderizarGrafica() {
        const canvas = document.getElementById('grafica-rendimiento');
        if (!canvas) return;

        const porSemestre = {};
        Object.values(this.semestresCache).forEach(sem => {
            (sem.materias || []).forEach(m => {
                const promedio = this.calcularPromedioMateria(m);
                if (promedio !== null) {
                    if (!porSemestre[sem.numero]) porSemestre[sem.numero] = [];
                    porSemestre[sem.numero].push(promedio);
                }
            });
        });

        const keys   = Object.keys(porSemestre).sort((a, b) => a - b);
        const labels = keys.map(s => `Sem. ${s}`);
        const datos  = keys.map(k => (porSemestre[k].reduce((a, b) => a + b, 0) / porSemestre[k].length).toFixed(2));

        if (this.grafica) this.grafica.destroy();

        this.grafica = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Promedio',
                    data: datos,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6,182,212,0.07)',
                    borderWidth: 3,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#06b6d4',
                    pointRadius: 7,
                    pointHoverRadius: 10,
                    tension: 0.4,
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(13,21,38,0.95)',
                        borderColor: 'rgba(37,99,235,0.4)',
                        borderWidth: 1,
                        titleColor: '#06b6d4',
                        bodyColor: '#e2e8f0',
                        callbacks: { label: ctx => `Promedio: ${ctx.raw}` }
                    }
                },
                scales: {
                    y: {
                        min: 0, max: parseFloat(this.perfil.escalaNotas),
                        grid:  { color: 'rgba(255,255,255,0.04)' },
                        ticks: { color: 'rgba(255,255,255,0.4)', font: { family: 'DM Sans' } }
                    },
                    x: {
                        grid:  { display: false },
                        ticks: { color: 'rgba(255,255,255,0.4)', font: { family: 'DM Sans' } }
                    }
                }
            }
        });
    }

    // ══════════════════════════════════════════
    // ALERTAS
    // ══════════════════════════════════════════

    verificarAlertas() {
        const contenedor = document.getElementById('alertas-section');
        if (!contenedor) return;
        contenedor.innerHTML = '';
        const semestre = this.getSemestreActual();
        const hoy      = new Date().toISOString().split('T')[0];
        const manana   = new Date(Date.now() + 86400000).toISOString().split('T')[0];
        const alertas  = [];

        semestre.materias.forEach(materia => {
            const promedio = this.calcularPromedioMateria(materia);
            const estado   = this.calcularEstadoMateria(materia, promedio);
            if (estado === 'riesgo')
                alertas.push({ tipo: 'riesgo', texto: `⚠️ ${materia.nombre} está en riesgo matemático.` });
            materia.actividades.forEach(act => {
                if (!act.nota && act.fechaLimite) {
                    if (act.fechaLimite === hoy)
                        alertas.push({ tipo: 'fecha', texto: `🔴 "${act.titulo}" en ${materia.nombre} vence HOY.` });
                    else if (act.fechaLimite === manana)
                        alertas.push({ tipo: 'fecha', texto: `🟡 "${act.titulo}" en ${materia.nombre} vence mañana.` });
                }
            });
        });

        alertas.forEach((a, i) => {
            const div = document.createElement('div');
            div.className = `alerta ${a.tipo}`;
            div.style.animationDelay = `${i * 0.08}s`;
            div.textContent = a.texto;
            contenedor.appendChild(div);
        });
    }

    programarAlertas() {
        setInterval(() => this.verificarAlertas(), 3600000);
    }

    // ══════════════════════════════════════════
    // MODAL PERFIL
    // ══════════════════════════════════════════

    abrirModalPerfil() {
        const p      = this.perfil;
        const titulo = this.calcularTitulo(p.carrera);
        const nombre = titulo ? `${titulo} ${p.nombreUsuario}` : p.nombreUsuario;
        const pct    = ((p.creditosAprobados / p.totalCreditos) * 100).toFixed(1);

        const bodyEl = document.getElementById('perfil-modal-body');
        if (!bodyEl) return;
        bodyEl.innerHTML = `
            <div class="perfil-modal-avatar">${(p.nombreUsuario || '?').charAt(0).toUpperCase()}</div>
            <div class="perfil-modal-nombre">${sanitizeHTML(nombre)}</div>
            <div class="perfil-modal-info">
                ${[
                    ['Universidad', p.universidad],
                    ['Carrera',     p.carrera],
                    p.facultad ? ['Facultad', p.facultad] : null,
                    ['Modalidad',   p.modalidad || '—'],
                    ['Semestre',    `${p.semestreActual} / ${p.totalSemestres}`],
                    ['Créditos',    `${p.creditosAprobados} / ${p.totalCreditos}`],
                    ['Progreso',    `${pct}%`],
                    ['Escala',      `0 — ${p.escalaNotas}`],
                    ['Nota mínima', p.notaMinima],
                    p.añoIngreso ? ['Año ingreso', p.añoIngreso] : null,
                ].filter(Boolean).map(([label, valor]) => `
                    <div class="perfil-info-item">
                        <span class="perfil-info-label">${label}</span>
                        <span class="perfil-info-valor">${sanitizeHTML(String(valor))}</span>
                    </div>`).join('')}
            </div>`;

        document.getElementById('modal-perfil').classList.add('open');
    }

    cerrarModalPerfil() {
        document.getElementById('modal-perfil').classList.remove('open');
    }

    // ══════════════════════════════════════════
    // HORARIO
    // ══════════════════════════════════════════

    async renderizarHorario() {
        const grid = document.getElementById('horario-grid');
        if (!grid) return;

        const horario  = await this.cargarHorario();
        const dias     = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];
        const horas    = [];
        for (let h = 6; h <= 20; h++) horas.push(h);

        const semestre  = this.getSemestreActual();
        const selectMat = document.getElementById('h-materia');
        if (selectMat) {
            selectMat.innerHTML = '<option value="">— Selecciona —</option>';
            semestre.materias.forEach(m => {
                selectMat.innerHTML += `<option value="${m._apiId}" data-color="${m.color}">${sanitizeHTML(m.nombre)}</option>`;
            });
        }

        let html = `<div class="horario-header"></div>`;
        dias.forEach(d => { html += `<div class="horario-header">${d}</div>`; });

        horas.forEach(hora => {
            const horaLabel = hora < 12 ? `${hora}:00 AM`
                : hora === 12 ? '12:00 PM'
                : `${hora - 12}:00 PM`;
            html += `<div class="horario-hora">${horaLabel}</div>`;

            dias.forEach((_, diaIdx) => {
                const clase   = horario.find(c => c.dia === diaIdx && c.horaInicio === hora);
                const ocupada = horario.find(c => c.dia === diaIdx && hora > c.horaInicio && hora < c.horaInicio + c.duracion);

                if (clase) {
                    const color = clase.color || '#2563eb';
                    html += `
                        <div class="horario-celda">
                            <div class="horario-bloque"
                                style="background:${color};grid-row:span ${clase.duracion}"
                                onclick="dashboard.eliminarClaseHorario('${clase.id}', ${clase._apiId})"
                                title="Click para eliminar · ${clase.nombreMateria}${clase.salon ? ' · ' + clase.salon : ''}">
                                <div class="horario-bloque-nombre">${sanitizeHTML(clase.nombreMateria)}</div>
                                <div class="horario-bloque-hora">${horaLabel}${clase.salon ? ' · ' + sanitizeHTML(clase.salon) : ''}</div>
                            </div>
                        </div>`;
                } else if (!ocupada) {
                    html += `
                        <div class="horario-celda" onclick="dashboard.abrirModalHorarioEn(${diaIdx}, ${hora})">
                            <div class="horario-celda-vacia">+</div>
                        </div>`;
                } else {
                    html += `<div class="horario-celda"></div>`;
                }
            });
        });

        grid.innerHTML = html;
    }

    abrirModalHorario() {
        document.getElementById('modal-horario').classList.add('open');
    }

    abrirModalHorarioEn(dia, hora) {
        const diaEl  = document.getElementById('h-dia');
        const horaEl = document.getElementById('h-hora');
        if (diaEl)  diaEl.value  = dia;
        if (horaEl) horaEl.value = hora;
        this.abrirModalHorario();
    }

    async guardarClaseHorario() {
        const materiaApiId = document.getElementById('h-materia').value;
        const dia          = parseInt(document.getElementById('h-dia').value);
        const horaInicio   = parseInt(document.getElementById('h-hora').value);
        const duracion     = parseInt(document.getElementById('h-duracion').value);
        const salon        = document.getElementById('h-salon').value.trim();

        if (!materiaApiId) { toast('Selecciona una materia', 'error'); return; }

        const semestre = this.getSemestreActual();
        const materia  = semestre.materias.find(m => String(m._apiId) === String(materiaApiId));

        try {
            const res  = await storage.fetchAuth('/horario/', {
                method: 'POST',
                body:   JSON.stringify({
                    materia:       materiaApiId,
                    nombre_materia:materia ? materia.nombre : '',
                    color:         materia ? materia.color : '#2563eb',
                    dia, hora_inicio: horaInicio, duracion, salon,
                }),
            });
            const data = await res.json();

            if (!res.ok) {
                toast(data.error || 'Error al guardar clase', 'error');
                return;
            }

            cerrarModal('modal-horario');
            this.renderizarHorario();
            toast('Clase agregada al horario ✅', 'exito');

        } catch (err) {
            toast('Error al guardar la clase', 'error');
            console.error(err);
        }
    }

    async eliminarClaseHorario(claseId, apiId) {
        if (!confirm('¿Eliminar esta clase del horario?')) return;
        try {
            await storage.fetchAuth(`/horario/${apiId}/`, { method: 'DELETE' });
            this.renderizarHorario();
            toast('Clase eliminada', 'info');
        } catch (err) {
            toast('Error al eliminar la clase', 'error');
        }
    }

    async limpiarHorario() {
        if (!confirm('¿Limpiar todo el horario?')) return;
        try {
            await storage.fetchAuth('/horario/', { method: 'DELETE' });
            this.renderizarHorario();
            toast('Horario limpiado', 'info');
        } catch (err) {
            toast('Error al limpiar el horario', 'error');
        }
    }

    // ══════════════════════════════════════════
    // HERRAMIENTAS
    // ══════════════════════════════════════════

    renderizarHerramientas() {
        this.renderizarRitmo();
        this.poblarSelectsHerramientas();
    }

    renderizarRitmo() {
        const p             = this.perfil;
        const pctSemestral  = p.semestreActual / p.totalSemestres;
        const pctCreditos   = p.creditosAprobados / p.totalCreditos;
        const diff          = pctCreditos - pctSemestral;
        const creditosIdeal = Math.round(pctSemestral * p.totalCreditos);

        let emoji, texto, color, subtexto;
        if (diff >= 0.05)       { emoji = '🚀'; texto = '¡Vas adelantado!';    color = 'var(--success)'; subtexto = `Llevas el ${(pctCreditos*100).toFixed(1)}% de créditos con solo el ${(pctSemestral*100).toFixed(1)}% del tiempo. ¡Excelente ritmo!`; }
        else if (diff >= -0.05) { emoji = '✅'; texto = 'Vas en buen ritmo';   color = 'var(--cyan)';    subtexto = `Estás exactamente donde deberías. Mantén el ritmo para graduarte en ${p.totalSemestres - p.semestreActual + 1} semestres.`; }
        else if (diff >= -0.15) { emoji = '⚠️'; texto = 'Vas un poco atrasado';color = 'var(--warning)'; subtexto = `Tienes el ${(pctCreditos*100).toFixed(1)}% de créditos pero vas en el ${(pctSemestral*100).toFixed(1)}% del tiempo.`; }
        else                    { emoji = '🔴'; texto = 'Vas atrasado';         color = 'var(--danger)';  subtexto = `Llevas un déficit significativo de créditos. Habla con tu asesor académico.`; }

        const ritmoEl = document.getElementById('ritmo-indicador');
        if (!ritmoEl) return;
        ritmoEl.innerHTML = `
            <div class="ritmo-emoji">${emoji}</div>
            <div class="ritmo-texto" style="color:${color}">${texto}</div>
            <div class="ritmo-subtexto">${subtexto}</div>
            <div class="ritmo-barra-wrap">
                <div class="ritmo-barra-labels">
                    <span>0 cr</span>
                    <span>Ideal: ${creditosIdeal} cr</span>
                    <span>Meta: ${p.totalCreditos} cr</span>
                </div>
                <div class="ritmo-barra">
                    <div class="ritmo-fill-ideal" style="width:${(pctSemestral*100).toFixed(1)}%"></div>
                    <div class="ritmo-fill-real" style="width:${(pctCreditos*100).toFixed(1)}%;background:${color};opacity:0.7"></div>
                </div>
            </div>
            <div style="display:flex;gap:24px;font-size:0.8rem;color:var(--gray-500)">
                <span>📍 Real: <strong style="color:${color}">${p.creditosAprobados} cr</strong></span>
                <span>🎯 Ideal ahora: <strong style="color:var(--cyan)">${creditosIdeal} cr</strong></span>
                <span>🏁 Meta: <strong style="color:white">${p.totalCreditos} cr</strong></span>
            </div>`;
    }

    poblarSelectsHerramientas() {
        const semestre = this.getSemestreActual();
        const opciones = semestre.materias.map(m =>
            `<option value="${m.id}">${sanitizeHTML(m.nombre)}</option>`
        ).join('');
        const placeholder = '<option value="">— Selecciona una materia —</option>';

        const calcEl = document.getElementById('calc-materia');
        const simEl  = document.getElementById('sim-materia');
        if (calcEl) calcEl.innerHTML = placeholder + opciones;
        if (simEl)  simEl.innerHTML  = placeholder + opciones;

        const calcRes = document.getElementById('calc-resultado');
        const simRes  = document.getElementById('sim-resultado');
        const simCtrl = document.getElementById('sim-controles');
        if (calcRes) calcRes.classList.remove('visible');
        if (simRes)  simRes.classList.remove('visible');
        if (simCtrl) simCtrl.innerHTML = '';
    }

    calcularNotaNecesaria() {
        const materiaId = document.getElementById('calc-materia').value;
        const resultado = document.getElementById('calc-resultado');
        const valorEl   = document.getElementById('calc-valor');
        const labelEl   = document.getElementById('calc-label');
        if (!materiaId) { resultado.classList.remove('visible'); return; }

        const semestre = this.getSemestreActual();
        const materia  = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;

        const conNota    = materia.actividades.filter(a => a.nota !== null && a.nota !== '');
        const sinNota    = materia.actividades.filter(a => a.nota === null || a.nota === '');
        const pctConNota = conNota.reduce((s, a) => s + a.porcentaje, 0);
        const pctSinNota = sinNota.reduce((s, a) => s + a.porcentaje, 0);
        const promedioActual = conNota.length > 0
            ? conNota.reduce((s, a) => s + parseFloat(a.nota) * a.porcentaje, 0) / 100 : 0;

        const escala        = parseFloat(materia.escala);
        const notaMinima    = materia.notaMinima;
        const pctRestante   = pctSinNota + (100 - pctConNota - pctSinNota);
        const notaNecesaria = pctRestante > 0
            ? ((notaMinima - promedioActual) * 100) / pctRestante : null;

        resultado.classList.add('visible');

        if (notaNecesaria === null) {
            valorEl.textContent = '—'; valorEl.style.color = 'var(--gray-500)';
            labelEl.textContent = 'No hay actividades pendientes.';
        } else if (notaNecesaria <= 0) {
            valorEl.textContent = '¡Ya aprobaste!'; valorEl.style.color = 'var(--success)';
            labelEl.textContent = `Con tus notas actuales ya superas el mínimo de ${notaMinima}.`;
        } else if (notaNecesaria > escala) {
            valorEl.textContent = 'Imposible'; valorEl.style.color = 'var(--danger)';
            labelEl.textContent = `Necesitarías ${notaNecesaria.toFixed(2)} pero el máximo es ${escala}.`;
        } else {
            valorEl.textContent = notaNecesaria.toFixed(2);
            valorEl.style.color = (notaNecesaria / escala) > 0.8 ? 'var(--warning)' : 'var(--success)';
            labelEl.textContent = `Necesitas mínimo ${notaNecesaria.toFixed(2)} en las ${sinNota.length} actividad(es) restantes.`;
        }
    }

    cargarSimulador() {
        const materiaId = document.getElementById('sim-materia').value;
        const controles = document.getElementById('sim-controles');
        const resultado = document.getElementById('sim-resultado');
        controles.innerHTML = ''; resultado.classList.remove('visible');
        if (!materiaId) return;

        const semestre = this.getSemestreActual();
        const materia  = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;

        const escala  = parseFloat(materia.escala);
        const sinNota = materia.actividades.filter(a => a.nota === null || a.nota === '');

        if (sinNota.length === 0) {
            controles.innerHTML = `<p style="color:var(--gray-500);font-size:0.85rem">Esta materia ya tiene todas las notas.</p>`;
            const prom = this.calcularPromedioMateria(materia);
            document.getElementById('sim-valor').textContent = prom !== null ? prom.toFixed(2) : '—';
            document.getElementById('sim-valor').style.color = prom >= materia.notaMinima ? 'var(--success)' : 'var(--danger)';
            document.getElementById('sim-label').textContent = prom >= materia.notaMinima ? '✅ Aprobada' : '❌ Perdida';
            resultado.classList.add('visible');
            return;
        }

        controles.innerHTML = sinNota.map(act => `
            <div class="sim-slider-wrap">
                <div class="sim-slider-label">
                    <span>${sanitizeHTML(act.titulo)} <small style="opacity:0.5">(${act.porcentaje}%)</small></span>
                    <strong id="val_${act.id}">${(escala / 2).toFixed(1)}</strong>
                </div>
                <input type="range" class="sim-slider" id="sl_${act.id}"
                    min="0" max="${escala}" step="${escala >= 10 ? 0.5 : 0.1}"
                    value="${escala / 2}"
                    oninput="dashboard.actualizarSimulador('${materiaId}')">
            </div>`).join('');

        this.actualizarSimulador(materiaId);
    }

    actualizarSimulador(materiaId) {
        const semestre = this.getSemestreActual();
        const materia  = semestre.materias.find(m => m.id === materiaId);
        if (!materia) return;
        const escala  = parseFloat(materia.escala);
        const sinNota = materia.actividades.filter(a => a.nota === null || a.nota === '');

        const notasSimuladas = sinNota.map(act => {
            const slider = document.getElementById(`sl_${act.id}`);
            const val    = slider ? parseFloat(slider.value) : escala / 2;
            const strong = document.getElementById(`val_${act.id}`);
            if (strong) strong.textContent = val.toFixed(1);
            return { porcentaje: act.porcentaje, nota: val };
        });

        const conNota   = materia.actividades.filter(a => a.nota !== null && a.nota !== '');
        let totalPuntos = conNota.reduce((s, a) => s + parseFloat(a.nota) * a.porcentaje, 0);
        let totalPct    = conNota.reduce((s, a) => s + a.porcentaje, 0);
        notasSimuladas.forEach(n => { totalPuntos += n.nota * n.porcentaje; totalPct += n.porcentaje; });

        const promedioSim = totalPct > 0 ? totalPuntos / totalPct : 0;
        const aprobada    = promedioSim >= materia.notaMinima;

        document.getElementById('sim-valor').textContent = promedioSim.toFixed(2);
        document.getElementById('sim-valor').style.color = aprobada ? 'var(--success)' : 'var(--danger)';
        document.getElementById('sim-label').textContent = aprobada
            ? `✅ Aprobarías con ${promedioSim.toFixed(2)}`
            : `❌ Perderías con ${promedioSim.toFixed(2)} (necesitas: ${materia.notaMinima})`;
        document.getElementById('sim-resultado').classList.add('visible');
    }

    // ══════════════════════════════════════════
    // NAVEGACIÓN
    // ══════════════════════════════════════════

    mostrarSeccion(id, el) {
        document.querySelectorAll('.seccion').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const sec = document.getElementById(`sec-${id}`);
        if (sec) sec.classList.add('active');
        if (el)  el.classList.add('active');

        if (window.innerWidth <= 768)
            document.getElementById('sidebar').classList.remove('open');

        if (id === 'historial')    this.renderizarHistorial();
        if (id === 'estadisticas') this.renderizarEstadisticas();
        if (id === 'semestres')    this.renderizarSemestresLista();
        if (id === 'horario')      this.renderizarHorario();
        if (id === 'herramientas') this.renderizarHerramientas();
    }

    renderizarSemestresLista() {
        const lista = document.getElementById('semestres-lista');
        if (!lista) return;
        lista.innerHTML = '';
        const p = this.perfil;

        for (let i = 1; i <= p.semestreActual; i++) {
            const semestre    = this.semestresCache[i] || { numero: i, materias: [] };
            const esActual    = i === p.semestreActual;
            const creditosSem = (semestre.materias || []).reduce((s, m) => s + m.creditos, 0);

            const item = document.createElement('div');
            item.className = 'semestre-item';
            item.style.animationDelay = `${(i - 1) * 0.06}s`;
            item.innerHTML = `
                <div class="semestre-item-header">
                    <span class="semestre-item-titulo">Semestre ${i}</span>
                    <span class="semestre-item-estado ${esActual ? 'estado-curso' : 'estado-anterior'}">
                        ${esActual ? 'En curso' : 'Anterior'}
                    </span>
                </div>
                <div class="semestre-item-meta">
                    <span>${(semestre.materias || []).length} materias</span>
                    <span>${creditosSem} créditos</span>
                </div>`;

            item.onclick = esActual
                ? () => this.mostrarSeccion('semestre', document.querySelector('.nav-item'))
                : () => this.abrirModalSemestreAnt(i);

            lista.appendChild(item);
        }
    }

    // ══════════════════════════════════════════
    // SESIÓN
    // ══════════════════════════════════════════

    async cerrarSesion() {
        if (!confirm('¿Cerrar sesión?')) return;
        try {
            await storage.fetchAuth('/logout/', {
                method: 'POST',
                body:   JSON.stringify({ refresh: storage.getRefresh() }),
            });
        } catch (e) { /* silencioso */ }
        storage.logout();
        window.location.href = 'login.html';
    }

    // ══════════════════════════════════════════
    // HELPERS MODALES
    // ══════════════════════════════════════════

    setModalError(id, msg) {
        const input = document.getElementById(id);
        const err   = document.getElementById('error-' + id);
        if (input) input.style.borderColor = 'var(--danger)';
        if (err)   err.textContent = msg;
    }

    clearModalError(id) {
        const input = document.getElementById(id);
        const err   = document.getElementById('error-' + id);
        if (input) input.style.borderColor = '';
        if (err)   err.textContent = '';
    }

    limpiarErroresMateria() {
        ['m-nombre', 'm-creditos', 'm-nota-minima', 'm-total-notas'].forEach(id => {
            this.clearModalError(id);
        });
    }

    configurarEventos() {
        document.addEventListener('click', (e) => {
            const sidebar = document.getElementById('sidebar');
            if (sidebar && window.innerWidth <= 768 &&
                sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !e.target.classList.contains('menu-toggle')) {
                sidebar.classList.remove('open');
            }
        });
    }
}

// ══════════════════════════════════════════
// FUNCIONES GLOBALES
// ══════════════════════════════════════════

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

function cerrarModal(id) {
    document.getElementById(id).classList.remove('open');
}

function cerrarModalSiOverlay(event, id) {
    if (event.target === event.currentTarget) {
        cerrarModal(id);
        if (id === 'modal-semestre-ant' && dashboard)
            dashboard.semestreModalId = null;
    }
}

// ── Cargar Chart.js e inicializar ──────────────────────
const chartScript  = document.createElement('script');
chartScript.src    = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
chartScript.onload = () => { dashboard = new Dashboard(); };
document.head.appendChild(chartScript);

let dashboard;