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
                    <div id="navDropdown" class="nav-dropdown" style="display:none"></div>
                </div>

                ${logueado ? `
                <div class="nav-links">
                    <a href="${base}pages/diario.html"    class="nav-link">Diario</a>
                    <a href="${base}pages/watchlist.html" class="nav-link">Watchlist</a>
                    <a href="${base}pages/listas.html"    class="nav-link">Listas</a>
                    <a href="${base}pages/logros.html"    class="nav-link">Logros</a>
                </div>
                ` : ''}

                ${authHTML}
            </div>
        </nav>
    `;

    const placeholder = document.getElementById('nav-placeholder');
    if (placeholder) placeholder.innerHTML = navHTML;

    const searchInput = document.getElementById('navSearch');
    const dropdown    = document.getElementById('navDropdown');

    if (searchInput && dropdown) {
        let navTimer = null;

        const cerrarDropdown = () => {
            dropdown.style.display = 'none';
            dropdown.innerHTML = '';
        };

        // Sugerencias en tiempo real
        searchInput.addEventListener('input', () => {
            clearTimeout(navTimer);
            const q = searchInput.value.trim();
            if (!q) { cerrarDropdown(); return; }

            navTimer = setTimeout(async () => {
                try {
                    let items = [];
                    if (q.startsWith('@')) {
                        const usuarios = await api.usuarios.buscar(q.slice(1), 0, 6);
                        items = usuarios.map(u => ({
                            img:      u.avatar_url || '',
                            titulo:   u.username,
                            sub:      u.bio ? u.bio.slice(0, 40) : '',
                            href:     `${base}pages/usuario.html?id=${u.id}`,
                            esAvatar: true,
                        }));
                    } else {
                        const data = await api.peliculas.buscar(q, 0, 6);
                        items = (data.results || []).map(p => ({
                            img:    p.poster_url || '',
                            titulo: p.titulo,
                            sub:    p.anio_estreno ? String(p.anio_estreno) : '',
                            href:   `${base}pages/pelicula.html?id=${p.tmdb_id}`,
                        }));
                    }

                    if (!items.length) { cerrarDropdown(); return; }

                    dropdown.innerHTML = items.map(it => `
                        <div class="nav-dropdown-item" onclick="location.href='${it.href}'">
                            ${it.img
                                ? `<img src="${it.img}" alt="" ${it.esAvatar ? 'style="height:28px;border-radius:50%"' : ''}>`
                                : `<div style="width:28px;height:42px;background:var(--surface3);border-radius:2px;flex-shrink:0"></div>`
                            }
                            <div class="nav-dropdown-item__info">
                                <div class="nav-dropdown-item__title">${it.titulo}</div>
                                ${it.sub ? `<div class="nav-dropdown-item__sub">${it.sub}</div>` : ''}
                            </div>
                        </div>
                    `).join('');
                    dropdown.style.display = 'block';
                } catch { cerrarDropdown(); }
            }, 300);
        });

        // Enter → página de resultados completa
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') { cerrarDropdown(); return; }
            if (e.key !== 'Enter') return;
            const q = searchInput.value.trim();
            if (!q) return;
            cerrarDropdown();
            if (q.startsWith('@')) {
                window.location.href = `${base}pages/buscar.html?q=${encodeURIComponent(q.slice(1).trim())}`;
            } else {
                sessionStorage.setItem('nav_search', q);
                window.location.href = `${base}index.html`;
            }
        });

        // Cerrar al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                cerrarDropdown();
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
