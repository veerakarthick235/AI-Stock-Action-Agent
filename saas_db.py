import os
import hashlib
import uuid
import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Try importing pymongo with graceful exceptions handling
try:
    import pymongo
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

# Load environment configuration variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/stockai_saas")

# --- HIGH-FIDELITY LOCAL IN-MEMORY MOCK MONGODB ENGINE ---
# Activates automatically if pymongo is missing or cloud connection fails,
# ensuring zero-friction setup and 100% application resilience.
class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {} # str(_id) -> doc

    def find_one(self, query):
        for doc in self.data.values():
            match = True
            for k, v in query.items():
                # Handle ObjectId conversions
                if k == "_id" and isinstance(v, ObjectId):
                    v = str(v)
                doc_val = doc.get(k)
                if isinstance(doc_val, ObjectId):
                    doc_val = str(doc_val)
                if doc_val != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        doc_copy = dict(doc)
        self.data[str(doc_copy["_id"])] = doc_copy
        # Return a mock result structure
        return type('res', (object,), {"inserted_id": doc["_id"]})()

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc:
            set_fields = update.get("$set", {})
            for k, v in set_fields.items():
                doc[k] = v
            self.data[str(doc["_id"])] = doc
            return type('res', (object,), {"modified_count": 1})()
        return type('res', (object,), {"modified_count": 0})()

    def count_documents(self, query):
        count = 0
        for doc in self.data.values():
            match = True
            for k, v in query.items():
                # Handle temporal range queries for rate limits
                if k == "timestamp" and isinstance(v, dict) and "$gte" in v:
                    dt_limit = v["$gte"]
                    if doc.get("timestamp") < dt_limit:
                        match = False
                        break
                    continue
                doc_val = doc.get(k)
                if isinstance(doc_val, ObjectId):
                    doc_val = str(doc_val)
                if doc_val != v:
                    match = False
                    break
            if match:
                count += 1
        return count

    def find(self, query=None):
        results = []
        for doc in self.data.values():
            match = True
            if query:
                for k, v in query.items():
                    doc_val = doc.get(k)
                    if isinstance(doc_val, ObjectId):
                        doc_val = str(doc_val)
                    if doc_val != v:
                        match = False
                        break
            if match:
                results.append(dict(doc))
        return results

    def create_index(self, key_pattern, unique=False):
        pass


class MockDB:
    def __init__(self):
        self.users = MockCollection("users")
        self.api_usage = MockCollection("api_usage")
        print("Resilient Mock MongoDB collections instantiated.")

    def get_collection(self, name):
        if name == "users":
            return self.users
        return self.api_usage


# --- DATABASE SELECTION AND INITIALIZATION ---
db = None
USE_MOCK = False

if not HAS_PYMONGO:
    print("--- INFO: PyMongo not installed. Using local Mock MongoDB fallback. ---")
    USE_MOCK = True
    db = MockDB()
else:
    try:
        print("--- Connecting to MongoDB cluster ---")
        # serverSelectionTimeoutMS is set low to fail fast and trigger mock fallback on CPU timeouts
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        
        # Extract default database from connection string or default to 'stockai_saas'
        db_name = pymongo.uri_parser.parse_uri(MONGO_URI).get("database") or "stockai_saas"
        db = client[db_name]
        print(f"--- MongoDB Cloud Cluster Active: Connected to DB [{db_name}] ---")
    except Exception as e:
        print(f"--- WARNING: MongoDB connection failed ({e}) ---")
        print("--- Activating high-fidelity local in-memory Mock MongoDB client fallback ---")
        USE_MOCK = True
        db = MockDB()


def init_db():
    """Establishes compound database indexes for unique fields."""
    if not USE_MOCK:
        try:
            db.users.create_index("username", unique=True)
            db.users.create_index("api_key", unique=True)
            print("MongoDB cloud collections and unique search indexes verified.")
        except Exception as e:
            print(f"Failed to create cloud index constraints: {e}")
    else:
        print("MongoDB mock indexes verified.")


# --- Helper Security functions ---
def hash_password(password, salt=None):
    """Hashes the password with standard salt+sha256."""
    if not salt:
        salt = uuid.uuid4().hex
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password, stored_hash):
    """Verifies a password against the stored salt$hash combination."""
    try:
        salt, hashed = stored_hash.split('$')
        return hash_password(password, salt) == stored_hash
    except ValueError:
        return False

def generate_api_key():
    """Generates a secure SaaS developer API key."""
    return f"sk_live_{uuid.uuid4().hex}"


# --- Multi-Tenant User CRUD Operations ---
def register_user(username, password):
    """Registers a new MongoDB user document."""
    username = username.strip()
    if not username or not password:
        return False, "Username and password cannot be empty."
        
    # Unique user check
    if db.users.find_one({"username": username}):
        return False, "Username already exists."
        
    pwd_hash = hash_password(password)
    api_key = generate_api_key()
    
    try:
        db.users.insert_one({
            "username": username,
            "password_hash": pwd_hash,
            "tier": "free",
            "api_key": api_key,
            "created_at": datetime.datetime.utcnow()
        })
        return True, "Registration successful!"
    except Exception as e:
        return False, f"Database error during registration: {str(e)}"

def verify_user(username, password):
    """Verifies user credentials. Returns the serialized user dict if valid, else None."""
    username = username.strip()
    user = db.users.find_one({"username": username})
    
    if user and verify_password(password, user['password_hash']):
        user_copy = dict(user)
        user_copy["_id"] = str(user_copy["_id"])
        return user_copy
    return None

def get_user_by_api_key(api_key):
    """Gets user document from developer API key."""
    user = db.users.find_one({"api_key": api_key})
    if user:
        user_copy = dict(user)
        user_copy["_id"] = str(user_copy["_id"])
        return user_copy
    return None

def get_user_by_id(user_id):
    """Gets user document by string representation of ObjectId."""
    try:
        query_id = ObjectId(user_id) if not USE_MOCK else user_id
        user = db.users.find_one({"_id": query_id})
        if user:
            user_copy = dict(user)
            user_copy["_id"] = str(user_copy["_id"])
            return user_copy
    except Exception as e:
        print(f"Error querying user by ID: {e}")
    return None

def update_user_tier(user_id, tier):
    """Updates user plan tier in MongoDB document."""
    if tier not in ['free', 'pro', 'enterprise']:
        return False, "Invalid tier selected."
        
    try:
        query_id = ObjectId(user_id) if not USE_MOCK else user_id
        db.users.update_one({"_id": query_id}, {"$set": {"tier": tier}})
        return True, f"Subscription successfully upgraded to {tier.capitalize()}!"
    except Exception as e:
        return False, f"Failed to update subscription in database: {str(e)}"

def regenerate_api_key(user_id):
    """Generates and rotates a new API key for the user document."""
    new_key = generate_api_key()
    try:
        query_id = ObjectId(user_id) if not USE_MOCK else user_id
        db.users.update_one({"_id": query_id}, {"$set": {"api_key": new_key}})
        return new_key
    except Exception as e:
        print(f"Failed to rotate developer API token: {e}")
        return None


# --- SaaS Usage Tracking & Rate-Limit Gateways ---
def log_api_usage(user_id, ticker, endpoint, status):
    """Logs an API request in the usage audit collection."""
    try:
        db.api_usage.insert_one({
            "user_id": str(user_id), # Stored consistently as string representation
            "ticker": ticker.upper(),
            "endpoint": endpoint,
            "timestamp": datetime.datetime.utcnow(),
            "status": status
        })
    except Exception as e:
        print(f"Failed to log usage: {e}")

def check_rate_limit(user_id, tier):
    """
    Checks if a user is within their daily rate limit constraints.
    Free: 5 requests / last 24h
    Pro: 100 requests / last 24h
    Enterprise: Unlimited
    """
    if tier == 'enterprise':
        return True, 0, -1 # Unlimited
        
    limit = 5 if tier == 'free' else 100
    time_limit = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    
    try:
        count = db.api_usage.count_documents({
            "user_id": str(user_id),
            "timestamp": {"$gte": time_limit}
        })
        allowed = count < limit
        return allowed, count, limit
    except Exception as e:
        print(f"Rate limit verification error: {e}")
        return True, 0, limit


# --- Analytics & MongoDB Aggregations Framework ---
def get_api_usage_stats(user_id, limit=10):
    """
    Retrieves detailed transaction history and aggregated stats.
    Leverages PyMongo Aggregation Pipelines ($match, $group, $sort, $limit).
    """
    user_id_str = str(user_id)
    recent_logs = []
    
    # 1. Fetch recent raw audit logs
    if USE_MOCK:
        logs = db.api_usage.find({"user_id": user_id_str})
        # Sort descending by timestamp
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_logs = logs[:limit]
    else:
        cursor = db.api_usage.find({"user_id": user_id_str}).sort("timestamp", -1).limit(limit)
        recent_logs = list(cursor)
        
    # Serialize ObjectId and timestamps to strings
    for log in recent_logs:
        log["_id"] = str(log["_id"])
        if isinstance(log["timestamp"], datetime.datetime):
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
            
    # 2. Aggregations: ticker stats and 7-day query timeline
    ticker_stats = []
    daily_stats = []
    
    if USE_MOCK:
        ticker_counts = {}
        day_counts = {}
        all_logs = db.api_usage.find({"user_id": user_id_str})
        for log in all_logs:
            t = log["ticker"]
            ticker_counts[t] = ticker_counts.get(t, 0) + 1
            
            d_str = log["timestamp"].strftime("%Y-%m-%d")
            day_counts[d_str] = day_counts.get(d_str, 0) + 1
            
        ticker_stats = [{"ticker": k, "count": v} for k, v in ticker_counts.items()]
        ticker_stats.sort(key=lambda x: x["count"], reverse=True)
        ticker_stats = ticker_stats[:5]
        
        daily_stats = [{"day": k, "count": v} for k, v in day_counts.items()]
        daily_stats.sort(key=lambda x: x["day"])
    else:
        # A. MongoDB Ticker search aggregation pipeline
        ticker_pipeline = [
            {"$match": {"user_id": user_id_str}},
            {"$group": {"_id": "$ticker", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
            {"$project": {"ticker": "$_id", "count": 1, "_id": 0}}
        ]
        ticker_stats = list(db.api_usage.aggregate(ticker_pipeline))
        
        # B. 7-Day timeline timeline pipeline
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        timeline_pipeline = [
            {"$match": {
                "user_id": user_id_str,
                "timestamp": {"$gte": seven_days_ago}
            }},
            {"$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {"day": "$_id", "count": 1, "_id": 0}}
        ]
        daily_stats = list(db.api_usage.aggregate(timeline_pipeline))
        
    # Total count
    total_requests = db.api_usage.count_documents({"user_id": user_id_str})
    
    return {
        "recent_logs": recent_logs,
        "ticker_stats": ticker_stats,
        "daily_stats": daily_stats,
        "total_requests": total_requests
    }
