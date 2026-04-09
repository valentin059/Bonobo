// js/ui.js — Modal de película, notificaciones y acciones

/* ─ Notificación ─ */
// Muestra una notificación pequeña y temporal en la esquina de la pantalla
// mensaje: texto a mostrar | tipo: 'ok' (verde), 'err' (rojo), 'inf' (informativo)
function notificacion(mensaje, tipo = 'ok') {
  // Busca el contenedor de notificaciones, o lo crea si no existe todavía
  let contenedor = document.getElementById('toastCnt');
  if (!contenedor) {
    contenedor = document.createElement('div');
    contenedor.id = 'toastCnt'; contenedor.className = 'notif-contenedor';
    document.body.appendChild(contenedor);
  }
  // Inyecta el mensaje en el contenedor
  contenedor.innerHTML = `<div class="notif ${tipo}">${mensaje}</div>`;
  // Espera 10ms y añade la clase 'show' para activar la animación de entrada del CSS
  setTimeout(() => { const n = contenedor.querySelector('.notif'); if(n) n.classList.add('show'); }, 10);
  // Tras 2,6 segundos quita la clase 'show' para que la notificación desaparezca
  setTimeout(() => { const n = contenedor.querySelector('.notif'); if(n) n.classList.remove('show'); }, 2600);
}

/* ─ Modal ─ */
// Guarda el ID de la película cuyo modal está abierto en este momento (null si no hay ninguno)
let idPeliculaActiva = null;

// Abre el modal de detalle de una película dado su ID
function abrirModal(idPelicula) {
  // Busca la película en el catálogo
  const pelicula = PELICULAS.find(mv => mv.id === idPelicula);
  // Si no existe la película, no hace nada
  if (!pelicula) return;
  idPeliculaActiva = idPelicula;

  // Busca el overlay del modal o lo crea si no existe en el DOM
  let overlay = document.getElementById('movieModalBg');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'movieModalBg';
    overlay.className = 'modal-fondo';
    document.body.appendChild(overlay);
  }

  // BUG 1 FIX: Si el overlay existe pero está vacío (declarado en el HTML sin contenido),
  // construir el HTML interior y añadir el listener de cierre.
  if (!document.getElementById('mClose')) {
    // Inyecta toda la estructura HTML interior del modal
    overlay.innerHTML = construirHTMLModal();
    // Cierra el modal si el usuario hace clic en el fondo oscuro (fuera del modal)
    overlay.addEventListener('click', e => { if(e.target === overlay) cerrarModal(); });
  }

  // Hace visible el overlay con flex para centrar el modal
  overlay.style.display = 'flex';
  // Bloquea el scroll del body mientras el modal está abierto
  document.body.style.overflow = 'hidden';

  // Rellena cada elemento del modal con los datos de la película seleccionada
  document.getElementById('mBgImg').src           = pelicula.imagen;
  document.getElementById('mPoster').src           = pelicula.imagen;
  document.getElementById('mTitle').textContent    = pelicula.titulo;
  document.getElementById('mDir').textContent      = `Dir. ${pelicula.director}`;
  document.getElementById('mGenre').textContent    = pelicula.genero;
  document.getElementById('mGlobalRating').innerHTML = `<span class="estrella-dorada">★</span>${pelicula.puntuacion}`;
  document.getElementById('mYear').textContent     = pelicula.anio;
  document.getElementById('mSynopsis').textContent = pelicula.sinopsis;
  document.getElementById('mCast').textContent     = '🎭 ' + pelicula.reparto.join(', ');

  // Conecta el botón de cerrar (✕) con la función cerrarModal
  document.getElementById('mClose').onclick = cerrarModal;

  // Renderiza los botones de acción (vista, watchlist, like, etc.) según el estado del usuario
  renderizarAccionesModal(pelicula);

  // Renderiza las secciones sociales si social.js está cargado (comprueba antes de llamar)
  if (typeof renderizarResenasAmigos   === 'function') renderizarResenasAmigos(idPelicula);
  if (typeof renderizarResenasGenerales === 'function') renderizarResenasGenerales(idPelicula);
}

// Genera y devuelve el HTML completo de la estructura interna del modal como string
// Se llama una sola vez al crear el modal por primera vez
function construirHTMLModal() {
  return `
  <div class="modal">
    <div class="modal-cabecera">
      <img id="mBgImg" class="modal-fondo-imagen" src="" alt="" />
      <!-- Imagen de fondo difuminada en la cabecera del modal -->
      <div class="modal-gradiente"></div>
      <!-- Gradiente oscuro sobre la imagen de fondo para que el texto sea legible -->
      <div class="modal-cabecera-contenido">
        <img id="mPoster" class="modal-poster" src="" alt="" />
        <!-- Póster pequeño de la película -->
        <div class="modal-info">
          <h2 id="mTitle" class="modal-titulo"></h2>
          <p  id="mDir"   class="modal-director"></p>
          <span id="mGenre" class="modal-pastilla"></span>
          <!-- Pastilla con el género de la película -->
        </div>
      </div>
      <button class="modal-cerrar" id="mClose">✕</button>
      <!-- Botón para cerrar el modal -->
    </div>
    <div class="modal-cuerpo">
      <div id="mActions"   class="acciones"></div>
      <!-- Zona de botones de acción: vista, watchlist, like, favorita, añadir a lista -->
      <div id="mRating"    style="display:none">
        <!-- Sección de puntuación — solo visible si la película está marcada como vista -->
        <div class="puntuacion-tarjeta">
          <div class="puntuacion-superior">
            <span class="puntuacion-etiqueta">Tu puntuación</span>
            <span id="mRatingVal" class="puntuacion-valor">—<sub>/10</sub></span>
            <!-- Muestra el valor numérico de la puntuación actual -->
          </div>
          <div class="estrellas" id="mStars"></div>
          <!-- Contenedor donde se renderizan los 10 botones de estrella -->
        </div>
      </div>
      <div id="mDiaryArea"></div>
      <!-- Zona dinámica: muestra el botón de diario, el formulario de entrada o el panel de listas -->
      <div class="modal-meta">
        <div class="meta-tarjeta"><div class="meta-etiqueta">Rating global</div><div id="mGlobalRating" class="meta-valor">—</div></div>
        <div class="meta-tarjeta"><div class="meta-etiqueta">Año</div><div id="mYear" class="meta-valor">—</div></div>
      </div>
      <p id="mSynopsis" class="modal-sinopsis"></p>
      <p id="mCast"     class="modal-reparto"></p>
      <div id="mFriendReviews"  style="display:none"></div>
      <!-- Reseñas de usuarios que el usuario sigue — relleno por social.js -->
      <div id="mGeneralReviews" style="display:none"></div>
      <!-- Reseñas de todos los usuarios — relleno por social.js -->
    </div>
  </div>`;
}

// Cierra el modal ocultando el overlay y restaurando el scroll de la página
function cerrarModal() {
  const overlay = document.getElementById('movieModalBg');
  if (overlay) overlay.style.display = 'none';
  // Restaura el scroll del body que se bloqueó al abrir el modal
  document.body.style.overflow = '';
  idPeliculaActiva = null;
}

/* ─ Renderizar acciones del modal ─ */
// Genera los botones de acción del modal según el estado actual del usuario y la película
function renderizarAccionesModal(pelicula) {
  const usuario    = AUTENTICACION.obtenerUsuarioActual();
  const accionesEl = document.getElementById('mActions');
  const puntuacionEl = document.getElementById('mRating');
  const diarioEl   = document.getElementById('mDiaryArea');

  if (!usuario) {
    // Si no hay sesión, muestra un mensaje invitando al usuario a iniciar sesión
    const raiz = rutaRaiz();
    accionesEl.innerHTML = `<div class="sin-sesion">
      <a href="${raiz}pages/login.html">Inicia sesión</a> o 
      <a href="${raiz}pages/registro.html">regístrate</a> para registrar películas
    </div>`;
    puntuacionEl.style.display = 'none';
    diarioEl.innerHTML = '';
    return;
  }

  // Carga los datos del usuario y comprueba el estado de la película para él
  const datos       = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  const entradaVista = datos.vistas.find(v => v.idPelicula === pelicula.id);
  const estaVista   = !!entradaVista;                              // true si está marcada como vista
  const enWatchlist = datos.watchlist.includes(pelicula.id);       // true si está en watchlist
  const tieneLike   = datos.megustas.includes(pelicula.id);        // true si tiene like
  const esFavorita  = datos.favoritas.includes(pelicula.id);       // true si está en favoritas
  const puntuacion  = entradaVista?.puntuacion || null;            // puntuación del usuario o null

  // Renderiza los 5 botones de acción con su estado visual activo/inactivo
  // Las clases 'g', 'b', 'r', 'y' cambian el color del botón cuando la acción está activa
  accionesEl.innerHTML = `
    <button class="accion-btn ${estaVista?'g':''}"    id="aBtnVista">
      ${estaVista   ? '✓ Vista'      : '🎬 Marcar Vista'}
    </button>
    <button class="accion-btn ${enWatchlist?'b':''}" id="aBtnWl">
      ${enWatchlist ? '🔖 En Lista'  : '+ Watchlist'}
    </button>
    <button class="accion-btn ${tieneLike?'r':''}"   id="aBtnLike">
      ${tieneLike   ? '❤️ Me gusta' : '♡ Me gusta'}
    </button>
    <button class="accion-btn ${esFavorita?'y':''}"  id="aBtnFav">
      ${esFavorita  ? '⭐ Favorita'  : '☆ Favorita'}
    </button>
    <button class="accion-btn" id="aBtnLista">
      📋 Añadir a lista
    </button>`;

  // Conecta cada botón con su función correspondiente
  document.getElementById('aBtnVista').onclick = () => alternarVista(pelicula.id);
  document.getElementById('aBtnWl').onclick    = () => alternarWatchlist(pelicula.id);
  document.getElementById('aBtnLike').onclick  = () => alternarMeGusta(pelicula.id);
  document.getElementById('aBtnFav').onclick   = () => alternarFavorita(pelicula.id);
  document.getElementById('aBtnLista').onclick = () => mostrarPanelAnadir(pelicula.id);

  // Puntuación (solo si está vista)
  if (estaVista) {
    // Muestra la sección de puntuación y el botón de añadir al diario
    puntuacionEl.style.display = 'block';
    renderizarEstrellas(puntuacion);
    diarioEl.innerHTML = `<button class="diario-btn-anadir" id="aDiaryBtn">📓 Añadir entrada al diario</button>`;
    document.getElementById('aDiaryBtn').onclick = () => mostrarFormularioDiario(pelicula.id);
  } else {
    // Si no está vista, oculta la puntuación y el diario
    puntuacionEl.style.display = 'none';
    diarioEl.innerHTML = '';
  }
}

/* ─ Estrellas ─ */
// Renderiza los 10 botones de puntuación (del 1 al 10) resaltando los seleccionados
function renderizarEstrellas(actual) {
  const el    = document.getElementById('mStars');
  const valor = document.getElementById('mRatingVal');
  if (!el) return;
  // Actualiza el texto numérico de la puntuación (o "—" si no hay puntuación)
  valor.innerHTML = actual ? `${actual}<sub>/10</sub>` : `—<sub>/10</sub>`;
  el.innerHTML    = '';
  // Crea un botón por cada número del 1 al 10
  for (let n = 1; n <= 10; n++) {
    const boton = document.createElement('button');
    // La clase 'lit' ilumina los botones hasta el valor seleccionado
    boton.className   = `estrella-btn ${actual && n <= actual ? 'lit' : ''}`;
    boton.textContent = n;
    // Al pulsar un botón, guarda esa puntuación para la película activa
    boton.onclick = () => establecerPuntuacion(idPeliculaActiva, n);
    el.appendChild(boton);
  }
}

/* ─ Formulario de diario ─ */
// Reemplaza el botón del diario por un formulario para escribir una nueva entrada
function mostrarFormularioDiario(idPelicula) {
  // Usa la fecha de hoy como valor por defecto del campo de fecha
  const hoy = new Date().toISOString().split('T')[0];
  document.getElementById('mDiaryArea').innerHTML = `
    <div class="diario-formulario">
      <span class="diario-formulario-titulo">Nueva entrada de diario</span>
      <input  type="date" id="dFecha"  class="campo-entrada" value="${hoy}" />
      <textarea id="dTexto" class="campo-entrada campo-textarea" rows="3"
        placeholder="¿Qué te pareció? Escribe tu reseña (opcional)…"></textarea>
      <div class="formulario-botones">
        <button class="btn-guardar" id="dGuardar">Guardar</button>
        <button class="btn-cancelar" id="dCancelar">Cancelar</button>
      </div>
    </div>`;
  document.getElementById('dGuardar').onclick  = () => guardarDiario(idPelicula);
  // Al cancelar, vuelve a mostrar los botones de acción normales del modal
  document.getElementById('dCancelar').onclick = () => {
    const pelicula = PELICULAS.find(mv => mv.id === idPelicula);
    if (pelicula) renderizarAccionesModal(pelicula);
  };
}

/* ─ Acciones ─ */
// Alterna el estado "vista/no vista" de una película para el usuario actual
function alternarVista(idPelicula) {
  const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return;
  let datos     = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  const estaVista = datos.vistas.some(v => v.idPelicula === idPelicula);

  if (estaVista) {
    // Comprueba si hay datos asociados (diario, puntuación o like) antes de desmarcar
    // Si los hay, no permite desmarcarla para evitar pérdida de datos
    const tieneDatos = datos.diario.some(e => e.idPelicula === idPelicula)
                    || datos.vistas.find(v => v.idPelicula === idPelicula)?.puntuacion
                    || datos.megustas.includes(idPelicula);
    if (tieneDatos) { notificacion('No puedes desmarcar: tiene datos asociados', 'err'); return; }
    // Si no tiene datos asociados, la elimina de vistas y de favoritas
    datos.vistas    = datos.vistas.filter(v => v.idPelicula !== idPelicula);
    datos.favoritas = datos.favoritas.filter(id => id !== idPelicula);
    notificacion('Película desmarcada', 'inf');
  } else {
    // Añade la película a vistas y la elimina de watchlist (ya no hay que verla)
    datos.vistas.push({ idPelicula, puntuacion: null });
    datos.watchlist = datos.watchlist.filter(id => id !== idPelicula);
    notificacion('✓ Marcada como vista');
  }

  // Comprueba si se ha desbloqueado algún logro, guarda y actualiza la UI
  datos = verificarLogros(usuario.nombreUsuario, datos);
  AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
  renderizarAccionesModal(PELICULAS.find(m => m.id === idPelicula));
  // refrescarGrid actualiza la cuadrícula de películas si la función está disponible en la página actual
  refrescarGrid?.(); inicializarSidebar();
}

// Guarda la puntuación del usuario para una película y actualiza las estrellas visualmente
function establecerPuntuacion(idPelicula, puntuacion) {
  const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return;
  let datos     = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  const idx     = datos.vistas.findIndex(v => v.idPelicula === idPelicula);
  // Si ya existe la entrada en vistas, actualiza la puntuación; si no, la crea
  if (idx >= 0) { datos.vistas[idx].puntuacion = puntuacion; }
  else { datos.vistas.push({ idPelicula, puntuacion }); datos.watchlist = datos.watchlist.filter(id => id !== idPelicula); }
  AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
  renderizarEstrellas(puntuacion);
  notificacion(`Puntuación: ${puntuacion}/10`);
  refrescarGrid?.();
}

// Alterna si una película está en la watchlist del usuario
function alternarWatchlist(idPelicula) {
  const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return;
  let datos     = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  if (datos.watchlist.includes(idPelicula)) {
    datos.watchlist = datos.watchlist.filter(id => id !== idPelicula);
    notificacion('Eliminada de watchlist', 'inf');
  } else {
    datos.watchlist.push(idPelicula);
    notificacion('🔖 Añadida a watchlist');
  }
  datos = verificarLogros(usuario.nombreUsuario, datos);
  AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
  renderizarAccionesModal(PELICULAS.find(m => m.id === idPelicula));
  refrescarGrid?.(); inicializarSidebar();
}

// Alterna el "me gusta" de una película — solo funciona si la película está marcada como vista
function alternarMeGusta(idPelicula) {
  const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return;
  let datos     = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  // Bloquea el like si la película no está marcada como vista
  if (!datos.vistas.some(v => v.idPelicula === idPelicula)) { notificacion('Márcala como vista primero', 'err'); return; }
  if (datos.megustas.includes(idPelicula)) { datos.megustas = datos.megustas.filter(id => id !== idPelicula); }
  else { datos.megustas.push(idPelicula); notificacion('❤️ ¡Te gusta!'); }
  AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
  renderizarAccionesModal(PELICULAS.find(m => m.id === idPelicula));
  refrescarGrid?.();
}

// Alterna si una película está en favoritas — máximo 4 películas favoritas permitidas
function alternarFavorita(idPelicula) {
  const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return;
  let datos     = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  // Bloquea añadir si ya hay 4 favoritas y la película no está en ellas
  if (!datos.favoritas.includes(idPelicula) && datos.favoritas.length >= 4) { notificacion('Máximo 4 favoritas', 'err'); return; }
  if (datos.favoritas.includes(idPelicula)) { datos.favoritas = datos.favoritas.filter(id => id !== idPelicula); }
  else { datos.favoritas.push(idPelicula); notificacion('⭐ Añadida a favoritas'); }
  datos = verificarLogros(usuario.nombreUsuario, datos);
  AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
  renderizarAccionesModal(PELICULAS.find(m => m.id === idPelicula));
}

// Guarda una nueva entrada en el diario del usuario para una película
function guardarDiario(idPelicula) {
  const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return;
  const texto   = document.getElementById('dTexto')?.value.trim();
  const fecha   = document.getElementById('dFecha')?.value;

  // BUG 2 FIX: La reseña es OPCIONAL según el documento — solo la fecha es obligatoria.
  // Se eliminó la validación que bloqueaba guardar sin texto de reseña.
  if (!fecha) { notificacion('Selecciona una fecha', 'err'); return; }

  let datos = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
  // Si la película no está marcada como vista, la marca automáticamente al guardar el diario
  if (!datos.vistas.some(v => v.idPelicula === idPelicula)) {
    datos.vistas.push({ idPelicula, puntuacion: null });
    datos.watchlist = datos.watchlist.filter(id => id !== idPelicula);
  }
  // Añade la nueva entrada al diario con ID único, fecha y reseña (vacía si no escribió nada)
  datos.diario.push({ id: Date.now(), idPelicula, fecha, resena: texto || '' });
  datos = verificarLogros(usuario.nombreUsuario, datos);
  AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
  notificacion('📓 Guardado en el diario');
  renderizarAccionesModal(PELICULAS.find(m => m.id === idPelicula));
  refrescarGrid?.(); inicializarSidebar();
}

/* ─ Panel "Añadir a lista" desde modal ─ */
// Muestra un panel dentro del modal para añadir o quitar la película de las listas del usuario
function mostrarPanelAnadir(idPelicula) {
  const usuario = AUTENTICACION.obtenerUsuarioActual();
  if (!usuario) { notificacion('Inicia sesión para usar listas', 'err'); return; }

  const diarioEl = document.getElementById('mDiaryArea');
  // Obtiene las listas del usuario (comprueba que LISTAS esté disponible antes de usarlo)
  const listas   = typeof LISTAS !== 'undefined' ? LISTAS.obtenerTodas(usuario.nombreUsuario) : [];

  if (!listas.length) {
    // Si el usuario no tiene listas creadas, muestra un mensaje y un enlace para crear la primera
    diarioEl.innerHTML = `
      <div class="diario-formulario">
        <span class="diario-formulario-titulo">📋 Añadir a lista</span>
        <p style="color:var(--apagado);font-size:12px;margin-bottom:12px">No tienes listas creadas aún.</p>
        <a href="${rutaRaiz()}pages/listas.html" class="btn-guardar" style="display:block;text-align:center;text-decoration:none">Crear mi primera lista →</a>
        <button class="btn-cancelar" id="listaCancelar" style="margin-top:8px">Cancelar</button>
      </div>`;
    document.getElementById('listaCancelar').onclick = () => {
      const pelicula = PELICULAS.find(mv => mv.id === idPelicula);
      if (pelicula) renderizarAccionesModal(pelicula);
    };
    return;
  }

  // Genera un botón por cada lista del usuario, marcando visualmente las que ya contienen la película
  const elementosLista = listas.map(lista => {
    const yaEsta = lista.peliculas.includes(idPelicula);
    return `<button class="lista-btn-seleccionar ${yaEsta ? 'en-lista' : ''}"
      data-listid="${lista.id}" data-esta="${yaEsta}">
      ${yaEsta ? '✓' : '+'} ${lista.nombre}
      <span style="font-size:9px;color:var(--apagado);margin-left:4px">${lista.peliculas.length} pelis</span>
    </button>`;
  }).join('');

  diarioEl.innerHTML = `
    <div class="diario-formulario">
      <span class="diario-formulario-titulo">📋 Añadir a lista</span>
      <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:12px">${elementosLista}</div>
      <div style="display:flex;gap:8px">
        <a href="${rutaRaiz()}pages/listas.html" style="font-size:11px;color:var(--acento);text-decoration:underline">+ Crear nueva lista</a>
        <button class="btn-cancelar" id="listaCancelar">Cerrar</button>
      </div>
    </div>`;

  document.getElementById('listaCancelar').onclick = () => {
    const pelicula = PELICULAS.find(mv => mv.id === idPelicula);
    if (pelicula) renderizarAccionesModal(pelicula);
  };

  // Añade el evento click a cada botón de lista para añadir o quitar la película
  diarioEl.querySelectorAll('.lista-btn-seleccionar').forEach(boton => {
    boton.onclick = () => {
      const idLista = parseInt(boton.dataset.listid);
      const yaEsta  = boton.dataset.esta === 'true';
      if (yaEsta) {
        LISTAS.quitarPelicula(usuario.nombreUsuario, idLista, idPelicula);
        notificacion('Película eliminada de la lista', 'inf');
      } else {
        LISTAS.agregarPelicula(usuario.nombreUsuario, idLista, idPelicula);
        notificacion('✓ Añadida a la lista');
      }
      // Re-renderiza el panel para reflejar el cambio inmediatamente
      mostrarPanelAnadir(idPelicula);
    };
  });
}

/* ─ Permitir que cada página exponga su propia función de refresco ─ */
// Variable global que cada página puede sobreescribir con su propia función para actualizar la cuadrícula
// Se llama con refrescarGrid?.() para que no falle si la página no la ha definido
let refrescarGrid = null;