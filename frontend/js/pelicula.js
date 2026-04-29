// pelicula.js — pagina de detalle de una peli
// Lee el tmdb_id de la URL (?id=XXXX) y monta toda la pantalla.

// estado actual del usuario respecto a la peli (se va actualizando)
let estado = { vista: false, puntuacion: null, me_gusta: false, en_watchlist: false };
let tmdbId = null;


function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}


// pone los botones (vista, like, watchlist) segun el estado actual
function actualizarBotonesAccion() {
    const btnVista     = document.getElementById('btnVista');
    const btnLike      = document.getElementById('btnLike');
    const btnWatchlist = document.getElementById('btnWatchlist');
    const lblVista     = document.getElementById('lblVista');

    if (estado.vista) {
        btnVista.classList.add('accion-btn--watched');
        lblVista.textContent = 'Vista ✓';
    } else {
        btnVista.classList.remove('accion-btn--watched');
        lblVista.textContent = 'Vista';
    }

    if (estado.me_gusta) {
        btnLike.classList.add('accion-btn--liked');
    } else {
        btnLike.classList.remove('accion-btn--liked');
    }

    if (estado.en_watchlist) {
        btnWatchlist.classList.add('accion-btn--watchlist');
    } else {
        btnWatchlist.classList.remove('accion-btn--watchlist');
    }
}

// botones del 1 al 10 con el activo marcado
function renderizarPuntuacion() {
    const selector = document.getElementById('selectorPuntuacion');
    if (!selector) return;

    selector.innerHTML = Array.from({ length: 10 }, (_, i) => {
        const num = i + 1;
        const activo = estado.puntuacion === num ? 'punt-btn--activo' : '';
        return `<button class="punt-btn ${activo}" onclick="setPuntuacion(${num})">${num}</button>`;
    }).join('');
}

// pinta la peli con los datos que devuelve la api
function renderizarPelicula(pelicula) {
    document.title = `BONOBO — ${pelicula.titulo || 'Película'}`;

    // Fondo: si hay backdrop 16:9 lo usamos, sino el poster difuminado
    const heroBg    = document.getElementById('heroBg');
    const heroWrap  = document.getElementById('peliculaHero');
    if (pelicula.backdrop_url) {
        heroBg.style.backgroundImage = `url('${pelicula.backdrop_url}')`;
        heroWrap.classList.add('has-backdrop');
    } else if (pelicula.poster_url) {
        heroBg.style.backgroundImage = `url('${pelicula.poster_url}')`;
    }

    // Poster
    const posterWrap = document.getElementById('posterWrap');
    if (pelicula.poster_url) {
        const tituloSafe = escapeHTML(pelicula.titulo || '');
        posterWrap.innerHTML = `<img src="${escapeHTML(pelicula.poster_url)}" alt="${tituloSafe}" style="cursor:zoom-in">`;
        posterWrap.querySelector('img').addEventListener('click', () => {
            document.getElementById('posterOverlayImg').src = pelicula.poster_url;
            document.getElementById('posterOverlay').classList.remove('poster-overlay--hidden');
        });
    } else {
        posterWrap.innerHTML = `<div class="pelicula-card__no-img" style="aspect-ratio:2/3">SIN IMAGEN</div>`;
    }

    document.getElementById('titulo').textContent = pelicula.titulo || '—';

    // director: lo buscamos en el crew
    const director = (pelicula.crew || []).find(p => p.rol === 'Director');
    const directorEl = document.getElementById('director');
    if (director) {
        directorEl.textContent = `Dirigida por ${director.nombre}`;
    } else {
        directorEl.textContent = '';
    }

    // meta: año, duracion, puntuacion TMDB
    const metas = [];
    if (pelicula.anio_estreno) metas.push(`<span>${pelicula.anio_estreno}</span>`);
    if (pelicula.duracion)     metas.push(`<span>${pelicula.duracion} min</span>`);
    if (pelicula.puntuacion)   metas.push(`<span>★ ${pelicula.puntuacion.toFixed(1)} TMDB</span>`);
    document.getElementById('meta').innerHTML = metas.join('<span>·</span>');

    // generos como pastillas (escapados por si TMDB devuelve algo raro)
    document.getElementById('generos').innerHTML = (pelicula.generos || [])
        .map(g => `<span class="genero-tag">${escapeHTML(g)}</span>`)
        .join('');

    // sinopsis con textContent, ya escapa por si solo
    document.getElementById('sinopsis').textContent = pelicula.descripcion || '';

    // reparto
    const gridReparto = document.getElementById('gridReparto');
    if (pelicula.reparto && pelicula.reparto.length > 0) {
        gridReparto.innerHTML = pelicula.reparto.map(actor => {
            const nombreSafe = escapeHTML(actor.nombre || '—');
            const personajeSafe = escapeHTML(actor.personaje || '');
            const fotoSafe = escapeHTML(actor.foto || '');
            return `
            <div class="actor-card" ${actor.person_id ? `onclick="irAPersona(${actor.person_id})"` : ''}>
                ${actor.foto
                    ? `<img class="actor-foto" src="${fotoSafe}" alt="${nombreSafe}" loading="lazy">`
                    : `<div class="actor-foto" style="display:flex;align-items:center;justify-content:center;color:var(--faint);font-family:var(--font-display);font-size:14px">?</div>`
                }
                <div class="actor-info">
                    <div class="actor-nombre">${nombreSafe}</div>
                    <div class="actor-personaje">${personajeSafe}</div>
                </div>
            </div>
        `;
        }).join('');
    } else {
        gridReparto.innerHTML = `<p class="text-faint" style="font-size:13px">Sin datos de reparto.</p>`;
    }

    // equipo tecnico (crew). Traduccion de departamentos al español.
    const DEPT_ES = {
        'Directing':         'Dirección',
        'Writing':           'Guion',
        'Camera':            'Fotografía',
        'Editing':           'Montaje',
        'Sound':             'Música',
        'Production':        'Producción',
        'Art':               'Dirección de Arte',
        'Costume & Make-Up': 'Vestuario',
        'Visual Effects':    'Efectos Visuales',
        'Lighting':          'Iluminación',
    };

    const gridEquipo = document.getElementById('gridEquipo');
    if (pelicula.crew && pelicula.crew.length > 0) {
        // agrupamos por departamento
        const grupos = {};
        pelicula.crew.forEach(p => {
            const dept = p.departamento || 'Otros';
            if (!grupos[dept]) grupos[dept] = [];
            grupos[dept].push(p);
        });

        gridEquipo.innerHTML = Object.entries(grupos).map(([dept, personas]) => `
            <div class="crew-grupo">
                <div class="crew-grupo__titulo">${DEPT_ES[dept] || dept}</div>
                ${personas.map(p => {
                    const nombreSafe = escapeHTML(p.nombre || '—');
                    const rolSafe = escapeHTML(p.rol || '');
                    const fotoSafe = escapeHTML(p.foto || '');
                    return `
                    <div class="crew-fila" ${p.person_id ? `onclick="irAPersona(${p.person_id})"` : ''}>
                        ${p.foto
                            ? `<img class="crew-foto" src="${fotoSafe}" alt="${nombreSafe}" loading="lazy">`
                            : `<div class="crew-foto crew-foto--placeholder">${escapeHTML((p.nombre || '?')[0])}</div>`
                        }
                        <div class="crew-info">
                            <div class="crew-nombre">${nombreSafe}</div>
                            <div class="crew-rol">${rolSafe}</div>
                        </div>
                    </div>
                `;
                }).join('')}
            </div>
        `).join('');
    } else {
        gridEquipo.innerHTML = `<p class="text-faint" style="font-size:13px">Sin datos de equipo técnico.</p>`;
    }

    // detalles (titulo original, idioma, paises...)
    const listaDetalles = document.getElementById('listaDetalles');
    const filas = [];

    function formatearDinero(n) {
        if (!n) return null;
        if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
        if (n >= 1_000_000)     return `$${Math.round(n / 1_000_000)}M`;
        return `$${n.toLocaleString('es-ES')}`;
    }

    if (pelicula.titulo_original && pelicula.titulo_original !== pelicula.titulo)
        filas.push(['Título original', pelicula.titulo_original]);
    if (pelicula.idioma_original)
        filas.push(['Idioma original', new Intl.DisplayNames(['es'], { type: 'language' }).of(pelicula.idioma_original) || pelicula.idioma_original]);
    if (pelicula.paises?.length)
        filas.push(['País', pelicula.paises.join(', ')]);
    if (pelicula.productoras?.length)
        filas.push(['Productora', pelicula.productoras.join(', ')]);
    if (pelicula.presupuesto)
        filas.push(['Presupuesto', formatearDinero(pelicula.presupuesto)]);
    if (pelicula.recaudacion)
        filas.push(['Taquilla', formatearDinero(pelicula.recaudacion)]);
    if (pelicula.duracion)
        filas.push(['Duración', `${pelicula.duracion} minutos`]);

    if (filas.length > 0) {
        listaDetalles.innerHTML = filas.map(([k, v]) =>
            `<dt>${escapeHTML(k)}</dt><dd>${escapeHTML(v)}</dd>`
        ).join('');
    } else {
        listaDetalles.innerHTML = `<p class="text-faint" style="font-size:13px;grid-column:1/-1">Sin detalles disponibles.</p>`;
    }

}


// Acciones (vista, like, watchlist, puntuacion)

async function toggleVista() {
    try {
        if (estado.vista) {
            await api.acciones.desmarcarVista(tmdbId);
            estado.vista = false;
            mostrarToast('Película desmarcada como vista');
        } else {
            await api.acciones.marcarVista(tmdbId);
            estado.vista = true;
            // si estaba en watchlist, el back la quita sola
            if (estado.en_watchlist) estado.en_watchlist = false;
            mostrarToast('Película marcada como vista ✓');
        }
        actualizarBotonesAccion();
    } catch (err) {
        console.warn('[pelicula] toggleVista', err);
        mostrarToast(err.message || 'Error al actualizar', 'error');
    }
}

async function toggleMeGusta() {
    try {
        if (estado.me_gusta) {
            await api.acciones.quitarMeGusta(tmdbId);
            estado.me_gusta = false;
            mostrarToast('Me gusta eliminado');
        } else {
            await api.acciones.darMeGusta(tmdbId);
            estado.me_gusta = true;
            mostrarToast('¡Me gusta! ♥');
        }
        actualizarBotonesAccion();
    } catch (err) {
        console.warn('[pelicula] toggleMeGusta', err);
        mostrarToast(err.message || 'Error al actualizar', 'error');
    }
}

async function toggleWatchlist() {
    try {
        if (estado.en_watchlist) {
            await api.acciones.quitarWatchlist(tmdbId);
            estado.en_watchlist = false;
            mostrarToast('Eliminada de la watchlist');
        } else {
            await api.acciones.añadirWatchlist(tmdbId);
            estado.en_watchlist = true;
            mostrarToast('Añadida a la watchlist ✓');
        }
        actualizarBotonesAccion();
    } catch (err) {
        console.warn('[pelicula] toggleWatchlist', err);
        mostrarToast(err.message || 'Error al actualizar', 'error');
    }
}

// si pulsas la misma puntuacion -> la quita (toggle)
async function setPuntuacion(valor) {
    try {
        if (estado.puntuacion === valor) {
            await api.acciones.eliminarPuntuacion(tmdbId);
            estado.puntuacion = null;
            mostrarToast('Puntuación eliminada');
        } else {
            await api.acciones.puntuar(tmdbId, valor);
            estado.puntuacion = valor;
            // puntuar marca como vista (lo hace el backend)
            if (!estado.vista) {
                estado.vista = true;
                if (estado.en_watchlist) estado.en_watchlist = false;
            }
            mostrarToast(`Puntuación: ${valor}/10 guardada`);
        }
        actualizarBotonesAccion();
        renderizarPuntuacion();
    } catch (err) {
        console.warn('[pelicula] setPuntuacion', err);
        mostrarToast(err.message || 'Error al puntuar', 'error');
    }
}

function irAPersona(personId) {
    window.location.href = `persona.html?id=${personId}`;
}


// Modal del diario

let puntuacionDiario = null;

function abrirModalDiario() {
    inicializarSelectorPuntuacionDiario();
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('fechaVisionado').value = hoy;
    document.getElementById('modalDiario').classList.remove('modal-overlay--hidden');
}

function cerrarModalDiario() {
    document.getElementById('modalDiario').classList.add('modal-overlay--hidden');
}

function inicializarSelectorPuntuacionDiario() {
    const sel = document.getElementById('selectorPuntuacionDiario');
    if (!sel || sel.innerHTML) return;
    sel.innerHTML = Array.from({ length: 10 }, (_, i) => {
        const v = i + 1;
        return `<button class="punt-btn" data-val="${v}" onclick="setPuntuacionDiario(${v})">${v}</button>`;
    }).join('');
}

function setPuntuacionDiario(val) {
    puntuacionDiario = puntuacionDiario === val ? null : val;
    document.querySelectorAll('#selectorPuntuacionDiario .punt-btn').forEach(btn => {
        btn.classList.toggle('punt-btn--activo', parseInt(btn.dataset.val) === puntuacionDiario);
    });
}

async function guardarDiario() {
    const fecha  = document.getElementById('fechaVisionado').value;
    const resena = document.getElementById('resena').value.trim();

    if (!fecha) {
        mostrarToast('Indica la fecha de visionado', 'error');
        return;
    }

    try {
        await api.acciones.crearDiario(tmdbId, {
            fecha_visionado: fecha,
            resena: resena || null,
            puntuacion: puntuacionDiario,
        });

        estado.vista = true;
        if (estado.en_watchlist) estado.en_watchlist = false;
        actualizarBotonesAccion();

        document.getElementById('resena').value = '';
        puntuacionDiario = null;
        document.querySelectorAll('#selectorPuntuacionDiario .punt-btn')
            .forEach(b => b.classList.remove('punt-btn--activo'));

        cerrarModalDiario();
        mostrarToast('Entrada guardada en el diario ✓');
    } catch (err) {
        console.warn('[pelicula] guardarDiario', err);
        mostrarToast(err.message || 'Error al guardar en el diario', 'error');
    }
}


// Pestañas (reparto, equipo, detalles, reseñas)

let resenasCargadas = false;

function activarTab(nombre) {
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.toggle('tab--activo', btn.dataset.tab === nombre);
    });
    document.getElementById('panelReparto').classList.toggle('oculto',  nombre !== 'reparto');
    document.getElementById('panelEquipo').classList.toggle('oculto',   nombre !== 'equipo');
    document.getElementById('panelDetalles').classList.toggle('oculto', nombre !== 'detalles');
    document.getElementById('panelResenas').classList.toggle('oculto',  nombre !== 'resenas');

    if (nombre === 'resenas' && !resenasCargadas) {
        resenasCargadas = true;
        cargarResenas();
    }
}


// Modal "añadir a lista"

let listasUsuarioCargadas = false;

async function abrirModalListas() {
    document.getElementById('modalListas').classList.remove('modal-overlay--hidden');
    if (!listasUsuarioCargadas) {
        listasUsuarioCargadas = true;
        await cargarModalListas();
    }
}

function cerrarModalListas() {
    document.getElementById('modalListas').classList.add('modal-overlay--hidden');
}

async function cargarModalListas() {
    const contenedor = document.getElementById('listasUsuario');
    try {
        const usuario  = await api.usuarios.mePerfil();
        const [listas, yaEn] = await Promise.all([
            api.usuarios.listas(usuario.id),
            api.listas.listasConPelicula(tmdbId),
        ]);

        if (listas.length === 0) {
            contenedor.innerHTML = `
                <p class="text-faint" style="font-size:13px">Sin listas.
                    <a href="listas.html" style="color:var(--accent)">Crea una →</a>
                </p>`;
            return;
        }

        // OJO con el nombre de la lista: lo escribe el usuario.
        // Lo metemos en data-attr y leemos desde el handler para evitar XSS.
        contenedor.innerHTML = listas.map(l => {
            const añadida = yaEn.includes(l.id);
            const nombreSafe = escapeHTML(l.nombre);
            return `
                <button class="btn btn--sm lista-modal-btn ${añadida ? 'lista-modal-btn--añadida' : 'btn--surface'}"
                        style="width:100%;justify-content:flex-start;font-weight:400"
                        id="lista-btn-${l.id}"
                        data-id-lista="${l.id}"
                        data-nombre="${nombreSafe}"
                        ${añadida ? 'disabled' : ''}>
                    ${nombreSafe}
                    <span style="margin-left:auto;font-size:11px">
                        ${añadida ? 'Añadida ✓' : (l.es_publica ? 'Pública' : 'Privada')}
                    </span>
                </button>
            `;
        }).join('');

        // listener delegado para los botones, sin onclick inline con strings interpolados
        contenedor.querySelectorAll('.lista-modal-btn:not([disabled])').forEach(btn => {
            btn.addEventListener('click', () => {
                añadirALista(parseInt(btn.dataset.idLista), btn.dataset.nombre);
            });
        });
    } catch (err) {
        console.warn('[pelicula] cargarModalListas', err);
        contenedor.innerHTML = '<p class="text-faint" style="font-size:13px">Error al cargar listas.</p>';
    }
}

async function añadirALista(idLista, nombreLista) {
    try {
        await api.listas.añadirPelicula(idLista, tmdbId);
        mostrarToast(`Añadida a "${nombreLista}" ✓`);
        const btn = document.getElementById(`lista-btn-${idLista}`);
        if (btn) {
            btn.classList.remove('btn--surface');
            btn.classList.add('lista-modal-btn--añadida');
            btn.disabled = true;
            btn.querySelector('span').textContent = 'Añadida ✓';
        }
    } catch (err) {
        console.warn('[pelicula] añadirALista', err);
        mostrarToast(err.message || 'Error al añadir', 'error');
    }
}


// Reseñas (amigos + comunidad)

async function cargarResenas() {
    // de amigos solo si hay sesion
    if (auth.estaLogueado()) {
        try {
            const amigos = await api.resenas.amigos(tmdbId);
            renderResenaAmigos(amigos);
            if (amigos.length > 0) {
                document.getElementById('seccionAmigos').classList.remove('oculto');
                document.getElementById('subtituloComunidad').textContent = 'Comunidad';
            }
        } catch (err) {
            console.warn('[pelicula] resenas amigos', err);
        }
    }

    // comunidad
    try {
        const comunidad = await api.resenas.comunidad(tmdbId);
        renderResenasComunidad(comunidad);
    } catch (err) {
        console.warn('[pelicula] resenas comunidad', err);
        document.getElementById('listaComunidad').innerHTML =
            '<p class="text-faint" style="font-size:13px">No se pudieron cargar las reseñas.</p>';
    }
}

function avatarHTML(avatar_url, username, size = 32) {
    const style = `width:${size}px;height:${size}px`;
    const userSafe = escapeHTML(username || '?');
    if (avatar_url) {
        const avatarSafe = escapeHTML(avatar_url);
        return `<div class="resena-card__avatar" style="${style}"><img src="${avatarSafe}" alt="${userSafe}"></div>`;
    }
    return `<div class="resena-card__avatar" style="${style}">${userSafe[0].toUpperCase()}</div>`;
}

function renderResenaAmigos(amigos) {
    const lista = document.getElementById('listaAmigos');
    if (amigos.length === 0) {
        lista.innerHTML = '<p class="text-faint" style="font-size:13px;padding:8px 0">Ningún amigo ha visto esta película aún.</p>';
        return;
    }
    lista.innerHTML = amigos.map(a => {
        const userSafe = escapeHTML(a.username);
        const avgEl = a.avatar_url
            ? `<img src="${escapeHTML(a.avatar_url)}" alt="${userSafe}">`
            : escapeHTML(a.username[0].toUpperCase());
        return `
            <div class="amigo-resena">
                <div class="amigo-resena__avatar">${avgEl}</div>
                <div class="amigo-resena__info">
                    <div class="amigo-resena__username"
                         onclick="location.href='usuario.html?id=${a.id_usuario}'">${userSafe}</div>
                    <div class="amigo-resena__stats">
                        ${a.puntuacion ? `<span>★ ${a.puntuacion}/10</span>` : ''}
                        <span>${a.total_entradas} ${a.total_entradas === 1 ? 'visionado' : 'visionados'}</span>
                    </div>
                    ${a.ultima_resena
                        ? `<p class="amigo-resena__texto">"${escapeHTML(a.ultima_resena)}"</p>`
                        : ''}
                </div>
            </div>
        `;
    }).join('');
}

function renderResenasComunidad(resenas) {
    const lista = document.getElementById('listaComunidad');
    if (resenas.length === 0) {
        lista.innerHTML = '<p class="text-faint" style="font-size:13px">Aún no hay reseñas de la comunidad.</p>';
        return;
    }
    lista.innerHTML = resenas.map(r => crearResenaCardHTML(r)).join('');
}

const resenasCache = {};

function abrirModalResena(id) {
    const r = resenasCache[id];
    if (!r) return;
    const fecha = new Date(r.fecha_visionado).toLocaleDateString('es', {
        day: 'numeric', month: 'short', year: 'numeric'
    });
    const avatarEl = document.getElementById('resenaModalAvatar');
    avatarEl.innerHTML = r.avatar_url
        ? `<img src="${escapeHTML(r.avatar_url)}" alt="${escapeHTML(r.username)}">`
        : escapeHTML(r.username[0].toUpperCase());
    document.getElementById('resenaModalUsername').textContent   = r.username;
    document.getElementById('resenaModalFecha').textContent      = fecha;
    document.getElementById('resenaModalPuntuacion').textContent = r.puntuacion ? `★ ${r.puntuacion}` : '';
    document.getElementById('resenaModalTexto').textContent      = r.resena || '';
    document.getElementById('modalVerResena').classList.remove('modal-overlay--hidden');
}

function cerrarModalResena() {
    document.getElementById('modalVerResena').classList.add('modal-overlay--hidden');
}

function crearResenaCardHTML(r) {
    resenasCache[r.id] = r;
    const fecha = new Date(r.fecha_visionado).toLocaleDateString('es', {
        day: 'numeric', month: 'short', year: 'numeric'
    });
    const likedClass = r.yo_di_like ? 'resena-accion-btn--liked' : '';
    const tieneTexto = !!r.resena;
    const userSafe = escapeHTML(r.username);

    return `
        <div class="resena-card" id="resena-${r.id}">
            <div class="resena-card__header" ${tieneTexto ? `style="cursor:pointer" onclick="abrirModalResena(${r.id})"` : ''}>
                ${avatarHTML(r.avatar_url, r.username)}
                <div class="resena-card__meta">
                    <div class="resena-card__username"
                         onclick="event.stopPropagation();location.href='usuario.html?id=${r.id_usuario}'">${userSafe}</div>
                    <div class="resena-card__fecha">${fecha}</div>
                </div>
                ${r.puntuacion ? `<div class="resena-card__puntuacion">★ ${r.puntuacion}</div>` : ''}
            </div>
            ${tieneTexto ? `<p class="resena-card__texto diario-resena" style="cursor:pointer" onclick="abrirModalResena(${r.id})">${escapeHTML(r.resena)}</p>` : ''}
            <div class="resena-card__acciones">
                <button class="resena-accion-btn ${likedClass}" id="like-btn-${r.id}"
                        onclick="toggleLike(${r.id}, this)" ${auth.estaLogueado() ? '' : 'disabled'}>
                    <svg viewBox="0 0 24 24" fill="${r.yo_di_like ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                    </svg>
                    <span id="like-count-${r.id}">${r.total_likes}</span>
                </button>
                <button class="resena-accion-btn" onclick="toggleComentarios(${r.id}, this)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    <span>${r.total_comentarios}</span>
                </button>
            </div>
            <div class="comentarios-seccion oculto" id="comentarios-${r.id}"></div>
        </div>
    `;
}

async function toggleLike(idEntrada, btn) {
    if (!auth.estaLogueado()) return;
    const liked = btn.classList.contains('resena-accion-btn--liked');
    const countEl = document.getElementById(`like-count-${idEntrada}`);
    try {
        if (liked) {
            await api.resenas.quitarLike(idEntrada);
            btn.classList.remove('resena-accion-btn--liked');
            btn.querySelector('svg').setAttribute('fill', 'none');
            countEl.textContent = Math.max(0, parseInt(countEl.textContent) - 1);
        } else {
            await api.resenas.darLike(idEntrada);
            btn.classList.add('resena-accion-btn--liked');
            btn.querySelector('svg').setAttribute('fill', 'currentColor');
            countEl.textContent = parseInt(countEl.textContent) + 1;
        }
    } catch (err) {
        console.warn('[pelicula] toggleLike', err);
        mostrarToast(err.message || 'Error al procesar like', 'error');
    }
}

async function toggleComentarios(idEntrada, btn) {
    const seccion = document.getElementById(`comentarios-${idEntrada}`);
    if (!seccion.classList.contains('oculto')) {
        seccion.classList.add('oculto');
        return;
    }
    seccion.classList.remove('oculto');
    if (seccion.dataset.cargado) return;
    seccion.dataset.cargado = '1';
    await cargarComentarios(idEntrada, seccion);
}

async function cargarComentarios(idEntrada, contenedor) {
    try {
        const comentarios = await api.resenas.comentarios(idEntrada);
        const miId = auth.getUsuario()?.id;

        const listHTML = comentarios.length === 0
            ? '<p class="text-faint" style="font-size:12px;padding:4px 0">Sin comentarios aún.</p>'
            : comentarios.map(c => {
                const userSafe = escapeHTML(c.username);
                const textoSafe = escapeHTML(c.texto);
                const avatarSafe = escapeHTML(c.avatar_url || '');
                return `
                <div class="comentario-item" id="comentario-${c.id}">
                    <div class="comentario-item__avatar">
                        ${c.avatar_url
                            ? `<img src="${avatarSafe}" alt="${userSafe}">`
                            : escapeHTML(c.username[0].toUpperCase())
                        }
                    </div>
                    <div class="comentario-item__body">
                        <span class="comentario-item__username">${userSafe}</span>
                        <span class="comentario-item__texto">${textoSafe}</span>
                        ${miId === c.id_usuario
                            ? `<button class="comentario-item__borrar"
                                       onclick="borrarComentario(${c.id}, ${idEntrada})">✕</button>`
                            : ''}
                    </div>
                </div>
            `;
            }).join('');

        const formHTML = auth.estaLogueado() ? `
            <div class="comentario-form" id="form-comentario-${idEntrada}">
                <input type="text" placeholder="Añadir comentario…"
                       maxlength="500"
                       onkeydown="if(event.key==='Enter') enviarComentario(${idEntrada})"/>
                <button class="btn btn--surface btn--sm"
                        onclick="enviarComentario(${idEntrada})">Enviar</button>
            </div>
        ` : '';

        contenedor.innerHTML = `<div id="lista-comentarios-${idEntrada}">${listHTML}</div>${formHTML}`;
    } catch (err) {
        console.warn('[pelicula] cargarComentarios', err);
        contenedor.innerHTML = '<p class="text-faint" style="font-size:12px">Error al cargar comentarios.</p>';
    }
}

async function enviarComentario(idEntrada) {
    const form = document.getElementById(`form-comentario-${idEntrada}`);
    const input = form.querySelector('input');
    const texto = input.value.trim();
    if (!texto) return;
    try {
        const nuevo = await api.resenas.crearComentario(idEntrada, texto);
        input.value = '';
        const lista = document.getElementById(`lista-comentarios-${idEntrada}`);
        const miId  = auth.getUsuario()?.id;
        const item  = document.createElement('div');
        item.className = 'comentario-item';
        item.id = `comentario-${nuevo.id}`;
        const userSafe = escapeHTML(nuevo.username);
        const textoSafe = escapeHTML(nuevo.texto);
        const avatarSafe = escapeHTML(nuevo.avatar_url || '');
        item.innerHTML = `
            <div class="comentario-item__avatar">
                ${nuevo.avatar_url
                    ? `<img src="${avatarSafe}" alt="${userSafe}">`
                    : escapeHTML(nuevo.username[0].toUpperCase())
                }
            </div>
            <div class="comentario-item__body">
                <span class="comentario-item__username">${userSafe}</span>
                <span class="comentario-item__texto">${textoSafe}</span>
                <button class="comentario-item__borrar"
                        onclick="borrarComentario(${nuevo.id}, ${idEntrada})">✕</button>
            </div>
        `;
        // si era el mensaje de "sin comentarios" lo limpiamos
        if (lista.querySelector('.text-faint')) lista.innerHTML = '';
        lista.appendChild(item);
    } catch (err) {
        console.warn('[pelicula] enviarComentario', err);
        mostrarToast(err.message || 'Error al comentar', 'error');
    }
}

async function borrarComentario(idComentario, idEntrada) {
    try {
        await api.resenas.borrarComentario(idComentario);
        const el = document.getElementById(`comentario-${idComentario}`);
        if (el) el.remove();
    } catch (err) {
        console.warn('[pelicula] borrarComentario', err);
        mostrarToast(err.message || 'Error al borrar', 'error');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    renderNav('../');

    document.getElementById('tabBar').addEventListener('click', e => {
        const tab = e.target.closest('.tab');
        if (tab) activarTab(tab.dataset.tab);
    });

    // sacamos el id de la peli de la URL (?id=XXXX)
    const params = new URLSearchParams(window.location.search);
    tmdbId = parseInt(params.get('id'));

    if (!tmdbId) {
        // sin id valido nos vamos a inicio
        window.location.href = '../index.html';
        return;
    }

    try {
        const pelicula = await api.peliculas.detalle(tmdbId);
        renderizarPelicula(pelicula);

        if (auth.estaLogueado()) {
            document.getElementById('accionesPanel').classList.remove('oculto');
            document.getElementById('panelVisitante').classList.add('oculto');

            // si el back ya nos manda el estado del user, lo guardamos
            if (pelicula.estado_usuario) {
                estado = pelicula.estado_usuario;
            }

            actualizarBotonesAccion();
            renderizarPuntuacion();
        } else {
            document.getElementById('accionesPanel').classList.add('oculto');
            document.getElementById('panelVisitante').classList.remove('oculto');
        }

    } catch (err) {
        console.warn('[pelicula] error cargando detalle', err);
        mostrarToast('No se pudo cargar la película', 'error');
    }
});
