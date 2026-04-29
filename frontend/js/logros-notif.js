// logros-notif.js — helper para los badges de logros pendientes en el navbar y perfil


// Cuenta logros desbloqueados pero sin reclamar XP.
// Devuelve 0 si no hay sesion o si la peticion falla.
async function contarLogrosPendientes() {
    if (!auth.estaLogueado()) return 0;
    try {
        const misLogros = await api.logros.misLogros();
        return misLogros.filter(l => l.xp_reclamado === false).length;
    } catch (err) {
        console.warn('[logros-notif] contarLogrosPendientes', err);
        return 0;
    }
}

// Pinta un badge dentro de un contenedor. Si n=0 quita el que haya.
function pintarBadge(contenedor, n, variante = '') {
    if (!contenedor) return;

    // borramos el badge anterior si lo hay
    const viejo = contenedor.querySelector('.notif-badge');
    if (viejo) viejo.remove();

    if (n <= 0) return;

    const badge = document.createElement('span');
    badge.className = variante === 'navbar'
        ? 'notif-badge notif-badge--navbar'
        : 'notif-badge';
    // si n>99 mostramos "99+"
    badge.textContent = n > 99 ? '99+' : String(n);
    contenedor.appendChild(badge);
}

// Actualiza los badges en navbar (link Logros) y en el perfil (stat de Nivel).
async function actualizarBadgesLogros() {
    const n = await contarLogrosPendientes();

    const linkLogros = document.querySelector('.nav-link[href$="logros.html"]');
    pintarBadge(linkLogros, n, 'navbar');

    const statNivel = document.getElementById('statNivel');
    if (statNivel) {
        pintarBadge(statNivel.parentElement, n, '');
    }
}
