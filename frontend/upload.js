// API Configuration
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'http://localhost:8000'; // Change this to your production URL

// State
let authToken = localStorage.getItem('token');
let currentUser = null;

// Utility Functions
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.classList.remove('hidden');
    setTimeout(() => element.classList.add('hidden'), 5000);
}

function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.classList.remove('hidden');
    setTimeout(() => element.classList.add('hidden'), 3000);
}

async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (authToken && !options.skipAuth) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(error.detail || 'Error en la solicitud');
    }

    return response.json();
}

// Authentication
async function login(email, password) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
            skipAuth: true
        });

        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        await loadUserData();
        showDashboard();
        showSuccess('loginSuccess', '¡Inicio de sesión exitoso!');
    } catch (error) {
        showError('loginError', error.message);
    }
}

async function register(email, password) {
    try {
        const data = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
            skipAuth: true
        });

        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        await loadUserData();
        showDashboard();
        showSuccess('registerSuccess', '¡Registro exitoso!');
    } catch (error) {
        showError('registerError', error.message);
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('token');
    showLogin();
}

// User Data
async function loadUserData() {
    try {
        currentUser = await apiRequest('/users/me');
        
        // Redirect admin/superadmin to admin panel
        if (currentUser.role === 'admin' || currentUser.role === 'superadmin') {
            window.location.href = 'admin.html';
            return;
        }
        
        document.getElementById('userEmail').textContent = currentUser.email;
        await loadAdmins();
        await loadFiles();
    } catch (error) {
        console.error('Error loading user data:', error);
        logout();
    }
}

async function loadAdmins() {
    try {
        const admins = await apiRequest('/users/me/admins');
        const select = document.getElementById('adminSelect');
        
        if (admins.length === 0) {
            select.innerHTML = '<option value="">No hay admins asociados</option>';
            document.getElementById('uploadBtn').disabled = true;
            showError('uploadError', 'No estás asociado a ningún admin. Contacta al administrador.');
        } else {
            select.innerHTML = admins.map(admin => 
                `<option value="${admin.id}">${admin.name} (${admin.email})</option>`
            ).join('');
            document.getElementById('uploadBtn').disabled = false;
        }
    } catch (error) {
        console.error('Error loading admins:', error);
        showError('uploadError', 'Error cargando administradores');
    }
}

// File Operations
async function uploadFile(formData) {
    try {
        const response = await fetch(`${API_URL}/files/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error subiendo archivo');
        }

        const data = await response.json();
        showSuccess('uploadSuccess', '¡Archivo subido exitosamente!');
        document.getElementById('uploadForm').reset();
        await loadFiles();
    } catch (error) {
        showError('uploadError', error.message);
    }
}

async function loadFiles() {
    try {
        const data = await apiRequest('/files/');
        const filesList = document.getElementById('filesList');
        
        if (data.files.length === 0) {
            filesList.innerHTML = '<p style="text-align: center; color: #666;">No hay archivos disponibles</p>';
            return;
        }

        filesList.innerHTML = data.files.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-meta">
                        Subido: ${new Date(file.created_at).toLocaleString()}
                        ${file.file_size ? ` | Tamaño: ${formatFileSize(file.file_size)}` : ''}
                    </div>
                    ${file.description ? `<div class="file-meta">${file.description}</div>` : ''}
                </div>
                <div class="file-actions">
                    <button class="btn-secondary" style="width: auto; padding: 0.5rem 1rem;" 
                            onclick="downloadFile(${file.id}, '${file.filename}')">
                        Descargar
                    </button>
                    ${file.uploaded_by_user_id === currentUser.id ? `
                        <button class="btn-danger" onclick="deleteFile(${file.id})">
                            Eliminar
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading files:', error);
        document.getElementById('filesList').innerHTML = 
            '<p style="text-align: center; color: #dc3545;">Error cargando archivos</p>';
    }
}

async function downloadFile(fileId, filename) {
    try {
        const response = await fetch(`${API_URL}/files/${fileId}/download`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Error descargando archivo');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert('Error descargando archivo: ' + error.message);
    }
}

async function deleteFile(fileId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este archivo?')) {
        return;
    }

    try {
        await apiRequest(`/files/${fileId}`, { method: 'DELETE' });
        await loadFiles();
    } catch (error) {
        alert('Error eliminando archivo: ' + error.message);
    }
}

// UI Functions
function showLogin() {
    document.getElementById('loginSection').classList.remove('hidden');
    document.getElementById('registerSection').classList.add('hidden');
    document.getElementById('filesSection').style.display = 'none';
}

function showRegister() {
    document.getElementById('loginSection').classList.add('hidden');
    document.getElementById('registerSection').classList.remove('hidden');
    document.getElementById('filesSection').style.display = 'none';
}

function showDashboard() {
    document.getElementById('loginSection').classList.add('hidden');
    document.getElementById('registerSection').classList.add('hidden');
    document.getElementById('filesSection').style.display = 'block';
}

function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    if (tabName === 'upload') {
        document.getElementById('uploadTab').classList.remove('hidden');
        document.getElementById('listTab').classList.add('hidden');
    } else {
        document.getElementById('uploadTab').classList.add('hidden');
        document.getElementById('listTab').classList.remove('hidden');
        loadFiles();
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Event Listeners
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    await login(email, password);
});

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    await register(email, password);
});

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const adminId = document.getElementById('adminSelect').value;
    const description = document.getElementById('description').value;

    if (!fileInput.files.length) {
        showError('uploadError', 'Por favor selecciona un archivo');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('admin_id', adminId);
    if (description) {
        formData.append('description', description);
    }

    await uploadFile(formData);
});

// Initialize
if (authToken) {
    loadUserData().then(() => {
        showDashboard();
    }).catch(() => {
        logout();
    });
} else {
    showLogin();
}
