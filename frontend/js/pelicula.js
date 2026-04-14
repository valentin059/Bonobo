// js/pelicula.js — Lógica de la página de detalle de una película
// Lee el tmdb_id de la URL (?id=XXXX), carga los datos y gestiona las acciones del usuario.

// Estado actual del usuario con esta película (se actualiza con cada acción)
let estado = { vista: false, puntuacion: null, me_gusta: false, en_watchlist: false };
let tmdbId = null;   // id de la película actual, necesario para las llamadas a la API

// ── UTILIDADES ────────────────────────────────────────────────────────────────

function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}

// ── RENDER ────────────────────────────────────────────────────────────────────

// Actualiza los botones de acción para que reflejen el estado actual del usuario.
function actualizarBotonesAccion() {
    const btnVista     = document.getElementById('btnVista');
    const btnLike      = document.getElementById('btnLike');
    const btnWatchlist = document.getElementById('btnWatchlist');
    const lblVista     = document.getElementById('lblVista');

    // Botón Vista: verde si está marcada, neutral si no
    if (estado.vista) {
        btnVista.classList.add('accion-btn--watched');
        lblVista.textContent = 'Vista ✓';
    } else {
        btnVista.classList.remove('accion-btn--watched');
        lblVista.textContent = 'Vista';
    }

    // Botón Me gusta: rojo si activo
    if (estado.me_gusta) {
        btnLike.classList.add('accion-btn--liked');
    } else {
        btnLike.classList.remove('accion-btn--liked');
    }

    // Botón Watchlist: azul si activo
    if (estado.en_watchlist) {
        btnWatchlist.classList.add('accion-btn--watchlist');
    } else {
        btnWatchlist.classList.remove('accion-btn--watchlist');
    }
}

// Genera los botones de puntuación del 1 al 10 y marca el activo.
function renderizarPuntuacion() {
    const selector = document.getElementById('selectorPuntuacion');
    if (!selector) return;

    selector.innerHTML = Array.from({ length: 10 }, (_, i) => {
        const num = i + 1;
        const activo = estado.puntuacion === num ? 'punt-btn--activo' : '';
        return `<button class="punt-btn ${activo}" onclick="setPuntuacion(${num})">${num}</button>`;
    }).join('');
}

// Rellena la página con los datos de la película obtenidos de la API.
function renderizarPelicula(pelicula) {
    document.title = `BONOBO — ${pelicula.titulo || 'Película'}`;

    // Fondo del hero: usamos el backdrop 16:9 de TMDB si existe (nítido),
    // y como fallback el póster muy difuminado.
    const heroBg    = document.getElementById('heroBg');
    const heroWrap  = document.getElementById('peliculaHero');
    if (pelicula.backdrop_url) {
        heroBg.style.backgroundImage = `url('${pelicula.backdrop_url}')`;
        heroWrap.classList.add('has-backdrop');   // activa el CSS sin blur
    } else if (pelicula.poster_url) {
        heroBg.style.backgroundImage = `url('${pelicula.poster_url}')`;
    }

    // Póster principal
    const posterWrap = document.getElementById('posterWrap');
    posterWrap.innerHTML = pelicula.poster_url
        ? `<img src="${pelicula.poster_url}" alt="${pelicula.titulo}">`
        : `<div class="pelicula-card__no-img" style="aspect-ratio:2/3">SIN IMAGEN</div>`;

    // Título
    document.getElementById('titulo').textContent = pelicula.titulo || '—';

    // Director — buscamos el cargo "Director" en el crew y lo mostramos bajo el título
    const director = (pelicula.crew || []).find(p => p.rol === 'Director');
    const directorEl = document.getElementById('director');
    if (director) {
        directorEl.textContent = `Dirigida por ${director.nombre}`;
    } else {
        directorEl.textContent = '';
    }

    // Meta: año, duración, puntuación TMDB
    const metas = [];
    if (pelicula.anio_estreno) metas.push(`<span>${pelicula.anio_estreno}</span>`);
    if (pelicula.duracion)     metas.push(`<span>${pelicula.duracion} min</span>`);
    if (pelicula.puntuacion)   metas.push(`<span>★ ${pelicula.puntuacion.toFixed(1)} TMDB</span>`);
    document.getElementById('meta').innerHTML = metas.join('<span>·</span>');

    // Géneros como pastillas
    document.getElementById('generos').innerHTML = (pelicula.generos || [])
        .map(g => `<span class="genero-tag">${g}</span>`)
        .join('');

    // Sinopsis
    document.getElementById('sinopsis').textContent = pelicula.descripcion || '';

    // ── Reparto ──────────────────────────────────────────────────────────────
    const gridReparto = document.getElementById('gridReparto');
    if (pelicula.reparto && pelicula.reparto.length > 0) {
        gridReparto.innerHTML = pelicula.reparto.map(actor => `
            <div class="actor-card">
                ${actor.foto
                    ? `<img class="actor-foto" src="${actor.foto}" alt="${actor.nombre}" loading="lazy">`
                    : `<div class="actor-foto" style="display:flex;align-items:center;justify-content:center;color:var(--faint)">?</div>`
                }
                <div class="actor-nombre">${actor.nombre || '—'}</div>
                <div class="actor-personaje">${actor.personaje || ''}</div>
            </div>
        `).join('');
    } else {
        gridReparto.innerHTML = `<p class="text-faint" style="font-size:13px">Sin datos de reparto.</p>`;
    }

    // ── Equipo técnico ────────────────────────────────────────────────────────
    // Traducción de departamentos TMDB al español
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
        // Agrupamos por departamento manteniendo el orden de DEPARTAMENTOS_CREW
        const grupos = {};
        pelicula.crew.forEach(p => {
            const dept = p.departamento || 'Otros';
            if (!grupos[dept]) grupos[dept] = [];
            grupos[dept].push(p);
        });

        gridEquipo.innerHTML = Object.entries(grupos).map(([dept, personas]) => `
            <div class="crew-grupo">
                <div class="crew-grupo__titulo">${DEPT_ES[dept] || dept}</div>
                ${personas.map(p => `
                    <div class="crew-fila">
                        ${p.foto
                            ? `<img class="crew-foto" src="${p.foto}" alt="${p.nombre}" loading="lazy">`
                            : `<div class="crew-foto crew-foto--placeholder">${(p.nombre || '?')[0]}</div>`
                        }
                        <div class="crew-info">
                            <div class="crew-nombre">${p.nombre || '—'}</div>
                            <div class="crew-rol">${p.rol || ''}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `).join('');
    } else {
        gridEquipo.innerHTML = `<p class="text-faint" style="font-size:13px">Sin datos de equipo técnico.</p>`;
    }

    // ── Detalles ──────────────────────────────────────────────────────────────
    const listaDetalles = document.getElementById('listaDetalles');
    const filas = [];

    // Función auxiliar para formatear monedas en millones/miles de millones
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
            `<dt>${k}</dt><dd>${v}</dd>`
        ).join('');
    } else {
        listaDetalles.innerHTML = `<p class="text-faint" style="font-size:13px;grid-column:1/-1">Sin detalles disponibles.</p>`;
    }

    // Ponemos la fecha de hoy como valor por defecto en el campo de diario
    const hoy = new Date().toISOString().split('T')[0];
    const fechaInput = document.getElementById('fechaVisionado');
    if (fechaInput) fechaInput.value = hoy;
}

// ── ACCIONES ──────────────────────────────────────────────────────────────────

// Alterna entre "vista" y "no vista".
async function toggleVista() {
    try {
        if (estado.vista) {
            await api.acciones.desmarcarVista(tmdbId);
            estado.vista = false;
            // Si se desmarca como vista, también pierde puntuación y me gusta en la interfaz
            // (el backend ya gestiona la lógica de restricciones)
            mostrarToast('Película desmarcada como vista');
        } else {
            await api.acciones.marcarVista(tmdbId);
            estado.vista = true;
            // Si estaba en watchlist, el backend la elimina automáticamente
            if (estado.en_watchlist) estado.en_watchlist = false;
            mostrarToast('Película marcada como vista ✓');
        }
        actualizarBotonesAccion();
    } catch (err) {
        mostrarToast(err.message || 'Error al actualizar', 'error');
    }
}

// Alterna entre "me gusta" y "no me gusta".
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
        mostrarToast(err.message || 'Error al actualizar', 'error');
    }
}

// Alterna entre "en watchlist" y "fuera de watchlist".
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
        mostrarToast(err.message || 'Error al actualizar', 'error');
    }
}

// Guarda o actualiza la puntuación. Si ya tenía la misma, la elimina (toggle).
async function setPuntuacion(valor) {
    try {
        if (estado.puntuacion === valor) {
            // Si pulsa la misma puntuación que ya tiene → la elimina
            await api.acciones.eliminarPuntuacion(tmdbId);
            estado.puntuacion = null;
            mostrarToast('Puntuación eliminada');
        } else {
            await api.acciones.puntuar(tmdbId, valor);
            estado.puntuacion = valor;
            // Puntuar marca la película como vista automáticamente
            if (!estado.vista) {
                estado.vista = true;
                if (estado.en_watchlist) estado.en_watchlist = false;
            }
            mostrarToast(`Puntuación: ${valor}/10 guardada`);
        }
        actualizarBotonesAccion();
        renderizarPuntuacion();
    } catch (err) {
        mostrarToast(err.message || 'Error al puntuar', 'error');
    }
}

// Guarda una nueva entrada en el diario del usuario.
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
            resena: resena || null   // si está vacío, mandamos null (es opcional)
        });

        // Crear entrada de diario marca la película como vista automáticamente
        estado.vista = true;
        if (estado.en_watchlist) estado.en_watchlist = false;
        actualizarBotonesAccion();

        // Limpiamos el campo de reseña tras guardar
        document.getElementById('resena').value = '';
        mostrarToast('Entrada guardada en el diario ✓');
    } catch (err) {
        mostrarToast(err.message || 'Error al guardar en el diario', 'error');
    }
}

// ── INIT ──────────────────────────────────────────────────────────────────────

// ── PESTAÑAS ──────────────────────────────────────────────────────────────────

// Cambia la pestaña activa y muestra el panel correspondiente.
function activarTab(nombre) {
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.toggle('tab--activo', btn.dataset.tab === nombre);
    });
    document.getElementById('panelReparto').classList.toggle('oculto', nombre !== 'reparto');
    document.getElementById('panelEquipo').classList.toggle('oculto',  nombre !== 'equipo');
    document.getElementById('panelDetalles').classList.toggle('oculto', nombre !== 'detalles');
}

document.addEventListener('DOMContentLoaded', async () => {
    renderNav('../');

    // Registramos el listener de las pestañas
    document.getElementById('tabBar').addEventListener('click', e => {
        const tab = e.target.closest('.tab');
        if (tab) activarTab(tab.dataset.tab);
    });

    // Leemos el id de la película de los parámetros de la URL (?id=XXXX)
    const params = new URLSearchParams(window.location.search);
    tmdbId = parseInt(params.get('id'));

    if (!tmdbId) {
        // Si no hay id válido, volvemos a inicio
        window.location.href = '../index.html';
        return;
    }

    try {
        // Pedimos el detalle de la película (incluye estado del usuario si está logueado)
        const pelicula = await api.peliculas.detalle(tmdbId);
        renderizarPelicula(pelicula);

        if (auth.estaLogueado()) {
            // Mostramos el panel de acciones y ocultamos el de visitante
            document.getElementById('accionesPanel').classList.remove('oculto');
            document.getElementById('panelVisitante').classList.add('oculto');

            // Si el backend nos devolvió el estado del usuario con la película, lo cargamos
            if (pelicula.estado_usuario) {
                estado = pelicula.estado_usuario;
            }

            actualizarBotonesAccion();
            renderizarPuntuacion();
        } else {
            // Visitante: mostramos el botón de "entrar para registrarla"
            document.getElementById('accionesPanel').classList.add('oculto');
            document.getElementById('panelVisitante').classList.remove('oculto');
        }

    } catch (err) {
        mostrarToast('No se pudo cargar la película', 'error');
    }
});
