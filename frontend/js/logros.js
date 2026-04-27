// js/logros.js — Lógica de la página de logros (nivel 3)

// ───────────────────────────────────────────────────────────────
// DICCIONARIO DE ICONOS
// Asignamos un emoji representativo a cada logro según su código.
// Si el backend añade un logro nuevo con un código no previsto,
// se muestra el icono por defecto 🏆.
// ───────────────────────────────────────────────────────────────
const ICONOS_LOGROS = {
    // Vistas
    PRIMERA_FUNCION:   '🎬',
    CINEFILO:          '🎞️',
    CINEFILO_PROGRESO: '📽️',
    MAESTRO_CINEFILO:  '🏆',
    // Reseñas
    CRITICO_PROCESO:   '✍️',
    PERIODISTA:        '📰',
    PLUMA_DE_ORO:      '🖋️',
    // Perfil
    CON_CRITERIO:      '⭐',
    PLANIFICADOR:      '📋',
    // Especiales
    MARATONISTA:       '🏃',
    DOBLE_FUNCION:     '🎭',
    TRASNOCHADOR:      '🌙',
    NOSTALGICO:        '📺',
    HATER_PROFESIONAL: '💀',
    // Sociales
    SOCIABLE:          '🤝',
    CONVERSADOR:       '💬',
    CONEXION_MUTUA:    '🔗',
    INFLUENCER:        '👑',
};

const ICONO_POR_DEFECTO = '🏆';
const XP_POR_NIVEL = 100;   // cada 100 XP sube de nivel

// Estado global de la página
let todosLogros = [];      // lista completa que devuelve /api/logros/todos
let filtroActivo = 'todos'; // 'todos' | 'desbloqueados' | 'bloqueados' | 'reclamables'

// ───────────────────────────────────────────────────────────────
// UTILIDADES
// ───────────────────────────────────────────────────────────────
function mostrarToast(msg, tipo = 'ok') {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { t.className = 'toast'; }, 2800);
}

// Formatea fecha ISO a "22 abr" (día + mes corto)
function formatearFecha(iso) {
    if (!iso) return '';
    try {
        const f = new Date(iso);
        const meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
        return `${f.getDate()} ${meses[f.getMonth()]}`;
    } catch {
        return '';
    }
}

// ───────────────────────────────────────────────────────────────
// RENDER DE LA CABECERA (nivel, XP, barra de progreso)
// ───────────────────────────────────────────────────────────────
function renderizarCabecera(perfil, logros) {
    const xpTotal   = perfil.xp_total || 0;
    const nivel     = perfil.nivel    || 1;

    // XP relativa al nivel actual: si tienes 250 XP y cada nivel son 100,
    // estás en el nivel 2 con 50 XP de progreso hacia el nivel 3.
    const xpEnNivel       = xpTotal % XP_POR_NIVEL;
    const xpSiguienteNivel = XP_POR_NIVEL;
    const porcentaje       = (xpEnNivel / xpSiguienteNivel) * 100;

    document.getElementById('lblNivel').textContent    = nivel;
    document.getElementById('lblXpTotal').textContent  = `${xpTotal} XP`;
    document.getElementById('lblXpSiguiente').textContent =
        `${xpEnNivel} / ${xpSiguienteNivel} XP para nivel ${nivel + 1}`;

    // Animación de la barra: primero a 0, luego al valor real (efecto de llenado)
    const barra = document.getElementById('barraFill');
    barra.style.width = '0%';
    setTimeout(() => { barra.style.width = `${porcentaje}%`; }, 100);

    // Resumen: X de Y logros desbloqueados
    const desbloqueados = logros.filter(l => l.desbloqueado).length;
    document.getElementById('lblResumen').textContent =
        `${desbloqueados} de ${logros.length} logros desbloqueados`;
}

// ───────────────────────────────────────────────────────────────
// RENDER DE UNA TARJETA DE LOGRO
// ───────────────────────────────────────────────────────────────
function renderizarTarjeta(logro) {
    const icono = ICONOS_LOGROS[logro.codigo] || ICONO_POR_DEFECTO;
    const desbloqueado = logro.desbloqueado;
    const yaReclamado  = logro.xp_reclamado === true;
    const pendienteReclamar = desbloqueado && !yaReclamado;

    // Clase de la tarjeta según estado
    const claseCard = desbloqueado
        ? 'logro-card logro-card--desbloqueado'
        : 'logro-card logro-card--bloqueado';

    // Contenido del pie según estado:
    //  - Bloqueado:         badge gris con XP pendiente
    //  - Desbloqueado + no reclamado: botón "Reclamar XP"
    //  - Desbloqueado + reclamado:    etiqueta gris "XP reclamados"
    let pieHTML = '';
    if (!desbloqueado) {
        pieHTML = `<span class="logro-xp-badge">+${logro.xp} XP</span>`;
    } else if (pendienteReclamar) {
        pieHTML = `
            <button class="logro-btn-reclamar"
                    onclick="reclamarXP('${escapeHTML(logro.codigo)}', this)">
                Reclamar +${logro.xp} XP
            </button>
        `;
    } else {
        pieHTML = `<span class="logro-xp-reclamado">+${logro.xp} XP reclamados</span>`;
    }

    // Cinta "NUEVO" solo si está pendiente de reclamar
    const cintaNuevo = pendienteReclamar
        ? `<div class="logro-cinta-nuevo">NUEVO</div>`
        : '';

    // Fecha de desbloqueo si existe
    const fecha = desbloqueado && logro.desbloqueado_el
        ? `<div class="logro-fecha">${formatearFecha(logro.desbloqueado_el)}</div>`
        : '';

    return `
        <div class="${claseCard}" data-codigo="${escapeHTML(logro.codigo)}">
            ${cintaNuevo}
            ${fecha}
            <div class="logro-icono">${icono}</div>
            <div class="logro-nombre">${escapeHTML(logro.nombre)}</div>
            <div class="logro-desc">${escapeHTML(logro.descripcion)}</div>
            <div class="logro-pie">${pieHTML}</div>
        </div>
    `;
}

// ───────────────────────────────────────────────────────────────
// RENDER DEL GRID COMPLETO según el filtro activo
// ───────────────────────────────────────────────────────────────
function renderizarGrid() {
    const grid = document.getElementById('gridLogros');

    // Aplicar filtro
    let lista;
    switch (filtroActivo) {
        case 'desbloqueados':
            lista = todosLogros.filter(l => l.desbloqueado);
            break;
        case 'bloqueados':
            lista = todosLogros.filter(l => !l.desbloqueado);
            break;
        case 'reclamables':
            lista = todosLogros.filter(l => l.desbloqueado && l.xp_reclamado === false);
            break;
        default:
            lista = todosLogros;
    }

    if (lista.length === 0) {
        grid.innerHTML = `
            <div class="estado-vacio" style="grid-column:1/-1">
                <p class="estado-vacio__titulo">No hay logros aquí</p>
                <p class="estado-vacio__desc">
                    ${filtroActivo === 'reclamables'
                        ? 'No tienes XP pendiente de reclamar.'
                        : 'Prueba con otro filtro.'}
                </p>
            </div>
        `;
        return;
    }

    grid.innerHTML = lista.map(renderizarTarjeta).join('');
}

// ───────────────────────────────────────────────────────────────
// ACTUALIZAR EL CONTADOR DEL BOTÓN "RECLAMABLES"
// ───────────────────────────────────────────────────────────────
function actualizarBadgeReclamables() {
    const n = todosLogros.filter(l => l.desbloqueado && l.xp_reclamado === false).length;
    document.getElementById('badgeReclamables').textContent = n;
}

// ───────────────────────────────────────────────────────────────
// RECLAMAR XP DE UN LOGRO
// El endpoint del backend necesita el id_usuario_logro, pero /api/logros/todos
// no lo devuelve. Por eso antes de reclamar pedimos mis-logros para mapear
// código -> id_usuario_logro.
// ───────────────────────────────────────────────────────────────
async function reclamarXP(codigo, boton) {
    try {
        boton.disabled = true;
        boton.textContent = 'Reclamando...';

        // Buscamos el id_usuario_logro para este código
        const misLogros = await api.logros.misLogros();
        const registro  = misLogros.find(ul => ul.codigo === codigo);

        if (!registro) {
            mostrarToast('No se encontró el logro', 'error');
            boton.disabled = false;
            return;
        }

        const resultado = await api.logros.reclamar(registro.id_usuario_logro);

        mostrarToast(resultado.detail || `+${registro.xp} XP reclamados`, 'ok');

        // Recargamos todo para que se actualice la barra de XP y el nivel
        await cargarTodo();

    } catch (err) {
        mostrarToast(err.message || 'Error al reclamar XP', 'error');
        boton.disabled = false;
        boton.textContent = `Reclamar +? XP`;
    }
}

// ───────────────────────────────────────────────────────────────
// CARGA INICIAL / RECARGA COMPLETA
// ───────────────────────────────────────────────────────────────
async function cargarTodo() {
    try {
        // Pedimos en paralelo el perfil (para XP y nivel) y los logros
        const [perfil, logros] = await Promise.all([
            api.usuarios.mePerfil(),
            api.logros.todos(),
        ]);

        todosLogros = logros;

        renderizarCabecera(perfil, logros);
        actualizarBadgeReclamables();
        renderizarGrid();
        actualizarBadgesLogros();

    } catch (err) {
        mostrarToast(err.message || 'Error al cargar los logros', 'error');
        document.getElementById('gridLogros').innerHTML = `
            <div class="estado-vacio" style="grid-column:1/-1">
                <p class="estado-vacio__titulo">No se pudieron cargar los logros</p>
                <p class="estado-vacio__desc">Comprueba que el servidor está en marcha.</p>
            </div>
        `;
    }
}

// ───────────────────────────────────────────────────────────────
// INICIALIZACIÓN
// ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    renderNav('../');
    actualizarBadgesLogros();

    // Si no está logueado, a login
    if (!auth.estaLogueado()) {
        window.location.href = 'login.html';
        return;
    }

    // Listeners de los filtros
    document.querySelectorAll('.logros-filtro').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.logros-filtro').forEach(b =>
                b.classList.remove('logros-filtro--activo')
            );
            btn.classList.add('logros-filtro--activo');
            filtroActivo = btn.dataset.filtro;
            renderizarGrid();
        });
    });

    // Carga inicial
    cargarTodo();
});