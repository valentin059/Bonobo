// js/perfil.js — Lógica de la página de perfil propio

let usuarioId = null;
let movieMap  = {};
// slots de favoritas: array de 4 posiciones, cada una { tmdb_id, titulo, poster_url } o null
let favSlots  = [null, null, null, null];
// timers de debounce para los buscadores de favoritas
let favTimers = [null, null, null, null];

function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}

function cerrarModal(id) {
    document.getElementById(id).classList.add('modal-overlay--hidden');
    document.getElementById('errorFavoritas')?.classList.remove('form-error--visible');
}

// ── RENDER ────────────────────────────────────────────────────────────────────

function renderizarCabecera(usuario) {
    document.title = `BONOBO — ${usuario.username}`;

    const avatarEl = document.getElementById('perfilAvatar');
    if (usuario.avatar_url) {
        avatarEl.innerHTML = `<img class="perfil-avatar" src="${usuario.avatar_url}" alt="${usuario.username}">`;
        avatarEl.className = '';
    } else {
        avatarEl.textContent = usuario.username[0].toUpperCase();
        avatarEl.className = 'perfil-avatar perfil-avatar--placeholder';
    }

    document.getElementById('perfilUsername').textContent    = usuario.username;
    document.getElementById('perfilBio').textContent         = usuario.bio || '';
    document.getElementById('statVistas').textContent        = usuario.total_vistas;
    document.getElementById('statSeguidores').textContent    = usuario.seguidores;
    document.getElementById('statSeguidos').textContent      = usuario.seguidos;
    document.getElementById('statNivel').textContent         = usuario.nivel || 1;
    document.getElementById('statXP').textContent            = `${usuario.xp_total || 0} XP`;
}

function renderizarFavoritas(favoritas) {
    const grid     = document.getElementById('favoritasGrid');
    const porOrden = {};
    favoritas.forEach(f => { porOrden[f.orden] = f.pelicula; });

    grid.innerHTML = Array.from({ length: 4 }, (_, i) => {
        const orden    = i + 1;
        const pelicula = porOrden[orden];
        if (pelicula) {
            return `
                <div class="favorita-slot" style="cursor:pointer"
                     onclick="irAPelicula(${pelicula.tmdb_id})" title="${pelicula.titulo}">
                    ${pelicula.poster_url
                        ? `<img src="${pelicula.poster_url}" alt="${pelicula.titulo}">`
                        : `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--faint);font-size:10px;text-align:center;padding:4px">${pelicula.titulo}</div>`
                    }
                </div>
            `;
        } else {
            return `<div class="favorita-slot favorita-slot--vacio" style="cursor:default"></div>`;
        }
    }).join('');
}

function renderizarVistas(vistas, totalVistas) {
    const grid = document.getElementById('gridVistas');
    const lbl  = document.getElementById('lblVistas');

    if (totalVistas > 0) {
        lbl.innerHTML = `<a href="vistas.html" style="color:var(--accent)">Ver todo →</a>`;
    } else {
        lbl.textContent = '';
    }

    if (vistas.length === 0) {
        grid.innerHTML = `<div class="estado-vacio" style="grid-column:1/-1">
            <p class="estado-vacio__desc">Aún no has marcado ninguna película como vista.</p>
        </div>`;
        return;
    }

    grid.innerHTML = vistas.map(v => {
        const p = v.pelicula;
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

function renderizarDiario(entradas) {
    const lista = document.getElementById('listaDiario');

    if (entradas.length === 0) {
        lista.innerHTML = `<div class="estado-vacio">
            <p class="estado-vacio__desc">Tu diario está vacío. Añade películas desde su ficha.</p>
        </div>`;
        return;
    }

    lista.innerHTML = entradas.slice(0, 5).map(entrada => {
        diarioCache$[entrada.id] = { entrada, pelicula: movieMap[entrada.id_pelicula] };
        const fecha = new Date(entrada.fecha_visionado);
        const dia   = fecha.getDate();
        const mes   = fecha.toLocaleString('es', { month: 'short' }).toUpperCase();
        const pelicula = movieMap[entrada.id_pelicula];

        return `
            <div class="diario-entrada" id="perfil-entrada-${entrada.id}">
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
                <div class="diario-contenido diario-contenido--clickable"
                     onclick="abrirModalDiarioEntrada(${entrada.id})">
                    <div class="diario-titulo-peli">
                        ${escapeHTML(pelicula?.titulo) || `Película #${entrada.id_pelicula}`}
                        <span class="diario-puntuacion" id="perfil-punt-${entrada.id}">${entrada.puntuacion ? `★ ${entrada.puntuacion}` : ''}</span>
                    </div>
                    <p class="diario-resena">${
                        entrada.resena
                            ? escapeHTML(entrada.resena)
                            : '<span class="text-faint">Sin reseña</span>'
                    }</p>
                </div>
            </div>
        `;
    }).join('');
}

// ── Modal editar entrada desde perfil ────────────────────────────────────────

const diarioCache$ = {};
let perfilEditPuntuacion = null;

function abrirModalDiarioEntrada(id) {
    const cached = diarioCache$[id];
    if (!cached) return;
    const { entrada, pelicula } = cached;

    const sel = document.getElementById('diarioEntradaSelector');
    if (!sel.innerHTML) {
        sel.innerHTML = Array.from({ length: 10 }, (_, i) => {
            const v = i + 1;
            return `<button class="punt-btn" data-val="${v}" onclick="setPerfilPuntuacion(${v})">${v}</button>`;
        }).join('');
    }
    document.getElementById('diarioEntradaId').value    = entrada.id;
    document.getElementById('diarioEntradaFecha').value = entrada.fecha_visionado;
    document.getElementById('diarioEntradaResena').value = entrada.resena || '';
    document.getElementById('modalDiarioTitulo').textContent = pelicula?.titulo || 'Entrada del diario';
    perfilEditPuntuacion = entrada.puntuacion || null;
    document.querySelectorAll('#diarioEntradaSelector .punt-btn').forEach(btn => {
        btn.classList.toggle('punt-btn--activo', parseInt(btn.dataset.val) === perfilEditPuntuacion);
    });
    document.getElementById('modalDiarioEntrada').classList.remove('modal-overlay--hidden');
}

function cerrarModalDiarioEntrada() {
    document.getElementById('modalDiarioEntrada').classList.add('modal-overlay--hidden');
}

function setPerfilPuntuacion(val) {
    perfilEditPuntuacion = perfilEditPuntuacion === val ? null : val;
    document.querySelectorAll('#diarioEntradaSelector .punt-btn').forEach(btn => {
        btn.classList.toggle('punt-btn--activo', parseInt(btn.dataset.val) === perfilEditPuntuacion);
    });
}

async function guardarEdicionDiario() {
    const id    = parseInt(document.getElementById('diarioEntradaId').value);
    const fecha = document.getElementById('diarioEntradaFecha').value;
    const resena = document.getElementById('diarioEntradaResena').value.trim() || null;

    if (!fecha) return;

    try {
        await api.acciones.editarDiario(id, {
            fecha_visionado: fecha,
            resena,
            puntuacion: perfilEditPuntuacion,
        });

        if (diarioCache$[id]) {
            diarioCache$[id].entrada.resena     = resena;
            diarioCache$[id].entrada.puntuacion = perfilEditPuntuacion;
        }
        const puntEl = document.getElementById(`perfil-punt-${id}`);
        if (puntEl) puntEl.textContent = perfilEditPuntuacion ? `★ ${perfilEditPuntuacion}` : '';

        cerrarModalDiarioEntrada();
        mostrarToast('Entrada actualizada ✓');
    } catch (err) {
        mostrarToast(err.message || 'Error al guardar', 'error');
    }
}

function renderizarListas(listas) {
    const lista = document.getElementById('listaListas');
    if (listas.length === 0) {
        lista.innerHTML = '<p class="text-faint" style="font-size:13px">Sin listas todavía. <a href="listas.html" style="color:var(--accent)">Crea una</a></p>';
        return;
    }
    lista.innerHTML = listas.slice(0, 4).map(l => `
        <div class="lista-card" onclick="location.href='listas.html?id=${l.id}'">
            <div class="lista-card__info">
                <div class="lista-card__nombre">${l.nombre}</div>
                ${l.descripcion ? `<div class="lista-card__desc">${l.descripcion}</div>` : ''}
            </div>
            <span class="lista-badge lista-badge--${l.es_publica ? 'publica' : 'privada'}">
                ${l.es_publica ? 'Pública' : 'Privada'}
            </span>
            <div class="lista-card__count">${l.total_peliculas ?? 0} pel.</div>
        </div>
    `).join('');
}

function irAPelicula(tmdbId) {
    window.location.href = `pelicula.html?id=${tmdbId}`;
}



// ── EDITOR INLINE DE FAVORITAS ───────────────────────────────────────────────

function abrirEditFavoritas() {
    document.getElementById('errorFavoritas').className = 'form-error';
    renderizarFavEditSlots();
    document.getElementById('modalFavoritas').classList.remove('modal-overlay--hidden');
}

function cerrarEditFavoritas() {
    document.getElementById('modalFavoritas').classList.add('modal-overlay--hidden');
}

function renderizarFavEditSlots() {
    const grid = document.getElementById('favEditGrid');
    grid.innerHTML = favSlots.map((peli, i) => `
        <div class="fav-edit-slot">
            <div class="fav-edit-slot__poster" id="fav-poster-${i}">
                ${peli
                    ? (peli.poster_url
                        ? `<img src="${peli.poster_url}" alt="${peli.titulo}">
                           <button class="fav-edit-slot__clear" onclick="limpiarSlot(${i})">✕</button>`
                        : `<div class="fav-edit-slot__vacio" style="font-size:10px;padding:4px;text-align:center">${peli.titulo}</div>
                           <button class="fav-edit-slot__clear" onclick="limpiarSlot(${i})">✕</button>`)
                    : `<div class="fav-edit-slot__vacio">+</div>`
                }
            </div>
            <div class="fav-edit-slot__label">${i + 1}º</div>
            <div class="fav-search-wrap">
                <input class="fav-edit-slot__search" type="text"
                       id="fav-search-${i}"
                       placeholder="Buscar película…"
                       oninput="buscarFav(${i}, this.value)"
                       autocomplete="off" />
                <div class="fav-resultados" id="fav-res-${i}"></div>
            </div>
        </div>
    `).join('');
}

function limpiarSlot(idx) {
    favSlots[idx] = null;
    renderizarFavEditSlots();
}

function buscarFav(idx, query) {
    clearTimeout(favTimers[idx]);
    const resEl = document.getElementById(`fav-res-${idx}`);

    if (!query.trim()) {
        resEl.style.display = 'none';
        return;
    }

    favTimers[idx] = setTimeout(async () => {
        try {
            const data = await api.peliculas.buscar(query, 0, 6);
            const resultados = data.results || [];
            if (!resultados.length) {
                resEl.style.display = 'none';
                return;
            }
            resEl.innerHTML = resultados.map(p => `
                <div class="fav-result-item"
                     data-idx="${idx}"
                     data-tmdb-id="${p.tmdb_id}"
                     data-titulo="${escapeHTML(p.titulo)}"
                     data-poster="${escapeHTML(p.poster_url || '')}">
                    ${p.poster_url ? `<img src="${escapeHTML(p.poster_url)}" alt="">` : ''}
                    <span>${escapeHTML(p.titulo)}${p.anio_estreno ? ` (${p.anio_estreno})` : ''}</span>
                </div>
            `).join('');
            resEl.querySelectorAll('.fav-result-item').forEach(el => {
                el.addEventListener('click', () => seleccionarFav(
                    parseInt(el.dataset.idx),
                    parseInt(el.dataset.tmdbId),
                    el.dataset.titulo,
                    el.dataset.poster
                ));
            });
            resEl.style.display = 'block';
        } catch { resEl.style.display = 'none'; }
    }, 350);
}

function seleccionarFav(idx, tmdbId, titulo, posterUrl) {
    favSlots[idx] = { tmdb_id: tmdbId, titulo, poster_url: posterUrl || null };
    document.getElementById(`fav-search-${idx}`).value = '';
    document.getElementById(`fav-res-${idx}`).style.display = 'none';
    renderizarFavEditSlots();
}

async function guardarFavoritas() {
    const errorEl = document.getElementById('errorFavoritas');
    // tmdb_ids de los slots con película (ignoramos nulls, compactamos el array)
    const tmdbIds = favSlots.filter(s => s !== null).map(s => s.tmdb_id);

    try {
        await api.usuarios.configurarFavoritas(tmdbIds);
        // recargar las favoritas en el perfil
        const favoritas = await api.usuarios.favoritas(usuarioId);
        renderizarFavoritas(favoritas);
        // sincronizar favSlots con el resultado guardado
        const porOrden = {};
        favoritas.forEach(f => { porOrden[f.orden] = f.pelicula; });
        for (let i = 0; i < 4; i++) favSlots[i] = porOrden[i + 1] || null;
        cerrarEditFavoritas();
        mostrarToast('Favoritas guardadas ✓');

    } catch (err) {
        errorEl.textContent = err.message || 'Error al guardar';
        errorEl.className = 'form-error form-error--visible';
    }
}

// ── MODALES SEGUIDORES / SEGUIDOS ─────────────────────────────────────────────

function renderUsuariosModal(usuarios) {
    if (!usuarios || usuarios.length === 0) {
        return '<p class="text-faint" style="font-size:13px;padding:8px 0">Ningún usuario.</p>';
    }
    return usuarios.map(u => `
        <a href="usuario.html?id=${u.id}" class="usuario-fila">
            <div class="usuario-fila__avatar ${u.avatar_url ? '' : 'usuario-fila__avatar--placeholder'}">
                ${u.avatar_url
                    ? `<img src="${u.avatar_url}" alt="${u.username}" class="usuario-fila__avatar">`
                    : u.username[0].toUpperCase()
                }
            </div>
            <span class="usuario-fila__username">${u.username}</span>
        </a>
    `).join('');
}

async function abrirModalSeguidores() {
    document.getElementById('modalSeguidores').classList.remove('modal-overlay--hidden');
    const lista = document.getElementById('listaModalSeguidores');
    lista.innerHTML = '<p class="text-faint" style="font-size:13px">Cargando…</p>';
    try {
        const data = await api.social.seguidores(usuarioId);
        lista.innerHTML = renderUsuariosModal(data);
    } catch {
        lista.innerHTML = '<p class="text-faint" style="font-size:13px">Error al cargar.</p>';
    }
}

async function abrirModalSeguidos() {
    document.getElementById('modalSeguidos').classList.remove('modal-overlay--hidden');
    const lista = document.getElementById('listaModalSeguidos');
    lista.innerHTML = '<p class="text-faint" style="font-size:13px">Cargando…</p>';
    try {
        const data = await api.social.seguidos(usuarioId);
        lista.innerHTML = renderUsuariosModal(data);
    } catch {
        lista.innerHTML = '<p class="text-faint" style="font-size:13px">Error al cargar.</p>';
    }
}

// ── INIT ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    renderNav('../');
    actualizarBadgesLogros();

    if (!auth.estaLogueado()) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const usuario = await api.usuarios.mePerfil();
        usuarioId = usuario.id;
        renderizarCabecera(usuario);

        // carga en paralelo todo lo que no tiene dependencias
        const [vistas, diario, favoritas, listas] = await Promise.all([
            api.usuarios.vistas(usuarioId, 0, 20),
            api.usuarios.diario(usuarioId, 0, 5),
            api.usuarios.favoritas(usuarioId),
            api.usuarios.listas(usuarioId),
        ]);

        renderizarVistas(vistas, usuario.total_vistas);   // construye movieMap

        renderizarDiario(diario);
        renderizarFavoritas(favoritas);
        renderizarListas(listas);

        // inicializar favSlots con las favoritas actuales para el modal de edición
        const porOrden = {};
        favoritas.forEach(f => { porOrden[f.orden] = f.pelicula; });
        for (let i = 0; i < 4; i++) {
            favSlots[i] = porOrden[i + 1] || null;
        }

    } catch (err) {
        mostrarToast('Error al cargar el perfil', 'error');
    }
});
