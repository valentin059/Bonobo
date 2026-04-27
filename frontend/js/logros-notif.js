// js/logros-notif.js — Helper para mostrar el badge de logros pendientes

/**
 * Cuenta cuántos logros tiene el usuario desbloqueados pero sin reclamar.
 * Devuelve 0 si no hay sesión o si falla la petición (silencioso).
 */
async function contarLogrosPendientes() {
    if (!auth.estaLogueado()) return 0;
    try {
        const misLogros = await api.logros.misLogros();
        return misLogros.filter(l => l.xp_reclamado === false).length;
    } catch {
        return 0;
    }
}

/**
 * Pinta un badge de notificación dentro de un elemento.
 * Si n = 0, borra el badge existente.
 *
 * @param {HTMLElement} contenedor - Elemento donde añadir el badge
 * @param {number} n - Número a mostrar (0 oculta el badge)
 * @param {string} variante - '' (default) o 'navbar' para estilos específicos
 */
function pintarBadge(contenedor, n, variante = '') {
    if (!contenedor) return;

    // borra el badge anterior si existe
    const viejo = contenedor.querySelector('.notif-badge');
    if (viejo) viejo.remove();

    if (n <= 0) return;  // nada que mostrar

    const badge = document.createElement('span');
    badge.className = variante === 'navbar'
        ? 'notif-badge notif-badge--navbar'
        : 'notif-badge';
    // si el número es > 99, mostrar "99+"
    badge.textContent = n > 99 ? '99+' : String(n);
    contenedor.appendChild(badge);
}

/**
 * Actualiza los badges de logros en toda la página:
 *  - el badge del enlace "Logros" en el navbar
 *  - el badge de la stat de nivel en el perfil (si existe)
 */
async function actualizarBadgesLogros() {
    const n = await contarLogrosPendientes();

    // Badge en el link "Logros" del navbar
    const linkLogros = document.querySelector('.nav-link[href$="logros.html"]');
    pintarBadge(linkLogros, n, 'navbar');

    // Badge sobre el número de nivel en el perfil
    const statNivel = document.getElementById('statNivel');
    if (statNivel) {
        pintarBadge(statNivel.parentElement, n, '');
    }
}