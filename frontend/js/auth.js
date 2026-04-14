// gestión de token JWT y datos de sesión en localStorage

const auth = {

    TOKEN_KEY: 'bonobo_token',
    USER_KEY:  'bonobo_user',

    guardarToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    estaLogueado() {
        return !!this.getToken();
    },

    // guarda id, username y avatar para no tener que llamar a /me en cada página
    guardarUsuario(usuario) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(usuario));
    },

    getUsuario() {
        const raw = localStorage.getItem(this.USER_KEY);
        if (!raw) return null;
        try { return JSON.parse(raw); }
        catch { return null; }
    },

    async login(email, password) {
        const data = await api.auth.login(email, password);
        this.guardarToken(data.access_token);
        const usuario = await api.usuarios.mePerfil();
        this.guardarUsuario(usuario);
        return usuario;
    },

    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    },

    requiereAuth(rutaLogin = '/pages/login.html') {
        if (!this.estaLogueado()) window.location.href = rutaLogin;
    },

    redirigeSiLogueado(rutaInicio = '/index.html') {
        if (this.estaLogueado()) window.location.href = rutaInicio;
    }
};
