from flask import Flask, jsonify, render_template
from finbert_model import StockActionAgent
import time
import random

# --- Flask Initialization ---
app = Flask(__name__)

# Initialize the AI Agent globally. This ensures the heavy FinBERT model 
# is loaded only once when the server starts, not on every request.
try:
    ai_agent = StockActionAgent()
except RuntimeError:
    # If model loading fails (e.g., due to dependency issues), 
    # we set the agent to None so the server can start, but API calls will error gracefully.
    ai_agent = None

# --- Simulated Real-Time News Database ---
# This dictionary simulates the real-time financial news results you would 
# fetch from a News API or a Google search for the specified ticker.
MOCK_NEWS_DB = {
    # Positive sentiment example (Focus shift to AI, boosting sentiment)
    "META": [
        {"source": "WSJ", "snippet": "Meta scales back metaverse push as focus shifts to AI-powered glasses and wearables, delighting investors with cost control.", "url": "#"},
        {"source": "Fox Business", "snippet": "Meta pivots from costly metaverse projects to AI, company redirects Reality Labs resources following reports of lukewarm metaverse reception.", "url": "#"},
        {"source": "Business Insider", "snippet": "Meta Platforms Inc. Class A (META) is up 3% on reports that it will cut spending on the Metaverse, signaling better profitability ahead.", "url": "#"},
        {"source": "Dow Jones", "snippet": "Meta Plans to Shift Spending Away From the Metaverse, boosting investor confidence in core ad business profitability.", "url": "#"},
        {"source": "Investopedia", "snippet": "High volatility in Meta stock following the pivot news, risks remain but growth potential is high.", "url": "#"},
    ],
    # Mixed/Neutral sentiment example (Good news vs. bad news)
    "AAPL": [
        {"source": "Bloomberg", "snippet": "Apple shares gain after news of new M4 chip production schedule, signaling a strong Mac lineup for the next quarter.", "url": "#"},
        {"source": "Reuters", "snippet": "iPhone sales in the China market underperformed expectations for the second consecutive month, putting pressure on margins.", "url": "#"},
        {"source": "WSJ", "snippet": "Analyst downgrades Apple due to concerns over regulatory challenges in the EU regarding the App Store commissions.", "url": "#"},
    ],
    # Mild Positive sentiment example (Future technology focus)
    "TSLA": [
        {"source": "Electrek", "snippet": "Tesla launches test run for FSD Supervised, an AI-powered ride hailing service, showing major progress toward robotaxi goals and future revenue.", "url": "#"},
        {"source": "MarketWatch", "snippet": "Tesla stock dips slightly after CEO Musk sells a minor stake for charity; no material impact expected by most analysts.", "url": "#"},
    ]
}

def fetch_daily_news(ticker: str):
    """
    Retrieves a random subset of news for the ticker from the mock database,
    simulating a real-world data pull.
    """
    news_list = MOCK_NEWS_DB.get(ticker.upper(), [])
    
    if not news_list:
        return [
            {"source": "System", "snippet": f"No specific news found for {ticker.upper()}. General market trend analysis required.", "url": "#"}
        ]
    
    # Randomly select between 1 and the max available articles for variability
    num_news = random.randint(1, len(news_list))
    return random.sample(news_list, num_news)


@app.route('/')
def index():
    """
    Flask route to serve the main HTML page.
    Uses render_template to ensure Jinja2, and thus url_for, is available.
    """
    return render_template('index.html')


@app.route('/api/action/<ticker>', methods=['GET'])
def get_stock_action(ticker):
    """
    API endpoint to fetch the AI's decision and reasoning.
    """
    if ai_agent is None:
        return jsonify({
            "error": "AI model unavailable (503)", 
            "message": "The FinBERT model failed to initialize on the server. Please check server logs for dependency errors (PyTorch/transformers)."
        }), 503

    # Simulate a delay for a realistic news fetching/AI processing time
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        ticker = ticker.upper()
        
        # 1. Fetch News
        news_items = fetch_daily_news(ticker)

        # 2. Get AI Decision from FinBERT Agent
        decision_data = ai_agent.make_decision(news_items)

        # 3. Combine Data for Frontend
        response_data = {
            "ticker": ticker,
            "action": decision_data['action'],
            "reasoning": decision_data['reasoning'],
            "key_event": decision_data['key_event'],
            "sentiment": decision_data['sentiment_score'],
            "news_items": news_items,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        return jsonify(response_data)
        
    except Exception as e:
        print(f"An unexpected error occurred during API call for {ticker}: {e}")
        # Return a user-friendly error response
        return jsonify({
            "error": "Internal Server Error (500)", 
            "message": f"An error occurred while processing the AI decision: {str(e)}"
        }), 500


if __name__ == '__main__':
    if ai_agent is None:
        print("--- WARNING: Flask running, but AI agent is disabled due to initialization error. ---")
    else:
        print("--- Initializing FinBERT Model (Complete) ---")
    
    # Run the Flask development server
    app.run(debug=True)