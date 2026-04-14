// js/auth.js — Gestión del token JWT y la sesión del usuario
// Este archivo maneja el almacenamiento del token y los datos básicos del usuario en memoria.

const auth = {

    // Clave usada en localStorage para guardar el token JWT
    TOKEN_KEY: 'bonobo_token',
    // Clave para guardar los datos básicos del usuario (evita llamar a /me en cada página)
    USER_KEY:  'bonobo_user',

    // ── TOKEN ─────────────────────────────────────────────────────────────────

    // Guarda el token JWT en localStorage tras un login exitoso
    guardarToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    // Devuelve el token JWT o null si no hay sesión activa
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    // Devuelve true si hay un token guardado (el usuario está logueado)
    estaLogueado() {
        return !!this.getToken();
    },

    // ── USUARIO ───────────────────────────────────────────────────────────────

    // Guarda los datos básicos del usuario (id, username, avatar_url) en localStorage.
    // Así no necesitamos llamar a /api/usuarios/me en cada carga de página.
    guardarUsuario(usuario) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(usuario));
    },

    // Devuelve el objeto de usuario guardado, o null si no hay sesión
    getUsuario() {
        const raw = localStorage.getItem(this.USER_KEY);
        if (!raw) return null;
        try { return JSON.parse(raw); }
        catch { return null; }
    },

    // ── LOGIN / LOGOUT ────────────────────────────────────────────────────────

    // Ejecuta el login completo: llama a la API, guarda el token y los datos del usuario.
    // Devuelve el objeto de usuario para que la página redirija o actualice la UI.
    async login(email, password) {
        const data = await api.auth.login(email, password);   // { access_token, token_type }
        this.guardarToken(data.access_token);

        // Pedimos los datos del usuario con el nuevo token para guardarlos
        const usuario = await api.usuarios.mePerfil();
        this.guardarUsuario(usuario);

        return usuario;
    },

    // Cierra sesión: elimina el token y los datos del usuario del localStorage
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    },

    // ── REDIRECCIONES ─────────────────────────────────────────────────────────

    // Redirige al login si el usuario no está logueado.
    // Úsalo al inicio de páginas que requieren autenticación.
    requiereAuth(rutaLogin = '/pages/login.html') {
        if (!this.estaLogueado()) {
            window.location.href = rutaLogin;
        }
    },

    // Redirige al inicio si el usuario YA está logueado.
    // Úsalo en las páginas de login y registro para evitar que las vean logueados.
    redirigeSiLogueado(rutaInicio = '/index.html') {
        if (this.estaLogueado()) {
            window.location.href = rutaInicio;
        }
    }
};
