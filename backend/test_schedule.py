import sys
sys.path.append('main.py')

from main import get_fresh_fleet, generate_ai_schedule, get_live_weather
from datetime import datetime

print("Testing Schedule Generation...\n")

# Get fleet data
fleet_data = get_fresh_fleet()
print(f"Total rakes fetched: {len(fleet_data)}")

# Count active vs maintenance
active_count = sum(1 for r in fleet_data if r['current_status'] == 'ACTIVE')
maintenance_count = sum(1 for r in fleet_data if r['current_status'] == 'IN MAINTENANCE')

print(f"Active rakes: {active_count}")
print(f"Maintenance rakes: {maintenance_count}\n")

# Get weather
temp, humidity, cond = get_live_weather()
print(f"Weather: {temp}°C, {cond}, Humidity: {humidity}%\n")

# Generate schedule
schedule_data = generate_ai_schedule(temp, cond, fleet_data)

if schedule_data:
    print(f"✅ Schedule generated successfully!")
    print(f"Frequency: Every {schedule_data['frequency']} minutes")
    print(f"Days scheduled: {len(schedule_data['schedules'])}")
    print(f"\nFirst day schedule:")
    first_day = schedule_data['schedules'][0]
    print(f"  Date: {first_day['date']}")
    print(f"  Standby rake: {first_day['standby']}")
    print(f"  Total trips: {len(first_day['timetable'])}")
    if first_day['timetable']:
        print(f"  First trip: {first_day['timetable'][0]}")
        print(f"  Last trip: {first_day['timetable'][-1]}")
else:
    print("❌ Failed to generate schedule - No active rakes available")
