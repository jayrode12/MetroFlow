from flask import Flask, render_template, redirect, url_for, session, request, jsonify, send_file
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta
import requests
import random
import numpy as np
from sklearn.ensemble import RandomForestRegressor

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
        API_KEY = "f99b3325008a9421b84a1c21685df9b4"  # Replace with actual key
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


def _apply_replacements(timetable, replacements, standby_rake):
    """Apply report-change replacements: from_serial_no onwards, replaced_rake becomes standby_rake."""
    if not replacements or not timetable:
        return list(timetable)
    out = []
    for row in timetable:
        r = dict(row)
        sn = r.get("Serial_No")
        if isinstance(sn, str) and sn.isdigit():
            sn = int(sn)
        for rep in replacements:
            from_sn = rep.get("from_serial_no")
            if isinstance(from_sn, str) and from_sn.isdigit():
                from_sn = int(from_sn)
            if sn >= from_sn and r.get("Rake_No") == rep.get("replaced_rake"):
                r["Rake_No"] = rep.get("standby_rake") or standby_rake
                break
        out.append(r)
    return out

# Mumbai Metro Line 1 round-trip distance (km) for one trip slot
KM_PER_TRIP = 23
# Number of days to generate in schedule (2 days)
SCHEDULE_DAYS = 2

def _order_fleet_by_random_forest(active_rakes):
    """Use Random Forest to order rakes: lower km_since_service = higher priority to run (arrange fleet)."""
    if not active_rakes:
        return []
    # Synthetic training: lower km_since -> more trips (higher target). RF learns to rank.
    X = np.array([[r.get("km_since_last_service", 0), r.get("total_distance_km", 0)] for r in active_rakes])
    # Target: inverse of km_since so rakes with less km get higher score
    y = np.array([max(0, 5000 - r.get("km_since_last_service", 0)) for r in active_rakes])
    if np.all(y == 0):
        y = np.array([1.0] * len(active_rakes))
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    scores = model.predict(X)
    # Sort descending: higher score = earlier in list = used first in round-robin
    indexed = list(zip(scores, active_rakes))
    indexed.sort(key=lambda x: -x[0])
    return [r for _, r in indexed]

def generate_ai_schedule(weather_temp, weather_cond, fleet_data):
    """Generate AI-powered schedule for the **next two days**.

    - Uses Random Forest to prioritise rakes with lower kilometres since last service.
    - Selects one standby rake per day in a round-robin fashion.
    - The standby rake chosen for a day is *not* available as standby on the next day.
    - Standby rotation is anchored on the last locked day's standby rake (if any),
      so day‑1's standby flows correctly into subsequent days.
    """
    active_rakes = [r for r in fleet_data if r["current_status"] == "ACTIVE"]
    if not active_rakes:
        return None

    # Order fleet by Random Forest (lower distance => higher priority)
    ordered_rakes = _order_fleet_by_random_forest(active_rakes)
    n_rakes = len(ordered_rakes)

    # Base date: start from tomorrow, so that today’s generation
    # always produces schedules for the next 2 days (D+1, D+2).
    base_date = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # Determine round‑robin starting index from the most recent locked schedule.
    # This ensures: previous day's standby won't be standby again the next day.
    standby_start_index = 0
    try:
        last_locked = schedule_col.find_one(
            {"locked": True, "date": {"$exists": True}},
            sort=[("date", -1)],
        )
        if last_locked:
            prev_standby = last_locked.get("standby_rake")
            if prev_standby:
                for i, r in enumerate(ordered_rakes):
                    if r.get("rake_id") == prev_standby:
                        standby_start_index = (i + 1) % n_rakes
                        break
    except Exception:
        # If anything goes wrong, fall back to starting at index 0
        standby_start_index = 0

    schedules = []
    OP_START = "05:30"
    OP_END = "23:45"
    PEAK_MORNING = ("08:00", "10:30")
    PEAK_EVENING = ("17:00", "19:00")

    for day_offset in range(SCHEDULE_DAYS):
        current_date = base_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")

        # Round‑robin standby:
        # - ordered_rakes already prioritised by Random Forest (less distance first)
        # - standby index rotated day by day, anchored to previous locked day's standby
        standby_index = (standby_start_index + day_offset) % n_rakes
        standby_rake = ordered_rakes[standby_index]["rake_id"]

        # Remove standby from running fleet
        running_rakes = [
            r for r in ordered_rakes
            if r["rake_id"] != standby_rake
        ]
        
        timetable = []
        rake_index = 0
        trip_number = 1
        current_trip_time = datetime.strptime(OP_START, "%H:%M")
        end_service_time = datetime.strptime(OP_END, "%H:%M")

        while current_trip_time <= end_service_time:
            if rake_index >= len(running_rakes):
                rake_index = 0
            time_str = current_trip_time.strftime("%H:%M")
            is_peak = (PEAK_MORNING[0] <= time_str <= PEAK_MORNING[1]) or (
                PEAK_EVENING[0] <= time_str <= PEAK_EVENING[1]
            )
            if is_peak:
                frequency = 3
                mode = "Peak"
            elif current_trip_time.hour >= 22:
                frequency = 8
                mode = "Return to Depot"
            else:
                frequency = 8
                mode = "Off-Peak"
            timetable.append({
                "Serial_No": trip_number,
                "Rake_No": running_rakes[rake_index]["rake_id"],
                "Time": time_str,
                "Mode": mode,
            })
            current_trip_time += timedelta(minutes=frequency)
            rake_index += 1
            trip_number += 1

        schedules.append({"date": date_str, "standby": standby_rake, "timetable": timetable})

    return {
        "schedules": schedules,
        "temp": weather_temp,
        "condition": weather_cond,
        "frequency": "Dynamic (3/8 min)",
    }

# ====================
# Routes
# ====================

@app.route("/")
def home():
    """Dashboard route"""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    _run_auto_end_of_day_if_due()
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
    # Ensure end-of-day mileage update runs if due
    _run_auto_end_of_day_if_due()

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
    """Schedule management route. Merges locked days from DB into displayed schedule."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    _run_auto_end_of_day_if_due()
    today = datetime.now().strftime("%Y-%m-%d")
    existing_schedule = schedule_col.find_one({"generated_date": today})

    if existing_schedule:
        schedule_data = existing_schedule
    else:
        fleet_data = get_fresh_fleet()
        temp, _, cond = get_live_weather()
        schedule_data = generate_ai_schedule(temp, cond, fleet_data)
        if schedule_data:
            schedule_col.insert_one({
                "generated_date": today,
                "schedules": schedule_data["schedules"],
                "weather": {"temp": temp, "condition": cond},
            })

    schedules = schedule_data.get("schedules", []) if schedule_data else []
    # Merge locked days from DB; apply report-change replacements for display
    for day in schedules:
        locked_doc = schedule_col.find_one({"date": day["date"], "locked": True})
        if locked_doc:
            base_timetable = locked_doc.get("timetable", day["timetable"])
            replacements = locked_doc.get("replacements") or []
            standby_rake = locked_doc.get("standby_rake") or day.get("standby")
            day["timetable"] = _apply_replacements(base_timetable, replacements, standby_rake)
            day["standby"] = standby_rake
            day["locked"] = True
            day["locked_at"] = locked_doc.get("locked_at", "")
            day["locked_by"] = locked_doc.get("locked_by", "")
            day["replacements"] = replacements
        else:
            day["locked"] = False
            day["replacements"] = []

    return render_template(
        "schedule.html",
        schedules=schedules,
        temp=schedule_data.get("temp", 30) if schedule_data else 30,
        cond=schedule_data.get("condition", "Sunny") if schedule_data else "Sunny",
        gap="Dynamic (3 / 8 min)" if schedule_data else 5,
        unlocked=request.args.get("unlocked"),
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
        
        # Get existing standby selections from locked schedules to preserve round-robin
        existing_standby = {}
        locked_schedules = list(schedule_col.find({"locked": True, "date": {"$exists": True}}))
        for ls in locked_schedules:
            if ls.get("standby_rake"):
                existing_standby[ls["date"]] = ls["standby_rake"]
        
        schedule_data = generate_ai_schedule(temp, cond, fleet_data, existing_standby)
        
        if schedule_data:
            # Save to DB (clear only generated doc, keep locked day docs)
            schedule_col.delete_many({"generated_date": {"$exists": True}})
            schedule_col.insert_one({
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "schedules": schedule_data["schedules"],
                "weather": {"temp": temp, "condition": cond},
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
    """Approve status only (no manual KM). MAINTENANCE->ACTIVE sets km_since to 0. Any status change unlocks timetable."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        data = request.json
        for item in data:
            rake_id = item.get("rake_id")
            status = item.get("status")
            prev = fleet_col.find_one({"rake_id": rake_id}) or {}
            prev_status = (prev.get("current_status") or "").upper()
            # No manual KM update: keep current km unless MAINTENANCE -> ACTIVE then set to 0
            km = prev.get("km_since_last_service", 0)
            if status == "ACTIVE" and prev_status in ("IN MAINTENANCE", "MAINTENANCE"):
                km = 0
            updates = {"km_since_last_service": km, "current_status": status}
            fleet_col.update_one({"rake_id": rake_id}, {"$set": updates})

        add_log(f"Inventory updates approved by {session.get('username')}")
        return jsonify({
            "status": "success",
            "message": "Fleet status updated",
            # For backward compatibility with frontend; always false now.
            "timetable_unlocked": False,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/commit_schedule", methods=["POST"])
def commit_schedule():
    """Commit schedule to database (lock & save). Saved in DB and shown in Analysis."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        data = request.json
        date = data.get("date")
        standby = data.get("standby")
        timetable = data.get("timetable")

        schedule_col.update_one(
            {"date": date},
            {
                "$set": {
                    "standby_rake": standby,
                    "timetable": timetable,
                    "locked": True,
                    "locked_at": datetime.now().isoformat(),
                    "locked_by": session.get("username"),
                    "fleet_updated_at": None,
                    "replacements": data.get("replacements") or [],
                }
            },
            upsert=True,
        )
        add_log(f"Schedule locked for {date} by {session.get('username')}")
        return jsonify({"status": "success", "message": "Schedule locked successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/report_change", methods=["POST"])
def api_report_change():
    """
    Report change: replace a rake by standby for the remaining schedule from selected trip.
    When rake is reported, immediately send to maintenance and update fleet.
    """
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        date = data.get("date")
        replaced_rake = data.get("replaced_rake")
        from_serial_no = data.get("from_serial_no")

        if not date or not replaced_rake:
            return jsonify({"status": "error", "message": "date and replaced_rake required"}), 400

        locked = schedule_col.find_one({"date": date, "locked": True})

        if not locked:
            return jsonify({"status": "error", "message": "No locked schedule for this date"}), 400

        standby_rake = locked.get("standby_rake")

        if not standby_rake:
            return jsonify({"status": "error", "message": "No standby rake for this day"}), 400

        replacements = list(locked.get("replacements") or [])

        # Update or add replacement entry
        found = False
        for r in replacements:
            if r.get("replaced_rake") == replaced_rake:
                r["standby_rake"] = standby_rake
                r["from_serial_no"] = from_serial_no or r.get("from_serial_no")
                r["reported_at"] = datetime.now().isoformat()
                found = True
                break

        if not found:
            replacements.append({
                "replaced_rake": replaced_rake,
                "standby_rake": standby_rake,
                "from_serial_no": from_serial_no,
                "reported_at": datetime.now().isoformat()
            })

        # Update schedule with replacements
        schedule_col.update_one(
            {"date": date, "locked": True},
            {"$set": {"replacements": replacements}}
        )

        # Immediately send reported rake to maintenance
        fleet_update_result = fleet_col.update_one(
            {"rake_id": replaced_rake},
            {
                "$set": {
                    "current_status": "IN MAINTENANCE",
                    "km_since_last_service": 0  # Reset since it's going for maintenance
                }
            }
        )

        if fleet_update_result.modified_count > 0:
            add_log(f"Rake {replaced_rake} sent to maintenance (reported change on {date})")

        add_log(f"Report change for {date}: {replaced_rake} replaced by standby {standby_rake} from trip {from_serial_no or 'N/A'}")

        return jsonify({
            "status": "success",
            "message": "Rake replaced with standby successfully. Reported rake sent to maintenance.",
            "replacements": replacements
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def _run_auto_end_of_day_if_due():
    """If current time >= 23:45, run end-of-day fleet update.

    - Processes **all locked days up to and including today** where `fleet_updated_at` is not set.
    - Uses the final locked timetable (after replacements) so mileage reflects actual operations.
    """
    now = datetime.now()
    if now.hour < 23 or (now.hour == 23 and now.minute < 45):
        return
    today_str = now.strftime("%Y-%m-%d")

    # Find all locked schedules (past and today) that have not yet updated fleet kms
    pending = list(
        schedule_col.find(
            {
                "locked": True,
                "date": {"$lte": today_str},
                "fleet_updated_at": {"$exists": False},
            }
        )
    )
    if not pending:
        return

    from collections import Counter

    for locked in pending:
        date = locked.get("date")
        base_timetable = locked.get("timetable") or []
        replacements = locked.get("replacements") or []
        standby_rake = locked.get("standby_rake")
        timetable = _apply_replacements(base_timetable, replacements, standby_rake)

        trips_per_rake = Counter(row.get("Rake_No") for row in timetable if row.get("Rake_No"))
        for rake_id, count in trips_per_rake.items():
            add_km = count * KM_PER_TRIP
            fleet_col.update_one(
                {"rake_id": rake_id},
                {"$inc": {"total_distance_km": add_km, "km_since_last_service": add_km}},
            )
        schedule_col.update_one(
            {"_id": locked["_id"]},
            {"$set": {"fleet_updated_at": datetime.now().isoformat()}},
        )
        add_log(f"Auto end-of-day fleet update for {date}")


@app.route("/api/end_of_day", methods=["POST"])
def api_end_of_day():
    """After last metro: update fleet total lifecycle from locked schedule for the given date."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    try:
        data = request.get_json() or {}
        date = data.get("date") or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        locked = schedule_col.find_one({"date": date, "locked": True})
        if not locked:
            return jsonify({"status": "error", "message": f"No locked schedule for {date}"}), 400
        if locked.get("fleet_updated_at"):
            return jsonify({"status": "success", "message": f"Fleet already updated for {date}"})
        base_timetable = locked.get("timetable") or []
        replacements = locked.get("replacements") or []
        standby_rake = locked.get("standby_rake")
        timetable = _apply_replacements(base_timetable, replacements, standby_rake)
        from collections import Counter
        trips_per_rake = Counter(row.get("Rake_No") for row in timetable if row.get("Rake_No"))
        now_iso = datetime.now().isoformat()
        for rake_id, count in trips_per_rake.items():
            add_km = count * KM_PER_TRIP
            fleet_col.update_one(
                {"rake_id": rake_id},
                {
                    "$inc": {"total_distance_km": add_km, "km_since_last_service": add_km},
                },
            )
        schedule_col.update_one(
            {"date": date, "locked": True},
            {"$set": {"fleet_updated_at": now_iso}},
        )
        add_log(f"End-of-day fleet update for {date} by {session.get('username')}")
        return jsonify({"status": "success", "message": f"Fleet updated for {date}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/update_fleet_from_locked_all", methods=["POST"])
def api_update_fleet_from_locked_all():
    """Admin utility: update fleet kms from **all** locked schedules without waiting for 23:45.

    - Looks at every document with `locked=True` and missing `fleet_updated_at`.
    - Applies replacements and updates `total_distance_km` and `km_since_last_service` from the final timetable.
    - Useful when you have already locked past/future days (e.g. 13th & 14th March) and
      want Fleet Inventory to reflect mileage immediately before generating new timetables.
    """
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    try:
        pending = list(
            schedule_col.find(
                {"locked": True, "fleet_updated_at": {"$exists": False}}
            )
        )
        if not pending:
            return jsonify({"status": "success", "message": "No pending locked schedules to apply"})

        from collections import Counter
        updated_dates = []

        for locked in pending:
            date = locked.get("date")
            base_timetable = locked.get("timetable") or []
            replacements = locked.get("replacements") or []
            standby_rake = locked.get("standby_rake")
            timetable = _apply_replacements(base_timetable, replacements, standby_rake)

            trips_per_rake = Counter(row.get("Rake_No") for row in timetable if row.get("Rake_No"))
            for rake_id, count in trips_per_rake.items():
                add_km = count * KM_PER_TRIP
                fleet_col.update_one(
                    {"rake_id": rake_id},
                    {"$inc": {"total_distance_km": add_km, "km_since_last_service": add_km}},
                )
            schedule_col.update_one(
                {"_id": locked["_id"]},
                {"$set": {"fleet_updated_at": datetime.now().isoformat()}},
            )
            updated_dates.append(date)
            add_log(f"Manual fleet update from locked schedule for {date} by {session.get('username')}")

        return jsonify(
            {
                "status": "success",
                "message": "Fleet updated from locked schedules",
                "updated_dates": updated_dates,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/analysis")
@app.route("/analytics")
def analysis():
    """Analysis: three cards – standby history, locked timetable history with PDF, and today's locked timetable.

    Only the **latest 10 locked days** are shown here; older locked days remain stored in MongoDB."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    # Ensure any pending end-of-day mileage updates are applied before analysis view
    _run_auto_end_of_day_if_due()
    # Show only latest 10 locked schedule days; older ones stay in DB
    locked = list(
        schedule_col.find({"locked": True, "date": {"$exists": True}})
        .sort("date", -1)
        .limit(10)
    )
    for doc in locked:
        doc.pop("_id", None)
        base_tt = doc.get("timetable") or []
        doc["timetable"] = _apply_replacements(base_tt, doc.get("replacements") or [], doc.get("standby_rake"))
    return render_template(
        "analysis.html",
        locked_schedules=locked,
        today_str=datetime.now().strftime("%Y-%m-%d"),
        now=datetime.now(),
    )


@app.route("/api/delete_locked_schedule", methods=["POST"])
def api_delete_locked_schedule():
    """Permanently delete a locked schedule for a given date (used from Analysis page)."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    try:
        data = request.get_json() or {}
        date_str = data.get("date")
        if not date_str:
            return jsonify({"status": "error", "message": "date is required"}), 400

        result = schedule_col.delete_one({"date": date_str, "locked": True})
        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "No locked schedule found for this date"}), 404

        add_log(f"Locked schedule permanently deleted for {date_str} by {session.get('username')}")
        return jsonify({"status": "success", "message": "Locked schedule deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/locked_schedule_pdf/<date_str>")
def api_locked_schedule_pdf(date_str):
    """Generate PDF for locked schedule for the given date."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO

        locked = schedule_col.find_one({"date": date_str, "locked": True})
        if not locked:
            return jsonify({"status": "error", "message": "No locked schedule for this date"}), 404
        base_tt = locked.get("timetable") or []
        timetable = _apply_replacements(base_tt, locked.get("replacements") or [], locked.get("standby_rake"))
        standby = locked.get("standby_rake") or "—"

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Mumbai Metro Line 1 – Locked Schedule", styles["Title"]))
        story.append(Paragraph(f"Date: {date_str} | Standby Rake: {standby}", styles["Normal"]))
        story.append(Spacer(1, 12))
        data = [["Sr No", "Rake No", "Departure Time", "Mode"]] + [
            [str(r.get("Serial_No", "")), str(r.get("Rake_No", "")), str(r.get("Time", "")), str(r.get("Mode", ""))]
            for r in timetable
        ]
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(t)
        doc.build(story)
        buf.seek(0)
        return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"schedule_{date_str}.pdf")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/locked_schedules")
def api_locked_schedules():
    """API: list locked schedules for analytics."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    locked = list(schedule_col.find({"locked": True, "date": {"$exists": True}}).sort("date", -1))
    for doc in locked:
        doc["_id"] = str(doc.get("_id")) if doc.get("_id") else None
    return jsonify({"status": "success", "data": locked})


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