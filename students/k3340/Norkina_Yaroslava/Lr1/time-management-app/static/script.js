// static/script.js
document.addEventListener('DOMContentLoaded', function () {
    // Загрузка статистики
    loadStats();

    // Загрузка списка задач
    loadTasks();

    // Обновление данных каждые 30 секунд
    setInterval(() => {
        loadStats();
        loadTasks();
    }, 30000);
});

async function loadStats() {
    try {
        const response = await fetch('/tasks/stats');
        if (!response.ok) throw new Error('Failed to load stats');
        
        const stats = await response.json();

        document.getElementById('totalTasks').textContent = stats.total_tasks || 0;
        document.getElementById('completedTasks').textContent = stats.completed_tasks || 0;
        document.getElementById('inProgressTasks').textContent = stats.in_progress_tasks || 0;
        document.getElementById('pendingTasks').textContent = stats.pending_tasks || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
        document.querySelector('.stats-grid').innerHTML = '<p class="error">Ошибка загрузки статистики</p>';
    }
}

async function loadTasks() {
    try {
        const response = await fetch('/tasks/?limit=10');
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
        document.getElementById('tasksList').innerHTML = '<p class="error">Ошибка загрузки задач</p>';
    }
}

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