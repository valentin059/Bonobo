// js/social.js — Sistema social: seguir, reseñas de amigos, likes y comentarios en reseñas

const SOCIAL = {

  seguir(objetivoNombre) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return false;
    if (usuario.nombreUsuario === objetivoNombre) return false;
    let datos = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    datos.seguidos = datos.seguidos || [];
    if (datos.seguidos.includes(objetivoNombre)) return false;
    datos.seguidos.push(objetivoNombre);
    datos = verificarLogros(usuario.nombreUsuario, datos);
    AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
    const datosObjetivo = AUTENTICACION.obtenerDatosUsuario(objetivoNombre);
    verificarLogros(objetivoNombre, datosObjetivo);
    return true;
  },

  dejarDeSeguir(objetivoNombre) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return false;
    let datos = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    datos.seguidos = (datos.seguidos || []).filter(u => u !== objetivoNombre);
    AUTENTICACION.guardarDatosUsuario(usuario.nombreUsuario, datos);
    return true;
  },

  estaSiguiendo(objetivoNombre) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return false;
    const datos   = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    return (datos.seguidos || []).includes(objetivoNombre);
  },

  obtenerSeguidos(nombreUsuario) {
    const datos = AUTENTICACION.obtenerDatosUsuario(nombreUsuario);
    return (datos.seguidos || []).map(u => AUTENTICACION.obtenerUsuarios().find(x => x.nombreUsuario === u)).filter(Boolean);
  },

  obtenerSeguidores(nombreUsuario) {
    return AUTENTICACION.obtenerUsuarios().filter(u => {
      if (u.nombreUsuario === nombreUsuario) return false;
      const datos = AUTENTICACION.obtenerDatosUsuario(u.nombreUsuario);
      return (datos.seguidos || []).includes(nombreUsuario);
    });
  },

  obtenerResenasAmigos(idPelicula) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return [];
    const datos   = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    const seguidos = datos.seguidos || [];
    const resultados = [];
    seguidos.forEach(nombreAmigo => {
      const datosAmigo   = AUTENTICACION.obtenerDatosUsuario(nombreAmigo);
      const usuarioAmigo = AUTENTICACION.obtenerUsuarios().find(u => u.nombreUsuario === nombreAmigo);
      const entradas = datosAmigo.diario.filter(e => e.idPelicula === idPelicula);
      if (entradas.length > 0) {
        const ultima = entradas[entradas.length - 1];
        resultados.push({ usuario: usuarioAmigo, todasEntradas: entradas, ultimaEntrada: ultima });
      } else {
        const vista = datosAmigo.vistas.find(v => v.idPelicula === idPelicula);
        if (vista) resultados.push({ usuario: usuarioAmigo, todasEntradas: [], ultimaEntrada: null, soloVista: true, puntuacion: vista.puntuacion });
      }
    });
    return resultados;
  },

  obtenerTodasResenas(idPelicula) {
    const resultados = [];
    AUTENTICACION.obtenerUsuarios().forEach(u => {
      const datos = AUTENTICACION.obtenerDatosUsuario(u.nombreUsuario);
      datos.diario.filter(e => e.idPelicula === idPelicula && e.resena).forEach(e => {
        resultados.push({ usuario: u, entrada: e });
      });
    });
    resultados.sort((a, b) => (b.entrada.id || 0) - (a.entrada.id || 0));
    return resultados;
  },

  alternarLike(nombrePropietario, idEntrada) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return null;
    const datos   = AUTENTICACION.obtenerDatosUsuario(nombrePropietario);
    const idx     = datos.diario.findIndex(e => e.id === idEntrada);
    if (idx < 0) return null;
    datos.diario[idx].likes = datos.diario[idx].likes || [];
    const posLike = datos.diario[idx].likes.indexOf(usuario.nombreUsuario);
    let dioLike;
    if (posLike >= 0) {
      datos.diario[idx].likes.splice(posLike, 1);
      dioLike = false;
    } else {
      datos.diario[idx].likes.push(usuario.nombreUsuario);
      dioLike = true;
    }
    AUTENTICACION.guardarDatosUsuario(nombrePropietario, datos);
    if (dioLike && nombrePropietario !== usuario.nombreUsuario) {
      const misDatos = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
      verificarLogros(usuario.nombreUsuario, misDatos);
    }
    return { dioLike, total: datos.diario[idx].likes.length };
  },

  yoLeDiLike(nombrePropietario, idEntrada) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return false;
    const datos   = AUTENTICACION.obtenerDatosUsuario(nombrePropietario);
    const entrada = datos.diario.find(x => x.id === idEntrada);
    return entrada ? (entrada.likes || []).includes(usuario.nombreUsuario) : false;
  },

  agregarComentario(nombrePropietario, idEntrada, texto) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario || !texto.trim()) return null;
    const datos   = AUTENTICACION.obtenerDatosUsuario(nombrePropietario);
    const idx     = datos.diario.findIndex(e => e.id === idEntrada);
    if (idx < 0) return null;
    datos.diario[idx].comentarios = datos.diario[idx].comentarios || [];
    const comentario = { id: Date.now(), autor: usuario.nombreUsuario, texto: texto.trim(), fecha: new Date().toISOString() };
    datos.diario[idx].comentarios.push(comentario);
    AUTENTICACION.guardarDatosUsuario(nombrePropietario, datos);
    if (nombrePropietario !== usuario.nombreUsuario) {
      const misDatos = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
      verificarLogros(usuario.nombreUsuario, misDatos);
    }
    return comentario;
  },

  eliminarComentario(nombrePropietario, idEntrada, idComentario) {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return false;
    const datos   = AUTENTICACION.obtenerDatosUsuario(nombrePropietario);
    const idx     = datos.diario.findIndex(e => e.id === idEntrada);
    if (idx < 0) return false;
    const comentario = (datos.diario[idx].comentarios || []).find(c => c.id === idComentario);
    if (!comentario || comentario.autor !== usuario.nombreUsuario) return false;
    datos.diario[idx].comentarios = datos.diario[idx].comentarios.filter(c => c.id !== idComentario);
    AUTENTICACION.guardarDatosUsuario(nombrePropietario, datos);
    return true;
  },

  obtenerComentarios(nombrePropietario, idEntrada) {
    const datos   = AUTENTICACION.obtenerDatosUsuario(nombrePropietario);
    const entrada = datos.diario.find(x => x.id === idEntrada);
    return entrada ? (entrada.comentarios || []) : [];
  },

  obtenerRankingAmigos() {
    const usuario = AUTENTICACION.obtenerUsuarioActual(); if (!usuario) return [];
    const datos   = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    const seguidos = datos.seguidos || [];
    const ranking = seguidos.map(nombreAmigo => {
      const usuarioAmigo = AUTENTICACION.obtenerUsuarios().find(u => u.nombreUsuario === nombreAmigo);
      const datosAmigo   = AUTENTICACION.obtenerDatosUsuario(nombreAmigo);
      const nivel        = Math.max(1, Math.floor(datosAmigo.xp / 100));
      return { usuario: usuarioAmigo, xp: datosAmigo.xp, nivel };
    });
    const misDatos = AUTENTICACION.obtenerDatosUsuario(usuario.nombreUsuario);
    ranking.push({ usuario: AUTENTICACION.obtenerUsuarioActual(), xp: misDatos.xp, nivel: Math.max(1, Math.floor(misDatos.xp / 100)) });
    ranking.sort((a, b) => b.xp - a.xp);
    return ranking;
  }
};

function renderizarResenasAmigos(idPelicula) {
  const el = document.getElementById('mFriendReviews');
  if (!el) return;
  const usuario = AUTENTICACION.obtenerUsuarioActual();
  if (!usuario) { el.style.display = 'none'; return; }

  const amigos = SOCIAL.obtenerResenasAmigos(idPelicula);
  if (!amigos.length) { el.innerHTML = ''; el.style.display = 'none'; return; }

  el.style.display = 'block';
  el.innerHTML = `
    <div class="resenas-titulo"><span>👥</span> Tus amigos</div>
    <div class="resenas-amigos">
      ${amigos.map(({ usuario: amigo, todasEntradas, ultimaEntrada, soloVista, puntuacion }) => {
        const av = amigo?.avatar || AUTENTICACION.obtenerDatosUsuario(amigo?.nombreUsuario || '')?.avatar;
        const htmlAvatar = av
          ? `<div class="resena-avatar" style="background-image:url(${av});background-size:cover"></div>`
          : `<div class="resena-avatar">${(amigo?.nombreUsuario||'?')[0].toUpperCase()}</div>`;
        if (soloVista) {
          return `<div class="resena-amigo">
            ${htmlAvatar}
            <div class="resena-amigo-info">
              <span class="resena-amigo-nombre">${amigo?.nombreUsuario}</span>
              <span class="resena-amigo-estado">Solo ha marcado como vista${puntuacion ? ` · <b>${puntuacion}/10</b>` : ''}</span>
            </div>
          </div>`;
        }
        const tieneResena = ultimaEntrada?.resena;
        return `<div class="resena-amigo" ${todasEntradas.length > 0 ? `onclick="abrirEntradasAmigo('${amigo?.nombreUsuario}',${idPelicula})"` : ''} style="${todasEntradas.length>0?'cursor:pointer':''}">
          ${htmlAvatar}
          <div class="resena-amigo-info">
            <span class="resena-amigo-nombre">${amigo?.nombreUsuario}</span>
            ${tieneResena ? `<p class="resena-amigo-texto">"${ultimaEntrada.resena.substring(0,120)}${ultimaEntrada.resena.length>120?'…':''}"</p>` : '<span class="resena-amigo-estado">Vista sin reseña</span>'}
            <div class="resena-amigo-meta">
              ${ultimaEntrada?.fecha ? `<span>${ultimaEntrada.fecha}</span>` : ''}
              ${todasEntradas.length > 1 ? `<span class="resena-amigo-mas">+${todasEntradas.length-1} entrada${todasEntradas.length>2?'s':''} más →</span>` : ''}
            </div>
          </div>
        </div>`;
      }).join('')}
    </div>`;
}

function renderizarResenasGenerales(idPelicula) {
  const el = document.getElementById('mGeneralReviews');
  if (!el) return;
  const usuario = AUTENTICACION.obtenerUsuarioActual();

  const todasResenas = SOCIAL.obtenerTodasResenas(idPelicula);
  if (!todasResenas.length) { el.innerHTML = ''; el.style.display='none'; return; }

  el.style.display = 'block';
  el.innerHTML = `
    <div class="resenas-titulo"><span>🌐</span> Reseñas de la comunidad</div>
    <div class="resenas-comunidad">
      ${todasResenas.map(({ usuario: autor, entrada }) => {
        const av = autor?.avatar || AUTENTICACION.obtenerDatosUsuario(autor?.nombreUsuario||'')?.avatar;
        const htmlAvatar = av
          ? `<div class="resena-avatar" style="background-image:url(${av});background-size:cover"></div>`
          : `<div class="resena-avatar">${(autor?.nombreUsuario||'?')[0].toUpperCase()}</div>`;
        const yaDiLike   = SOCIAL.yoLeDiLike(autor.nombreUsuario, entrada.id);
        const numLikes   = (entrada.likes || []).length;
        const numComents = (entrada.comentarios || []).length;
        const puedeLike  = usuario && usuario.nombreUsuario !== autor.nombreUsuario;
        return `<div class="resena-comunidad-tarjeta">
          <div class="resena-comunidad-superior">
            ${htmlAvatar}
            <div class="resena-comunidad-info">
              <span class="resena-comunidad-nombre">${autor.nombreUsuario}</span>
              <span class="resena-comunidad-fecha">${entrada.fecha || ''}</span>
            </div>
          </div>
          <p class="resena-comunidad-texto">${entrada.resena}</p>
          <div class="resena-comunidad-acciones">
            ${puedeLike ? `<button class="resena-btn-like ${yaDiLike?'liked':''}" onclick="alternarLikeResena('${autor.nombreUsuario}',${entrada.id},this)">
              ${yaDiLike?'❤️':'♡'} <span>${numLikes}</span>
            </button>` : `<span class="resena-like-estatico">❤️ ${numLikes}</span>`}
            <button class="resena-btn-comentarios" onclick="alternarSeccionComentarios('comentarios-${autor.nombreUsuario}-${entrada.id}')">
              💬 ${numComents}
            </button>
          </div>
          <div class="resena-comentarios" id="comentarios-${autor.nombreUsuario}-${entrada.id}" style="display:none">
            ${renderizarListaComentarios(autor.nombreUsuario, entrada.id)}
            ${usuario ? `<div class="resena-formulario-comentario">
              <input type="text" class="resena-comentario-input" placeholder="Escribe un comentario…" id="ci-${autor.nombreUsuario}-${entrada.id}" />
              <button class="resena-comentario-enviar" onclick="enviarComentario('${autor.nombreUsuario}',${entrada.id})">Enviar</button>
            </div>` : ''}
          </div>
        </div>`;
      }).join('')}
    </div>`;
}

function renderizarListaComentarios(nombrePropietario, idEntrada) {
  const comentarios = SOCIAL.obtenerComentarios(nombrePropietario, idEntrada);
  const usuario     = AUTENTICACION.obtenerUsuarioActual();
  if (!comentarios.length) return '<p style="color:var(--apagado);font-size:11px;padding:8px 0">Sin comentarios aún.</p>';
  return `<div class="lista-comentarios">${comentarios.map(c => `
    <div class="comentario">
      <div class="comentario-avatar">${c.autor[0].toUpperCase()}</div>
      <div class="comentario-cuerpo">
        <span class="comentario-autor">${c.autor}</span>
        <p class="comentario-texto">${c.texto}</p>
      </div>
      ${usuario && usuario.nombreUsuario === c.autor ? `<button class="comentario-btn-eliminar" onclick="borrarComentario('${nombrePropietario}',${idEntrada},${c.id},this)" title="Eliminar">✕</button>` : ''}
    </div>`).join('')}</div>`;
}

function alternarSeccionComentarios(idSeccion) {
  const el = document.getElementById(idSeccion);
  if (!el) return;
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function alternarLikeResena(nombrePropietario, idEntrada, boton) {
  const resultado = SOCIAL.alternarLike(nombrePropietario, idEntrada);
  if (!resultado) return;
  boton.className = `resena-btn-like ${resultado.dioLike ? 'liked' : ''}`;
  boton.innerHTML = `${resultado.dioLike ? '❤️' : '♡'} <span>${resultado.total}</span>`;
  if (idPeliculaActiva) {
    renderizarResenasAmigos(idPeliculaActiva);
    renderizarResenasGenerales(idPeliculaActiva);
  }
}

function enviarComentario(nombrePropietario, idEntrada) {
  const campo = document.getElementById(`ci-${nombrePropietario}-${idEntrada}`);
  if (!campo || !campo.value.trim()) return;
  const comentario = SOCIAL.agregarComentario(nombrePropietario, idEntrada, campo.value);
  if (!comentario) return;
  notificacion('💬 Comentario enviado');
  const idSeccion = `comentarios-${nombrePropietario}-${idEntrada}`;
  const seccion   = document.getElementById(idSeccion);
  if (seccion) {
    const usuario = AUTENTICACION.obtenerUsuarioActual();
    seccion.innerHTML = renderizarListaComentarios(nombrePropietario, idEntrada)
      + (usuario ? `<div class="resena-formulario-comentario">
          <input type="text" class="resena-comentario-input" placeholder="Escribe un comentario…" id="ci-${nombrePropietario}-${idEntrada}" />
          <button class="resena-comentario-enviar" onclick="enviarComentario('${nombrePropietario}',${idEntrada})">Enviar</button>
        </div>` : '');
    seccion.style.display = 'block';
  }
}

function borrarComentario(nombrePropietario, idEntrada, idComentario, boton) {
  if (!SOCIAL.eliminarComentario(nombrePropietario, idEntrada, idComentario)) return;
  notificacion('Comentario eliminado', 'inf');
  const idSeccion = `comentarios-${nombrePropietario}-${idEntrada}`;
  const seccion   = document.getElementById(idSeccion);
  if (seccion) {
    const usuario = AUTENTICACION.obtenerUsuarioActual();
    seccion.innerHTML = renderizarListaComentarios(nombrePropietario, idEntrada)
      + (usuario ? `<div class="resena-formulario-comentario">
          <input type="text" class="resena-comentario-input" placeholder="Escribe un comentario…" id="ci-${nombrePropietario}-${idEntrada}" />
          <button class="resena-comentario-enviar" onclick="enviarComentario('${nombrePropietario}',${idEntrada})">Enviar</button>
        </div>` : '');
  }
}

function abrirEntradasAmigo(nombreAmigo, idPelicula) {
  const usuarioAmigo = AUTENTICACION.obtenerUsuarios().find(u => u.nombreUsuario === nombreAmigo);
  const datosAmigo   = AUTENTICACION.obtenerDatosUsuario(nombreAmigo);
  const pelicula     = PELICULAS.find(m => m.id === idPelicula);
  const entradas     = datosAmigo.diario.filter(e => e.idPelicula === idPelicula);

  let overlay = document.getElementById('entradasAmigoOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'entradasAmigoOverlay';
    overlay.className = 'modal-fondo';
    document.body.appendChild(overlay);
  }
  overlay.innerHTML = `<div class="modal" style="max-width:520px">
    <div style="padding:24px 24px 12px;display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--borde)">
      <button onclick="document.getElementById('entradasAmigoOverlay').style.display='none'" style="color:var(--apagado);font-size:20px;background:none;border:none;cursor:pointer">←</button>
      <div>
        <div style="font-family:var(--fuente-display);font-size:18px">${nombreAmigo}</div>
        <div style="font-size:11px;color:var(--apagado)">${pelicula?.titulo || ''}</div>
      </div>
    </div>
    <div style="padding:16px 24px;overflow-y:auto;max-height:60vh">
      ${entradas.map(e => `
        <div style="margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid var(--borde)">
          <div style="font-size:11px;color:var(--apagado);margin-bottom:6px">${e.fecha}</div>
          <p style="font-size:13px;color:var(--tenue);line-height:1.7">${e.resena || '<em style="color:var(--apagado)">Sin reseña</em>'}</p>
          <div style="margin-top:10px;display:flex;gap:12px;align-items:center">
            <button class="resena-btn-like ${SOCIAL.yoLeDiLike(nombreAmigo, e.id)?'liked':''}" onclick="alternarLikeResena('${nombreAmigo}',${e.id},this)">
              ${SOCIAL.yoLeDiLike(nombreAmigo, e.id)?'❤️':'♡'} <span>${(e.likes||[]).length}</span>
            </button>
            <button class="resena-btn-comentarios" onclick="alternarSeccionComentarios('ea-comentarios-${nombreAmigo}-${e.id}')">💬 ${(e.comentarios||[]).length}</button>
          </div>
          <div class="resena-comentarios" id="ea-comentarios-${nombreAmigo}-${e.id}" style="display:none">
            ${renderizarListaComentarios(nombreAmigo, e.id)}
            ${AUTENTICACION.obtenerUsuarioActual() ? `<div class="resena-formulario-comentario">
              <input type="text" class="resena-comentario-input" placeholder="Escribe un comentario…" id="eaci-${nombreAmigo}-${e.id}" />
              <button class="resena-comentario-enviar" onclick="enviarComentarioAmigo('${nombreAmigo}',${e.id})">Enviar</button>
            </div>` : ''}
          </div>
        </div>`).join('')}
    </div>
  </div>`;
  overlay.addEventListener('click', ev => { if (ev.target === overlay) overlay.style.display = 'none'; });
  overlay.style.display = 'flex';
}

function enviarComentarioAmigo(nombrePropietario, idEntrada) {
  const campo = document.getElementById(`eaci-${nombrePropietario}-${idEntrada}`);
  if (!campo || !campo.value.trim()) return;
  SOCIAL.agregarComentario(nombrePropietario, idEntrada, campo.value);
  notificacion('💬 Comentario enviado');
  const seccion = document.getElementById(`ea-comentarios-${nombrePropietario}-${idEntrada}`);
  if (seccion) {
    const usuario = AUTENTICACION.obtenerUsuarioActual();
    seccion.innerHTML = renderizarListaComentarios(nombrePropietario, idEntrada)
      + (usuario ? `<div class="resena-formulario-comentario">
          <input type="text" class="resena-comentario-input" placeholder="Escribe un comentario…" id="eaci-${nombrePropietario}-${idEntrada}" />
          <button class="resena-comentario-enviar" onclick="enviarComentarioAmigo('${nombrePropietario}',${idEntrada})">Enviar</button>
        </div>` : '');
    seccion.style.display = 'block';
  }
}