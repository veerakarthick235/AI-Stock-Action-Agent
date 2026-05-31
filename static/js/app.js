/**
 * Antigravity StockAI SaaS — Frontend Engine
 * Handles State Management, Authentication, Tab Navigation, Stripe Sim, and Chart.js Integrations.
 */

// --- Global Application State ---
let currentUser = null;
let currentAuthMode = "LOGIN"; // or "REGISTER"
let activeCheckoutTier = null;

// Chart instances (to avoid memory leaks on updates)
let sentimentChart = null;
let apiUsageTrendChart = null;
let quotaDonutChart = null;

// --- DOM Bootstrapper ---
document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    checkSessionStatus();
    setupInputFormatters();
});

// --- Tab Navigation Setup ---
function initTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    // 1. Update navigation active state
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
        if (item.getAttribute("data-tab") === tabId) {
            item.classList.add("active");
        }
    });

    // 2. Toggle active tab panel
    document.querySelectorAll(".tab-content").forEach(panel => {
        panel.classList.remove("active");
    });
    const targetPanel = document.getElementById(`tab-${tabId}`);
    if (targetPanel) {
        targetPanel.classList.add("active");
    }

    // 3. Update topbar titles
    const pageTitle = document.getElementById("pageTitle");
    const pageSubTitle = document.getElementById("pageSubTitle");
    
    if (tabId === "dashboard") {
        pageTitle.textContent = "SaaS AI Terminal";
        pageSubTitle.textContent = "Real-time deep learning sentiment decisions";
    } else if (tabId === "api") {
        pageTitle.textContent = "Developer API Gateway";
        pageSubTitle.textContent = "Integrate FinBERT sentiment checks directly into your workflows";
        if (currentUser) {
            loadStats();
        }
    } else if (tabId === "billing") {
        pageTitle.textContent = "Subscription Dashboard";
        pageSubTitle.textContent = "Manage plans, upgrades, and monthly API transactions";
        if (currentUser) {
            loadStats();
        }
    }
}

// --- Session and Auth Check ---
function checkSessionStatus() {
    fetch("/api/user")
        .then(res => res.json())
        .then(data => {
            if (data.logged_in) {
                currentUser = data.user;
                updateAuthUI(true);
            } else {
                currentUser = null;
                updateAuthUI(false);
            }
        })
        .catch(err => console.error("Session check anomaly:", err));
}

function updateAuthUI(isLoggedIn) {
    const authBtn = document.getElementById("authBtn");
    const userCard = document.getElementById("userCard");
    const quotaProgressBox = document.getElementById("quotaProgressBox");
    
    if (isLoggedIn && currentUser) {
        // Logged In State
        authBtn.style.display = "none";
        userCard.style.display = "flex";
        quotaProgressBox.style.display = "block";
        
        // Render user details
        document.getElementById("userDisplayName").textContent = currentUser.username;
        
        // Tier specific updates
        const badge = document.getElementById("userTierBadge");
        badge.className = `user-tier-badge badge-${currentUser.tier}`;
        badge.textContent = currentUser.tier.toUpperCase() + " Tier";
        
        // Set Developer tokens
        document.getElementById("apiKeyInput").value = currentUser.api_key;
        updateCodePlaceholders(currentUser.api_key);
        
        // Quota indicators
        const currentQuota = currentUser.usage.current;
        const maxQuota = currentUser.usage.max;
        
        document.getElementById("quotaSpent").textContent = currentQuota;
        if (maxQuota === -1) {
            document.getElementById("quotaMax").textContent = "∞";
            document.getElementById("quotaProgressBar").style.width = "100%";
        } else {
            document.getElementById("quotaMax").textContent = maxQuota;
            const pct = Math.min(100, (currentQuota / maxQuota) * 100);
            document.getElementById("quotaProgressBar").style.width = `${pct}%`;
        }
        
        // Reset Pricing plans button states
        resetPricingButtons();
        
        // If we are currently showing an error card, hide it
        const errorCard = document.getElementById("dashboardError");
        if (errorCard.style.display === "block" && document.getElementById("errorActionBtn").textContent === "Sign In") {
            errorCard.style.display = "none";
        }
    } else {
        // Logged Out State
        authBtn.style.display = "inline-flex";
        userCard.style.display = "none";
        quotaProgressBox.style.display = "none";
        
        // Key placeholders
        document.getElementById("apiKeyInput").value = "sk_live_00000000000000";
        updateCodePlaceholders("sk_live_...");
        
        // Re-enable plan selections for guest mockups
        document.querySelectorAll(".plan-card button").forEach(btn => {
            btn.disabled = false;
        });
        document.getElementById("upgradeBtn-free").disabled = true;
        document.getElementById("upgradeBtn-free").textContent = "Active Plan";
    }
}

function resetPricingButtons() {
    // Enable all plan buttons first
    const freeBtn = document.getElementById("upgradeBtn-free");
    const proBtn = document.getElementById("upgradeBtn-pro");
    const enterpriseBtn = document.getElementById("upgradeBtn-enterprise");
    
    freeBtn.disabled = false;
    freeBtn.textContent = "Downgrade";
    freeBtn.className = "btn btn-outline btn-block";
    
    proBtn.disabled = false;
    proBtn.textContent = "Upgrade to Pro";
    proBtn.className = "btn btn-primary btn-block";
    
    enterpriseBtn.disabled = false;
    enterpriseBtn.textContent = "Upgrade to Enterprise";
    enterpriseBtn.className = "btn btn-outline btn-block";
    
    // De-activate cards highlight classes
    document.querySelectorAll(".plan-card").forEach(card => card.classList.remove("recommended"));
    document.getElementById("planCard-pro").classList.add("recommended"); // Default Pro styling
    
    // Disable current user tier button
    if (currentUser.tier === "free") {
        freeBtn.disabled = true;
        freeBtn.textContent = "Active Plan";
        freeBtn.className = "btn btn-outline btn-block";
    } else if (currentUser.tier === "pro") {
        proBtn.disabled = true;
        proBtn.textContent = "Active Plan";
        proBtn.className = "btn btn-primary btn-block";
        document.getElementById("planCard-free").classList.remove("recommended");
        document.getElementById("planCard-pro").classList.add("recommended");
    } else if (currentUser.tier === "enterprise") {
        enterpriseBtn.disabled = true;
        enterpriseBtn.textContent = "Active Plan";
        enterpriseBtn.className = "btn btn-outline btn-block";
        document.getElementById("planCard-pro").classList.remove("recommended");
        document.getElementById("planCard-enterprise").classList.add("recommended");
    }
}

function updateCodePlaceholders(apiKey) {
    document.querySelectorAll(".api-key-placeholder").forEach(el => {
        el.textContent = apiKey;
    });
}

// --- Auth Modal Overlays ---
function openAuthModal() {
    document.getElementById("authModal").style.display = "flex";
    setAuthMode("LOGIN");
}

function closeAuthModal() {
    document.getElementById("authModal").style.display = "none";
}

function toggleAuthMode() {
    setAuthMode(currentAuthMode === "LOGIN" ? "REGISTER" : "LOGIN");
}

function setAuthMode(mode) {
    currentAuthMode = mode;
    const title = document.getElementById("authModalTitle");
    const subTitle = document.getElementById("authModalSubTitle");
    const submitBtn = document.getElementById("authSubmitBtn");
    const toggleText = document.getElementById("authToggleText");
    const errBox = document.getElementById("authErrorMsg");
    
    errBox.style.display = "none";
    
    if (mode === "LOGIN") {
        title.textContent = "Welcome to StockAI";
        subTitle.textContent = "Sign in to initialize deep learning analytics";
        submitBtn.textContent = "Sign In";
        toggleText.innerHTML = `Don't have an account? <a href="#" onclick="toggleAuthMode()">Create one</a>`;
    } else {
        title.textContent = "Initialize SaaS Account";
        subTitle.textContent = "Establish a multi-tenant subscription";
        submitBtn.textContent = "Sign Up and Create Plan";
        toggleText.innerHTML = `Already registered? <a href="#" onclick="toggleAuthMode()">Sign In</a>`;
    }
}

function handleAuthSubmit(e) {
    e.preventDefault();
    const username = document.getElementById("authUsername").value.trim();
    const password = document.getElementById("authPassword").value;
    const errBox = document.getElementById("authErrorMsg");
    
    errBox.style.display = "none";
    
    const endpoint = currentAuthMode === "LOGIN" ? "/api/login" : "/api/register";
    
    fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.message || "Authentication anomaly.");
        }
        return data;
    })
    .then(data => {
        closeAuthModal();
        checkSessionStatus();
        
        // Reset values
        document.getElementById("authUsername").value = "";
        document.getElementById("authPassword").value = "";
    })
    .catch(err => {
        errBox.textContent = err.message;
        errBox.style.display = "block";
    });
}

function handleLogout() {
    fetch("/api/logout", { method: "POST" })
        .then(res => res.json())
        .then(() => {
            currentUser = null;
            updateAuthUI(false);
            switchTab("dashboard");
            
            // Hide previous results
            document.getElementById("analysisResult").style.display = "none";
            
            // Draw default blank charts
            if (sentimentChart) {
                sentimentChart.destroy();
                sentimentChart = null;
            }
        })
        .catch(err => console.error("Logout runtime error:", err));
}

// --- Stripe Billing Simulation Modal ---
function openCheckoutModal(tier, price) {
    // If not logged in, force registration modal first
    if (!currentUser) {
        openAuthModal();
        return;
    }
    
    activeCheckoutTier = tier;
    document.getElementById("checkoutModal").style.display = "flex";
    
    // Update plan names and checkout labels
    const tierName = tier.toUpperCase();
    document.getElementById("checkoutPlanLabel").textContent = `${tierName} Subscription Upgrade`;
    document.getElementById("checkoutPriceLabel").textContent = `$${price}.00`;
    document.getElementById("checkoutDueLabel").textContent = `$${price}.00`;
    
    // Clear card fields
    document.getElementById("cardNum").value = "";
    document.getElementById("cardExpiry").value = "";
    document.getElementById("cardCvv").value = "";
    document.getElementById("checkoutErrorMsg").style.display = "none";
}

function closeCheckoutModal() {
    document.getElementById("checkoutModal").style.display = "none";
}

function handleCheckoutSubmit(e) {
    e.preventDefault();
    const cardNum = document.getElementById("cardNum").value.replace(/\s+/g, '');
    const cardExpiry = document.getElementById("cardExpiry").value;
    const cardCvv = document.getElementById("cardCvv").value;
    const errBox = document.getElementById("checkoutErrorMsg");
    const submitBtn = document.getElementById("checkoutSubmitBtn");
    
    errBox.style.display = "none";
    
    // Simulating card rules validation
    if (cardNum.length < 16) {
        errBox.textContent = "Card number must contain precisely 16 digits.";
        errBox.style.display = "block";
        return;
    }
    if (!cardExpiry.includes("/")) {
        errBox.textContent = "Expiry must match format MM/YY.";
        errBox.style.display = "block";
        return;
    }
    
    // Lock submit button with spinner (simulate Stripe authorization logic)
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing Payment streams...`;
    
    setTimeout(() => {
        // Trigger server upgrade request
        fetch("/api/upgrade", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tier: activeCheckoutTier })
        })
        .then(async res => {
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.message || "Failed subscription update.");
            }
            return data;
        })
        .then(data => {
            // Close Checkout
            closeCheckoutModal();
            
            // Show Success screen overlay
            document.getElementById("successOverlay").style.display = "flex";
            
            // Reload user session metrics
            checkSessionStatus();
            
            // Restore button text
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-shield-halved"></i> Pay and Subscribe`;
        })
        .catch(err => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-shield-halved"></i> Pay and Subscribe`;
            errBox.textContent = err.message;
            errBox.style.display = "block";
        });
    }, 1500);
}

function closeSuccessOverlay() {
    document.getElementById("successOverlay").style.display = "none";
    switchTab("dashboard");
}

// Format credit card strings during typing
function setupInputFormatters() {
    const cardNum = document.getElementById("cardNum");
    const expiry = document.getElementById("cardExpiry");
    const cvv = document.getElementById("cardCvv");
    
    if (cardNum) {
        cardNum.addEventListener("input", (e) => {
            let value = e.target.value.replace(/\D/g, '');
            let formatted = value.match(/.{1,4}/g);
            e.target.value = formatted ? formatted.join(' ') : '';
        });
    }
    
    if (expiry) {
        expiry.addEventListener("input", (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 2) {
                e.target.value = value.substring(0, 2) + '/' + value.substring(2, 4);
            } else {
                e.target.value = value;
            }
        });
    }
}

// --- Key Token and SDK Sandbox Actions ---
function toggleApiKey() {
    const apiInput = document.getElementById("apiKeyInput");
    const btnIcon = document.querySelector("#toggleKeyBtn i");
    if (apiInput.type === "password") {
        apiInput.type = "text";
        btnIcon.className = "fa-solid fa-eye-slash";
    } else {
        apiInput.type = "password";
        btnIcon.className = "fa-solid fa-eye";
    }
}

function copyApiKey() {
    const apiInput = document.getElementById("apiKeyInput");
    navigator.clipboard.writeText(apiInput.value)
        .then(() => alert("API developer token copied to clipboard!"))
        .catch(err => console.error("Clipboard copy failure:", err));
}

function regenerateApiKey() {
    if (!confirm("Are you sure you want to invalidate your existing API token? Any active third-party integrations using it will immediately fail.")) {
        return;
    }
    
    fetch("/api/apikey/regenerate", { method: "POST" })
        .then(res => {
            if (!res.ok) throw new Error("Key refresh fail.");
            return res.json();
        })
        .then(data => {
            currentUser.api_key = data.api_key;
            document.getElementById("apiKeyInput").value = data.api_key;
            updateCodePlaceholders(data.api_key);
            alert("API developer token refreshed successfully!");
        })
        .catch(err => alert("Server error refreshing API key: " + err.message));
}

function switchSandboxTab(tabName) {
    document.querySelectorAll(".sandbox-tab").forEach(tab => {
        tab.classList.remove("active");
        if (tab.textContent.toLowerCase() === tabName) {
            tab.classList.add("active");
        }
    });
    
    document.querySelectorAll(".sandbox-code-panel").forEach(panel => {
        panel.classList.remove("active");
    });
    document.getElementById(`code-${tabName}`).classList.add("active");
}

function copyCodeSnippet(tabName) {
    const codeContainer = document.querySelector(`#code-${tabName} pre code`);
    // Extract actual inner text without HTML structures
    const text = codeContainer.innerText;
    navigator.clipboard.writeText(text)
        .then(() => alert(`${tabName.toUpperCase()} code integration snippet copied!`))
        .catch(err => console.error("Clipboard failed:", err));
}

// --- Core Sentiment Analysis Calls ---
function selectTag(ticker) {
    document.getElementById("tickerInput").value = ticker;
    triggerAnalysis();
}

function triggerAnalysis() {
    const tickerInput = document.getElementById("tickerInput").value.trim().toUpperCase();
    if (!tickerInput) {
        alert("Please select or input a financial ticker.");
        return;
    }
    
    // Force sign in modal if not logged in
    if (!currentUser) {
        openAuthModal();
        return;
    }
    
    const loading = document.getElementById("dashboardLoading");
    const results = document.getElementById("analysisResult");
    const errorCard = document.getElementById("dashboardError");
    
    // Reset Views
    results.style.display = "none";
    errorCard.style.display = "none";
    loading.style.display = "block";
    
    fetch(`/api/action/${tickerInput}`)
        .then(async response => {
            const data = await response.json();
            if (!response.ok) {
                // Return descriptive error structure
                return Promise.reject({ status: response.status, data });
            }
            return data;
        })
        .then(data => {
            loading.style.display = "none";
            displayAnalysisResults(data);
            checkSessionStatus(); // Refresh top progress widgets
        })
        .catch(errObj => {
            loading.style.display = "none";
            const errBtn = document.getElementById("errorActionBtn");
            const errTitle = document.getElementById("errorTitle");
            const errMsg = document.getElementById("errorMessage");
            
            errorCard.style.display = "block";
            
            if (errObj.status === 429) {
                // Rate Limit Trigger
                errTitle.textContent = "Hourly API Limit Exceeded";
                errMsg.textContent = errObj.data.message;
                errBtn.textContent = "Upgrade Subscription";
                errBtn.onclick = () => switchTab("billing");
                errBtn.className = "btn btn-primary";
            } else if (errObj.status === 401) {
                // Session expired
                errTitle.textContent = "Session Access Denied";
                errMsg.textContent = "Authentication credentials expired. Log back in to continue.";
                errBtn.textContent = "Sign In";
                errBtn.onclick = () => openAuthModal();
                errBtn.className = "btn btn-primary";
            } else {
                // Regular Error
                errTitle.textContent = "Analysis Interrupted";
                errMsg.textContent = errObj.data?.message || "An unexpected network issue occurred. Verify connection.";
                errBtn.textContent = "Retry Query";
                errBtn.onclick = () => triggerAnalysis();
                errBtn.className = "btn btn-outline";
            }
        });
}

function displayAnalysisResults(data) {
    const ticker = data.ticker;
    const action = data.action;
    const reasoning = data.reasoning;
    const keyEvent = data.key_event;
    const timestamp = data.timestamp;
    const newsItems = data.news_items;
    
    // Page values
    document.getElementById("resultTickerBadge").textContent = ticker;
    document.getElementById("resultTimestamp").textContent = `Generated: ${timestamp}`;
    
    // Recommended action styling
    const textNode = document.getElementById("decisionActionText");
    textNode.textContent = action;
    textNode.className = `decision-${action.toLowerCase()}`;
    
    // Core reasoning details
    document.getElementById("keyEventText").textContent = keyEvent;
    document.getElementById("reasoningText").innerHTML = reasoning.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Engine banner
    document.getElementById("activeEngineText").textContent = data.engine;
    
    // Append chronological news cards
    const timeline = document.getElementById("newsTimelineList");
    timeline.innerHTML = "";
    document.getElementById("newsArticlesCount").textContent = newsItems.length;
    
    newsItems.forEach(item => {
        const li = document.createElement("li");
        li.className = "news-timeline-item";
        li.innerHTML = `
            <span class="news-item-source">${item.source}</span>
            <p class="news-item-snippet">${item.snippet}</p>
        `;
        timeline.appendChild(li);
    });
    
    // Render horizontal Chart.js bar graphs
    const pos = parseFloat(data.sentiment.Positive);
    const neg = parseFloat(data.sentiment.Negative);
    const neut = parseFloat(data.sentiment.Neutral);
    
    drawSentimentChart(pos, neg, neut);
    
    // Show results
    document.getElementById("analysisResult").style.display = "grid";
}

function drawSentimentChart(pos, neg, neut) {
    const ctx = document.getElementById("sentimentChart").getContext("2d");
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    sentimentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [pos * 100, neut * 100, neg * 100],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.75)', // Emerald Green
                    'rgba(245, 158, 11, 0.75)',  // Amber Gold
                    'rgba(244, 63, 94, 0.75)'   // Hot Crimson
                ],
                borderColor: [
                    '#10b981',
                    '#f59e0b',
                    '#f43f5e'
                ],
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af', callback: (val) => `${val}%` }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#f3f4f6', font: { weight: '600' } }
                }
            }
        }
    });
}

// --- Fetch Database Metrics to populate developer graphs & logs ---
function loadStats() {
    fetch("/api/stats")
        .then(res => {
            if (!res.ok) throw new Error("Stats lookup fail.");
            return res.json();
        })
        .then(data => {
            // 1. Total Requests Indicator
            document.getElementById("totalUserRequestsText").textContent = data.total_requests;
            
            // 2. Render Billing Progress Gauge
            updateBillingDonutChart(currentUser.usage.current, currentUser.usage.max);
            
            // 3. Render Audit Table log items
            const tableBody = document.getElementById("apiLogsTableBody");
            tableBody.innerHTML = "";
            
            const logs = data.recent_logs;
            if (logs.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="4" class="text-center">No recent query transactions logged.</td></tr>`;
            } else {
                logs.forEach(log => {
                    let statusBadgeClass = "badge-success";
                    if (log.status.includes("BLOCKED")) statusBadgeClass = "badge-warning";
                    if (log.status.includes("ERROR")) statusBadgeClass = "badge-danger";
                    
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${log.timestamp}</td>
                        <td><code>${log.endpoint}</code></td>
                        <td><strong>${log.ticker}</strong></td>
                        <td><span class="log-badge ${statusBadgeClass}">${log.status}</span></td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // 4. Render 7-day query trends
            drawApiTrendChart(data.daily_stats);
        })
        .catch(err => console.error("Metrics render error:", err));
}

function updateBillingDonutChart(current, max) {
    const ctx = document.getElementById("quotaDonutChart").getContext("2d");
    
    if (quotaDonutChart) {
        quotaDonutChart.destroy();
    }
    
    // Update summary labels
    document.getElementById("billingActivePlanText").textContent = `${currentUser.tier.toUpperCase()} Subscription Plan`;
    
    let chartData = [];
    let bgColors = [];
    
    if (max === -1) {
        // Unlimited
        document.getElementById("billingQuotaSummaryText").textContent = `${current} / ∞`;
        chartData = [100, 0];
        bgColors = ['rgba(99, 102, 241, 0.8)', 'rgba(255,255,255,0.03)'];
    } else {
        document.getElementById("billingQuotaSummaryText").textContent = `${current} / ${max}`;
        const remaining = Math.max(0, max - current);
        chartData = [current, remaining];
        bgColors = ['rgba(6, 182, 212, 0.8)', 'rgba(255, 255, 255, 0.03)'];
    }
    
    quotaDonutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: chartData,
                backgroundColor: bgColors,
                borderWidth: 0
            }]
        },
        options: {
            cutout: '80%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

function drawApiTrendChart(dailyStats) {
    const ctx = document.getElementById("apiUsageTrendChart").getContext("2d");
    
    if (apiUsageTrendChart) {
        apiUsageTrendChart.destroy();
    }
    
    // Build days and counts datasets
    const labels = [];
    const counts = [];
    
    // Setup blank placeholders if stats are empty
    if (dailyStats.length === 0) {
        // Add fake 7-day blank matrix
        for(let i=6; i>=0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            labels.push(d.toISOString().split('T')[0]);
            counts.push(0);
        }
    } else {
        dailyStats.forEach(item => {
            labels.push(item.day);
            counts.push(item.count);
        });
    }
    
    apiUsageTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Requests',
                data: counts,
                fill: true,
                backgroundColor: 'rgba(99, 102, 241, 0.12)',
                borderColor: '#6366f1',
                borderWidth: 2,
                pointBackgroundColor: '#6366f1',
                pointHoverRadius: 5,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#6b7280', font: { size: 9 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { 
                        color: '#6b7280', 
                        font: { size: 9 }, 
                        precision: 0 
                    }
                }
            }
        }
    });
}
