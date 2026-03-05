from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['MumbaiMetroDB']

print('Fleet Status:')
for rake in db.fleet.find({}, {'rake_id': 1, 'current_status': 1, 'km_since_last_service': 1}):
    print(f"{rake['rake_id']}: {rake['current_status']} - {rake['km_since_last_service']} km")

print(f"\nTotal rakes: {db.fleet.count_documents({})}")
print(f"Active rakes: {db.fleet.count_documents({'current_status': 'ACTIVE'})}")
print(f"Maintenance rakes: {db.fleet.count_documents({'current_status': 'IN MAINTENANCE'})}")
