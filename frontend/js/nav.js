// js/nav.js — Barra de navegación compartida
// Inyecta el navbar en cualquier página que incluya este script.
// Detecta automáticamente si el usuario está logueado y ajusta los enlaces.

// Renderiza la barra de navegación en el elemento con id="nav-placeholder".
// base: ruta relativa al directorio raíz ('' desde index.html, '../' desde pages/).
function renderNav(base = '') {
    const usuario = auth.getUsuario();
    const logueado = auth.estaLogueado();

    // Bloque de autenticación: varía según el estado de sesión
    const authHTML = logueado ? `
        <div class="nav-user-info">
            <a href="${base}pages/perfil.html" class="nav-username">
                ${usuario?.avatar_url
                    ? `<img src="${usuario.avatar_url}" alt="" class="nav-avatar">`
                    : `<div class="nav-avatar nav-avatar--placeholder"></div>`
                }
                ${usuario?.username || 'Perfil'}
            </a>
            <button class="nav-btn nav-btn--ghost" id="btnLogout">Salir</button>
        </div>
    ` : `
        <div class="nav-auth">
            <a href="${base}pages/login.html" class="nav-btn nav-btn--ghost">Entrar</a>
            <a href="${base}pages/registro.html" class="nav-btn nav-btn--primary">Registrarse</a>
        </div>
    `;

    // HTML completo del navbar
    const navHTML = `
        <nav class="navbar">
            <div class="nav-inner">

                <!-- Logo -->
                <a href="${base}index.html" class="nav-logo">BONOBO</a>

                <!-- Buscador de películas: al hacer Enter navega a la home con la búsqueda -->
                <div class="nav-search-wrap">
                    <svg class="nav-search-icon" viewBox="0 0 20 20" fill="none">
                        <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input
                        type="text"
                        id="navSearch"
                        class="nav-search"
                        placeholder="Buscar película…"
                        autocomplete="off"
                    />
                </div>

                <!-- Links principales (solo visibles cuando está logueado) -->
                ${logueado ? `
                <div class="nav-links">
                    <a href="${base}pages/diario.html"   class="nav-link">Diario</a>
                    <a href="${base}pages/watchlist.html" class="nav-link">Watchlist</a>
                    <a href="${base}pages/buscar.html"   class="nav-link">Buscar</a>
                </div>
                ` : ''}

                <!-- Bloque de usuario / botones de auth -->
                ${authHTML}
            </div>
        </nav>
    `;

    // Inyectamos el HTML en el contenedor reservado para el nav
    const placeholder = document.getElementById('nav-placeholder');
    if (placeholder) placeholder.innerHTML = navHTML;

    // ── EVENTOS DEL NAV ───────────────────────────────────────────────────────

    // Buscar película al pulsar Enter en el buscador del nav
    const searchInput = document.getElementById('navSearch');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && searchInput.value.trim()) {
                // Guardamos la búsqueda y navegamos a la home donde se mostrará el resultado
                sessionStorage.setItem('nav_search', searchInput.value.trim());
                window.location.href = `${base}index.html`;
            }
        });
    }

    // Cerrar sesión
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            auth.logout();
            window.location.href = `${base}index.html`;
        });
    }

    // Marcar el link activo según la página actual
    const path = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (path.includes(link.getAttribute('href').split('/').pop())) {
            link.classList.add('nav-link--active');
        }
    });
}
