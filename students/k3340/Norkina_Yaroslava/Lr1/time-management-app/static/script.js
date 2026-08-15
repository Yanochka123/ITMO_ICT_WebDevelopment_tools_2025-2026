let token = localStorage.getItem('token');
let currentUser = null;

// Check if user is logged in
if (token) {
    loadTasks();
    loadStats();
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('user-info').style.display = 'block';
}

// Login function
async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('user-info').style.display = 'block';
            loadTasks();
            loadStats();
        } else {
            alert('Login failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Register function
async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        if (response.ok) {
            alert('Registration successful! Please login.');
            showLogin();
        } else {
            const error = await response.json();
            alert('Registration failed: ' + error.detail);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Show register form
function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

// Show login form
function showLogin() {
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
}

// Logout
function logout() {
    localStorage.removeItem('token');
    token = null;
    document.getElementById('user-info').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('tasks-container').innerHTML = '';
}

// Load tasks
async function loadTasks() {
    try {
        const response = await fetch('/tasks/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const tasks = await response.json();
            displayTasks(tasks);
        } else if (response.status === 401) {
            logout();
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/tasks/stats', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('total-tasks').textContent = stats.total;
            document.getElementById('completed-tasks').textContent = stats.completed;
            document.getElementById('pending-tasks').textContent = stats.pending;
            document.getElementById('due-today').textContent = stats.due_today;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Display tasks
function displayTasks(tasks) {
    const container = document.getElementById('tasks-container');
    container.innerHTML = '';
    
    tasks.sort((a, b) => b.priority - a.priority);
    
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item ${task.status === 'completed' ? 'completed' : ''}`;
        
        const dueDate = task.due_date ? new Date(task.due_date).toLocaleString() : 'No due date';
        
        taskElement.innerHTML = `
            <div class="task-info">
                <h3>${task.title}</h3>
                <p>${task.description || 'No description'}</p>
                <small>Priority: ${task.priority} | Status: ${task.status} | Due: ${dueDate}</small>
                ${task.time_spent > 0 ? `<small>Time spent: ${task.time_spent.toFixed(1)} hours</small>` : ''}
            </div>
            <div class="task-actions">
                ${task.status !== 'completed' ? 
                    `<button class="complete-btn" onclick="completeTask(${task.id})">Complete</button>` : 
                    ''}
                <button class="delete-btn" onclick="deleteTask(${task.id})">Delete</button>
            </div>
        `;
        
        container.appendChild(taskElement);
    });
}

// Add task
document.getElementById('task-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-description').value;
    const priority = parseInt(document.getElementById('task-priority').value);
    const due_date = document.getElementById('task-due-date').value;
    
    try {
        const response = await fetch('/tasks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                title,
                description,
                priority,
                due_date: due_date || null
            })
        });
        
        if (response.ok) {
            this.reset();
            loadTasks();
            loadStats();
        } else if (response.status === 401) {
            logout();
        } else {
            alert('Failed to add task');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Complete task
async function completeTask(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ status: 'completed' })
        });
        
        if (response.ok) {
            loadTasks();
            loadStats();
        }
    } catch (error) {
        console.error('Error completing task:', error);
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadTasks();
            loadStats();
        }
    } catch (error) {
        console.error('Error deleting task:', error);
    }
}