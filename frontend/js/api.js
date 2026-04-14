// js/api.js — Capa de comunicación con el backend de Bonobo
// Todas las llamadas HTTP al backend van aquí. Nunca uses fetch() directamente en otras partes.
// Esto centraliza el manejo de errores, tokens y la URL base en un solo sitio.

const API_BASE = 'http://localhost:8000';

// ── HELPERS INTERNOS ──────────────────────────────────────────────────────────

// Construye las cabeceras HTTP para una petición.
// Si hay token JWT en localStorage, lo añade automáticamente.
// esJSON indica si el cuerpo de la petición es JSON (por defecto sí).
function _headers(esJSON = true) {
    const token = localStorage.getItem('bonobo_token');
    const h = {};
    if (esJSON) h['Content-Type'] = 'application/json';
    if (token)  h['Authorization'] = `Bearer ${token}`;
    return h;
}

// Función genérica para hacer peticiones al backend.
// Lanza un Error con el mensaje del backend si la respuesta no es OK.
async function _req(method, endpoint, body = null) {
    const opts = { method, headers: _headers() };
    if (body !== null) opts.body = JSON.stringify(body);

    const res = await fetch(`${API_BASE}${endpoint}`, opts);

    // 204 No Content: éxito pero sin cuerpo (ej: DELETE exitoso)
    if (res.status === 204) return null;

    const data = await res.json().catch(() => ({ detail: `Error ${res.status}` }));

    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
}

// ── AUTENTICACIÓN ─────────────────────────────────────────────────────────────

const api = {

    auth: {
        // Registra un usuario nuevo.
        // body: { email: string, username: string, password: string }
        registro: (body) => _req('POST', '/api/auth/registro', body),

        // Inicia sesión. El backend usa OAuth2 form (no JSON).
        // email va en el campo "username" porque así lo espera FastAPI.
        login: async (email, password) => {
            const form = new URLSearchParams();
            form.append('username', email);    // FastAPI llama "username" al campo de email
            form.append('password', password);

            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                body: form   // URLSearchParams se envía como application/x-www-form-urlencoded
            });

            const data = await res.json().catch(() => ({ detail: 'Error al conectar con el servidor' }));
            if (!res.ok) throw new Error(data.detail || 'Credenciales incorrectas');
            return data;   // { access_token, token_type }
        }
    },

    // ── PELÍCULAS ─────────────────────────────────────────────────────────────

    peliculas: {
        // Busca películas en TMDB por título. Devuelve { results, total, page }.
        buscar: (q, skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/buscar?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),

        // Películas actualmente en cartelera en España.
        cartelera: (skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/cartelera?skip=${skip}&limit=${limit}`),

        // Próximos estrenos en España.
        estrenos: (skip = 0, limit = 20) =>
            _req('GET', `/api/peliculas/estrenos?skip=${skip}&limit=${limit}`),

        // Detalle completo de una película.
        // Si hay token, incluye estado_usuario (vista, puntuacion, me_gusta, en_watchlist).
        detalle: (tmdbId) => _req('GET', `/api/peliculas/${tmdbId}`)
    },

    // ── ACCIONES SOBRE PELÍCULAS ──────────────────────────────────────────────

    acciones: {
        // Marcar película como vista
        marcarVista:       (tmdbId) => _req('POST',   `/api/peliculas/${tmdbId}/vista`),
        // Desmarcar como vista (falla con 409 si tiene puntuación, diario o me gusta)
        desmarcarVista:    (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/vista`),

        // Guardar o actualizar puntuación. puntuacion: número del 1 al 10.
        puntuar:           (tmdbId, puntuacion) => _req('PUT', `/api/peliculas/${tmdbId}/puntuacion`, { puntuacion }),
        // Eliminar puntuación (vuelve a null, pero la Vista se mantiene)
        eliminarPuntuacion:(tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/puntuacion`),

        // Dar me gusta a una película
        darMeGusta:        (tmdbId) => _req('POST',   `/api/peliculas/${tmdbId}/me-gusta`),
        // Quitar me gusta
        quitarMeGusta:     (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/me-gusta`),

        // Añadir a watchlist
        añadirWatchlist:   (tmdbId) => _req('POST',   `/api/peliculas/${tmdbId}/watchlist`),
        // Quitar de watchlist
        quitarWatchlist:   (tmdbId) => _req('DELETE', `/api/peliculas/${tmdbId}/watchlist`),

        // Crear una entrada en el diario.
        // body: { fecha_visionado: "YYYY-MM-DD", resena: "texto opcional" }
        crearDiario:       (tmdbId, body) => _req('POST', `/api/peliculas/${tmdbId}/diario`, body),
        // Editar una entrada existente del diario por su id interno.
        editarDiario:      (idEntrada, body) => _req('PUT', `/api/diario/${idEntrada}`, body),
    },

    // ── USUARIOS ──────────────────────────────────────────────────────────────

    usuarios: {
        // Mi perfil (requiere token). Devuelve UserProfile con estadísticas.
        mePerfil:   () => _req('GET', '/api/usuarios/me'),
        // Editar mi perfil. body: { bio: string, avatar_url: string }
        editarPerfil: (body) => _req('PUT', '/api/usuarios/me', body),
        // Configurar favoritas. tmdbIds: array de hasta 4 tmdb_ids en orden.
        configurarFavoritas: (tmdbIds) => _req('PUT', '/api/usuarios/me/favoritas', tmdbIds),

        // Buscar usuarios por username (búsqueda parcial, sin auth necesaria).
        buscar: (q, skip = 0, limit = 20) =>
            _req('GET', `/api/usuarios/buscar?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`),

        // Perfil público de cualquier usuario por su id.
        perfil:    (id) => _req('GET', `/api/usuarios/${id}`),
        // Lista de películas vistas de un usuario. Devuelve VistaConPelicula[].
        vistas:    (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/vistas?skip=${skip}&limit=${limit}`),
        // Diario de un usuario. Devuelve EntradaDiarioOut[].
        diario:    (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/diario?skip=${skip}&limit=${limit}`),
        // Watchlist de un usuario.
        watchlist: (id, skip = 0, limit = 20) => _req('GET', `/api/usuarios/${id}/watchlist?skip=${skip}&limit=${limit}`),
        // Las hasta 4 películas favoritas de un usuario. Devuelve FavoritaOut[].
        favoritas: (id) => _req('GET', `/api/usuarios/${id}/favoritas`),
    }
};
