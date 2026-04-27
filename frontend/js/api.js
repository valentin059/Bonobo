// capa centralizada de comunicación con el backend

const API_BASE = 'http://localhost:8000';

// escapa texto de usuario antes de insertarlo con innerHTML
function escapeHTML(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ── Loading bar ───────────────────────────────────────────────────────────────
// Barra fina en la parte superior que aparece mientras hay peticiones en curso.

let _pendingRequests = 0;

function _showLoading() {
    _pendingRequests++;
    let bar = document.getElementById('_api-loading-bar');
    if (!bar) {
        bar = document.createElement('div');
        bar.id = '_api-loading-bar';
        bar.style.cssText = [
            'position:fixed', 'top:0', 'left:0', 'width:0%', 'height:3px',
            'background:var(--accent,#e8a020)', 'z-index:99999',
            'transition:width .25s ease,opacity .3s ease',
            'pointer-events:none'
        ].join(';');
        document.body.appendChild(bar);
    }
    bar.style.opacity = '1';
    bar.style.width   = '40%';
}

function _hideLoading() {
    _pendingRequests = Math.max(0, _pendingRequests - 1);
    if (_pendingRequests > 0) return;
    const bar = document.getElementById('_api-loading-bar');
    if (!bar) return;
    bar.style.width = '100%';
    setTimeout(() => {
        bar.style.opacity = '0';
        setTimeout(() => { bar.style.width = '0%'; }, 300);
    }, 150);
}

// ── Cabeceras ─────────────────────────────────────────────────────────────────

function _headers(esJSON = true) {
    const token = localStorage.getItem('bonobo_token');
    const h = {};
    if (esJSON) h['Content-Type'] = 'application/json';
    if (token)  h['Authorization'] = `Bearer ${token}`;
    return h;
}

// ── Petición central con retry exponencial ────────────────────────────────────
// Reintenta hasta 3 veces (con espera 300ms, 600ms, 1200ms) solo en errores de red.
// Los errores HTTP (4xx, 5xx) se lanzan directamente sin reintentar.

async function _req(method, endpoint, body = null, _retry = 0) {
    _showLoading();
    try {
        const opts = { method, headers: _headers() };
        if (body !== null) opts.body = JSON.stringify(body);

        let res;
        try {
            res = await fetch(`${API_BASE}${endpoint}`, opts);
        } catch (_networkErr) {
            // error de red (sin respuesta del servidor)
            if (_retry < 2) {
                await new Promise(r => setTimeout(r, 300 * (2 ** _retry)));
                return _req(method, endpoint, body, _retry + 1);
            }
            throw new Error('Sin conexión con el servidor. Comprueba tu red e inténtalo de nuevo.');
        }

        if (res.status === 204) return null;

        const data = await res.json().catch(() => ({ detail: `Error ${res.status}` }));

        if (res.status === 401 && localStorage.getItem('bonobo_token')) {
            // token caducado — cerramos sesión y redirigimos a login
            localStorage.removeItem('bonobo_token');
            localStorage.removeItem('bonobo_user');
            const inPages = window.location.pathname.includes('/pages/');
            window.location.href = inPages ? 'login.html' : 'pages/login.html';
            return null;
        }

        if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
        return data;

    } finally {
        _hideLoading();
    }
}

const api = {

    auth: {
        registro: (body) => _req('POST', '/api/auth/registro', body),

        // el login usa form-urlencoded porque así lo espera FastAPI OAuth2
        login: async (email, password) => {
            _showLoading();
            try {
                const form = new URLSearchParams();
                form.append('username', email);
                form.append('password', password);

                const res = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    body: form
                });

                const data = await res.json().catch(() => ({ detail: 'Error al conectar' }));
                if (!res.ok) throw new Error(data.detail || 'Credenciales incorrectas');
                return data;
            } finally {
                _hideLoading();
            }
        }
    },

    peliculas: {
        buscar:    (q, skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/buscar?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),
        cartelera: (skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/cartelera?skip=${skip}&limit=${limit}`),
        estrenos:  (skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/estrenos?skip=${skip}&limit=${limit}`),
        // incluye estado_usuario si hay token
        detalle:   (tmdbId)   => _req('GET', `/api/peliculas/${tmdbId}`),
        persona:   (personId) => _req('GET', `/api/peliculas/persona/${personId}`),
    },

    acciones: {
        marcarVista:        (tmdbId) => _req('POST',   `/api/peliculas/${tmdbId}/vista`),
        desmarcarVista:     (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/vista`),

        puntuar:            (tmdbId, puntuacion) => _req('PUT', `/api/peliculas/${tmdbId}/puntuacion`, { puntuacion }),
        eliminarPuntuacion: (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/puntuacion`),

        darMeGusta:         (tmdbId) => _req('POST',   `/api/peliculas/${tmdbId}/me-gusta`),
        quitarMeGusta:      (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/me-gusta`),

        añadirWatchlist:    (tmdbId) => _req('POST',   `/api/peliculas/${tmdbId}/watchlist`),
        quitarWatchlist:    (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/watchlist`),

        crearDiario:        (tmdbId, body) => _req('POST', `/api/peliculas/${tmdbId}/diario`, body),
        editarDiario:       (idEntrada, body) => _req('PUT', `/api/diario/${idEntrada}`, body),
    },

    usuarios: {
        mePerfil:            () => _req('GET', '/api/usuarios/me'),
        editarPerfil:        (body) => _req('PUT', '/api/usuarios/me', body),
        configurarFavoritas: (tmdbIds) => _req('PUT', '/api/usuarios/me/favoritas', tmdbIds),

        cambiarPassword: (password_actual, password_nueva) =>
            _req('PUT', '/api/usuarios/me/password', { password_actual, password_nueva }),

        buscar:    (q, skip = 0, limit = 20) =>
            _req('GET', `/api/usuarios/buscar?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),

        perfil:    (id) => _req('GET', `/api/usuarios/${id}`),
        vistas:    (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/vistas?skip=${skip}&limit=${limit}`),
        diario:    (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/diario?skip=${skip}&limit=${limit}`),
        watchlist: (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/watchlist?skip=${skip}&limit=${limit}`),
        favoritas: (id) => _req('GET', `/api/usuarios/${id}/favoritas`),
        listas:    (id) => _req('GET', `/api/usuarios/${id}/listas`),
    },

    social: {
        seguir:        (id) => _req('POST',   `/api/usuarios/${id}/seguir`),
        dejarDeSeguir: (id) => _req('DELETE', `/api/usuarios/${id}/seguir`),
        seguidores:    (id, skip = 0, limit = 50) =>
            _req('GET', `/api/usuarios/${id}/seguidores?skip=${skip}&limit=${limit}`),
        seguidos:      (id, skip = 0, limit = 50) =>
            _req('GET', `/api/usuarios/${id}/seguidos?skip=${skip}&limit=${limit}`),
    },

    resenas: {
        amigos:          (tmdbId) =>
            _req('GET', `/api/peliculas/${tmdbId}/resenas/amigos`),
        comunidad:       (tmdbId, skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/${tmdbId}/resenas?skip=${skip}&limit=${limit}`),
        darLike:         (idEntrada) => _req('POST',   `/api/diario/${idEntrada}/like`),
        quitarLike:      (idEntrada) => _req('DELETE', `/api/diario/${idEntrada}/like`),
        comentarios:     (idEntrada) => _req('GET',    `/api/diario/${idEntrada}/comentarios`),
        crearComentario: (idEntrada, texto) =>
            _req('POST', `/api/diario/${idEntrada}/comentarios`, { texto }),
        borrarComentario:(idComentario) => _req('DELETE', `/api/comentarios/${idComentario}`),
    },

    listas: {
        crear:          (body)          => _req('POST',   '/api/listas', body),
        detalle:        (id)            => _req('GET',    `/api/listas/${id}`),
        editar:         (id, body)      => _req('PUT',    `/api/listas/${id}`, body),
        borrar:         (id)            => _req('DELETE', `/api/listas/${id}`),
        añadirPelicula: (idLista, tmdbId) =>
            _req('POST',   `/api/listas/${idLista}/peliculas/${tmdbId}`),
        quitarPelicula: (idLista, tmdbId) =>
            _req('DELETE', `/api/listas/${idLista}/peliculas/${tmdbId}`),
        listasConPelicula: (tmdbId) =>
            _req('GET', `/api/listas/mis-listas-con-pelicula/${tmdbId}`),
    },

    logros: {
        todos:     () => _req('GET',  '/api/logros/todos'),
        misLogros: () => _req('GET',  '/api/logros/mis-logros'),
        reclamar:  (idUsuarioLogro) => _req('POST', `/api/logros/${idUsuarioLogro}/reclamar`),
    },
};
