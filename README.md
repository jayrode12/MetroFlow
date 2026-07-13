# 🚇 MetroFlow: Mumbai Metro Rail Management System

MetroFlow is an end-to-end AI-powered scheduling and fleet management system built for the Mumbai Metro Line 1. It automates timetable generation, tracks real-time fleet health, and utilizes machine learning to intelligently prioritize metro units (rakes) for operation and maintenance.

## 🌟 Key Features

- **AI-Powered Schedule Generation**: Dynamically creates daily timetables based on active fleet status, automatically allocating operational and standby rakes.
- **Machine Learning Fleet Prioritization**: Uses a Random Forest algorithm to optimize the use of metro units based on their accumulated mileage and service history.
- **Intelligent Standby Rotation**: Uses a round-robin algorithm to cycle standby vehicles across consecutive operational days seamlessly.
- **Real-Time Fleet Health Monitoring**: Automatically flags rakes for maintenance (e.g., crossing the 5000 KM threshold) and adjusts their availability.
- **Analytics & PDF Export**: Provides a comprehensive three-card analytics dashboard, tracking standby rake history, archiving locked schedules through automated PDF generation, and presenting real-time timetables.
- **Responsive Dashboard UI**: Visually rich interfaces including interactive dashboards and visual tracking of fleet inventory health using Plotly charts.

---

## 🛠️ Tech Stack

### Core Frameworks
- **Backend Server:** Python, Flask, RESTful APIs
- **Frontend Server:** Python, Flask (acting as reverse proxy), HTML5, CSS3, JavaScript (Jinja2 Templates)
- **Database:** MongoDB (using `pymongo`)

### Machine Learning & Data Processing
- **Algorithms:** Scikit-Learn (Random Forest Regressor)
- **Data Manipulation:** Pandas, NumPy

### Visualization & Reporting
- **Interactive Charts:** Plotly (`plotly.express`)
- **PDF Generation:** ReportLab (`reportlab`)

### External Integration
- **Live Weather Data:** OpenWeather API Integration

---

## 🧠 Algorithms & Machine Learning Models

### 1. Fleet Prioritization - Random Forest Regressor
**Purpose:** To decide the optimal order in which active rakes should be deployed into service.  
**How it Works:** 
- The system trains a **Random Forest Regressor** using synthetic features such as `km_since_last_service` and `total_distance_km`. 
- The model learns to rank rakes by predicting an explicit "fitness score" — prioritizing vehicles that have lower kilometers driven since their last service.
- The sorted array determines the assignment of operational cycles for the day, ensuring wear and tear is uniformly distributed across the fleet.

### 2. Standby Allocation - Round-Robin Algorithm
**Purpose:** Ensure a fair and consistent rotation of backup (standby) units across the schedule.
**How it Works:**
- Each day, the system reserves one rake to act as a standby replacement.
- The allocation employs a round-robin shift mechanism anchored securely to the prior locked day. This ensures a continuously rotating standby choice without re-selecting yesterday's backup unit.

### 3. Cumulative Distance Algorithm
**Purpose:** Compute wear and tear reflecting real-world operations dynamically.
**How it Works:**
- At the end of the day or immediately upon a schedule lock, a reconciliation algorithm calculates the explicit trips taken by each assigned rake (accounting for any emergency replacements), aggregating total distance based on Mumbai Metro Line 1 configurations (e.g., 23 km per trip slot) and pushing updates to MongoDB automatically.

---

## 🏗️ Architecture

The system operates on a dual-Flask architecture connected via MongoDB:
```
[ Frontend (Port 5001) ] ← Proxy → [ Backend (Port 5001) ] ← PyMongo → [ MongoDB ]
        |                                    |                              |
  Jinja Templates                   ML Engine | Rest API             (Fleet, Schedules)
```

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- MongoDB instance running locally on default port `27017`

### 1. Initialization
First, initialize the database and collections:
```bash
cd backend
python init_db.py
```

### 2. Start Servers
You will need to open two separate terminal instances.

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
python app.py
```

### 3. Access Application
Navigate to `http://localhost:5001` in your web browser. 
- **Admin Username:** `admin`
- **Admin Password:** `metro2025`

---

## 📖 Additional Documentation

For more in-depth testing and setup details, please review our other markdown files:
- `QUICK_START.md` - Step-by-step guides for workflows (Reporting Changes, Auto-maintenance).
- `SETUP_GUIDE.md` - Further details on routes, architectural flow, and database schemas.
- `TESTING_GUIDE.md` - Scripts and test cases for validating core workflows.
