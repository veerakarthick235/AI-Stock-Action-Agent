/**
 * Fetches the AI's stock action decision from the Flask API.
 */
function fetchDecision() {
    const tickerInput = document.getElementById('tickerInput').value.trim().toUpperCase();
    if (!tickerInput) {
        alert("Please enter a stock ticker.");
        return;
    }

    // Show loading and hide results/error
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';
    document.getElementById('loading').style.display = 'block';

    const apiUrl = `/api/action/${tickerInput}`;

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            if (data.error) {
                 throw new Error(data.error);
            }
            displayDecision(data);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'block';
        });
}

/**
 * Updates the HTML with the decision data received from the backend.
 * @param {object} data - The decision data from the API.
 */
function displayDecision(data) {
    // --- Update Main Decision ---
    const action = data.action;
    document.getElementById('tickerDisplay').textContent = data.ticker;
    document.getElementById('actionOutput').textContent = action;
    document.getElementById('timestamp').textContent = `Generated: ${data.timestamp}`;
    document.getElementById('reasoningOutput').innerHTML = data.reasoning.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    document.getElementById('keyEventOutput').textContent = data.key_event;

    // Set card styling based on the action
    const decisionCard = document.getElementById('decisionCard');
    decisionCard.className = `card decision-card action-${action.toLowerCase()}`;
    
    // --- Update Sentiment Scores ---
    document.getElementById('posScore').textContent = (parseFloat(data.sentiment.Positive) * 100).toFixed(2) + '%';
    document.getElementById('negScore').textContent = (parseFloat(data.sentiment.Negative) * 100).toFixed(2) + '%';
    document.getElementById('neutScore').textContent = (parseFloat(data.sentiment.Neutral) * 100).toFixed(2) + '%';
    
    // --- Update News List ---
    const newsList = document.getElementById('newsList');
    newsList.innerHTML = '';
    document.getElementById('newsCount').textContent = data.news_items.length;
    
    data.news_items.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${item.source}:</strong> ${item.snippet}`;
        newsList.appendChild(li);
    });

    // Show the results section
    document.getElementById('results').style.display = 'block';
}
