/**
 * DNI Lookup - Frontend Application
 */

// ==================== Estado Global ====================
const state = {
    isLoggedIn: false,
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
        return { 'Content-Type': 'application/json' };
    }
    const encoded = btoa(`${state.credentials.username}:${state.credentials.password}`);
    return {
        'Authorization': `Basic ${encoded}`,
        'Content-Type': 'application/json'
    };
}

// ==================== Login/Logout ====================

function showLoginScreen() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-container').classList.add('hidden');
    state.isLoggedIn = false;
    state.credentials = null;
}

function showAppScreen() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');
    state.isLoggedIn = true;
}

async function handleLogin(username, password) {
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();

        if (result.success) {
            state.credentials = { username, password };
            showAppScreen();
            showToast('Bienvenido al sistema', 'success');
            return true;
        } else {
            return false;
        }
    } catch (error) {
        console.error('Error en login:', error);
        showToast('Error de conexión', 'error');
        return false;
    }
}

function handleLogout() {
    state.credentials = null;
    state.isLoggedIn = false;
    showLoginScreen();
    showToast('Sesión cerrada', 'info');
}

// ==================== Database State ====================

const dbState = {
    searchTerm: '',
    currentPage: 1,
    perPage: 10,
    totalPages: 1,
    total: 0,
    debounceTimer: null
};

// ==================== Debounce Function ====================

function debounce(func, delay) {
    return function (...args) {
        clearTimeout(dbState.debounceTimer);
        dbState.debounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
}

// ==================== Backup Function ====================

async function downloadBackup() {
    try {
        const response = await fetch('/api/backup', {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            showLoginScreen();
            return;
        }

        if (response.status === 429) {
            showToast('Límite de descargas excedido. Intente más tarde.', 'warning');
            return;
        }

        if (response.status === 404) {
            showToast('Base de datos no encontrada', 'error');
            return;
        }

        if (response.ok) {
            // Obtener el nombre del archivo del header o usar uno por defecto
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'backup_personas.db';
            if (contentDisposition) {
                // Buscar filename="..." o filename=...
                const match = contentDisposition.match(/filename="?([^"\s;]+)"?/);
                if (match) {
                    filename = match[1].replace(/["';]/g, '').trim();
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showToast('Backup descargado exitosamente', 'success');
        } else {
            showToast('Error al descargar backup', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al descargar backup', 'error');
    }
}

// ==================== Database API Functions ====================

async function fetchPersonas(searchTerm = '', page = 1, perPage = 10) {
    try {
        const params = new URLSearchParams({
            q: searchTerm,
            page: page.toString(),
            per_page: perPage.toString()
        });

        const response = await fetch(`/api/personas?${params}`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            showLoginScreen();
            return null;
        }

        const result = await response.json();
        // Extraer data si viene en estructura estandarizada
        if (result.success && result.data) {
            return result.data;
        }
        return result;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar personas', 'error');
        return null;
    }
}

async function createPersona(data) {
    try {
        const response = await fetch('/api/personas', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (response.status === 401) {
            showLoginScreen();
            return null;
        }

        if (response.status === 400) {
            const error = await response.json();
            showToast(error.detail || 'Error al crear persona', 'error');
            return null;
        }

        if (response.ok) {
            showToast('Persona creada exitosamente', 'success');
            return await response.json();
        }

        return null;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al crear persona', 'error');
        return null;
    }
}

async function updatePersona(id, data) {
    try {
        const response = await fetch(`/api/personas/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (response.status === 401) {
            showLoginScreen();
            return null;
        }

        if (response.ok) {
            showToast('Persona actualizada', 'success');
            return await response.json();
        }

        return null;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al actualizar persona', 'error');
        return null;
    }
}

async function deletePersona(id) {
    try {
        const response = await fetch(`/api/personas/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            showToast('Persona eliminada', 'success');
            return true;
        }

        return false;
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al eliminar persona', 'error');
        return false;
    }
}

// ==================== API Functions ====================

async function buscarDNI(dni) {
    try {
        const response = await fetch(`/api/buscar/${dni}`, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            showLoginScreen();
            showToast('Sesión expirada, ingrese nuevamente', 'warning');
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

    try {
        const response = await fetch('/api/config', {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            showLoginScreen();
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

async function updateConfig(token) {

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ apisperu_token: token })
        });

        if (response.status === 401) {
            showLoginScreen();
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

    try {
        const response = await fetch('/api/tokens', {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            showLoginScreen();
            return [];
        }

        const result = await response.json();
        // Extraer tokens de la estructura estandarizada
        if (result.success && result.data && result.data.tokens) {
            return result.data.tokens;
        }
        return result.tokens || [];
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

async function createToken(nombre, descripcion) {

    try {
        const response = await fetch('/api/tokens', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ nombre, descripcion })
        });

        if (response.status === 401) {
            showLoginScreen();
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
    } else if (tabName === 'database') {
        loadPersonas();
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

// ==================== Database UI Functions ====================

async function loadPersonas() {
    const table = document.getElementById('personas-table');
    const tbody = document.getElementById('personas-tbody');
    const emptyState = document.getElementById('db-empty');
    const pagination = document.getElementById('pagination');

    table.classList.add('loading');

    const result = await fetchPersonas(dbState.searchTerm, dbState.currentPage, dbState.perPage);

    table.classList.remove('loading');

    if (!result) return;

    dbState.total = result.total;
    dbState.totalPages = result.total_pages;
    dbState.currentPage = result.page;

    if (result.items.length === 0) {
        tbody.innerHTML = '';
        emptyState.classList.remove('hidden');
        pagination.classList.add('hidden');
    } else {
        emptyState.classList.add('hidden');
        pagination.classList.remove('hidden');
        renderPersonasTable(result.items);
        updatePagination();
    }
}

function renderPersonasTable(personas) {
    const tbody = document.getElementById('personas-tbody');

    tbody.innerHTML = personas.map(persona => `
        <tr data-id="${persona.id}">
            <td>${persona.nrodoc}</td>
            <td>${persona.nombres || '-'}</td>
            <td>${persona.apellido_paterno || '-'}</td>
            <td>${persona.apellido_materno || '-'}</td>
            <td>${persona.codigo_verificacion || '-'}</td>
            <td class="actions">
                <button class="btn-icon edit-persona" data-id="${persona.id}" title="Editar">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                        <path d="m15 5 4 4"/>
                    </svg>
                </button>
                <button class="btn-icon delete delete-persona" data-id="${persona.id}" title="Eliminar">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"/>
                        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');

    // Event listeners para editar y eliminar
    tbody.querySelectorAll('.edit-persona').forEach(btn => {
        btn.addEventListener('click', () => editPersona(parseInt(btn.dataset.id)));
    });

    tbody.querySelectorAll('.delete-persona').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (confirm('¿Está seguro de eliminar esta persona?')) {
                if (await deletePersona(parseInt(btn.dataset.id))) {
                    loadPersonas();
                }
            }
        });
    });
}

function updatePagination() {
    const info = document.getElementById('pagination-info');
    const indicator = document.getElementById('page-indicator');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');

    const start = (dbState.currentPage - 1) * dbState.perPage + 1;
    const end = Math.min(dbState.currentPage * dbState.perPage, dbState.total);

    info.textContent = `Mostrando ${start}-${end} de ${dbState.total} registros`;
    indicator.textContent = `Página ${dbState.currentPage} de ${dbState.totalPages}`;

    prevBtn.disabled = dbState.currentPage <= 1;
    nextBtn.disabled = dbState.currentPage >= dbState.totalPages;
}

function showPersonaModal(persona = null) {
    const modal = document.getElementById('persona-modal');
    const title = document.getElementById('persona-modal-title');
    const form = document.getElementById('persona-form');
    const dniInput = document.getElementById('persona-dni');

    form.reset();
    document.getElementById('persona-id').value = '';

    if (persona) {
        title.textContent = 'Editar Persona';
        document.getElementById('persona-id').value = persona.id;
        document.getElementById('persona-dni').value = persona.nrodoc;
        document.getElementById('persona-nombres').value = persona.nombres || '';
        document.getElementById('persona-ap-paterno').value = persona.apellido_paterno || '';
        document.getElementById('persona-ap-materno').value = persona.apellido_materno || '';
        document.getElementById('persona-codigo').value = persona.codigo_verificacion || '';
        dniInput.readOnly = true;
    } else {
        title.textContent = 'Nueva Persona';
        dniInput.readOnly = false;
    }

    modal.classList.remove('hidden');
}

function hidePersonaModal() {
    document.getElementById('persona-modal').classList.add('hidden');
    document.getElementById('persona-form').reset();
}

async function editPersona(id) {
    // Buscar la persona en la tabla actual
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (row) {
        const cells = row.querySelectorAll('td');
        const persona = {
            id: id,
            nrodoc: cells[0].textContent,
            nombres: cells[1].textContent !== '-' ? cells[1].textContent : '',
            apellido_paterno: cells[2].textContent !== '-' ? cells[2].textContent : '',
            apellido_materno: cells[3].textContent !== '-' ? cells[3].textContent : '',
            codigo_verificacion: cells[4].textContent !== '-' ? cells[4].textContent : ''
        };
        showPersonaModal(persona);
    }
}

// Debounced search function
const debouncedSearch = debounce(() => {
    dbState.currentPage = 1;
    loadPersonas();
}, 1000);

// ==================== Event Listeners ====================

document.addEventListener('DOMContentLoaded', () => {
    // Login form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const loginBtn = document.getElementById('login-btn');
        const loginError = document.getElementById('login-error');

        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="loading"></span> Ingresando...';
        loginError.classList.add('hidden');

        const success = await handleLogin(username, password);

        if (!success) {
            loginError.textContent = 'Usuario o contraseña incorrectos';
            loginError.classList.remove('hidden');
        }

        loginBtn.disabled = false;
        loginBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                <polyline points="10 17 15 12 10 7"/>
                <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            Iniciar Sesión
        `;
    });

    // Logout button
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

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

    // ==================== Database Event Listeners ====================

    // Botón de backup
    document.getElementById('backup-btn').addEventListener('click', async () => {
        const btn = document.getElementById('backup-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Descargando...';
        
        await downloadBackup();
        
        btn.disabled = false;
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Descargar Backup
        `;
    });

    // Búsqueda con debounce
    document.getElementById('db-search').addEventListener('input', (e) => {
        const value = e.target.value.trim();
        dbState.searchTerm = value;

        // Solo buscar si tiene 3 o más caracteres, o si está vacío (mostrar todos)
        if (value.length >= 3 || value.length === 0) {
            debouncedSearch();
        }
    });

    // Cambio de registros por página
    document.getElementById('per-page').addEventListener('change', (e) => {
        dbState.perPage = parseInt(e.target.value);
        dbState.currentPage = 1;
        loadPersonas();
    });

    // Paginación
    document.getElementById('prev-page').addEventListener('click', () => {
        if (dbState.currentPage > 1) {
            dbState.currentPage--;
            loadPersonas();
        }
    });

    document.getElementById('next-page').addEventListener('click', () => {
        if (dbState.currentPage < dbState.totalPages) {
            dbState.currentPage++;
            loadPersonas();
        }
    });

    // Modal de persona
    document.getElementById('new-persona-btn').addEventListener('click', () => showPersonaModal());
    document.getElementById('persona-modal-close').addEventListener('click', hidePersonaModal);
    document.getElementById('persona-modal-cancel').addEventListener('click', hidePersonaModal);
    document.querySelector('#persona-modal .modal-overlay').addEventListener('click', hidePersonaModal);

    // Solo números en DNI de persona
    document.getElementById('persona-dni').addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '').slice(0, 8);
    });

    // Formulario de persona
    document.getElementById('persona-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const id = document.getElementById('persona-id').value;
        const data = {
            nrodoc: document.getElementById('persona-dni').value.trim(),
            nombres: document.getElementById('persona-nombres').value.trim() || null,
            apellido_paterno: document.getElementById('persona-ap-paterno').value.trim() || null,
            apellido_materno: document.getElementById('persona-ap-materno').value.trim() || null,
            codigo_verificacion: document.getElementById('persona-codigo').value.trim() || null
        };

        if (!data.nrodoc || data.nrodoc.length !== 8) {
            showToast('El DNI debe tener 8 dígitos', 'warning');
            return;
        }

        let result;
        if (id) {
            // Actualizar
            result = await updatePersona(parseInt(id), data);
        } else {
            // Crear
            result = await createPersona(data);
        }

        if (result) {
            hidePersonaModal();
            loadPersonas();
        }
    });
});
