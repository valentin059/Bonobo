// capa centralizada de comunicación con el backend

const API_BASE = 'http://localhost:8000';

// añade Content-Type y el token JWT si existe
function _headers(esJSON = true) {
    const token = localStorage.getItem('bonobo_token');
    const h = {};
    if (esJSON) h['Content-Type'] = 'application/json';
    if (token)  h['Authorization'] = `Bearer ${token}`;
    return h;
}

// petición genérica; lanza Error con el mensaje del backend si falla
async function _req(method, endpoint, body = null) {
    const opts = { method, headers: _headers() };
    if (body !== null) opts.body = JSON.stringify(body);

    const res = await fetch(`${API_BASE}${endpoint}`, opts);

    if (res.status === 204) return null;

    const data = await res.json().catch(() => ({ detail: `Error ${res.status}` }));

    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
}

const api = {

    auth: {
        registro: (body) => _req('POST', '/api/auth/registro', body),

        // el login usa form-urlencoded porque así lo espera FastAPI OAuth2
        login: async (email, password) => {
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

        // body: { fecha_visionado: "YYYY-MM-DD", resena: "..." }
        crearDiario:        (tmdbId, body) => _req('POST', `/api/peliculas/${tmdbId}/diario`, body),
        editarDiario:       (idEntrada, body) => _req('PUT', `/api/diario/${idEntrada}`, body),
    },

    usuarios: {
        mePerfil:            () => _req('GET', '/api/usuarios/me'),
        editarPerfil:        (body) => _req('PUT', '/api/usuarios/me', body),
        configurarFavoritas: (tmdbIds) => _req('PUT', '/api/usuarios/me/favoritas', tmdbIds),

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
        seguidores:    (id) => _req('GET',    `/api/usuarios/${id}/seguidores`),
        seguidos:      (id) => _req('GET',    `/api/usuarios/${id}/seguidos`),
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
    },
};
