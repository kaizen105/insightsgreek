let myLeadScoreChart;
let myTrendChart;
let mySentimentChart;

// Helper to get token/user from either storage
function getToken() { return localStorage.getItem('token') || sessionStorage.getItem('token'); }
function getUser() { return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user')); }

/**
 * This function automatically adds your token and logs you out
 * if the token is bad.
 */
async function secureFetch(url, options = {}) {
    const token = getToken();
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
    options.headers = { ...defaultHeaders, ...options.headers };
    const response = await fetch(url, options);

    if (response.status === 401) {
        logout(); 
        throw new Error('Unauthorized');
    }
    return response;
}

// Load dashboard on page load
window.addEventListener('DOMContentLoaded', async () => {
    const user = getUser();
    if (!user || user.role !== 'manager') {
        window.location.href = '/login';
        return;
    }
    
    document.getElementById('username').textContent = user.username;
    await loadDashboardData();
    // Keep-alive and auto-refresh
    setInterval(loadDashboardData, 30000); 
});

// Load all dashboard data
async function loadDashboardData() {
    try {
        const response = await secureFetch('/api/dashboard');
        const data = await response.json();
        
        if (response.ok) {
            updateStats(data.stats);
            generateLeadScoreChart(data.stats.leads);
            generateTrendChart(data.trends);
            generateWordCloud(data.wordcloud_data);
            displayRecentFeedbacks(data.recent);
            generateSentimentChart(data.sentiment);
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Update statistics text
function updateStats(stats) {
    document.getElementById('totalFeedbacks').textContent = stats.total || 0;
    document.getElementById('weekFeedbacks').textContent = stats.week || 0;
    document.getElementById('activeSales').textContent = stats.active_sales || 0;
}

// 1. AI Lead Score Chart
function generateLeadScoreChart(leads) {
    const ctx = document.getElementById('leadScoreChart').getContext('2d');
    if (myLeadScoreChart) {
        myLeadScoreChart.destroy();
    }
    myLeadScoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High Quality', 'Medium Quality', 'Low Quality'],
            datasets: [{
                data: [leads.high, leads.medium, leads.low],
                backgroundColor: ['#059669', '#d97706', '#dc2626'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeOutQuart' },
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: 'AI Lead Quality Distribution' }
            }
        }
    });
}

// 2. Trend Chart (Line)
function generateTrendChart(trends) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (myTrendChart) {
        myTrendChart.destroy();
    }
    myTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trends.labels,
            datasets: [{
                label: 'Daily Feedbacks',
                data: trends.data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeOutQuart' },
            plugins: { 
                legend: { display: false },
            },
            scales: { 
                y: { 
                    beginAtZero: true, 
                    ticks: { precision: 0 },
                    title: { display: true, text: 'Feedback Count' }
                },
                x: {
                    title: { display: true, text: 'Date (MM/DD)' }
                }
            }
        }
    });
}

// 3. Word Cloud
function generateWordCloud(wordData) {
    const canvas = document.getElementById('wordcloud');
    const container = canvas.parentElement; // This is now .dashboard-card
    if (!container) return; 
    
    const dpr = window.devicePixelRatio || 1;
    // Get width from container, use fixed CSS height
    const width = container.clientWidth; 
    const height = 400; // Matches .chart-canvas-large height
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    WordCloud(canvas, {
        list: wordData,
        gridSize: Math.round(16 * dpr),
        weightFactor: (size) => size * 8 * dpr,
        fontFamily: 'Segoe UI, sans-serif',
        color: () => {
            const shades = ['#8B5CF6', '#A78BFA', '#C4B5FD', '#DDA0DD', '#E879F9'];
            return shades[Math.floor(Math.random() * shades.length)];
        },
        rotateRatio: 0.2,
        backgroundColor: 'transparent',
        shape: 'rectangular'
    });
}

// 4. Sentiment Chart (Pie)
function generateSentimentChart(sentiment) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    if (mySentimentChart) {
        mySentimentChart.destroy();
    }
    mySentimentChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [sentiment.positive, sentiment.neutral, sentiment.negative],
                backgroundColor: ['#059669', '#6b7280', '#dc2626'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeOutQuart' },
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: 'Customer Feedback Sentiment' }
            }
        }
    });
}

// 5. Display recent list
function displayRecentFeedbacks(feedbacks) {
    const list = document.getElementById('feedbackList');
    list.innerHTML = ''; // Clear old list
    feedbacks.forEach(f => {
        const div = document.createElement('div');
        div.className = 'feedback-item';
        
        let scoreBadge = ''; 
        if (f.lead_label) { 
             scoreBadge = `<span style="float:right; font-size:0.8em; padding: 2px 8px; border-radius:10px; background:${f.lead_label === 'High' ? '#dcfce7; color:#166534' : '#f3f4f6; color:#374151'}">${f.lead_label} (${(f.lead_score*100).toFixed(0)}%)</span>`;
        } else if (f.sentiment_label) {
            scoreBadge = `<span style="float:right; font-size:0.8em; padding: 2px 8px; border-radius:10px; background:${f.sentiment_label === 'Positive' ? '#dcfce7; color:#166534' : (f.sentiment_label === 'Negative' ? '#fee2e2; color:#991b1b' : '#f3f4f6; color:#374151')}">${f.sentiment_label}</span>`;
        }
            
        div.innerHTML = `
            <div class="feedback-header">
                <strong>${f.salesperson}</strong>
                ${scoreBadge}
                <span>${new Date(f.timestamp).toLocaleDateString()}</span>
            </div>
            <p>${f.text}</p>
        `;
        list.appendChild(div);
    });
}

// 6. Download CSV Report
async function downloadReport() {
    try {
        const response = await secureFetch('/api/download-report');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sales_report_${new Date().toISOString().slice(0,10)}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        }
    } catch (error) {
        alert("Failed to download report.");
    }
}

// 7. Logout
function logout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/login';
}