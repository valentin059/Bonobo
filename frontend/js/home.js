// home.js — pagina principal (index.html)
// Hero, cartelera, estrenos y busqueda.


function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}

// Crea la tarjeta de una peli para el grid.
// pelicula = { tmdb_id, titulo, poster_url, anio_estreno, puntuacion? }
function crearTarjetaPelicula(pelicula) {
    const tituloSafe = escapeHTML(pelicula.titulo || 'Sin título');
    const posterSafe = escapeHTML(pelicula.poster_url || '');

    const imgHTML = pelicula.poster_url
        ? `<img class="pelicula-card__img" src="${posterSafe}" alt="${tituloSafe}" loading="lazy">`
        : `<div class="pelicula-card__no-img">SIN IMAGEN</div>`;

    // puntuacion de TMDB (solo si la hay)
    const puntHTML = pelicula.puntuacion
        ? `<div class="pelicula-card__puntuacion">★ ${pelicula.puntuacion.toFixed(1)}</div>`
        : '';

    return `
        <div class="pelicula-card" onclick="irAPelicula(${pelicula.tmdb_id})">
            <div class="pelicula-card__poster">
                ${imgHTML}
                <div class="pelicula-card__overlay">
                    ${puntHTML}
                </div>
            </div>
            <div class="pelicula-card__info">
                <div class="pelicula-card__titulo">${tituloSafe}</div>
                <div class="pelicula-card__anio">${pelicula.anio_estreno || ''}</div>
            </div>
        </div>
    `;
}

function irAPelicula(tmdbId) {
    window.location.href = `pages/pelicula.html?id=${tmdbId}`;
}

// pinta un array de pelis en un contenedor. si esta vacio muestra estado vacio.
function renderizarGrid(peliculas, contenedorId) {
    const contenedor = document.getElementById(contenedorId);
    if (!contenedor) return;

    if (!peliculas || peliculas.length === 0) {
        contenedor.innerHTML = `<div class="estado-vacio"><p class="estado-vacio__desc">Sin resultados</p></div>`;
        return;
    }

    contenedor.innerHTML = peliculas.map(crearTarjetaPelicula).join('');
}

// esqueletos animados mientras llega la respuesta de la API
function mostrarEsqueletos(contenedorId, cantidad = 10) {
    const contenedor = document.getElementById(contenedorId);
    if (!contenedor) return;
    contenedor.innerHTML = Array(cantidad).fill(0).map(() => `
        <div class="pelicula-card">
            <div class="pelicula-card__poster skeleton" style="aspect-ratio:2/3"></div>
            <div style="margin-top:8px">
                <div class="skeleton" style="height:12px;border-radius:4px;margin-bottom:4px"></div>
                <div class="skeleton" style="height:10px;width:60%;border-radius:4px"></div>
            </div>
        </div>
    `).join('');
}

// Mosaico de fondo del hero con posters. Solo si NO hay sesion.
async function cargarHeroBg() {
    try {
        const data = await api.peliculas.cartelera(0, 20);
        const heroBg = document.getElementById('heroBg');
        if (!heroBg) return;

        // si no hay suficientes posters, los repetimos hasta llenar
        const peliculas = data.results.filter(p => p.poster_url);
        if (peliculas.length === 0) return;

        const CELDAS = 80;   // suficiente para cubrir hasta ~1920px
        heroBg.innerHTML = Array.from({ length: CELDAS }, (_, i) => {
            const p = peliculas[i % peliculas.length];
            return `<div class="hero-bg-poster" style="background-image:url('${escapeHTML(p.poster_url)}')"></div>`;
        }).join('');
    } catch (err) {
        // si falla queda el degradado a pelo, no es critico
        console.warn('[home] no se pudo cargar hero bg', err);
    }
}


// busca pelis y sustituye cartelera/estrenos por los resultados
async function buscarPeliculas(query) {
    const secBusqueda = document.getElementById('seccionBusqueda');
    const secCartelera = document.getElementById('seccionCartelera');
    const secEstrenos  = document.getElementById('seccionEstrenos');
    const label = document.getElementById('labelBusqueda');

    secBusqueda.classList.remove('oculto');
    secCartelera.classList.add('oculto');
    secEstrenos.classList.add('oculto');

    label.textContent = `"${query}"`;
    mostrarEsqueletos('gridBusqueda', 12);

    try {
        const data = await api.peliculas.buscar(query);
        renderizarGrid(data.results, 'gridBusqueda');
    } catch (err) {
        console.warn('[home] error al buscar', err);
        mostrarToast('Error al buscar películas', 'error');
    }
}


async function cargarCartelera() {
    mostrarEsqueletos('gridCartelera', 10);
    try {
        const data = await api.peliculas.cartelera(0, 20);
        renderizarGrid(data.results, 'gridCartelera');
    } catch (err) {
        console.warn('[home] error cartelera', err);
        mostrarToast('No se pudo cargar la cartelera', 'error');
    }
}

async function cargarEstrenos() {
    mostrarEsqueletos('gridEstrenos', 10);
    try {
        const data = await api.peliculas.estrenos(0, 10);
        renderizarGrid(data.results, 'gridEstrenos');
    } catch (err) {
        console.warn('[home] error estrenos', err);
        mostrarToast('No se pudieron cargar los estrenos', 'error');
    }
}


document.addEventListener('DOMContentLoaded', async () => {

    renderNav('');
    actualizarBadgesLogros();

    const estaLogueado = auth.estaLogueado();
    const hero = document.getElementById('hero');
    const contenido = document.getElementById('contenidoPrincipal');

    if (estaLogueado) {
        // logueado: oculta hero y muestra el contenido directo
        hero.classList.add('oculto');
        contenido.style.paddingTop = 'calc(var(--navbar-h) + 32px)';
    } else {
        // visitante: hero con mosaico de posters
        cargarHeroBg();
    }

    // si vienen de buscar en el nav -> ejecutamos la busqueda
    const navSearch = sessionStorage.getItem('nav_search');
    if (navSearch) {
        sessionStorage.removeItem('nav_search');

        // si es visitante achicamos el hero para que se vean los resultados
        if (!estaLogueado) {
            hero.classList.add('hero--mini');
        }

        buscarPeliculas(navSearch);
    } else {
        // cargamos cartelera y estrenos en paralelo
        cargarCartelera();
        cargarEstrenos();
    }
});
