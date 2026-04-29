// logros.js — pagina de logros (nivel 3)


// Diccionario de iconos por codigo de logro.
// Si el back añade un logro nuevo cuyo codigo no este aqui se ve el de por defecto.
const ICONOS_LOGROS = {
    // vistas
    PRIMERA_FUNCION:   '🎬',
    CINEFILO:          '🎞️',
    CINEFILO_PROGRESO: '📽️',
    MAESTRO_CINEFILO:  '🏆',
    // reseñas
    CRITICO_PROCESO:   '✍️',
    PERIODISTA:        '📰',
    PLUMA_DE_ORO:      '🖋️',
    // perfil
    CON_CRITERIO:      '⭐',
    PLANIFICADOR:      '📋',
    // especiales
    MARATONISTA:       '🏃',
    DOBLE_FUNCION:     '🎭',
    TRASNOCHADOR:      '🌙',
    NOSTALGICO:        '📺',
    HATER_PROFESIONAL: '💀',
    // sociales
    SOCIABLE:          '🤝',
    CONVERSADOR:       '💬',
    CONEXION_MUTUA:    '🔗',
    INFLUENCER:        '👑',
};

const ICONO_POR_DEFECTO = '🏆';
const XP_POR_NIVEL = 100;   // formula: nivel = (xp_total // 100) + 1

let todosLogros = [];
let filtroActivo = 'todos';   // 'todos' | 'desbloqueados' | 'bloqueados' | 'reclamables'


function mostrarToast(msg, tipo = 'ok') {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { t.className = 'toast'; }, 2800);
}

// fecha ISO -> "22 abr"
function formatearFecha(iso) {
    if (!iso) return '';
    try {
        const f = new Date(iso);
        const meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
        return `${f.getDate()} ${meses[f.getMonth()]}`;
    } catch (err) {
        console.warn('[logros] fecha rara', iso, err);
        return '';
    }
}


// Cabecera con nivel, XP y barra de progreso.
// Misma formula que el back: si tienes 250 XP estas a nivel 3 con 50/100 hacia el 4.
function renderizarCabecera(perfil, logros) {
    const xpTotal = perfil.xp_total || 0;
    const nivel   = perfil.nivel    || 1;

    const xpEnNivel        = xpTotal % XP_POR_NIVEL;
    const xpSiguienteNivel = XP_POR_NIVEL;
    const porcentaje       = (xpEnNivel / xpSiguienteNivel) * 100;

    document.getElementById('lblNivel').textContent    = nivel;
    document.getElementById('lblXpTotal').textContent  = `${xpTotal} XP`;
    document.getElementById('lblXpSiguiente').textContent =
        `${xpEnNivel} / ${xpSiguienteNivel} XP para nivel ${nivel + 1}`;

    // animacion de la barra: arranca en 0% y se llena al valor real
    const barra = document.getElementById('barraFill');
    barra.style.width = '0%';
    setTimeout(() => { barra.style.width = `${porcentaje}%`; }, 100);

    const desbloqueados = logros.filter(l => l.desbloqueado).length;
    document.getElementById('lblResumen').textContent =
        `${desbloqueados} de ${logros.length} logros desbloqueados`;
}


// Tarjeta de un logro
function renderizarTarjeta(logro) {
    const icono = ICONOS_LOGROS[logro.codigo] || ICONO_POR_DEFECTO;
    const desbloqueado = logro.desbloqueado;
    const yaReclamado  = logro.xp_reclamado === true;
    const pendienteReclamar = desbloqueado && !yaReclamado;

    const claseCard = desbloqueado
        ? 'logro-card logro-card--desbloqueado'
        : 'logro-card logro-card--bloqueado';

    // pie de la tarjeta segun estado:
    //   bloqueado -> badge gris con XP
    //   desbloqueado pero no reclamado -> boton "Reclamar"
    //   desbloqueado y reclamado -> "XP reclamados"
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

    const cintaNuevo = pendienteReclamar
        ? `<div class="logro-cinta-nuevo">NUEVO</div>`
        : '';

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


// Pinta el grid segun el filtro activo.
// Hacemos un mapa de filtros para no usar switch/case con breaks.
const FILTROS = {
    todos:          () => true,
    desbloqueados:  l => l.desbloqueado,
    bloqueados:     l => !l.desbloqueado,
    reclamables:    l => l.desbloqueado && l.xp_reclamado === false,
};

function renderizarGrid() {
    const grid = document.getElementById('gridLogros');
    const fnFiltro = FILTROS[filtroActivo] || FILTROS.todos;
    const lista = todosLogros.filter(fnFiltro);

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


function actualizarBadgeReclamables() {
    const n = todosLogros.filter(l => l.desbloqueado && l.xp_reclamado === false).length;
    document.getElementById('badgeReclamables').textContent = n;
}


// Reclamar XP de un logro.
// El backend pide el id_usuario_logro pero /api/logros/todos no lo devuelve,
// asi que pedimos mis-logros para mapear codigo -> id_usuario_logro.
async function reclamarXP(codigo, boton) {
    try {
        boton.disabled = true;
        boton.textContent = 'Reclamando...';

        const misLogros = await api.logros.misLogros();
        const registro  = misLogros.find(ul => ul.codigo === codigo);

        if (!registro) {
            mostrarToast('No se encontró el logro', 'error');
            boton.disabled = false;
            return;
        }

        const resultado = await api.logros.reclamar(registro.id_usuario_logro);

        mostrarToast(resultado.detail || `+${registro.xp} XP reclamados`, 'ok');

        // recargamos para que se actualice barra y nivel
        await cargarTodo();

    } catch (err) {
        console.warn('[logros] reclamarXP', err);
        mostrarToast(err.message || 'Error al reclamar XP', 'error');
        boton.disabled = false;
        boton.textContent = `Reclamar +? XP`;
    }
}


async function cargarTodo() {
    try {
        // perfil para XP/nivel y todos los logros del catalogo
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
        console.warn('[logros] cargarTodo', err);
        mostrarToast(err.message || 'Error al cargar los logros', 'error');
        document.getElementById('gridLogros').innerHTML = `
            <div class="estado-vacio" style="grid-column:1/-1">
                <p class="estado-vacio__titulo">No se pudieron cargar los logros</p>
                <p class="estado-vacio__desc">Comprueba que el servidor está en marcha.</p>
            </div>
        `;
    }
}


document.addEventListener('DOMContentLoaded', () => {
    renderNav('../');
    actualizarBadgesLogros();

    if (!auth.estaLogueado()) {
        window.location.href = 'login.html';
        return;
    }

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

    cargarTodo();
});
