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

// === SHARED SUBMISSION FUNCTION (UPDATED) ===
async function submitData(type) {
    // 1. Determine which elements to use
    const isLead = (type === 'lead');
    const inputId = isLead ? 'leadText' : 'feedbackText';
    const text = document.getElementById(inputId).value;

    if (!text.trim()) { 
        showStatus('Please enter some text first', 'error'); 
        return; 
    }

    // 2. THIS IS THE NEW LOGIC
    // Set the correct API endpoint and result elements based on type
    let apiUrl, resultSectionId, labelId, scoreId;

    if (isLead) {
        apiUrl = '/api/submit-lead'; // <-- Calls the Lead model
        resultSectionId = 'aiResultLead';
        labelId = 'aiLabelLead';
        scoreId = 'aiScoreLead';
    } else {
        apiUrl = '/api/analyze-feedback'; // <-- Calls the Feedback (TextBlob) model
        resultSectionId = 'aiResultFeedback';
        labelId = 'aiLabelFeedback';
        scoreId = 'aiScoreFeedback';
    }
    // ------------------------------------

    try {
        // 3. Call the correct API URL
        const response = await secureFetch(apiUrl, {
            method: 'POST',
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();

        if (response.ok) {
            showStatus(`${isLead ? 'Lead' : 'Feedback'} submitted successfully!`, 'success');
            document.getElementById(inputId).value = ''; // Clear input
            
            // 4. Handle the two different types of results
            let resultData;
            if (isLead && data.ml_result) {
                resultData = data.ml_result; // From the ML model
            } else if (!isLead && data.sentiment_result) {
                resultData = data.sentiment_result; // From the Sentiment model
            }

            // 5. Display the result
            if (resultData) {
                const labelEl = document.getElementById(labelId);
                let scoreText;
                let labelColor;

                if (isLead) {
                    // This is a Lead (0 to 1 score)
                    scoreText = (resultData.score * 100).toFixed(1);
                    if (resultData.label === 'High') labelColor = '#059669';
                    else if (resultData.label === 'Medium') labelColor = '#d97706';
                    else labelColor = '#dc2626';
                } else {
                    // This is Feedback (-1 to 1 score)
                    scoreText = (resultData.score*100); // Show sentiment score
                    if (resultData.label === 'Positive') labelColor = '#059669';
                    else if (resultData.label === 'Neutral') labelColor = '#6b7280';
                    else labelColor = '#dc2626';
                }

                document.getElementById(scoreId).textContent = scoreText;
                labelEl.textContent = resultData.label;
                labelEl.style.color = labelColor;
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

// === CHATBOT LOGIC (ENHANCED WITH LEAD VALIDATION) ===
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    
    // Add user message to UI
    addMessage(msg, 'user');
    input.value = '';
    
    // Get context from active tab
    let context = '';
    let contextType = 'lead'; // Default to lead
   
    const feedbackTab = document.getElementById('feedbackTab');
    if (feedbackTab && feedbackTab.style.display === 'block') {
        // We are in the feedback tab
        context = document.getElementById('feedbackText').value;
        contextType = 'feedback';
    } else {
        // We are in the lead tab
        context = document.getElementById('leadText').value;
        contextType = 'lead';
    }
    
    try {
        // Call the chat API
        const response = await secureFetch('/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: msg,
                context: context,
                context_type: contextType
            })
        });
       
        const data = await response.json();
       
        if (response.ok) {
            // Check if response contains leads
            if (data.reply && (data.reply.includes('Prospect:') || data.reply.includes('- Lead'))) {
                // Call validation endpoint
                const valResponse = await secureFetch('/api/validate-leads', {
                    method: 'POST',
                    body: JSON.stringify({
                        leads_text: data.reply
                    })
                });
                
                const valData = await valResponse.json();
                
                if (valResponse.ok) {
                    // Format scored leads for display with improved styling
                    let scoredReply = '<div style="margin-bottom: 15px;">';
                    
                    // 1. Show the original leads with proper formatting
                    scoredReply += '<strong>💼 Generated Leads:</strong><br><br>';
                    scoredReply += data.reply.replace(/\n/g, '<br>').replace(/- Lead \d+:/g, '<br><strong>$&</strong>');
                    
                    // 2. Add a divider
                    scoredReply += '<br><hr style="margin: 15px 0; border: 1px solid #e5e7eb;"><br>';
                    
                    // 3. Show AI quality scores in a clean format
                    scoredReply += '<strong>🎯 AI Quality Scores:</strong><br><br>';
                    scoredReply += '<ul style="list-style: none; padding: 0;">';
                    
                    valData.validated_leads.forEach((lead, index) => {
                        const colorClass = lead.label === 'High' ? '#059669' : 
                                         lead.label === 'Medium' ? '#d97706' : '#dc2626';
                        const emoji = lead.label === 'High' ? '🔥' : lead.label === 'Medium' ? '⚡' : '❄️';
                        
                        scoredReply += `
                            <li style="margin-bottom: 12px; padding: 10px; background: #f9fafb; border-left: 4px solid ${colorClass}; border-radius: 4px;">
                                ${emoji} <strong style="color: ${colorClass};">${lead.label}</strong> 
                                (Score: ${(lead.score * 100).toFixed(0)}%) 
                                <br>
                                <span style="font-size: 0.9em; color: #6b7280;">${lead.lead_snippet}</span>
                                <br>
                                <em style="font-size: 0.85em; color: #9ca3af;">💡 ${lead.tip}</em>
                            </li>
                        `;
                    });
                    
                    scoredReply += '</ul><br>';
                    scoredReply += `<strong>📊 Summary:</strong> ${valData.recommendation}</div>`;
                    
                    addMessage(scoredReply, 'bot');
                } else {
                    // Fallback: Just show raw reply if validation fails
                    addMessage(data.reply, 'bot');
                }
            } else {
                // Non-lead response: Show raw
                addMessage(data.reply, 'bot');
            }
        } else {
            addMessage("Error: " + (data.error || "AI is offline."), 'bot');
        }
    } catch (error) {
        // This will now only catch real network errors
        addMessage("Connection error.", 'bot');
    }
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    
    // Basic markdown-like replacement for bolding
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // If the text contains HTML tags (like <ul>, <li>, <br>, <div>), 
    // we trust it (since we generated it) and set innerHTML directly.
    if (text.includes('<') && text.includes('>')) {
        div.innerHTML = formattedText; 
    } else {
        // Otherwise, treat newlines as breaks for normal text
        div.innerHTML = formattedText.replace(/\n/g, '<br>');
    }

    document.getElementById('chatMessages').appendChild(div);
    document.getElementById('chatMessages').scrollTop = 9999; // Auto-scroll to bottom
}