from pymongo import MongoClient

# ==============================
# MongoDB Configuration
# ==============================
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "MumbaiMetroDB"   # ✅ AI removed, matches your MongoDB

# ==============================
# MongoDB Client
# ==============================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    """
    Returns MongoDB database instance
    """
    return db

def get_collection(collection_name):
    """
    Returns a specific MongoDB collection
    Example: get_collection("fleet")
    """
    return db[collection_name]

# ==============================
# Test Connection
# ==============================
if __name__ == "__main__":
    try:
        print("✅ Connected to MongoDB Database:", DB_NAME)
        print("📂 Available Collections:")
        for col in db.list_collection_names():
            print(" -", col)
    except Exception as e:
        print("❌ MongoDB connection error:", e)