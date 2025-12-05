🤖 AI Stock Action Agent: FinBERT + RL Simulation

This project implements a web-based financial news analyst agent that uses a pre-trained FinBERT (Financial BERT) model to determine the sentiment of market news and simulates a Reinforced Learning (RL) agent to generate a stock action recommendation (BUY, SELL, or HOLD).

The application is built using a Python Flask backend for the AI logic and API, and a simple, responsive HTML/CSS/JavaScript frontend for interaction.

✨ Features

Real-Time Sentiment Analysis: Leverages the state-of-the-art FinBERT model (fine-tuned for financial text) to process news snippets.

Simulated Event Extraction (EE): The decision layer uses sentiment scores to infer the Key Event (e.g., Earnings Miss, Product Launch).

Simulated RL Decision Logic: A rule-based system mimics the final action choice of a sophisticated trading agent based on sentiment magnitude.

Themed Frontend: A stylish, responsive user interface with a "money theme" for clear display of market actions and reasoning.

API Driven: Clear separation between the UI and the analysis engine via a simple REST API (/api/action/<ticker>).

📐 Architecture

The application follows a standard Web API pattern, decoupling the AI model from the presentation layer.

Frontend (HTML/CSS/JS): Served by Flask, handles user input (ticker) and sends requests to the API. It visually renders the AI's complex output.

Backend (Python/Flask): Handles routing, data simulation, and orchestrates the AI process.

AI Engine (finbert_model.py): The core intelligence. It loads the large FinBERT model once and performs sentiment calculation on demand.

📦 Project Structure

stock-action-agent/
├── app.py                     # Flask App: Routes, API endpoint, News simulation.
├── requirements.txt           # Python dependencies (torch, transformers, flask, etc.)
├── finbert_model.py           # AI Core: FinBERT loading and decision logic.
├── static/
│   ├── css/
│   │   └── style.css          # The stylish, money-themed CSS.
│   └── js/
│       └── app.js             # Frontend logic (AJAX calls, UI updates).
└── templates/
    └── index.html             # Main application UI (uses Jinja2 url_for).

🚀 Setup and Installation

Prerequisites:
You must have Python 3.9+ installed. A virtual environment is highly recommended.

Clone the Project:
git clone https://github.com/your-repo/stock-action-agent.git
cd stock-action-agent

Create and Activate Virtual Environment:
python -m venv venv

# Windows:
.env\Scriptsctivate

# Linux/macOS:
source venv/bin/activate

Install Dependencies:
pip install -r requirements.txt

If you encounter a ValueError related to torch.load and version < 2.6:
pip install torch --upgrade

Running the Application:
python app.py

Open Dashboard:
http://127.0.0.1:5000/

💡 Usage
Enter a ticker symbol (META, AAPL, or TSLA are pre-loaded with simulated news).
Click Analyze News.
The backend calculates FinBERT sentiment and generates BUY/SELL/HOLD.

⚙️ Customization and Expansion

Live Data Feed:
Replace MOCK_NEWS_DB with real news sources using requests, BeautifulSoup, or APIs.

True RL Agent:
Use Stable Baselines 3 or RLlib to train on historical data.

Advanced Event Tagging:
Implement NER and event classification for deeper insights.
