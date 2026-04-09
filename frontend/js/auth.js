// js/auth.js — Sistema de autenticación con localStorage

// Objeto principal que agrupa todas las funciones relacionadas con usuarios y sesión
const AUTENTICACION = {

  /* ─ Usuarios ─ */
  // Obtiene la lista completa de usuarios guardada en localStorage. Si no existe, devuelve un array vacío
  obtenerUsuarios()          { return JSON.parse(localStorage.getItem('bnb_users') || '[]'); },
  // Guarda la lista completa de usuarios en localStorage convirtiéndola a texto JSON
  guardarUsuarios(u)         { localStorage.setItem('bnb_users', JSON.stringify(u)); },

  /* ─ Sesión ─ */
  // Devuelve el nombre de usuario de la sesión activa (o null si no hay sesión)
  obtenerSesion()            { return localStorage.getItem('bnb_session'); },
  // Guarda el nombre de usuario en localStorage para mantener la sesión activa
  establecerSesion(u)        { localStorage.setItem('bnb_session', u); },
  // Elimina la sesión activa del localStorage (se usa al cerrar sesión)
  limpiarSesion()            { localStorage.removeItem('bnb_session'); },
  // Devuelve true si hay sesión activa, false si no. El !! convierte el valor a booleano
  estaConectado()            { return !!this.obtenerSesion(); },

  /* ─ Usuario actual ─ */
  obtenerUsuarioActual() {
    // Obtiene el nombreUsuario de la sesión activa
    const s = this.obtenerSesion();
    // Si no hay sesión, devuelve null
    if (!s) return null;
    // Busca y devuelve el objeto completo del usuario en la lista, o null si no lo encuentra
    return this.obtenerUsuarios().find(u => u.nombreUsuario === s) || null;
  },

  /* ─ Datos personales ─ */
  obtenerDatosUsuario(nombreUsuario) {
    // Objeto con la estructura por defecto de datos de un usuario nuevo (todo vacío)
    const porDefecto = {
      vistas:     [],  // [{ idPelicula, puntuacion }]
      watchlist:  [],  // [idPelicula]
      megustas:   [],  // [idPelicula] — me gusta en película
      favoritas:  [],  // [idPelicula] max 4
      diario:     [],  // [{ id, idPelicula, fecha, resena, likes:[nombreUsuario], comentarios:[{id,autor,texto,fecha}] }]
      xp:         0,
      nivel:      1,
      logros:     [],  // [{ ...CATALOGO_LOGROS, fecha, reclamado }]
      seguidos:   [],  // [nombreUsuario] — a quién sigo
      avatar:     null,// data URL o null
    };
    // Intenta cargar los datos del usuario desde localStorage. Si no existen, usa la estructura por defecto
    return JSON.parse(localStorage.getItem(`bnb_data_${nombreUsuario}`) || JSON.stringify(porDefecto));
  },
  // Guarda los datos personales de un usuario específico en localStorage
  guardarDatosUsuario(nombreUsuario, datos) {
    localStorage.setItem(`bnb_data_${nombreUsuario}`, JSON.stringify(datos));
  },

  /* ─ Actualizar perfil (bio, avatar) ─ */
  actualizarPerfil(nombreUsuario, { bio, avatar }) {
    const usuarios = this.obtenerUsuarios();
    // Busca la posición del usuario en el array
    const idx      = usuarios.findIndex(u => u.nombreUsuario === nombreUsuario);
    // Si no encuentra el usuario, sale sin hacer nada
    if (idx < 0) return;
    // Solo actualiza bio y avatar si se han pasado como parámetros (undefined significa "no cambiar")
    if (bio    !== undefined) usuarios[idx].bio    = bio;
    if (avatar !== undefined) usuarios[idx].avatar = avatar;
    // Guarda la lista de usuarios actualizada
    this.guardarUsuarios(usuarios);
    // También actualiza el avatar en los datos personales del usuario para mantener consistencia
    const datos = this.obtenerDatosUsuario(nombreUsuario);
    if (avatar !== undefined) datos.avatar = avatar;
    this.guardarDatosUsuario(nombreUsuario, datos);
  },

  /* ─ Registro ─ */
  registrar(correo, nombreUsuario, contrasena) {
    const usuarios = this.obtenerUsuarios();
    // Validaciones en orden: campos vacíos, contraseña corta, email inválido, email duplicado, nombreUsuario duplicado
    if (!correo || !nombreUsuario || !contrasena)                return { ok:false, err:'Rellena todos los campos.' };
    if (contrasena.length < 8)                                   return { ok:false, err:'La contraseña debe tener al menos 8 caracteres.' };
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo))             return { ok:false, err:'El formato del email no es válido.' };
    if (usuarios.find(u => u.correo === correo))                 return { ok:false, err:'El email ya está registrado.' };
    if (usuarios.find(u => u.nombreUsuario === nombreUsuario))   return { ok:false, err:'El username ya está en uso.' };
    // Si pasa todas las validaciones, añade el nuevo usuario al array con su fecha de registro
    usuarios.push({ id:Date.now(), correo, nombreUsuario, contrasena, bio:'', avatar:null, fecha:new Date().toISOString() });
    this.guardarUsuarios(usuarios);
    return { ok:true };
  },

  /* ─ Login ─ */
  iniciarSesion(correo, contrasena) {
    // Busca un usuario que coincida con el correo introducido
    const usuario = this.obtenerUsuarios().find(u => u.correo === correo);
    // Si no existe el usuario o la contraseña no coincide, devuelve error
    if (!usuario || usuario.contrasena !== contrasena) return { ok:false, err:'Credenciales incorrectas.' };
    // Si las credenciales son correctas, guarda la sesión y devuelve el usuario
    this.establecerSesion(usuario.nombreUsuario);
    return { ok:true, usuario };
  },

  /* ─ Logout ─ */
  cerrarSesion() {
    // Elimina la sesión y redirige al usuario a la página principal
    this.limpiarSesion();
    window.location.href = rutaRaiz() + 'index.html';
  }
};

/* ─ Ruta raíz ─ */
// Detecta si la página actual está dentro de /pages/ para construir rutas relativas correctas
// Si estamos en /pages/ devuelve '../', si estamos en la raíz devuelve ''
function rutaRaiz() {
  return window.location.pathname.includes('/pages/') ? '../' : '';
}

/* ─ Inicializar sidebar en todas las páginas ─ */
// Se ejecuta en cada página para mostrar el sidebar correctamente según si hay sesión o no
function inicializarSidebar() {
  // Obtiene el usuario actual (null si no hay sesión)
  const usuario    = AUTENTICACION.obtenerUsuarioActual();
  const raiz       = rutaRaiz();

  // Corrige los hrefs de los botones de login y registro según la ubicación actual
  const enlaceLogin    = document.querySelector('.btn-iniciar-sesion');
  const enlaceRegistro = document.querySelector('.btn-registro');
  if (enlaceLogin)    enlaceLogin.href    = raiz + 'pages/login.html';
  if (enlaceRegistro) enlaceRegistro.href = raiz + 'pages/registro.html';

  // Corrige los hrefs de los links del menú de navegación según la ubicación actual
  const mapaNav = { navPerfil:'perfil', navDiario:'diario', navWatchlist:'watchlist', navLogros:'logros', navBuscar:'buscar-usuarios' };
  Object.entries(mapaNav).forEach(([id, pagina]) => {
    const el = document.getElementById(id);
    if (el) el.href = raiz + 'pages/' + pagina + '.html';
  });

  if (usuario) {
    // ── USUARIO LOGUEADO: muestra toda la info personalizada ──
    const datos   = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    // Calcula el nivel dividiendo el XP total entre 100 (mínimo nivel 1)
    const nivel   = Math.max(1, Math.floor(datos.xp / 100));
    // Calcula el XP dentro del nivel actual (el resto de dividir entre 100)
    const xpNivel = datos.xp % 100;

    // Oculta los botones de login/registro y muestra la sección del usuario
    document.getElementById('sAuth')?.style.setProperty('display','none');
    const seccionUsuario = document.getElementById('sUser');
    if (seccionUsuario) { seccionUsuario.style.display = 'flex'; }

    // Muestra el avatar del usuario en el sidebar
    const avatarEl = document.querySelector('#sUser .sb-avatar');
    if (avatarEl) {
      const av = usuario.avatar || datos.avatar;
      // Si tiene avatar guardado, lo muestra como imagen de fondo
      if (av) { avatarEl.style.backgroundImage = `url(${av})`; avatarEl.style.backgroundSize = 'cover'; avatarEl.textContent = ''; }
      // Si no tiene avatar, muestra la primera letra del nombreUsuario en mayúscula
      else    { avatarEl.textContent = usuario.nombreUsuario[0].toUpperCase(); }
    }

    // Muestra el nombre del usuario en el sidebar
    const nombreEl = document.getElementById('sUsername');
    if (nombreEl) nombreEl.textContent = usuario.nombreUsuario;

    // Actualiza la barra de XP con el nivel, puntos y progreso visual
    const barraXp = document.getElementById('sXp');
    if (barraXp) {
      barraXp.style.display = 'block';
      document.getElementById('sLevel').textContent  = `NIVEL ${nivel}`;
      document.getElementById('sXpNum').textContent  = `${datos.xp} XP`;
      // Ajusta el ancho de la barra de progreso en porcentaje (0-100%)
      document.getElementById('sXpFill').style.width = `${xpNivel}%`;
      document.getElementById('sXpNext').textContent = `${xpNivel}/100 → nivel ${nivel+1}`;
    }

    // Actualiza los 4 contadores de estadísticas del sidebar
    const statsEl = document.getElementById('sStats');
    if (statsEl) {
      statsEl.style.display = 'grid';
      document.getElementById('stVistas').textContent    = datos.vistas.length;
      document.getElementById('stResenas').textContent   = datos.diario.length;
      document.getElementById('stWatchlist').textContent = datos.watchlist.length;
      document.getElementById('stLogros').textContent    = datos.logros.length;
    }

    // Muestra el badge rojo con el número de logros sin reclamar (oculta si no hay ninguno)
    const sinReclamar = datos.logros.filter(l => !l.reclamado).length;
    const badge       = document.getElementById('logrosBadge');
    if (badge) { badge.style.display = sinReclamar ? 'inline' : 'none'; badge.textContent = sinReclamar; }

    // Conecta el botón de cerrar sesión con la función cerrarSesion
    document.getElementById('btnLogout')?.addEventListener('click', () => AUTENTICACION.cerrarSesion());

  } else {
    // ── USUARIO NO LOGUEADO: muestra solo los botones de login/registro ──
    document.getElementById('sAuth')?.style.setProperty('display','flex');
    document.getElementById('sUser')?.style.setProperty('display','none');
    document.getElementById('sXp')?.style.setProperty('display','none');
    document.getElementById('sStats')?.style.setProperty('display','none');
  }
}

/* ─ Verificar logros ─ */
// Comprueba si el usuario ha cumplido las condiciones para desbloquear nuevos logros
function verificarLogros(nombreUsuario, datos) {
  // Recoge los contadores necesarios para evaluar cada condición de logro
  const numVistas    = datos.vistas.length;
  const numResenas   = datos.diario.length;
  const numFavs      = datos.favoritas.length;
  const numWatchlist = datos.watchlist.length;
  const numSeguidos  = (datos.seguidos || []).length;
  // Array con los IDs de los logros que el usuario ya tiene desbloqueados
  const yaDesbloqueados = datos.logros.map(l => l.id);

  // Cuenta cuántos usuarios siguen a este usuario (sus seguidores)
  const todosUsuarios = AUTENTICACION.obtenerUsuarios();
  const numSeguidores = todosUsuarios.filter(u => {
    if (u.nombreUsuario === nombreUsuario) return false;
    const datosU = AUTENTICACION.obtenerDatosUsuario(u.nombreUsuario);
    return (datosU.seguidos || []).includes(nombreUsuario);
  }).length;

  // Calcula cuántas películas únicas ha visto el usuario en el mes actual
  const ahora     = new Date();
  // Construye el prefijo del mes actual en formato "YYYY-MM" para comparar fechas
  const mesActual = `${ahora.getFullYear()}-${String(ahora.getMonth()+1).padStart(2,'0')}`;
  const pelisEsteMes = datos.vistas.filter(v => {
    // buscamos entradas de diario de este mes para esta peli
    const entradas = datos.diario.filter(d => d.idPelicula === v.idPelicula && (d.fecha || '').startsWith(mesActual));
    // o si fue marcada como vista este mes (usamos una heurística: si hay entrada de diario este mes)
    return entradas.length > 0;
  }).length;
  // Cuenta películas únicas vistas este mes usando un Set para eliminar duplicados
  const pelisUniqMes = new Set(
    datos.diario.filter(e => (e.fecha || '').startsWith(mesActual)).map(e => e.idPelicula)
  ).size;

  // Calcula cuántos géneros diferentes ha visto el usuario
  const generos = new Set(
    datos.vistas.map(v => PELICULAS.find(m => m.id === v.idPelicula)?.genero).filter(Boolean)
  );

  // Cuenta cuántos likes ha dado este usuario a reseñas de otros usuarios
  const totalLikesDados = todosUsuarios.reduce((acc, u) => {
    if (u.nombreUsuario === nombreUsuario) return acc;
    const datosU = AUTENTICACION.obtenerDatosUsuario(u.nombreUsuario);
    return acc + datosU.diario.filter(e => (e.likes || []).includes(nombreUsuario)).length;
  }, 0);

  // Cuenta cuántos comentarios ha dejado este usuario en reseñas de otros
  const totalComentarios = todosUsuarios.reduce((acc, u) => {
    if (u.nombreUsuario === nombreUsuario) return acc;
    const datosU = AUTENTICACION.obtenerDatosUsuario(u.nombreUsuario);
    return acc + datosU.diario.reduce((a, e) => a + (e.comentarios || []).filter(c => c.autor === nombreUsuario).length, 0);
  }, 0);

  // Filtra los logros que aún no tiene y cuyas condiciones se cumplen ahora
  const porDesbloquear = CATALOGO_LOGROS.filter(a => {
    // Si ya lo tiene desbloqueado, lo salta
    if (yaDesbloqueados.includes(a.id)) return false;
    // Evalúa la condición específica de cada logro según su código
    switch (a.codigo) {
      case 'primera_vista':      return numVistas    >= 1;
      case 'primera_resena':     return numResenas   >= 1;
      case 'cinco_vistas':       return numVistas    >= 5;
      case 'diez_vistas':        return numVistas    >= 10;
      case 'maratonista':        return pelisUniqMes >= 10;
      case 'primera_fav':        return numFavs      >= 1;
      case 'watchlist_5':        return numWatchlist >= 5;
      case 'tres_resenas':       return numResenas   >= 3;
      case 'cuatro_generos':     return generos.size >= 4;
      case 'primer_seguido':     return numSeguidos  >= 1;
      case 'primer_like_resena': return totalLikesDados    >= 1;
      case 'primer_comentario':  return totalComentarios   >= 1;
      case 'diez_seguidores':    return numSeguidores >= 10;
    }
    return false;
  });

  if (porDesbloquear.length) {
    // Añade los nuevos logros al array del usuario con la fecha actual y marcados como no reclamados
    porDesbloquear.forEach(a => datos.logros.push({ ...a, fecha:new Date().toISOString(), reclamado:false }));
    AUTENTICACION.guardarDatosUsuario(nombreUsuario, datos);
    // Muestra el popup solo del primer logro desbloqueado (si hay varios, no se acumulan)
    mostrarPopupLogro(porDesbloquear[0]);
  }
  return datos;
}

/* ─ Popup logro ─ */
// Muestra una notificación temporal en pantalla cuando se desbloquea un logro
function mostrarPopupLogro(logro) {
  // Reutiliza el popup si ya existe en el DOM, o lo crea si es la primera vez
  let popup = document.getElementById('achPop');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'achPop'; popup.className = 'popup-logro';
    document.body.appendChild(popup);
  }
  // Rellena el popup con el icono, título, nombre, descripción y XP del logro desbloqueado
  popup.innerHTML = `
    <div class="popup-logro-icono">${logro.ico}</div>
    <div class="popup-logro-etiqueta">¡Logro desbloqueado!</div>
    <div class="popup-logro-nombre">${logro.nombre}</div>
    <div class="popup-logro-desc">${logro.desc}</div>
    <div class="popup-logro-xp">+${logro.xp} XP disponibles</div>`;
  popup.style.display = 'block';
  // El popup desaparece automáticamente después de 4,2 segundos
  setTimeout(() => { popup.style.display = 'none'; }, 4200);
}

/* ─ Init global ─ */
// Espera a que todo el HTML esté cargado antes de inicializar el sidebar
document.addEventListener('DOMContentLoaded', inicializarSidebar);