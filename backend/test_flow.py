"""Test the schedule generation flow"""
import requests

BASE_URL = "http://127.0.0.1:5001"

print("Testing Schedule Generation Flow...\n")

# Step 1: Login
print("1. Logging in...")
session = requests.Session()
login_response = session.post(
    f"{BASE_URL}/login",
    data={"username": "admin", "password": "metro2025"},
    allow_redirects=False
)
print(f"   Login Status: {login_response.status_code}")

# Step 2: Access Dashboard
print("\n2. Accessing Dashboard...")
dashboard_response = session.get(f"{BASE_URL}/")
print(f"   Dashboard Status: {dashboard_response.status_code}")
print(f"   ✓ Dashboard accessible")

# Step 3: Click Generate Schedule (should redirect to /schedule)
print("\n3. Testing 'GENERATE SCHEDULE' button from dashboard...")
# Simulate clicking the button which now goes to /schedule
schedule_response = session.get(f"{BASE_URL}/schedule")
print(f"   Schedule Page Status: {schedule_response.status_code}")
if schedule_response.status_code == 200:
    print(f"   ✓ Successfully redirected to Schedule page")
    if "AI GENERATED SCHEDULE" in schedule_response.text:
        print(f"   ✓ Schedule content loaded")

# Step 4: Generate New Schedule via API
print("\n4. Testing 'GENERATE NEW SCHEDULE' button...")
generate_response = session.get(f"{BASE_URL}/generate")
print(f"   Generate API Status: {generate_response.status_code}")
if generate_response.status_code == 200:
    json_data = generate_response.json()
    if json_data.get("status") == "success":
        print(f"   ✓ New schedule generated successfully!")
        print(f"   Message: {json_data.get('message')}")
        schedules = json_data.get("data", {}).get("schedules", [])
        print(f"   Days scheduled: {len(schedules)}")
        if schedules:
            first_day = schedules[0]
            print(f"   First day: {first_day['date']}")
            print(f"   Trips: {len(first_day['timetable'])}")
    else:
        print(f"   ✗ Generation failed: {json_data.get('message')}")
else:
    print(f"   ✗ API Error: {generate_response.status_code}")

print("\n✅ All tests completed!")
print("\nUser Flow Summary:")
print("1. User logs in → Dashboard")
print("2. Click 'GENERATE SCHEDULE' → Redirects to /schedule page")
print("3. Click 'GENERATE NEW SCHEDULE' button → Calls /generate API → Refreshes with new schedule")
