// js/ajustes.js — Página de ajustes de cuenta

function mostrarToast(mensaje, tipo = 'ok', duracion = 2800) {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast toast--${tipo} toast--visible`;
    setTimeout(() => { toast.className = 'toast'; }, duracion);
}

// ── PERFIL ────────────────────────────────────────────────────────────────────

async function guardarPerfil() {
    const avatar_url = document.getElementById('inputAvatar').value.trim() || null;
    const bio        = document.getElementById('inputBio').value.trim() || null;
    const errorEl   = document.getElementById('errorPerfil');

    try {
        await api.usuarios.editarPerfil({ bio, avatar_url });

        const usuarioGuardado = auth.getUsuario();
        auth.guardarUsuario({ ...usuarioGuardado, bio, avatar_url });

        errorEl.className = 'form-error';
        mostrarToast('Perfil actualizado ✓');
    } catch (err) {
        errorEl.textContent = err.message || 'Error al guardar.';
        errorEl.className = 'form-error form-error--visible';
    }
}

// ── CONTRASEÑA ────────────────────────────────────────────────────────────────

async function guardarPassword() {
    const actual  = document.getElementById('inputPasswordActual').value;
    const nueva   = document.getElementById('inputPasswordNueva').value;
    const repetir = document.getElementById('inputPasswordRepetir').value;
    const errorEl = document.getElementById('errorPassword');

    if (nueva.length < 8) {
        errorEl.textContent = 'La nueva contraseña debe tener al menos 8 caracteres.';
        errorEl.className = 'form-error form-error--visible';
        return;
    }
    if (nueva !== repetir) {
        errorEl.textContent = 'Las contraseñas no coinciden.';
        errorEl.className = 'form-error form-error--visible';
        return;
    }

    try {
        await api.usuarios.cambiarPassword(actual, nueva);
        document.getElementById('inputPasswordActual').value = '';
        document.getElementById('inputPasswordNueva').value  = '';
        document.getElementById('inputPasswordRepetir').value = '';
        errorEl.className = 'form-error';
        mostrarToast('Contraseña actualizada ✓');
    } catch (err) {
        errorEl.textContent = err.message || 'Error al cambiar la contraseña.';
        errorEl.className = 'form-error form-error--visible';
    }
}

// ── INIT ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    renderNav('../');
    actualizarBadgesLogros();

    if (!auth.estaLogueado()) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const usuario = await api.usuarios.mePerfil();
        document.getElementById('inputAvatar').value = usuario.avatar_url || '';
        document.getElementById('inputBio').value    = usuario.bio || '';
    } catch {
        mostrarToast('Error al cargar los datos', 'error');
    }
});
