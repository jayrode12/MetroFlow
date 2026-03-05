from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta
import requests
import random

# ====================
# Flask App Setup
# ====================
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, 'templates'),
    static_folder=os.path.join(FRONTEND_DIR, 'static')
)
app.secret_key = 'mumbai_metro_secret_key_2025'

# ====================
# MongoDB Connection
# ====================
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "MumbaiMetroDB"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
fleet_col = db.get_collection("fleet")
schedule_col = db.get_collection("schedules")
logs_col = db.get_collection("logs")

# ====================
# Helper Functions
# ====================
def get_fresh_fleet():
    """Fetch fresh fleet data from DB and apply maintenance rules"""
    data = list(fleet_col.find({}, {"_id": 0}))
    for rake in data:
        # Normalize status field (handle both "Operational" and "ACTIVE")
        status = rake.get("current_status", "").upper()
        if status in ["OPERATIONAL", "ACTIVE"]:
            rake["current_status"] = "ACTIVE"
        elif status in ["IN MAINTENANCE", "MAINTENANCE"]:
            rake["current_status"] = "IN MAINTENANCE"
        
        # Apply maintenance rule: 5000 KM threshold
        if rake["km_since_last_service"] >= 5000:
            rake["current_status"] = "IN MAINTENANCE"
            # Update in DB
            fleet_col.update_one(
                {"rake_id": rake["rake_id"]},
                {"$set": {"current_status": "IN MAINTENANCE"}}
            )
    return data

def get_live_weather():
    """Fetch live weather from OpenWeather API or return mock data"""
    try:
        API_KEY = "YOUR_OPENWEATHER_API_KEY"  # Replace with actual key
        city = "Mumbai"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()
        temp = round(data['main']['temp'])
        condition = data['weather'][0]['main']
        humidity = data['main'].get('humidity', 60)
        return temp, humidity, condition
    except:
        # Fallback to mock data
        temp = random.randint(25, 35)
        humidity = random.randint(50, 80)
        condition = random.choice(['Sunny', 'Cloudy', 'Humid', 'Clear'])
        return temp, humidity, condition

def add_log(message):
    """Add entry to system logs"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    logs_col.insert_one({"message": message, "timestamp": timestamp})
    return log_entry

def generate_ai_schedule(weather_temp, weather_cond, fleet_data):
    """Generate AI-powered schedule based on weather and fleet availability"""
    # Filter active rakes
    active_rakes = [r for r in fleet_data if r['current_status'] == 'ACTIVE']
    
    if not active_rakes:
        return None
    
    # Simple frequency logic based on weather
    if weather_temp > 32:
        frequency = 3  # High frequency for hot days
    elif weather_temp > 28:
        frequency = 5  # Normal frequency
    else:
        frequency = 7  # Lower frequency for pleasant weather
    
    # Generate next 7 days schedule
    schedules = []
    base_date = datetime.now()
    
    for day_offset in range(7):
        current_date = base_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = current_date.strftime("%A")
        
        # Weekend vs Weekday demand
        if weekday in ['Saturday', 'Sunday']:
            trips_per_hour = 15
        else:
            trips_per_hour = 20
        
        timetable = []
        rake_index = 0
        trip_number = 1
        
        # Generate trips from 6 AM to 11 PM
        for hour in range(6, 23):
            for minute in range(0, 60, frequency):
                if rake_index >= len(active_rakes):
                    rake_index = 0
                
                departure_time = f"{hour:02d}:{minute:02d}"
                mode = "Normal" if hour < 22 else "Return to Depot"
                
                timetable.append({
                    "Serial_No": trip_number,
                    "Rake_No": active_rakes[rake_index]['rake_id'],
                    "Time": departure_time,
                    "Mode": mode
                })
                
                rake_index += 1
                trip_number += 1
        
        # Select standby rake
        standby_rake = active_rakes[0]['rake_id'] if active_rakes else "N/A"
        
        schedules.append({
            "date": date_str,
            "standby": standby_rake,
            "timetable": timetable[:50]  # Limit for display
        })
    
    return {
        "schedules": schedules,
        "temp": weather_temp,
        "condition": weather_cond,
        "frequency": frequency
    }

# ====================
# Routes
# ====================

@app.route("/")
def home():
    """Dashboard route"""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    fleet_data = get_fresh_fleet()
    temp, humidity, cond = get_live_weather()
    
    # Get alerts
    alerts = [r["rake_id"] for r in fleet_data if r["current_status"] == "IN MAINTENANCE"]
    
    # Get recent logs
    recent_logs = list(logs_col.find().sort("timestamp", -1).limit(6))
    log_messages = [log["message"] for log in recent_logs]
    
    if not log_messages:
        log_messages = [
            "System initialized - Admin login",
            "AI Model loaded successfully",
            "Database connection established"
        ]
    
    return render_template(
        "index.html",
        temp=temp,
        cond=cond,
        logs=log_messages,
        alerts=alerts,
        now=datetime.now()
    )

@app.route("/inventory")
def inventory():
    """Fleet inventory route"""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    fleet_data = get_fresh_fleet()
    df = pd.DataFrame(fleet_data)
    
    # Create visualization
    fig = px.bar(
        df, 
        x='rake_id', 
        y='km_since_last_service',
        color='current_status',
        title='Fleet Health - KM Since Last Service',
        labels={'rake_id': 'Rake ID', 'km_since_last_service': 'KM Since Service'},
        color_discrete_map={'ACTIVE': '#10b981', 'IN MAINTENANCE': '#ef4444'}
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1f2937'),
        showlegend=True
    )
    
    return render_template(
        "inventory.html",
        chart_html=pio.to_html(fig, full_html=False),
        inventory_data=fleet_data
    )

@app.route("/schedule")
def schedule():
    """Schedule management route"""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    # Check if schedule exists in DB
    existing_schedule = schedule_col.find_one({"generated_date": datetime.now().strftime("%Y-%m-%d")})
    
    if existing_schedule:
        # Use existing schedule
        schedule_data = existing_schedule
    else:
        # Generate new schedule
        fleet_data = get_fresh_fleet()
        temp, _, cond = get_live_weather()
        schedule_data = generate_ai_schedule(temp, cond, fleet_data)
        
        if schedule_data:
            schedule_col.insert_one({
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "schedules": schedule_data["schedules"],
                "weather": {"temp": temp, "condition": cond}
            })
    
    return render_template(
        "schedule.html",
        schedules=schedule_data.get("schedules", []) if schedule_data else [],
        temp=schedule_data.get("temp", 30) if schedule_data else 30,
        cond=schedule_data.get("condition", "Sunny") if schedule_data else "Sunny",
        gap=schedule_data.get("frequency", 5) if schedule_data else 5
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login route"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Simple authentication (can be enhanced with DB)
        if username == "admin" and password == "metro2025":
            session["logged_in"] = True
            session["username"] = username
            add_log(f"Admin login successful - {username}")
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout route"""
    if session.get("logged_in"):
        add_log(f"Admin logout - {session.get('username')}")
    session.clear()
    return redirect(url_for("login"))

@app.route("/generate")
def generate():
    """Generate AI schedule endpoint"""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    try:
        fleet_data = get_fresh_fleet()
        temp, _, cond = get_live_weather()
        schedule_data = generate_ai_schedule(temp, cond, fleet_data)
        
        if schedule_data:
            # Save to DB
            schedule_col.delete_many({})  # Clear old schedules
            schedule_col.insert_one({
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "schedules": schedule_data["schedules"],
                "weather": {"temp": temp, "condition": cond}
            })
            
            add_log(f"AI schedule generated - Weather: {temp}°C, {cond}")
            
            return jsonify({
                "status": "success",
                "message": "Schedule generated successfully!",
                "data": schedule_data
            })
        else:
            return jsonify({"status": "error", "message": "No active rakes available"}), 400
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/approve_inventory", methods=["POST"])
def approve_inventory():
    """Approve and commit inventory changes"""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    try:
        data = request.json
        
        for item in data:
            rake_id = item.get("rake_id")
            km = int(item.get("km"))
            status = item.get("status")
            
            # Update in database
            fleet_col.update_one(
                {"rake_id": rake_id},
                {
                    "$set": {
                        "km_since_last_service": km,
                        "current_status": status
                    }
                }
            )
        
        add_log(f"Inventory updates approved by {session.get('username')}")
        
        return jsonify({"status": "success", "message": "Fleet status updated"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/commit_schedule", methods=["POST"])
def commit_schedule():
    """Commit schedule to database"""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    try:
        data = request.json
        date = data.get("date")
        standby = data.get("standby")
        timetable = data.get("timetable")
        
        # Save individual day schedule
        schedule_col.update_one(
            {"date": date},
            {
                "$set": {
                    "standby_rake": standby,
                    "timetable": timetable,
                    "locked": True,
                    "locked_at": datetime.now().isoformat(),
                    "locked_by": session.get("username")
                }
            },
            upsert=True
        )
        
        add_log(f"Schedule locked for {date} by {session.get('username')}")
        
        return jsonify({"status": "success", "message": "Schedule locked successfully"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for frontend connectivity
@app.route("/api/fleet")
def api_get_fleet():
    """API endpoint to get fleet data"""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    fleet_data = get_fresh_fleet()
    return jsonify({"status": "success", "data": fleet_data})

@app.route("/api/weather")
def api_get_weather():
    """API endpoint to get weather data"""
    temp, humidity, cond = get_live_weather()
    return jsonify({
        "status": "success",
        "data": {"temperature": temp, "humidity": humidity, "condition": cond}
    })

@app.route("/api/logs")
def api_get_logs():
    """API endpoint to get recent logs"""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    recent_logs = list(logs_col.find().sort("timestamp", -1).limit(10))
    for log in recent_logs:
        log.pop("_id", None)
    
    return jsonify({"status": "success", "data": recent_logs})

# ====================
# Main Execution
# ====================
if __name__ == "__main__":
    print("🚇 Mumbai Metro Backend Server Starting...")
    print(f"📊 Connected to MongoDB: {DB_NAME}")
    print(f"📂 Collections: {db.list_collection_names()}")
    app.run(debug=True, port=5001, host="0.0.0.0")