let myLeadScoreChart;
let myTrendChart;
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

// 3. Word Cloud (OPTIMIZED & FIXED)
function generateWordCloud(wordData) {
    const canvas = document.getElementById('wordcloud');
    const container = canvas.parentElement;
    
    // Handle empty data
    if (!wordData || wordData.length === 0) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = '16px Segoe UI';
        ctx.fillStyle = '#999';
        ctx.textAlign = 'center';
        ctx.fillText('No keyword data available', canvas.width / 2, canvas.height / 2);
        return;
    }
    
    // Get device pixel ratio for sharp rendering on retina displays
    const dpr = window.devicePixelRatio || 1;
    
    // Get actual display dimensions
    const displayWidth = container.offsetWidth;
    const displayHeight = 400;

    // Set internal canvas resolution (scaled up for sharpness)
    canvas.width = displayWidth * dpr;
    canvas.height = displayHeight * dpr;

    // Set CSS size to match display dimensions
    canvas.style.width = `${displayWidth}px`;
    canvas.style.height = `${displayHeight}px`;

    // Clear previous rendering
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Sort and limit words for better display
    const sortedWords = [...wordData].sort((a, b) => b[1] - a[1]).slice(0, 50);
    
    // Find max weight for normalization
    const maxWeight = Math.max(...sortedWords.map(w => w[1]));
    
    // Generate word cloud with optimized settings
    WordCloud(canvas, {
        list: sortedWords,
        gridSize: Math.round(12 * dpr),
        weightFactor: function(size) {
            // Normalize and scale appropriately
            const normalized = size / maxWeight;
            const baseSize = displayWidth / 25; // Responsive base size
            return normalized * baseSize * dpr;
        },
        fontFamily: 'Segoe UI, Tahoma, sans-serif',
        fontWeight: '600',
        color: function() {
            // Vibrant color palette matching your theme
            const colors = [
                '#667eea', // Primary purple
                '#764ba2', // Deep purple
                '#f093fb', // Pink
                '#4facfe', // Blue
                '#43e97b', // Green
                '#fa709a', // Rose
                '#feca57', // Yellow
                '#48dbfb'  // Cyan
            ];
            return colors[Math.floor(Math.random() * colors.length)];
        },
        rotateRatio: 0.5,
        minRotation: -Math.PI / 4,
        maxRotation: Math.PI / 4,
        rotationSteps: 2,
        backgroundColor: 'transparent',
        drawOutOfBound: false,
        shrinkToFit: true,
        minSize: 10 * dpr,
        shuffle: true,
        wait: 0,
        abortThreshold: 0,
        abort: function() {
            return false;
        }
    });
}
// Display recent list (FIXED VERSION)
function displayRecentFeedbacks(feedbacks) {
    const list = document.getElementById('feedbackList');
    list.innerHTML = ''; // Clear old list
    
    feedbacks.forEach(f => {
        const div = document.createElement('div');
        div.className = 'feedback-item';
        
        let statusTag = '';
        let scoreBadge = '';

        // 1. Check the 'status' to decide what to show
        if (f.status === 'lead') {
            // --- This is a LEAD ---
            statusTag = `<span class="status-tag lead">LEAD</span>`;
            
            // Use the lead_label and lead_score
            if (f.lead_label) {
                let scorePercent = (f.lead_score * 100).toFixed(0);
                let bgColor = f.lead_label === 'High' ? '#dcfce7' : '#f3f4f6';
                let fgColor = f.lead_label === 'High' ? '#166534' : '#374151';
                
                scoreBadge = `<span class="score-badge" style="background:${bgColor}; color:${fgColor}">
                                ${f.lead_label} (${scorePercent}%)
                              </span>`;
            }

        } else if (f.status === 'feedback') {
            // --- This is FEEDBACK ---
            statusTag = `<span class="status-tag feedback">FEEDBACK</span>`;

            // Use the sentiment_label and sentiment_score
            if (f.sentiment_label) {
                // 2. Convert sentiment score (-1 to 1) to percentage (0 to 100)
                let scorePercent = ((f.sentiment_score + 1) / 2 * 100).toFixed(0);
                
                let bgColor = '#f3f4f6'; // Neutral
                let fgColor = '#374151';
                if (f.sentiment_label === 'Positive') {
                    bgColor = '#dcfce7'; fgColor = '#166534';
                } else if (f.sentiment_label === 'Negative') {
                    bgColor = '#fee2e2'; fgColor = '#991b1b';
                }

                scoreBadge = `<span class="score-badge" style="background:${bgColor}; color:${fgColor}">
                                ${f.sentiment_label} (${scorePercent}%)
                              </span>`;
            }
        }
            
        // 3. Build the final HTML with the new tags
        div.innerHTML = `
            <div class="feedback-header">
                <strong>${f.salesperson}</strong>
                <div>
                    ${statusTag}    ${scoreBadge}   </div>
            </div>
            <p>${f.text}</p>
            <span class="feedback-timestamp">${new Date(f.timestamp).toLocaleDateString()}</span>
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