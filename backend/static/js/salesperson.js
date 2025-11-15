// Helper to get token
function getToken() { return localStorage.getItem('token') || sessionStorage.getItem('token'); }

// Load initial data
window.addEventListener('DOMContentLoaded', async () => {
    const user = JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user'));
    if (!user) { window.location.href = '/login'; return; }
    document.getElementById('username').textContent = user.username;
    await loadProducts();
});
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
        // Log the user out and redirect to login
        logout(); 
        // Throw an error to stop the rest of the code from running
        throw new Error('Unauthorized');
    }

    // If it's not a 401, just return the response
    return response;
}
// === TAB MANAGEMENT ===
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

    // Show selected tab
    if (tabName === 'feedback') {
        document.getElementById('feedbackTab').style.display = 'block';
        document.querySelector('button[onclick="showTab(\'feedback\')"]').classList.add('active');
    } else if (tabName === 'leads') {
        document.getElementById('leadsTab').style.display = 'block';
        document.querySelector('button[onclick="showTab(\'leads\')"]').classList.add('active');
    }
}

// === SHARED SUBMISSION FUNCTION ===
async function submitData(type) {
    // Determine which elements to use based on type ('feedback' or 'lead')
    const isLead = type === 'lead';
    const inputId = isLead ? 'leadText' : 'feedbackText';
    const resultSectionId = isLead ? 'aiResultLead' : 'aiResultFeedback';
    const labelId = isLead ? 'aiLabelLead' : 'aiLabelFeedback';
    const scoreId = isLead ? 'aiScoreLead' : 'aiScoreFeedback';

    const text = document.getElementById(inputId).value;
    if (!text.trim()) { showStatus('Please enter some text first', 'error'); return; }

    try {
        // We use the same API endpoint for now, as the model handles both text types well
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();

        if (response.ok) {
            showStatus(`${isLead ? 'Lead' : 'Feedback'} submitted successfully!`, 'success');
            document.getElementById(inputId).value = ''; // Clear input
            
            // Show AI Result in the correct tab
            if (data.ml_result) {
                const labelEl = document.getElementById(labelId);
                document.getElementById(scoreId).textContent = (data.ml_result.score * 100).toFixed(1);
                labelEl.textContent = data.ml_result.label;

                // Color coding
                if (data.ml_result.label === 'High') labelEl.style.color = '#059669';
                else if (data.ml_result.label === 'Medium') labelEl.style.color = '#d97706';
                else labelEl.style.color = '#dc2626';

                document.getElementById(resultSectionId).style.display = 'block';
            }
        } else {
            showStatus(data.error || 'Submission failed', 'error');
        }
    } catch (error) {
        showStatus('Error submitting data', 'error');
    }
}

// === GRAMMAR CHECKER (Now handles both inputs) ===
async function checkGrammar(inputId) {
    const text = document.getElementById(inputId).value;
    // Determine which output box to use
    const outputId = inputId === 'leadText' ? 'correctedTextLead' : 'correctedText';
    const outputDiv = document.getElementById(outputId);

    if (!text.trim()) { showStatus('Enter text to check', 'error'); return; }

    outputDiv.style.display = 'block';
    outputDiv.innerHTML = 'Checking...';

    try {
        const res = await secureFetch('/api/check-grammar', {
            method: 'POST',
            body: JSON.stringify({ text: text })
        });
        const data = await res.json();
        if (res.ok) {
            // Add a "Use This" button that knows which input to update
            outputDiv.innerHTML = `
                <strong>Suggestion:</strong><br>${data.corrected_text}
                <br><button onclick="applyCorrection('${inputId}', \`${data.corrected_text.replace(/`/g, "\\`")}\`)" class="btn-secondary" style="margin-top:10px; padding: 5px 10px; font-size: 12px;">Apply</button>
            `;
        } else { outputDiv.textContent = 'Grammar check failed'; }
    } catch (e) { outputDiv.textContent = 'Error checking grammar'; }
}

function applyCorrection(inputId, correctedText) {
    document.getElementById(inputId).value = correctedText;
    // Hide the correction box after applying
    const outputId = inputId === 'leadText' ? 'correctedTextLead' : 'correctedText';
    document.getElementById(outputId).style.display = 'none';
}

// === UTILITIES ===
function resetForm(type) {
    if (type === 'feedback') {
        document.getElementById('feedbackText').value = '';
        document.getElementById('aiResultFeedback').style.display = 'none';
        document.getElementById('correctedText').style.display = 'none';
    } else {
        document.getElementById('leadText').value = '';
        document.getElementById('aiResultLead').style.display = 'none';
        document.getElementById('correctedTextLead').style.display = 'none';
    }
}

async function loadProducts() {
    try {
        const res = await secureFetch('/api/products');
        const data = await res.json();
        const list = document.getElementById('productList');
        list.innerHTML = '';
        (data.products || []).forEach(p => {
            list.innerHTML += `<div class="product-card"><h5>${p.name}</h5><p>${p.description}</p><small>${p.details}</small></div>`;
        });
    } catch (e) { console.error(e); }
}

function showStatus(msg, type) {
    const el = document.getElementById('statusMsg');
    el.textContent = msg;
    el.className = `status-msg ${type}`;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
}

function logout() {
    localStorage.clear(); sessionStorage.clear();
    window.location.href = '/login';
}
// ... existing code ...

// === CHATBOT LOGIC ===
function toggleChat() {
    const body = document.getElementById('chatBody');
    const toggle = document.getElementById('chatToggle');
    if (body.style.display === 'none') {
        body.style.display = 'flex';
        toggle.textContent = '▼';
    } else {
        body.style.display = 'none';
        toggle.textContent = '▲';
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    // Add user message to UI
    addMessage(msg, 'user');
    input.value = '';

    // Get current context (whichever tab is active)
    const activeTab = document.querySelector('.tab-content.active').id;
    const contextId = activeTab === 'feedbackTab' ? 'feedbackText' : 'leadText';
    const context = document.getElementById(contextId).value;

    try {
        const response = await secureFetch('/api/feedback', {
            method: 'POST',
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();
        if (response.ok) {
            addMessage(data.reply, 'bot');
        } else {
            addMessage("Error: " + (data.error || "AI is offline."), 'bot');
        }
    } catch (error) {
        addMessage("Connection error.", 'bot');
    }
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    // Simple markdown-like bolding for AI responses
    div.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); 
    document.getElementById('chatMessages').appendChild(div);
    document.getElementById('chatMessages').scrollTop = 9999; // Auto-scroll to bottom
}