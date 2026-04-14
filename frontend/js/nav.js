// navbar compartido — se inyecta en todas las páginas
// base: '' desde index.html, '../' desde pages/

function renderNav(base = '') {
    const usuario = auth.getUsuario();
    const logueado = auth.estaLogueado();

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

    const navHTML = `
        <nav class="navbar">
            <div class="nav-inner">
                <a href="${base}index.html" class="nav-logo">BONOBO</a>

                <div class="nav-search-wrap">
                    <svg class="nav-search-icon" viewBox="0 0 20 20" fill="none">
                        <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <input
                        type="text"
                        id="navSearch"
                        class="nav-search"
                        placeholder="Buscar película o @usuario…"
                        autocomplete="off"
                    />
                </div>

                ${logueado ? `
                <div class="nav-links">
                    <a href="${base}pages/diario.html"    class="nav-link">Diario</a>
                    <a href="${base}pages/watchlist.html" class="nav-link">Watchlist</a>
                    <a href="${base}pages/listas.html"    class="nav-link">Listas</a>
                </div>
                ` : ''}

                ${authHTML}
            </div>
        </nav>
    `;

    const placeholder = document.getElementById('nav-placeholder');
    if (placeholder) placeholder.innerHTML = navHTML;

    // buscar al pulsar Enter
    // si empieza por @ → busca usuarios; si no → busca películas
    const searchInput = document.getElementById('navSearch');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter') return;
            const q = searchInput.value.trim();
            if (!q) return;

            if (q.startsWith('@')) {
                // búsqueda de usuarios: quitamos el @ y vamos a buscar.html
                const usuario = q.slice(1).trim();
                window.location.href = `${base}pages/buscar.html?q=${encodeURIComponent(usuario)}`;
            } else {
                // búsqueda de películas: guardamos y vamos a la home
                sessionStorage.setItem('nav_search', q);
                window.location.href = `${base}index.html`;
            }
        });
    }

    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            auth.logout();
            window.location.href = `${base}index.html`;
        });
    }

    // marca el link activo según la URL actual
    const path = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (path.includes(link.getAttribute('href').split('/').pop())) {
            link.classList.add('nav-link--active');
        }
    });
}
