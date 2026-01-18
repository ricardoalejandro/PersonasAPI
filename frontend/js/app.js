/**
 * DNI Lookup - Frontend Application
 */

// ==================== Estado Global ====================
const state = {
    credentials: null,
    currentTab: 'buscar'
};

// ==================== Utilidades ====================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function getAuthHeaders() {
    if (!state.credentials) {
        return {};
    }
    const encoded = btoa(`${state.credentials.username}:${state.credentials.password}`);
    return {
        'Authorization': `Basic ${encoded}`,
        'Content-Type': 'application/json'
    };
}

async function promptCredentials() {
    const username = prompt('Usuario administrador:', 'admin');
    if (!username) return false;

    const password = prompt('Contraseña:');
    if (!password) return false;

    state.credentials = { username, password };
    return true;
}

async function checkAuth() {
    if (!state.credentials && !await promptCredentials()) {
        return false;
    }
    return true;
}

// ==================== API Functions ====================

async function buscarDNI(dni) {
    if (!await checkAuth()) return null;

    try {
        const response = await fetch(`/api/buscar/${dni}`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            state.credentials = null;
            showToast('Credenciales incorrectas', 'error');
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error de conexión', 'error');
        return null;
    }
}

async function getConfig() {
    if (!await checkAuth()) return null;

    try {
        const response = await fetch('/api/config', {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            state.credentials = null;
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

async function updateConfig(token) {
    if (!await checkAuth()) return false;

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ apisperu_token: token })
        });

        if (response.status === 401) {
            state.credentials = null;
            showToast('Credenciales incorrectas', 'error');
            return false;
        }

        if (response.ok) {
            showToast('Configuración actualizada', 'success');
            return true;
        }

        return false;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al guardar configuración', 'error');
        return false;
    }
}

async function getTokens() {
    if (!await checkAuth()) return [];

    try {
        const response = await fetch('/api/tokens', {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            state.credentials = null;
            return [];
        }

        const data = await response.json();
        return data.tokens || [];
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

async function createToken(nombre, descripcion) {
    if (!await checkAuth()) return null;

    try {
        const response = await fetch('/api/tokens', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ nombre, descripcion })
        });

        if (response.status === 401) {
            state.credentials = null;
            showToast('Credenciales incorrectas', 'error');
            return null;
        }

        if (response.ok) {
            showToast('Token creado exitosamente', 'success');
            return await response.json();
        }

        return null;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al crear token', 'error');
        return null;
    }
}

async function deleteToken(id) {
    if (!await checkAuth()) return false;

    try {
        const response = await fetch(`/api/tokens/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            showToast('Token eliminado', 'success');
            return true;
        }

        return false;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al eliminar token', 'error');
        return false;
    }
}

async function toggleToken(id) {
    if (!await checkAuth()) return null;

    try {
        const response = await fetch(`/api/tokens/${id}/toggle`, {
            method: 'PATCH',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            return await response.json();
        }

        return null;
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

// ==================== UI Functions ====================

function switchTab(tabName) {
    // Actualizar pestañas
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Actualizar contenido
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });

    state.currentTab = tabName;

    // Cargar datos según la pestaña
    if (tabName === 'tokens') {
        loadTokens();
    } else if (tabName === 'config') {
        loadConfig();
    }
}

function showResult(data) {
    const container = document.getElementById('result-container');
    const content = document.getElementById('result-content');
    const source = document.getElementById('result-source');
    const errorContainer = document.getElementById('error-container');

    errorContainer.classList.add('hidden');

    if (data.desde_cache) {
        source.textContent = 'Base de datos local';
        source.className = 'badge cache';
    } else {
        source.textContent = 'API Externa';
        source.className = 'badge api';
    }

    content.innerHTML = `
        <div class="result-item">
            <span class="result-label">Tipo de Documento</span>
            <span class="result-value">${data.tipodoc || 'DNI'}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Número de Documento</span>
            <span class="result-value">${data.nrodoc}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Nombres</span>
            <span class="result-value">${data.nombres || '-'}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Apellido Paterno</span>
            <span class="result-value">${data.apellido_paterno || '-'}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Apellido Materno</span>
            <span class="result-value">${data.apellido_materno || '-'}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Código de Verificación</span>
            <span class="result-value">${data.codigo_verificacion || '-'}</span>
        </div>
    `;

    container.classList.remove('hidden');
}

function showError(message) {
    const container = document.getElementById('error-container');
    const resultContainer = document.getElementById('result-container');
    const errorMessage = document.getElementById('error-message');

    resultContainer.classList.add('hidden');
    errorMessage.textContent = message;
    container.classList.remove('hidden');
}

async function loadTokens() {
    const tokens = await getTokens();
    const list = document.getElementById('tokens-list');
    const noTokens = document.getElementById('no-tokens');

    if (tokens.length === 0) {
        list.innerHTML = '';
        noTokens.classList.remove('hidden');
        return;
    }

    noTokens.classList.add('hidden');

    list.innerHTML = tokens.map(token => `
        <div class="token-item" data-id="${token.id}">
            <div class="token-info">
                <div class="token-name">${token.nombre}</div>
                <div class="token-value">${token.token}</div>
                <div class="token-meta">
                    <span>Creado: ${new Date(token.fecha_creacion).toLocaleDateString()}</span>
                    ${token.ultimo_uso ? `<span>Último uso: ${new Date(token.ultimo_uso).toLocaleDateString()}</span>` : ''}
                </div>
            </div>
            <div class="token-actions">
                <span class="token-status ${token.activo ? 'active' : 'inactive'}">
                    ${token.activo ? 'Activo' : 'Inactivo'}
                </span>
                <button class="btn btn-sm btn-secondary toggle-token" data-id="${token.id}">
                    ${token.activo ? 'Desactivar' : 'Activar'}
                </button>
                <button class="btn btn-sm btn-secondary copy-token" data-token="${token.token}">
                    Copiar
                </button>
                <button class="btn btn-sm btn-danger delete-token" data-id="${token.id}">
                    Eliminar
                </button>
            </div>
        </div>
    `).join('');

    // Event listeners para los botones
    list.querySelectorAll('.toggle-token').forEach(btn => {
        btn.addEventListener('click', async () => {
            const result = await toggleToken(btn.dataset.id);
            if (result) loadTokens();
        });
    });

    list.querySelectorAll('.copy-token').forEach(btn => {
        btn.addEventListener('click', () => {
            navigator.clipboard.writeText(btn.dataset.token);
            showToast('Token copiado al portapapeles', 'success');
        });
    });

    list.querySelectorAll('.delete-token').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (confirm('¿Está seguro de eliminar este token?')) {
                if (await deleteToken(btn.dataset.id)) {
                    loadTokens();
                }
            }
        });
    });
}

async function loadConfig() {
    const config = await getConfig();
    const statusIndicator = document.getElementById('token-status');

    if (config) {
        if (config.apisperu_token_configured) {
            statusIndicator.className = 'status-indicator configured';
            statusIndicator.title = 'Token configurado';
        } else {
            statusIndicator.className = 'status-indicator not-configured';
            statusIndicator.title = 'Token no configurado';
        }
    }
}

function showModal() {
    document.getElementById('token-modal').classList.remove('hidden');
}

function hideModal() {
    document.getElementById('token-modal').classList.add('hidden');
    document.getElementById('token-form').reset();
}

// ==================== Event Listeners ====================

document.addEventListener('DOMContentLoaded', () => {
    // Navegación por pestañas
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Formulario de búsqueda
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const dni = document.getElementById('dni-input').value.trim();
        const btn = document.getElementById('search-btn');

        if (!/^\d{8}$/.test(dni)) {
            showToast('El DNI debe tener 8 dígitos', 'warning');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Buscando...';

        const result = await buscarDNI(dni);

        btn.disabled = false;
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.3-4.3"/>
            </svg>
            Buscar
        `;

        if (result) {
            if (result.success && result.data) {
                showResult(result.data);
            } else {
                showError(result.message || 'No se encontraron datos');
            }
        }
    });

    // Solo números en el campo DNI
    document.getElementById('dni-input').addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '').slice(0, 8);
    });

    // Modal de nuevo token
    document.getElementById('new-token-btn').addEventListener('click', showModal);
    document.getElementById('modal-close').addEventListener('click', hideModal);
    document.getElementById('modal-cancel').addEventListener('click', hideModal);
    document.querySelector('.modal-overlay').addEventListener('click', hideModal);

    // Formulario de nuevo token
    document.getElementById('token-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const nombre = document.getElementById('token-name').value.trim();
        const descripcion = document.getElementById('token-desc').value.trim();

        const result = await createToken(nombre, descripcion);

        if (result) {
            hideModal();
            loadTokens();
        }
    });

    // Formulario de configuración
    document.getElementById('config-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const token = document.getElementById('apisperu-token').value.trim();

        if (!token) {
            showToast('Ingrese el token de apisperu.com', 'warning');
            return;
        }

        if (await updateConfig(token)) {
            loadConfig();
            document.getElementById('apisperu-token').value = '';
        }
    });
});
