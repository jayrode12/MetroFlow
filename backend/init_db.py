"""
Initialize MongoDB database with CSV data
"""
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["MumbaiMetroDB"]

print("🔄 Initializing Mumbai Metro Database...")

# Clear existing collections
for collection_name in ["fleet", "schedules", "logs", "weather", "demand"]:
    if collection_name in db.list_collection_names():
        db[collection_name].drop()
        print(f"📂 Cleared collection: {collection_name}")

# 1. Load Fleet Inventory
print("\n📊 Loading Fleet Inventory...")
fleet_df = pd.read_csv("data/metro_fleet_inventory.csv")
fleet_records = fleet_df.to_dict('records')

# Ensure proper field names
for record in fleet_records:
    if 'rake_id' not in record and 'Rake ID' in record:
        record['rake_id'] = str(record.pop('Rake ID'))
    if 'total_distance_km' not in record and 'Total Distance (km)' in record:
        record['total_distance_km'] = int(record.pop('Total Distance (km)'))
    if 'km_since_last_service' not in record and 'KM Since Last Service' in record:
        record['km_since_last_service'] = int(record.pop('KM Since Last Service'))
    if 'current_status' not in record and 'Current Status' in record:
        record['current_status'] = record.pop('Current Status')
    if 'last_service_date' not in record and 'Last Service Date' in record:
        record['last_service_date'] = record.pop('Last Service Date')

db.fleet.insert_many(fleet_records)
print(f"✅ Loaded {len(fleet_records)} fleet records")

# 2. Load Weather Data
print("\n🌤️ Loading Weather Data...")
try:
    weather_df = pd.read_csv("data/mumbai_metro_weather_2025.csv")
    weather_records = weather_df.to_dict('records')
    db.weather.insert_many(weather_records)
    print(f"✅ Loaded {len(weather_records)} weather records")
except Exception as e:
    print(f"⚠️ Weather data loading skipped: {e}")

# 3. Load Passenger Demand Data
print("\n👥 Loading Passenger Demand Data...")
try:
    demand_df = pd.read_csv("data/passenger_demand_2025.csv")
    demand_records = demand_df.to_dict('records')
    db.demand.insert_many(demand_records)
    print(f"✅ Loaded {len(demand_records)} demand records")
except Exception as e:
    print(f"⚠️ Demand data loading skipped: {e}")

# 4. Initialize Logs Collection
print("\n📝 Initializing Logs...")
initial_logs = [
    {"message": "Database initialized", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"message": "Fleet data loaded successfully", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    {"message": "System ready for operations", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
]
db.logs.insert_many(initial_logs)
print(f"✅ Initialized {len(initial_logs)} log entries")

# 5. Verify Data
print("\n🔍 Verifying Database...")
collections = db.list_collection_names()
for collection_name in collections:
    count = db[collection_name].count_documents({})
    print(f"   📂 {collection_name}: {count} documents")

print("\n✅ Database initialization complete!")
print("\n📋 Summary:")
print(f"   - Fleet: {db.fleet.count_documents({})} rakes")
print(f"   - Weather: {db.weather.count_documents({})} records")
print(f"   - Demand: {db.demand.count_documents({})} records")
print(f"   - Logs: {db.logs.count_documents({})} entries")
print("\n🚇 Ready to start backend server!")
