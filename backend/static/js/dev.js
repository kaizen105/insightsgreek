let currentTab = 'products';

// Helper to get token/user from either storage
function getToken() { return localStorage.getItem('token') || sessionStorage.getItem('token'); }
function getUser() { return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user')); }

// Load page on DOM load
window.addEventListener('DOMContentLoaded', async () => {
    const user = getUser(); // <-- USE HELPER
    
    // Check for user AND correct role
    if (!user || user.role !== 'dev') {
        logout(); // <-- Use your logout function
        return;
    }
    
    document.getElementById('username').textContent = user.username;
    await loadProducts();
    await loadUsers();
    await loadLogs();

    // === FIX FOR PROBLEM 3 (Numbness) ===
    // Keep the server awake by refreshing logs every 60 seconds
    setInterval(loadLogs, 60000); 
});

// Tab switching
function showTab(tabName) {
    currentTab = tabName;
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}Tab`).classList.add('active');
    event.target.classList.add('active');
}

// ========== PRODUCTS ==========

async function loadProducts() {
    try {
        const response = await secureFetch('/api/products');
        const data = await response.json();
        displayProducts(data.products);
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function displayProducts(products) {
    const productsList = document.getElementById('productsList');
    productsList.innerHTML = '';
    
    if (!products || products.length === 0) {
        productsList.innerHTML = '<p>No products found</p>';
        return;
    }
    
    products.forEach(product => {
        const item = document.createElement('div');
        item.className = 'data-item';
        item.innerHTML = `
            <div class="item-content">
                <h4>${product.name}</h4>
                <p><strong>Description:</strong> ${product.description}</p>
                <p><strong>Details:</strong> ${product.details}</p>
            </div>
            <div class="item-actions">
                <button onclick="deleteProduct(${product.id})" class="btn-danger">Delete</button>
            </div>
        `;
        productsList.appendChild(item);
    });
}

function showAddProduct() {
    document.getElementById('addProductForm').style.display = 'block';
}

function cancelAddProduct() {
    document.getElementById('addProductForm').style.display = 'none';
    document.getElementById('productName').value = '';
    document.getElementById('productDesc').value = '';
    document.getElementById('productDetails').value = '';
}

async function addProduct() {
    const name = document.getElementById('productName').value;
    const description = document.getElementById('productDesc').value;
    const details = document.getElementById('productDetails').value;
    
    if (!name || !description) {
        alert('Please fill in required fields');
        return;
    }
    
    try {
        const response = await secureFetch('/api/products', {
            method: 'POST',
            body: JSON.stringify({ name, description, details })
        });
        
        if (response.ok) {
            cancelAddProduct();
            await loadProducts();
        } else {
            alert('Failed to add product');
        }
    } catch (error) {
        console.error('Error adding product:', error);
        alert('Error adding product');
    }
}

async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) {
        return;
    }
    
    try {
        const response = await secureFetch(`/api/products/${productId}`, {
            method: 'DELETE',
        });  
        if (response.ok) {
            await loadProducts();
        } else {
            alert('Failed to delete product');
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        alert('Error deleting product');
    }
}

// ========== USERS ==========

async function loadUsers() {
    try {
        const response = await SecureFetch('/api/users', {
        });
        const data = await response.json();
        displayUsers(data.users);
    } catch (error) {
        console.error('Error loading users:', error);
    }
}
/**
 * This new "secureFetch" function will replace all your 
 * 'fetch' calls. It automatically adds the token and
 * logs the user out if the token is bad.
 */
async function secureFetch(url, options = {}) {
    const token = getToken();

    // 1. Set up the default headers
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };

    // 2. Merge our default headers with any custom headers (like 'POST' method)
    options.headers = { ...defaultHeaders, ...options.headers };

    // 3. Make the request
    const response = await fetch(url, options);

    // 4. THIS IS THE CRITICAL FIX
    // If the server says we're Unauthorized, our token is bad.
    if (response.status === 401) {
        logout(); // Call your existing logout function
        throw new Error('Unauthorized');
    }

    // If it's not a 401, just return the response
    return response;
}
function displayUsers(users) {
    const usersList = document.getElementById('usersList');
    usersList.innerHTML = '';
    
    if (!users || users.length === 0) {
        usersList.innerHTML = '<p>No users found</p>';
        return;
    }
    
    users.forEach(user => {
        const item = document.createElement('div');
        item.className = 'data-item';
        item.innerHTML = `
            <div class="item-content">
                <h4>${user.username}</h4>
                <p><strong>Role:</strong> ${user.role}</p>
                <p><strong>Last Login:</strong> ${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</p>
            </div>
            <div class="item-actions">
                <button onclick="deleteUser(${user.id})" class="btn-danger">Delete</button>
            </div>
        `;
        usersList.appendChild(item);
    });
}

function showAddUser() {
    document.getElementById('addUserForm').style.display = 'block';
}

function cancelAddUser() {
    document.getElementById('addUserForm').style.display = 'none';
    document.getElementById('newUsername').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('newRole').value = 'salesperson';
}

async function addUser() {
    const username = document.getElementById('newUsername').value;
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;
    
    if (!username || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await SecureFetch('/api/users', {
            method: 'POST',
            body: JSON.stringify({ username, password, role })
        });
        
        if (response.ok) {
            cancelAddUser();
            await loadUsers();
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to add user');
        }
    } catch (error) {
        console.error('Error adding user:', error);
        alert('Error adding user');
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        const response = await SecureFetch(`/api/users/${userId}`, {
            method: 'DELETE',
        });
        
        if (response.ok) {
            await loadUsers();
        } else {
            alert('Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error deleting user');
    }
}

// ========== LOGS ==========

async function loadLogs() {
    try {
        const response = await SecureFetch('/api/logs', {
        });      
        const data = await response.json();
        displayLogs(data.logs);
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function displayLogs(logs) {
    const logsList = document.getElementById('logsList');
    logsList.innerHTML = '';
    
    if (!logs || logs.length === 0) {
        logsList.innerHTML = '<p>No activity logs found</p>';
        return;
    }
    
    logs.forEach(log => {
        const item = document.createElement('div');
        item.className = 'log-item';
        item.innerHTML = `
            <div class="log-time">${new Date(log.timestamp).toLocaleString()}</div>
            <div class="log-user">${log.username}</div>
            <div class="log-action">${log.action}</div>
            <div class="log-details">${log.details || ''}</div>
        `;
        logsList.appendChild(item);
    });
}

function filterLogs() {
    const filter = document.getElementById('logFilter').value;
    loadLogs(filter);
}

// Logout
function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}