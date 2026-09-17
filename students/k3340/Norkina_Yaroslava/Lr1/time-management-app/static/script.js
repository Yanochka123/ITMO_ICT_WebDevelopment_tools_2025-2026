// static/script.js

// ===== Утилиты для работы с токеном =====
function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function clearToken() {
    localStorage.removeItem('access_token');
}

// ===== Обёртка над fetch с автоматическим добавлением токена =====
async function authFetch(url, options = {}) {
    const token = getToken();
    const headers = { ...(options.headers || {}) };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        clearToken();
        showLogin();
        throw new Error('Unauthorized');
    }
    return response;
}

// ===== Показ/скрытие формы логина =====
function showLogin() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('appContent').style.display = 'none';
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = 'none';
}

function showApp() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('appContent').style.display = 'block';
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = 'inline-block';
}

// ===== Логин =====
async function login(email, password) {
    const body = new URLSearchParams();
    body.append('username', email);
    body.append('password', password);

    const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
    });

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Ошибка входа');
    }

    const data = await response.json();
    setToken(data.access_token || data.token);
}

// ===== Инициализация =====
document.addEventListener('DOMContentLoaded', function () {
    console.log('=== script.js загружен ===');

    const loginForm = document.getElementById('loginForm');
    const loginError = document.getElementById('loginError');
    const logoutBtn = document.getElementById('logoutBtn');

    if (!loginForm) {
        console.error('❌ loginForm не найден в DOM');
        return;
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('=== submit перехвачен ===');
        loginError.style.display = 'none';

        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        try {
            await login(email, password);
            console.log('=== логин успешен ===');
            showApp();
            loadStats();
            loadTasks();
            setInterval(() => {
                loadStats();
                loadTasks();
            }, 30000);
        } catch (err) {
            console.error('Ошибка логина:', err);
            loginError.textContent = err.message;
            loginError.style.display = 'block';
        }
    });

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            clearToken();
            showLogin();
        });
    }

    // Если токен уже есть — сразу показываем приложение
    if (getToken()) {
        showApp();
        loadStats();
        loadTasks();
        setInterval(() => {
            loadStats();
            loadTasks();
        }, 30000);
    } else {
        showLogin();
    }
});

// ===== Загрузка статистики =====
async function loadStats() {
    try {
        const response = await authFetch('/tasks/stats');
        if (!response.ok) throw new Error('Failed to load stats');

        const stats = await response.json();
        document.getElementById('totalTasks').textContent = stats.total_tasks || 0;
        document.getElementById('completedTasks').textContent = stats.completed_tasks || 0;
        document.getElementById('inProgressTasks').textContent = stats.in_progress_tasks || 0;
        document.getElementById('pendingTasks').textContent = stats.pending_tasks || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
        if (error.message !== 'Unauthorized') {
            document.querySelector('.stats-grid').innerHTML =
                '<p class="error">Ошибка загрузки статистики</p>';
        }
    }
}

// ===== Загрузка задач =====
async function loadTasks() {
    try {
        const response = await authFetch('/tasks/?limit=10');
        if (!response.ok) throw new Error('Failed to load tasks');

        const tasks = await response.json();
        const tasksList = document.getElementById('tasksList');

        if (tasks.length === 0) {
            tasksList.innerHTML = '<p class="loading">Нет задач</p>';
            return;
        }

        tasksList.innerHTML = tasks.map(task => `
            <div class="task-item">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-meta">
                    <span class="task-status status-${task.status}">${getStatusLabel(task.status)}</span>
                    <span class="task-priority priority-${task.priority}">${getPriorityLabel(task.priority)}</span>
                    ${task.due_date ? `<span class="task-due">📅 ${formatDate(task.due_date)}</span>` : ''}
                    ${task.progress > 0 ? `<span class="task-progress">${Math.round(task.progress)}%</span>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tasks:', error);
        if (error.message !== 'Unauthorized') {
            document.getElementById('tasksList').innerHTML =
                '<p class="error">Ошибка загрузки задач</p>';
        }
    }
}

// ===== Вспомогательные функции =====
function getStatusLabel(status) {
    const labels = {
        'pending': 'Ожидает',
        'in_progress': 'В процессе',
        'completed': 'Выполнена',
        'cancelled': 'Отменена',
        'overdue': 'Просрочена'
    };
    return labels[status] || status;
}

function getPriorityLabel(priority) {
    const labels = {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий',
        'urgent': 'Срочный',
        'critical': 'Критический'
    };
    return labels[priority] || priority;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}