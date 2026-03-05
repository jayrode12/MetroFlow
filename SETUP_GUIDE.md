# Mumbai Metro Rail Management System - Setup Guide

## ✅ System Successfully Synced!

### Architecture Overview
```
Frontend (Port 5000) ←→ Backend (Port 5001) ←→ MongoDB
   Flask                    Flask                 Local
   Templates               API + Routes          Database
```

## 🚀 Quick Start

### 1. **Start MongoDB** (if not running)
```bash
mongod
```

### 2. **Initialize Database** (first time only)
```bash
cd backend
python init_db.py
```

### 3. **Start Backend Server**
```bash
cd backend
python main.py
```
- Runs on: `http://127.0.0.1:5001`
- Handles: Database operations, AI scheduling, business logic

### 4. **Start Frontend Server**
```bash
cd frontend
python app.py
```
- Runs on: `http://127.0.0.1:5000`
- Acts as: Reverse proxy to backend

## 🔐 Login Credentials
- **Username:** `admin`
- **Password:** `metro2025`

## 📊 Data Loaded
- **Fleet:** 16 metro rakes with real-time status
- **Weather:** 365 days of historical data
- **Passenger Demand:** 365 days of demand patterns
- **Logs:** Auto-generated system audit trail

## 🎯 Key Features Implemented

### Backend (`backend/main.py`)
✅ Complete Flask application with all routes
✅ MongoDB integration with auto-maintenance rules
✅ AI-powered schedule generation based on weather & demand
✅ Real-time fleet health monitoring
✅ Session-based authentication
✅ RESTful API endpoints for scalability

### Frontend (`frontend/app.py`)
✅ Reverse proxy architecture
✅ Seamless backend connectivity
✅ All routes forward to backend
✅ Fallback handling for offline mode
✅ Responsive UI templates

### Database Collections
- `fleet`: Rake inventory with maintenance tracking
- `schedules`: AI-generated timetables
- `logs`: Security audit trail
- `weather`: Historical weather data
- `demand`: Passenger demand patterns

## 🔄 End-to-End Data Flow

1. **Dashboard View**
   ```
   User → Frontend (/) → Backend (/) → MongoDB Fleet + Weather API → Render Template
   ```

2. **Schedule Generation**
   ```
   User clicks "Generate" → Frontend (/generate) → Backend AI Engine → 
   Fetch Fleet + Weather + Demand → Generate Timetable → Save to MongoDB → Return JSON
   ```

3. **Inventory Management**
   ```
   User views inventory → Frontend (/inventory) → Backend fetches fleet → 
   Create Plotly charts → Render table → User approves changes → 
   Frontend sends POST → Backend updates MongoDB → Redirect to dashboard
   ```

## 🌐 API Endpoints

### Public Routes
- `GET /api/weather` - Current weather conditions
- `GET /api/fleet` - Fleet inventory data (requires auth)
- `GET /api/logs` - System logs (requires auth)

### Protected Routes
- `POST /approve_inventory` - Update fleet status
- `POST /commit_schedule` - Lock daily timetable
- `GET /generate` - Generate AI schedule

## 🛠️ Maintenance Rules

The system automatically enforces:
- **5000 KM Rule**: Any rake exceeding 5000 km since last service is marked "IN MAINTENANCE"
- **Weather-Based Frequency**: 
  - Hot days (>32°C): 3-minute intervals
  - Normal days (28-32°C): 5-minute intervals
  - Pleasant days (<28°C): 7-minute intervals
- **Weekend vs Weekday**: Different demand patterns for Saturdays/Sundays

## 📱 Responsive Design

All templates are mobile-responsive with:
- Flexible grid layouts
- Touch-friendly controls
- Adaptive navigation
- Print-optimized views

## 🔧 Troubleshooting

### Backend won't start
- Check MongoDB is running: `mongod`
- Verify port 5001 is available
- Check database connection string in `main.py`

### Frontend can't connect to backend
- Ensure backend is running on port 5001
- Check `BACKEND_URL` in `frontend/app.py`
- Verify firewall allows localhost communication

### Database empty
- Run `python init_db.py` in backend folder
- Check CSV files exist in `backend/data/`
- Verify MongoDB connection

## 📈 Next Steps

1. Click the preview button to view the application
2. Login with admin credentials
3. Explore dashboard, inventory, and schedule features
4. Generate AI-powered timetable
5. Approve maintenance schedules

---

**System Status:** ✅ Fully Operational  
**Data Connectivity:** ✅ End-to-End Enabled  
**Responsiveness:** ✅ Mobile-Ready  
