// js/home.js — Grid de películas y filtros

// Variables globales que guardan el estado actual de los filtros aplicados
let filtroGenero   = 'todas'; // Género seleccionado ('todas' significa sin filtro de género)
let filtroBusqueda = '';      // Texto escrito en el buscador (vacío = sin filtro de búsqueda)

// Construye y devuelve el HTML de una tarjeta de película
// peli: objeto película | datosUsuario: datos del usuario actual | mostrarGlobal: si mostrar la puntuación global
function construirTarjeta(peli, datosUsuario, mostrarGlobal = false) {
  // Busca si el usuario tiene esta película en su lista de vistas
  const vista      = datosUsuario?.vistas.find(v => v.idPelicula === peli.id);
  const estaVista  = !!vista;                                 // true si está marcada como vista
  const puntuacion = vista?.puntuacion || null;               // puntuación del usuario o null si no ha puntuado
  const enWl       = datosUsuario?.watchlist.includes(peli.id);  // true si está en su watchlist
  const tieneLike  = datosUsuario?.megustas.includes(peli.id);   // true si le ha dado like

  // Devuelve el HTML de la tarjeta con las insignias correspondientes según el estado
  return `
  <div class="tarjeta-peli" data-id="${peli.id}">
    <div class="tarjeta-poster">
      <img class="tarjeta-imagen" src="${peli.imagen}" alt="${peli.titulo}" loading="lazy" />
      <!-- loading="lazy" hace que la imagen solo se cargue cuando está cerca de ser visible -->
      <div class="tarjeta-overlay"><div class="tarjeta-play">▶</div></div>
      <!-- Overlay con icono de play que aparece al pasar el ratón por encima -->
      ${estaVista  ? '<span class="tarjeta-insignia insignia-vista">VISTA</span>' : ''}
      <!-- Insignia verde "VISTA" si el usuario ya la ha visto -->
      ${puntuacion ? `<span class="tarjeta-insignia insignia-puntuacion">${puntuacion}</span>` : ''}
      <!-- Insignia con la puntuación del usuario si ha valorado la película -->
      ${enWl       ? '<span class="tarjeta-insignia insignia-watchlist">🔖</span>' : ''}
      <!-- Insignia de marcador si está en la watchlist -->
      ${tieneLike  ? '<span class="tarjeta-insignia insignia-like">❤️</span>' : ''}
      <!-- Insignia de corazón si el usuario le ha dado like -->
      ${mostrarGlobal && !estaVista ? `<span class="tarjeta-insignia insignia-global">★ ${peli.puntuacion}</span>` : ''}
      <!-- Muestra la puntuación global solo si mostrarGlobal es true Y la película NO está vista -->
    </div>
    <p class="tarjeta-titulo">${peli.titulo}</p>
    <p class="tarjeta-meta">${peli.anio} · ${peli.genero}</p>
  </div>`;
}

// Añade el evento click a todas las tarjetas de un contenedor para abrir su modal
function asignarClicksTarjetas(contenedor) {
  contenedor.querySelectorAll('.tarjeta-peli').forEach(tarjeta => {
    // Al hacer click en una tarjeta, abre el modal con el ID de película guardado en data-id
    tarjeta.onclick = () => abrirModal(parseInt(tarjeta.dataset.id));
  });
}

// Renderiza la cuadrícula principal de películas aplicando los filtros activos
function renderizarGrid() {
  const usuario = AUTENTICACION.obtenerUsuarioActual();
  // Si hay usuario logueado obtiene sus datos para mostrar el estado de cada película
  const datos   = usuario ? AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario) : null;

  // Filtra el catálogo aplicando simultáneamente el filtro de búsqueda y el de género
  const filtradas = PELICULAS.filter(peli => {
    const coincideBusqueda = peli.titulo.toLowerCase().includes(filtroBusqueda.toLowerCase());
    const coincideGenero   = filtroGenero === 'todas' || peli.genero === filtroGenero;
    // Solo incluye películas que cumplan AMBOS filtros a la vez
    return coincideBusqueda && coincideGenero;
  });

  // Actualiza el contador de películas del hero con el número de resultados filtrados
  const contadorEl = document.getElementById('heroCount');
  if (contadorEl) contadorEl.textContent = `${filtradas.length} películas`;

  // Renderiza la cuadrícula principal con las películas filtradas
  const grid = document.getElementById('movieGrid');
  if (grid) {
    if (filtradas.length === 0) {
      // Si no hay resultados, muestra un mensaje de "sin resultados" en lugar de la cuadrícula
      grid.innerHTML = `<div class="vacio" style="grid-column:1/-1">
        <div class="vacio-icono">🎬</div>
        <div class="vacio-titulo">Sin resultados</div>
        <p class="vacio-texto">Prueba con otro término o género</p>
      </div>`;
    } else {
      // Construye el HTML de todas las tarjetas y las inyecta en el grid de una sola vez
      grid.innerHTML = filtradas.map(peli => construirTarjeta(peli, datos)).join('');
      asignarClicksTarjetas(grid);
    }
  }

  // Renderiza la sección de películas mejor valoradas con las 6 primeras del ranking global
  const gridTop = document.getElementById('topGrid');
  if (gridTop) {
    // Ordena una copia del catálogo de mayor a menor puntuación y coge las 6 primeras
    const topPeliculas = [...PELICULAS].sort((a, b) => b.puntuacion - a.puntuacion).slice(0, 6);
    gridTop.innerHTML  = topPeliculas.map(peli => construirTarjeta(peli, datos, true)).join('');
    // true en construirTarjeta para que muestre la puntuación global en estas tarjetas
    asignarClicksTarjetas(gridTop);
  }
}

// Exponer para que ui.js pueda refrescar
// Asigna renderizarGrid a la variable global refrescarGrid para que ui.js pueda llamarla tras una acción
refrescarGrid = renderizarGrid;

// Inicializa los eventos de búsqueda y filtros de género
function inicializarFiltros() {
  const campoBusqueda = document.getElementById('searchInput');
  if (campoBusqueda) {
    // Cada vez que el usuario escribe, actualiza el filtro y vuelve a renderizar el grid
    campoBusqueda.addEventListener('input', e => { filtroBusqueda = e.target.value; renderizarGrid(); });
  }
  // Añade el evento click a cada filtro de género
  document.querySelectorAll('.filtro').forEach(filtro => {
    filtro.addEventListener('click', () => {
      // Quita la clase 'activo' de todos los filtros
      document.querySelectorAll('.filtro').forEach(f => f.classList.remove('activo'));
      // Marca como activo solo el filtro pulsado
      filtro.classList.add('activo');
      // Actualiza el filtro de género con el valor del filtro y re-renderiza
      filtroGenero = filtro.dataset.genre;
      renderizarGrid();
    });
  });
}

// Cuando el DOM está listo, inicializa la página: grid principal, filtros y secciones especiales
document.addEventListener('DOMContentLoaded', () => {
  renderizarGrid();
  inicializarFiltros();
  renderizarCartelera();
});

/* ─ Cartelera y Próximos Estrenos (HU-04) ─ */
// Renderiza las secciones "En cartelera" y "Próximos estrenos" usando los IDs definidos en data.js
function renderizarCartelera() {
  const usuario = AUTENTICACION.obtenerUsuarioActual();
  const datos   = usuario ? AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario) : null;

  const elCartelera = document.getElementById('carteleraGrid');
  const elEstrenos  = document.getElementById('estrenosGrid');

  if (elCartelera && typeof CARTELERA_IDS !== 'undefined') {
    // Obtiene los objetos película a partir de los IDs de cartelera, descartando los que no existan
    const pelisCartelera = CARTELERA_IDS.map(id => PELICULAS.find(m => m.id === id)).filter(Boolean);
    elCartelera.innerHTML = pelisCartelera.map(peli => construirTarjeta(peli, datos, true)).join('');
    // true para mostrar la puntuación global en las tarjetas de cartelera
    asignarClicksTarjetas(elCartelera);
  }

  if (elEstrenos && typeof ESTRENOS_IDS !== 'undefined') {
    // Igual que cartelera pero con los IDs de próximos estrenos
    const pelisEstrenos = ESTRENOS_IDS.map(id => PELICULAS.find(m => m.id === id)).filter(Boolean);
    elEstrenos.innerHTML = pelisEstrenos.map(peli => construirTarjeta(peli, datos, true)).join('');
    asignarClicksTarjetas(elEstrenos);
  }
}