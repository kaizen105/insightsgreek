let myLeadScoreChart;
let myTrendChart;
let mySentimentChart;

// Helper to get token/user from either storage (matches other pages)
function getToken() { return localStorage.getItem('token') || sessionStorage.getItem('token'); }
function getUser() { return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user')); }
/**
 * This is the missing function.
 * It automatically adds your token and logs you out
 * if the token is bad.
 */
async function secureFetch(url, options = {}) {
    const token = getToken();

    // Set up default headers
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };

    // Merge our default headers with any custom headers
    options.headers = { ...defaultHeaders, ...options.headers };

    const response = await fetch(url, options);

    // This part handles expired tokens
    if (response.status === 401) {
        logout(); // Call your existing logout function
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
    setInterval(loadDashboardData, 30000);
});

// Load all dashboard data
async function loadDashboardData() {
    try {
        const response = await secureFetch('/api/dashboard', {
        });
        
        if (response.status === 401) {
             logout(); 
             return;
        }

        const data = await response.json();
        
        if (response.ok) {
            updateStats(data.stats);
            generateLeadScoreChart(data.stats.leads); // NEW: ML Score Chart
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

// 1. NEW: AI Lead Score Chart (Doughnut)
function generateLeadScoreChart(leads) {
    const ctx = document.getElementById('leadScoreChart').getContext('2d');
    
    // 1. DESTROY THE OLD CHART if it exists
    if (myLeadScoreChart) {
        myLeadScoreChart.destroy();
    }

    // 2. CREATE THE NEW CHART and store it
    myLeadScoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High Quality', 'Medium Quality', 'Low Quality'],
            datasets: [{
                data: [leads.high, leads.medium, leads.low],
                backgroundColor: [
                    '#059669', // Green
                    '#d97706', // Amber
                    '#dc2626'  // Red
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
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

    // 1. DESTROY THE OLD CHART if it exists
    if (myTrendChart) {
        myTrendChart.destroy();
    }

    // 2. CREATE THE NEW CHART and store it
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
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function generateWordCloud(wordData) {
    const canvas = document.getElementById('wordcloud');
    const container = canvas.parentElement;
    
    const dpr = window.devicePixelRatio || 1;
    const width = container.offsetWidth;
    const height = container.clientHeight; // <-- NEW
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    
    WordCloud(canvas, {
        list: wordData,
        gridSize: Math.round(4 * dpr),
        weightFactor: (size) => Math.pow(size, 2.5) * (canvas.width / 500) * dpr * 2,
        fontFamily: 'Segoe UI, sans-serif',
        color: function() {
            // Better color palette
            const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a'];
            return colors[Math.floor(Math.random() * colors.length)];
        },
        rotateRatio: 0.3,
        backgroundColor: 'transparent',
        minSize: 12 * dpr
    });
}
// 4. NEW: Sentiment Chart (Pie)
function generateSentimentChart(sentiment) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    // Destroy the old chart if it exists
    if (mySentimentChart) {
        mySentimentChart.destroy();
    }

    // Create the new chart
    mySentimentChart = new Chart(ctx, {
        type: 'pie', // Pie or Doughnut works well
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [
                    sentiment.positive, 
                    sentiment.neutral, 
                    sentiment.negative
                ],
                backgroundColor: [
                    '#059669', // Positive (Green)
                    '#6b7280', // Neutral (Gray)
                    '#dc2626'  // Negative (Red)
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: 'Customer Feedback Sentiment' }
            }
        }
    });
}
// Display recent list
function displayRecentFeedbacks(feedbacks) {
    const list = document.getElementById('feedbackList');
    list.innerHTML = '';
    feedbacks.forEach(f => {
        const div = document.createElement('div');
        div.className = 'feedback-item';
        // Show ML score if available
        const scoreBadge = f.lead_label ? 
            `<span style="float:right; font-size:0.8em; padding: 2px 8px; border-radius:10px; background:${f.lead_label === 'High' ? '#dcfce7; color:#166534' : '#f3f4f6; color:#374151'}">${f.lead_label} (${(f.lead_score*100).toFixed(0)}%)</span>` 
            : '';
            
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

// Download CSV Report
async function downloadReport() {
    try {
        const response = await secureFetch('/api/download-report', {
        });
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

function logout() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/login';
}