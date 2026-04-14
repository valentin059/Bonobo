// js/perfil.js — Lógica de la página de perfil propio
// Carga el perfil del usuario logueado, sus vistas, diario y favoritas.

let usuarioId = null;   // id del usuario logueado, necesario para las llamadas a la API
let movieMap  = {};     // mapa { id_pelicula_interno → datos de película } para el diario

function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}

// ── RENDER ────────────────────────────────────────────────────────────────────

// Rellena la cabecera del perfil con los datos del usuario.
function renderizarCabecera(usuario) {
    document.title = `BONOBO — ${usuario.username}`;

    // Avatar: si tiene URL lo mostramos, si no mostramos la inicial del username
    const avatarEl = document.getElementById('perfilAvatar');
    if (usuario.avatar_url) {
        avatarEl.innerHTML = `<img class="perfil-avatar" src="${usuario.avatar_url}" alt="${usuario.username}">`;
        avatarEl.className = '';
    } else {
        avatarEl.textContent = usuario.username[0].toUpperCase();
        avatarEl.className = 'perfil-avatar perfil-avatar--placeholder';
    }

    document.getElementById('perfilUsername').textContent = usuario.username;
    document.getElementById('perfilBio').textContent = usuario.bio || '';
    document.getElementById('statVistas').textContent   = usuario.total_vistas;
    document.getElementById('statSeguidores').textContent = usuario.seguidores;
    document.getElementById('statSeguidos').textContent   = usuario.seguidos;

    // Precargamos los inputs del modal de edición con los valores actuales
    document.getElementById('inputAvatar').value = usuario.avatar_url || '';
    document.getElementById('inputBio').value    = usuario.bio || '';
}

// Renderiza los 4 huecos de películas favoritas.
// favoritas: array de FavoritaOut { orden, pelicula: { tmdb_id, titulo, poster_url } }
function renderizarFavoritas(favoritas) {
    const grid = document.getElementById('favoritasGrid');

    // Creamos un mapa por orden para acceder rápidamente a cada hueco (1-4)
    const porOrden = {};
    favoritas.forEach(f => { porOrden[f.orden] = f.pelicula; });

    grid.innerHTML = Array.from({ length: 4 }, (_, i) => {
        const orden = i + 1;
        const pelicula = porOrden[orden];
        if (pelicula) {
            return `
                <div class="favorita-slot" onclick="irAPelicula(${pelicula.tmdb_id})" title="${pelicula.titulo}">
                    ${pelicula.poster_url
                        ? `<img src="${pelicula.poster_url}" alt="${pelicula.titulo}">`
                        : `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--faint);font-size:10px;text-align:center;padding:4px">${pelicula.titulo}</div>`
                    }
                </div>
            `;
        } else {
            // Hueco vacío: muestra un "+"
            return `<div class="favorita-slot favorita-slot--vacio" title="Hueco ${orden}">+</div>`;
        }
    }).join('');
}

// Renderiza la cuadrícula de películas vistas.
// vistas: array de VistaConPelicula { id, id_pelicula, puntuacion, pelicula: PeliculaCache }
function renderizarVistas(vistas) {
    const grid = document.getElementById('gridVistas');
    const lbl  = document.getElementById('lblVistas');

    lbl.textContent = `${vistas.length} película${vistas.length !== 1 ? 's' : ''}`;

    if (vistas.length === 0) {
        grid.innerHTML = `<div class="estado-vacio" style="grid-column:1/-1">
            <p class="estado-vacio__desc">Aún no has marcado ninguna película como vista.</p>
        </div>`;
        return;
    }

    grid.innerHTML = vistas.map(v => {
        const p = v.pelicula;
        // Guardamos el mapeo id_interno → datos de película para usarlo en el diario
        movieMap[v.id_pelicula] = p;

        return `
            <div class="pelicula-card" onclick="irAPelicula(${p.tmdb_id})">
                <div class="pelicula-card__poster">
                    ${p.poster_url
                        ? `<img class="pelicula-card__img" src="${p.poster_url}" alt="${p.titulo}" loading="lazy">`
                        : `<div class="pelicula-card__no-img">SIN IMAGEN</div>`
                    }
                    <div class="pelicula-card__overlay">
                        ${v.puntuacion ? `<div class="pelicula-card__puntuacion">★ ${v.puntuacion}</div>` : ''}
                    </div>
                    <div class="pelicula-card__badges">
                        <div class="badge badge--watched">✓</div>
                    </div>
                </div>
                <div class="pelicula-card__info">
                    <div class="pelicula-card__titulo">${p.titulo || '—'}</div>
                    <div class="pelicula-card__anio">${p.anio_estreno || ''}</div>
                </div>
            </div>
        `;
    }).join('');
}

// Renderiza las últimas entradas del diario (máximo 5 en el perfil).
// entradas: array de EntradaDiarioOut { id, id_pelicula, fecha_visionado, resena }
function renderizarDiario(entradas) {
    const lista = document.getElementById('listaDiario');

    if (entradas.length === 0) {
        lista.innerHTML = `<div class="estado-vacio">
            <p class="estado-vacio__desc">Tu diario está vacío. Añade películas desde su ficha.</p>
        </div>`;
        return;
    }

    lista.innerHTML = entradas.slice(0, 5).map(entrada => {
        const fecha = new Date(entrada.fecha_visionado);
        const dia   = fecha.getDate();
        const mes   = fecha.toLocaleString('es', { month: 'short' }).toUpperCase();

        // Buscamos los datos de la película usando el mapa que construimos en renderizarVistas
        const pelicula = movieMap[entrada.id_pelicula];

        return `
            <div class="diario-entrada">
                <div class="diario-fecha">
                    <div class="diario-fecha__dia">${dia}</div>
                    <div class="diario-fecha__mes">${mes}</div>
                </div>
                ${pelicula?.poster_url
                    ? `<div class="diario-poster" style="cursor:pointer" onclick="irAPelicula(${pelicula.tmdb_id})">
                           <img src="${pelicula.poster_url}" alt="${pelicula.titulo}">
                       </div>`
                    : `<div class="diario-poster"></div>`
                }
                <div class="diario-contenido">
                    <div class="diario-titulo-peli"
                         ${pelicula ? `style="cursor:pointer" onclick="irAPelicula(${pelicula.tmdb_id})"` : ''}>
                        ${pelicula?.titulo || `Película #${entrada.id_pelicula}`}
                    </div>
                    ${entrada.resena
                        ? `<p class="diario-resena">${entrada.resena}</p>`
                        : `<p class="diario-resena text-faint">Sin reseña</p>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

function irAPelicula(tmdbId) {
    window.location.href = `pelicula.html?id=${tmdbId}`;
}

// ── MODAL EDITAR PERFIL ───────────────────────────────────────────────────────

function abrirModalEditar() {
    document.getElementById('modalEditar').classList.remove('modal-overlay--hidden');
}

function cerrarModalEditar() {
    document.getElementById('modalEditar').classList.add('modal-overlay--hidden');
    document.getElementById('errorEditar').className = 'form-error';
}

async function guardarPerfil() {
    const avatar_url = document.getElementById('inputAvatar').value.trim() || null;
    const bio        = document.getElementById('inputBio').value.trim() || null;
    const errorEl    = document.getElementById('errorEditar');

    try {
        const updated = await api.usuarios.editarPerfil({ bio, avatar_url });

        // Actualizamos el usuario guardado en localStorage para que el nav lo refleje
        const usuarioGuardado = auth.getUsuario();
        auth.guardarUsuario({ ...usuarioGuardado, bio, avatar_url });

        // Actualizamos la UI sin recargar
        document.getElementById('perfilBio').textContent = bio || '';
        if (avatar_url) {
            document.getElementById('perfilAvatar').innerHTML =
                `<img class="perfil-avatar" src="${avatar_url}" alt="avatar">`;
        }

        cerrarModalEditar();
        mostrarToast('Perfil actualizado ✓');
    } catch (err) {
        errorEl.textContent = err.message || 'Error al guardar';
        errorEl.className = 'form-error form-error--visible';
    }
}

// ── INIT ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    renderNav('../');

    // El perfil propio requiere estar logueado
    if (!auth.estaLogueado()) {
        window.location.href = 'login.html';
        return;
    }

    try {
        // Pedimos los datos del perfil propio
        const usuario = await api.usuarios.mePerfil();
        usuarioId = usuario.id;
        renderizarCabecera(usuario);

        // Cargamos vistas primero (necesitamos el movieMap para el diario)
        const vistas = await api.usuarios.vistas(usuarioId, 0, 40);
        renderizarVistas(vistas);

        // Ahora podemos renderizar el diario usando el movieMap que acabamos de construir
        const diario = await api.usuarios.diario(usuarioId, 0, 5);
        renderizarDiario(diario);

        // Favoritas (se cargan en paralelo con el resto)
        const favoritas = await api.usuarios.favoritas(usuarioId);
        renderizarFavoritas(favoritas);

    } catch (err) {
        mostrarToast('Error al cargar el perfil', 'error');
    }
});
