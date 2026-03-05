# 🚇 Mumbai Metro Rail Management System

AI-Powered Timetable Prediction & Fleet Inventory Management

A web-based management platform designed for Mumbai Metro Line 1.  
The system uses Artificial Intelligence to generate optimized train schedules using weather data, passenger demand patterns, and fleet availability.

--------------------------------------------------

## 📋 Features

### AI Schedule Generation
• Generates 7-day metro timetable automatically  
• Uses Random Forest Regression model  
• Considers weather conditions, demand patterns, and fleet status  

### Fleet Inventory Management
• Tracks 16 metro rakes  
• Monitors total mileage of each rake  
• Automatic maintenance alerts after 5000 KM  
• Real-time health monitoring of fleet

### Real-Time Dashboard
• Displays current weather conditions using OpenWeather API  
• Shows system alerts and notifications  
• Provides activity logs for system monitoring  
• Interactive metro map visualization

### Smart Maintenance Logic
• Rakes automatically flagged for maintenance above 5000 KM  
• Train frequency dynamically adjusted based on weather  
• Weekend and weekday demand patterns handled separately

--------------------------------------------------

## 🛠️ Tech Stack

Backend
Python 3.8+
Flask
MongoDB
PyMongo
Pandas
NumPy

Frontend
HTML5
CSS3
JavaScript
Flask Jinja Templates
Font Awesome
MapTiler SDK

Machine Learning & Data
Scikit-learn (Random Forest Regressor)
Plotly (Data Visualization)
OpenWeather API (Weather Data)

--------------------------------------------------

## 🏗️ System Architecture

Frontend (Port 5000)
        │
        ▼
Backend API (Port 5001)
        │
        ▼
MongoDB Database

The frontend interacts with the backend Flask API which processes data and communicates with the MongoDB database.

--------------------------------------------------

## 📦 Installation

### Prerequisites

Python 3.8+
MongoDB
Git

### Step 1 — Clone Repository

git clone https://github.com/jayrode12/MetroFlow.git
cd MetroFlow

### Step 2 — Install Backend Dependencies

cd backend
pip install -r requirements.txt

### Step 3 — Start MongoDB

mongod

### Step 4 — Initialize Database

cd backend
python init_db.py

This will create:
• MumbaiMetroDB database  
• Fleet inventory data  
• Weather dataset  
• Passenger demand dataset  

### Step 5 — Start Backend

python main.py

Backend will run at:
http://127.0.0.1:5001

### Step 6 — Start Frontend

Open new terminal

cd frontend
python app.py

Frontend will run at:
http://127.0.0.1:5000

--------------------------------------------------

## 🚀 Usage

### Login

Username: admin  
Password: metro2025  

### Generate Schedule

1. Open Dashboard
2. Click "Generate Schedule"
3. System creates a new AI timetable for 7 days

### Fleet Inventory

1. Open Fleet Inventory page
2. View all 16 metro rakes
3. Monitor mileage and maintenance status
4. Approve maintenance updates

--------------------------------------------------

## 🔌 API Endpoints

Public Endpoints

GET /api/weather  
Returns current weather data

GET /api/fleet  
Returns fleet inventory data (authentication required)

GET /api/logs  
Returns system logs

Protected Endpoints

POST /approve_inventory  
Update fleet maintenance status

POST /commit_schedule  
Save generated timetable

GET /generate  
Generate new AI schedule

--------------------------------------------------

## 📁 Project Structure

MetroFlow
│
├── backend
│   ├── data
│   │   ├── metro_fleet_inventory.csv
│   │   ├── mumbai_metro_weather_2025.csv
│   │   └── passenger_demand_2025.csv
│   ├── database.py
│   ├── init_db.py
│   ├── main.py
│   └── requirements.txt
│
├── frontend
│   ├── templates
│   │   ├── index.html
│   │   ├── inventory.html
│   │   ├── login.html
│   │   └── schedule.html
│   └── app.py
│
├── .gitignore
└── SETUP_GUIDE.md

--------------------------------------------------

## ⚙️ Maintenance Rules

5000 KM Rule  
Any metro rake exceeding 5000 km since its last service is automatically marked for maintenance.

Weather Based Frequency

Temperature > 32°C → 3 minute interval  
Temperature 28-32°C → 5 minute interval  
Temperature < 28°C → 7 minute interval  

Passenger Demand

Weekdays → 20 trips per hour  
Weekends → 15 trips per hour  

--------------------------------------------------

## 📊 Database Collections

fleet  
Contains information of 16 metro rakes

schedules  
Stores generated AI timetables

logs  
System activity and audit logs

weather  
Historical weather dataset

demand  
Passenger demand dataset

--------------------------------------------------

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a Pull Request

--------------------------------------------------

## 📄 License

MIT License

--------------------------------------------------

## 👨‍💻 Author

Jay Rode  
GitHub: https://github.com/jayrode12

--------------------------------------------------

Made with ❤️ for Mumbai Metro
