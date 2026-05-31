from flask import Flask, jsonify, render_template, request, session, redirect, url_for, send_from_directory
from finbert_model import StockActionAgent
import saas_db
import time
import random
from functools import wraps
from dotenv import load_dotenv
import os

# Load environment configurations
load_dotenv()

# --- Flask Initialization ---
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "antigravity_stockai_saas_super_secret_session_key_2026")

# Initialize database collections and indexes on startup
saas_db.init_db()

# Initialize AI Stock Agent lazily
ai_agent = None

# --- Expanded Mock News Database for Tickers ---
MOCK_NEWS_DB = {
    "META": [
        {"source": "WSJ", "snippet": "Meta scales back metaverse push as focus shifts to AI-powered glasses and wearables, delighting investors with cost control.", "url": "#"},
        {"source": "Fox Business", "snippet": "Meta pivots from costly metaverse projects to AI, company redirects Reality Labs resources following reports of lukewarm metaverse reception.", "url": "#"},
        {"source": "Business Insider", "snippet": "Meta Platforms Inc. Class A (META) is up 3% on reports that it will cut spending on the Metaverse, signaling better profitability ahead.", "url": "#"},
        {"source": "Dow Jones", "snippet": "Meta Plans to Shift Spending Away From the Metaverse, boosting investor confidence in core ad business profitability.", "url": "#"},
        {"source": "Investopedia", "snippet": "High volatility in Meta stock following the pivot news, risks remain but growth potential is high.", "url": "#"}
    ],
    "AAPL": [
        {"source": "Bloomberg", "snippet": "Apple shares gain after news of new M4 chip production schedule, signaling a strong Mac lineup for the next quarter.", "url": "#"},
        {"source": "Reuters", "snippet": "iPhone sales in the China market underperformed expectations for the second consecutive month, putting pressure on margins.", "url": "#"},
        {"source": "WSJ", "snippet": "Analyst downgrades Apple due to concerns over regulatory challenges in the EU regarding the App Store commissions.", "url": "#"},
        {"source": "Forbes", "snippet": "Apple announces groundbreaking features for iOS with deeply integrated generative AI core capabilities, stock trends upward.", "url": "#"}
    ],
    "TSLA": [
        {"source": "Electrek", "snippet": "Tesla launches test run for FSD Supervised, an AI-powered ride hailing service, showing major progress toward robotaxi goals and future revenue.", "url": "#"},
        {"source": "MarketWatch", "snippet": "Tesla stock dips slightly after CEO Musk sells a minor stake for charity; no material impact expected by most analysts.", "url": "#"},
        {"source": "TechCrunch", "snippet": "Tesla Gigafactory expansion plans hit a regulatory snag in Europe, raising concerns over short-term production ramp-ups.", "url": "#"}
    ],
    "NVDA": [
        {"source": "CNBC", "snippet": "NVIDIA posts blockbusting earnings beating expectations, outlook remains highly bullish driven by massive Blackwell GPU demands.", "url": "#"},
        {"source": "Barrons", "snippet": "Demand for AI hardware accelerates, Nvidia datacenter revenues surge over 250% year-over-year as tech giants buy chips in bulk.", "url": "#"},
        {"source": "Reuters", "snippet": "NVIDIA launches high-performance developer tools for edge devices, strengthening ecosystem lock-in against competitors.", "url": "#"},
        {"source": "MarketWatch", "snippet": "Analysts project NVIDIA profit margins to set new historical records next quarter, stock rallies in pre-market.", "url": "#"}
    ],
    "AMZN": [
        {"source": "Bloomberg", "snippet": "AWS cloud revenue growth re-accelerates, powered by strong corporate adoption of custom Bedrock generative AI models.", "url": "#"},
        {"source": "Yahoo Finance", "snippet": "Amazon holiday season sales surpass projections; automation in fulfillment warehouses keeps operations highly profitable.", "url": "#"},
        {"source": "FT", "snippet": "Amazon Prime pricing increases slightly in key regions to offset high domestic transportation and logistics expenses.", "url": "#"}
    ],
    "GOOGL": [
        {"source": "TechCrunch", "snippet": "Google integrated Gemini 1.5 Pro deep into Workspace suites, driving a strong surge in premium commercial subscriptions.", "url": "#"},
        {"source": "WSJ", "snippet": "Antitrust lawsuit rulings cause minor structural setbacks for Google search segments, but analysts note strong YouTube ads.", "url": "#"},
        {"source": "Bloomberg", "snippet": "Alphabet announces inaugural dividend and a major stock buyback plan, delighting retail and institutional stakeholders.", "url": "#"}
    ],
    "MSFT": [
        {"source": "CNBC", "snippet": "Microsoft Azure cloud segment records 31% YoY expansion, outstripping competition as enterprise Copilot licenses scale up.", "url": "#"},
        {"source": "Business Insider", "snippet": "Microsoft strengthens partnership with OpenAI, preparing a next-generation multimodal agent for desktop automation.", "url": "#"},
        {"source": "Reuters", "snippet": "Microsoft rolls out quick security patches globally following minor cloud vulnerability discovery; no client databases breached.", "url": "#"}
    ]
}

def fetch_daily_news(ticker: str):
    """
    Retrieves a random subset of news for the ticker from the mock database.
    """
    news_list = MOCK_NEWS_DB.get(ticker.upper(), [])
    if not news_list:
        return [
            {"source": "SaaS Engine", "snippet": f"No specific news found for {ticker.upper()}. General market trend analysis required.", "url": "#"}
        ]
    # Randomly select between 1 and max available articles
    num_news = random.randint(1, len(news_list))
    return random.sample(news_list, num_news)


# --- Rate Limit and Key Auth Decorator ---
def require_saas_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        auth_method = None
        
        # 1. Check API Key Header (X-API-KEY)
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            user = saas_db.get_user_by_api_key(api_key)
            auth_method = "API_KEY"
            
        # 2. Check Session (Browser User)
        elif "user_id" in session:
            user = saas_db.get_user_by_id(session["user_id"])
            auth_method = "SESSION"
            
        if not user:
            return jsonify({
                "error": "Unauthorized (401)",
                "message": "Access Denied. Please log in to your SaaS dashboard or provide a valid 'X-API-KEY' header."
            }), 401
            
        # Check rate limits
        allowed, current, limit = saas_db.check_rate_limit(user["_id"], user["tier"])
        
        if not allowed:
            # Log the blocked attempt
            ticker = kwargs.get("ticker", "GENERIC")
            saas_db.log_api_usage(user["_id"], ticker, request.path, "BLOCKED_RATE_LIMIT")
            return jsonify({
                "error": "Too Many Requests (429)",
                "message": f"Daily API quota exceeded for your '{user['tier'].upper()}' tier. You have used {current}/{limit} requests in the last 24h. Please upgrade to Pro or Enterprise in your Billing panel.",
                "quota_status": {
                    "tier": user["tier"],
                    "current": current,
                    "max": limit,
                    "upgrade_required": True
                }
            }), 429
            
        # Attach the authenticated user and method to the request context
        request.user = user
        request.auth_method = auth_method
        return f(*args, **kwargs)
    return decorated_function


# --- HTML Routes ---
@app.route('/')
def index():
    """Serves the premium single-page SaaS dashboard."""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Serves the circular favicon image to prevent 404 errors."""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/png')


# --- SaaS Authentication Endpoints ---
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        
        success, message = saas_db.register_user(username, password)
        if not success:
            return jsonify({"error": "Bad Request", "message": message}), 400
            
        # Log user in automatically
        user = saas_db.verify_user(username, password)
        if user:
            session["user_id"] = user["_id"]
            session["username"] = user["username"]
            
        return jsonify({"success": True, "message": message})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        
        user = saas_db.verify_user(username, password)
        if not user:
            return jsonify({"error": "Unauthorized", "message": "Invalid username or password credentials."}), 401
            
        session["user_id"] = user["_id"]
        session["username"] = user["username"]
        return jsonify({"success": True, "message": "Authentication successful!", "user": {
            "username": user["username"],
            "tier": user["tier"]
        }})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Successfully logged out."})

@app.route('/api/user', methods=['GET'])
def api_user():
    if "user_id" not in session:
        return jsonify({"logged_in": False}), 200
        
    user = saas_db.get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"logged_in": False}), 200
        
    # Check current quota status
    _, current_usage, max_limit = saas_db.check_rate_limit(user["_id"], user["tier"])
    
    return jsonify({
        "logged_in": True,
        "user": {
            "id": user["_id"],
            "username": user["username"],
            "tier": user["tier"],
            "api_key": user["api_key"],
            "created_at": user["created_at"],
            "usage": {
                "current": current_usage,
                "max": max_limit
            }
        }
    })


# --- SaaS Billing / Subscription Endpoints ---
@app.route('/api/upgrade', methods=['POST'])
def api_upgrade():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized", "message": "You must be logged in to modify subscriptions."}), 401
        
    data = request.get_json() or {}
    tier = data.get("tier")
    
    success, message = saas_db.update_user_tier(session["user_id"], tier)
    if not success:
        return jsonify({"error": "Bad Request", "message": message}), 400
        
    return jsonify({"success": True, "message": message})


# --- SaaS Developer Key Management ---
@app.route('/api/apikey/regenerate', methods=['POST'])
def api_regenerate_key():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized", "message": "Authentication session required."}), 401
        
    new_key = saas_db.regenerate_api_key(session["user_id"])
    if not new_key:
        return jsonify({"error": "Server Error", "message": "Failed to generate key."}), 500
        
    return jsonify({"success": True, "api_key": new_key, "message": "API key successfully regenerated."})


# --- SaaS Analytics / Statistics Endpoint ---
@app.route('/api/stats', methods=['GET'])
def api_stats():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized", "message": "Log in required."}), 401
        
    stats = saas_db.get_api_usage_stats(session["user_id"])
    return jsonify(stats)


# --- Core AI Analysis SaaS API Endpoint ---
@app.route('/api/action/<ticker>', methods=['GET'])
@require_saas_auth
def get_stock_action(ticker):
    """
    SaaS API endpoint that analyzes news and returns decision data.
    Securely rate-limited and logged.
    """
    # 1. Verify that the agent helper is ready
    global ai_agent
    if ai_agent is None:
        try:
            ai_agent = StockActionAgent()
        except Exception:
            pass
            
    if ai_agent is None:
        saas_db.log_api_usage(request.user["_id"], ticker, request.path, "ERROR_503")
        return jsonify({
            "error": "Service Unavailable (503)", 
            "message": "The backend sentiment engine is temporarily unavailable. Check engine configuration."
        }), 503

    # Simulate realistic processing/inference time (0.4s to 1s)
    time.sleep(random.uniform(0.4, 1.0))
    
    try:
        ticker = ticker.upper()
        
        # 1. Fetch Ticker news from our SaaS simulator
        news_items = fetch_daily_news(ticker)

        # 2. Compute sentiment and decision using either FinBERT or lexicon fallback
        decision_data = ai_agent.make_decision(news_items)

        # 3. Log the successful request in SQLite
        saas_db.log_api_usage(request.user["_id"], ticker, request.path, "SUCCESS")

        # 4. Formulate premium JSON response
        response_data = {
            "ticker": ticker,
            "action": decision_data['action'],
            "reasoning": decision_data['reasoning'],
            "key_event": decision_data['key_event'],
            "sentiment": decision_data['sentiment_score'],
            "news_items": news_items,
            "engine": "Lexicon Fallback" if getattr(ai_agent, 'is_fallback', True) else "FinBERT Deep Learning",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "auth_method": request.auth_method
        }

        return jsonify(response_data)
        
    except Exception as e:
        print(f"API processor error for {ticker}: {e}")
        saas_db.log_api_usage(request.user["_id"], ticker, request.path, "ERROR_500")
        return jsonify({
            "error": "Internal Server Error (500)", 
            "message": f"Processing anomaly detected: {str(e)}"
        }), 500


# --- Server Start ---
if __name__ == '__main__':
    print("--- ANTIGRAVITY STOCKAI SAAS INITIALIZATION ---")
    if ai_agent is not None and not getattr(ai_agent, 'is_fallback', True):
        print("Running in standard Deep Learning mode (FinBERT enabled).")
    else:
        print("Running in safe hybrid mode (High-fidelity Lexicon fallback enabled).")
        
    app.run(debug=False, port=5000)