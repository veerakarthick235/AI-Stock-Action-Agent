# 🤖 StockAI Agent

### Intelligent Financial Sentiment Terminal & Cloud Trading Insights Platform


## 📌 Overview

StockAI SaaS is a modern AI-powered financial sentiment analysis platform that transforms real-time market news into actionable trading intelligence.

Using FinBERT (Financial BERT), advanced sentiment scoring, and an intelligent trading decision engine, the platform analyzes financial headlines and generates BUY, SELL, or HOLD recommendations.

Built as a production-ready SaaS application, StockAI supports multi-tenant user accounts, API key management, subscription plans, usage quotas, analytics dashboards, MongoDB Atlas cloud persistence, and modern glassmorphism UI experiences.

---

# 🚀 Key Features

## 🧠 AI-Powered Sentiment Analysis

* FinBERT financial sentiment model
* Real-time news sentiment scoring
* Positive, Neutral, Negative confidence outputs
* Intelligent trading signal generation
* BUY / SELL / HOLD recommendations

---

## 🔐 Authentication & Security

### Browser Authentication

* Secure Flask sessions
* Login and Registration
* Session management
* Logout support

### Developer Authentication

* API Key generation
* API Key rotation
* Header-based access

```http
X-API-KEY: sk_live_xxxxxxxxxxxxxx
```

---

## 💳 Subscription Plans

| Plan       | Price      | Daily Requests |
| ---------- | ---------- | -------------- |
| Free       | $0         | 5              |
| Pro        | $49/month  | 100            |
| Enterprise | $199/month | Unlimited      |

### Enterprise Benefits

* Unlimited requests
* Priority processing
* Dedicated resources
* Premium support

---

## 📊 Analytics Dashboard

### User Metrics

* Daily request usage
* Remaining quota
* Top searched stocks
* Historical request trends

### Visualizations

* Chart.js line charts
* Doughnut usage indicators
* Sentiment confidence bars
* Activity analytics

---

## ☁️ MongoDB Atlas Integration

### Cloud Features

* MongoDB Atlas support
* User storage
* API key storage
* Request auditing
* Analytics aggregation

### Intelligent Fallback

If Atlas is unavailable:

* Mock database activates automatically
* Application continues operating
* Zero startup failures

---

# 🏗️ Architecture

```mermaid
graph TD

User[Browser User]
Developer[API Developer]

User --> Dashboard
Developer --> API

Dashboard --> Flask

API --> Flask

Flask --> FinBERT
Flask --> MongoDB

FinBERT --> TradingAgent

MongoDB --> Analytics

Analytics --> Dashboard
```

---

# 📁 Project Structure

```text
AI-Stock-Action-Agent/
│
├── app.py
├── finbert_model.py
├── saas_db.py
├── requirements.txt
├── .env
│
├── templates/
│   └── index.html
│
├── static/
│   ├── favicon.png
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── app.js
│
└── README.md
```

---

# ⚙️ Installation

## Prerequisites

* Python 3.9+
* MongoDB Atlas Account
* Git

---

## Clone Repository

```bash
git clone https://github.com/your-username/stockai-saas.git

cd stockai-saas
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔧 Environment Variables

Create a `.env` file:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/stockai_saas

SECRET_KEY=your_super_secret_key
```

---

# ☁️ MongoDB Atlas Setup

## Create Database User

MongoDB Atlas

→ Database Access

→ Add New Database User

Example:

```text
Username: stockai_admin
Password: StrongPassword123
```

---

## Add Network Access

MongoDB Atlas

→ Network Access

→ Add IP Address

Development:

```text
0.0.0.0/0
```

Production:

Whitelist only your server IP.

---

# ▶️ Run Application

```bash
python app.py
```

Server:

```text
http://127.0.0.1:5000
```

---

# 📡 API Documentation

## Register User

### Endpoint

```http
POST /api/register
```

### Request

```json
{
  "username":"john",
  "password":"password123"
}
```

---

## Login

```http
POST /api/login
```

---

## User Profile

```http
GET /api/user
```

---

## Logout

```http
POST /api/logout
```

---

## Upgrade Plan

```http
POST /api/upgrade
```

### Body

```json
{
  "plan":"pro"
}
```

---

## Generate API Key

```http
POST /api/apikey/regenerate
```

---

## Get Analytics

```http
GET /api/stats
```

---

## Trading Signal Endpoint

```http
GET /api/action/AAPL
```

### Example Response

```json
{
  "ticker":"AAPL",
  "sentiment":"Positive",
  "confidence":0.91,
  "recommendation":"BUY"
}
```

---

# 🐍 Python Example

```python
import requests

API_KEY = "sk_live_xxxxxxxxxxxxx"

headers = {
    "X-API-KEY": API_KEY
}

response = requests.get(
    "http://localhost:5000/api/action/AAPL",
    headers=headers
)

print(response.json())
```

---

# 🌐 cURL Example

```bash
curl \
-H "X-API-KEY: sk_live_xxxxxxxxx" \
http://localhost:5000/api/action/AAPL
```

---

# 📈 Trading Decision Logic

## BUY

Conditions:

* Strong positive sentiment
* Positive confidence > 70%

---

## SELL

Conditions:

* Strong negative sentiment
* Negative confidence > 70%

---

## HOLD

Conditions:

* Mixed sentiment
* Weak confidence

---

# 🧪 Automated Testing

Run:

```bash
python test_saas.py
```

Tests:

* Registration
* Login
* Quota limits
* API keys
* Upgrades
* Analytics
* Trading endpoints

---

# 🔒 Security Best Practices

### Recommended

✅ HTTPS

✅ Strong SECRET_KEY

✅ Environment variables

✅ Rate limiting

✅ MongoDB Atlas Authentication

✅ API key rotation

---

# 📦 Tech Stack

## Backend

* Flask
* PyMongo
* Python Dotenv
* Requests

## AI / ML

* FinBERT
* Transformers
* PyTorch
* NumPy
* Scikit-Learn

## Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js

## Database

* MongoDB Atlas

---

# 📄 License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.

---

# 👨‍💻 Author

**Veera Karthick**

AI Engineer • Full Stack Developer • Data Science Enthusiast

Building intelligent AI systems that solve real-world problems.
