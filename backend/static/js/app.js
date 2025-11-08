// SHARED AUTH & UTILITY JS

// --- LOGIN LOGIC ---
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerText;
        btn.innerText = 'Logging in...'; btn.disabled = true;

        const errorMsg = document.getElementById('errorMsg');
        if (errorMsg) errorMsg.style.display = 'none';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    role: document.getElementById('role').value,
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                })
            });
            const data = await response.json();

            if (response.ok) {
                // Save to BOTH for maximum compatibility across your app
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                sessionStorage.setItem('token', data.token);
                sessionStorage.setItem('user', JSON.stringify(data.user));

                // Redirect based on role
                if (data.user.role === 'salesperson') window.location.href = '/salesperson';
                else if (data.user.role === 'manager') window.location.href = '/manager';
                else if (data.user.role === 'dev') window.location.href = '/dev';
            } else {
                throw new Error(data.error || 'Login failed');
            }
        } catch (error) {
            if (errorMsg) {
                errorMsg.textContent = error.message || 'Connection error';
                errorMsg.style.display = 'block';
            }
            btn.innerText = originalText; btn.disabled = false;
        }
    });
}

// --- REGISTER LOGIC ---
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerText;
        btn.innerText = 'Creating Account...'; btn.disabled = true;

        const errorMsg = document.getElementById('errorMsg');
        if (errorMsg) errorMsg.style.display = 'none';

        try {
            // Log to console to verify it's running
            console.log("Attempting registration...");
            
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    role: document.getElementById('role').value,
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                })
            });
            const data = await response.json();

            if (response.ok) {
                console.log("Registration success!");
                btn.innerText = 'Success! Redirecting...';
                // Optional: change button color to green for feedback
                // btn.style.background = '#10b981'; 
                setTimeout(() => window.location.href = '/login', 1500);
            } else {
                throw new Error(data.error || 'Registration failed');
            }
        } catch (error) {
            console.error("Registration error:", error);
            if (errorMsg) {
                errorMsg.textContent = error.message || 'Connection error';
                errorMsg.style.display = 'block';
            }
            btn.innerText = originalText; btn.disabled = false;
        }
    });
}

// --- GLOBAL LOGOUT ---
function logout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/';
}