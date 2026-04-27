// js/home.js — Lógica de la página principal (index.html)
// Controla el hero, la carga de cartelera y estrenos, y la búsqueda de películas.

// ── UTILIDADES ────────────────────────────────────────────────────────────────

// Muestra una notificación toast temporal en la parte inferior de la pantalla.
// tipo: 'ok' (verde) o 'error' (rojo). duración en milisegundos.
function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}

// Genera el HTML de una tarjeta de película para el grid.
// pelicula: objeto con { tmdb_id, titulo, poster_url, anio_estreno, puntuacion? }
function crearTarjetaPelicula(pelicula) {
    const imgHTML = pelicula.poster_url
        ? `<img class="pelicula-card__img" src="${pelicula.poster_url}" alt="${pelicula.titulo}" loading="lazy">`
        : `<div class="pelicula-card__no-img">SIN IMAGEN</div>`;

    // Puntuación de TMDB (solo aparece si existe)
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
                <div class="pelicula-card__titulo">${pelicula.titulo || 'Sin título'}</div>
                <div class="pelicula-card__anio">${pelicula.anio_estreno || ''}</div>
            </div>
        </div>
    `;
}

// Redirige a la página de detalle de una película.
function irAPelicula(tmdbId) {
    window.location.href = `pages/pelicula.html?id=${tmdbId}`;
}

// Renderiza un array de películas en un contenedor.
// Si el array está vacío, muestra un estado vacío.
function renderizarGrid(peliculas, contenedorId) {
    const contenedor = document.getElementById(contenedorId);
    if (!contenedor) return;

    if (!peliculas || peliculas.length === 0) {
        contenedor.innerHTML = `<div class="estado-vacio"><p class="estado-vacio__desc">Sin resultados</p></div>`;
        return;
    }

    contenedor.innerHTML = peliculas.map(crearTarjetaPelicula).join('');
}

// Muestra esqueletos de carga (placeholders animados) mientras llega la API.
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

// ── HERO ──────────────────────────────────────────────────────────────────────

// Rellena el mosaico de fondo del hero con pósters de cartelera.
// Solo se llama si el usuario NO está logueado.
async function cargarHeroBg() {
    try {
        const data = await api.peliculas.cartelera(0, 20);
        const heroBg = document.getElementById('heroBg');
        if (!heroBg) return;

        // Usamos los pósters disponibles para rellenar la cuadrícula de fondo.
        // Si no hay suficientes para cubrir el hero, los repetimos en bucle.
        const peliculas = data.results.filter(p => p.poster_url);
        if (peliculas.length === 0) return;

        const CELDAS = 80;   // suficiente para cualquier pantalla (hasta ~1920px de ancho)
        heroBg.innerHTML = Array.from({ length: CELDAS }, (_, i) => {
            const p = peliculas[i % peliculas.length];
            return `<div class="hero-bg-poster" style="background-image:url('${p.poster_url}')"></div>`;
        }).join('');
    } catch {
        // Si falla, el hero simplemente muestra el degradado sin fondo
    }
}

// ── BÚSQUEDA ──────────────────────────────────────────────────────────────────

// Busca películas en TMDB y muestra los resultados sustituyendo la cartelera/estrenos.
async function buscarPeliculas(query) {
    const secBusqueda = document.getElementById('seccionBusqueda');
    const secCartelera = document.getElementById('seccionCartelera');
    const secEstrenos  = document.getElementById('seccionEstrenos');
    const label = document.getElementById('labelBusqueda');

    // Mostramos búsqueda, ocultamos las otras secciones
    secBusqueda.classList.remove('oculto');
    secCartelera.classList.add('oculto');
    secEstrenos.classList.add('oculto');

    label.textContent = `"${query}"`;
    mostrarEsqueletos('gridBusqueda', 12);

    try {
        const data = await api.peliculas.buscar(query);
        renderizarGrid(data.results, 'gridBusqueda');
    } catch (err) {
        mostrarToast('Error al buscar películas', 'error');
    }
}

// ── CARTELERA Y ESTRENOS ──────────────────────────────────────────────────────

async function cargarCartelera() {
    mostrarEsqueletos('gridCartelera', 10);
    try {
        const data = await api.peliculas.cartelera(0, 20);
        renderizarGrid(data.results, 'gridCartelera');
    } catch {
        mostrarToast('No se pudo cargar la cartelera', 'error');
    }
}

async function cargarEstrenos() {
    mostrarEsqueletos('gridEstrenos', 10);
    try {
        const data = await api.peliculas.estrenos(0, 10);
        renderizarGrid(data.results, 'gridEstrenos');
    } catch {
        mostrarToast('No se pudieron cargar los estrenos', 'error');
    }
}

// ── INIT ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {

    // Renderizamos el navbar (desde la raíz, sin prefijo de ruta)
    renderNav('');
    actualizarBadgesLogros();

    const estaLogueado = auth.estaLogueado();
    const hero = document.getElementById('hero');
    const contenido = document.getElementById('contenidoPrincipal');

    if (estaLogueado) {
        // Usuario logueado: ocultamos el hero y mostramos el contenido directamente
        hero.classList.add('oculto');
        contenido.style.paddingTop = 'calc(var(--navbar-h) + 32px)';
    } else {
        // Visitante: mostramos el hero con mosaico de pósters
        // El contenido de cartelera aparece debajo del hero para atraer al usuario
        cargarHeroBg();
    }

    // Comprobamos si viene una búsqueda desde el nav (sessionStorage)
    const navSearch = sessionStorage.getItem('nav_search');
    if (navSearch) {
        sessionStorage.removeItem('nav_search');   // limpiamos para que no persista

        // Si el usuario no está logueado, colapsamos el hero a una tira mínima
        // para que los resultados de búsqueda sean lo primero que se vea
        if (!estaLogueado) {
            hero.classList.add('hero--mini');
        }

        buscarPeliculas(navSearch);
    } else {
        // Cargamos cartelera y estrenos en paralelo para ser más rápidos
        cargarCartelera();
        cargarEstrenos();
    }
});
