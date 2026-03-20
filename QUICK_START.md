# 🚇 MetroFlow Quick Start Guide

## Prerequisites
- Python 3.8+ installed
- MongoDB running locally on port 27017
- Required Python packages (see requirements.txt)

## Installation & Startup

### Step 1: Initialize Database (First Time Only)
```bash
cd backend
python init_db.py
```

This will:
- Create MongoDB collections
- Load fleet inventory data
- Initialize system logs

### Step 2: Start Backend Server
```bash
cd backend
python main.py
```
**Expected Output**:
```
🚇 Mumbai Metro Backend Server Starting...
📊 Connected to MongoDB: MumbaiMetroDB
📂 Collections: ['fleet', 'schedules', 'logs']
* Running on http://0.0.0.0:5001
```

### Step 3: Start Frontend Server (New Terminal)
```bash
cd frontend
python app.py
```
**Expected Output**:
```
🚇 Mumbai Metro Frontend Server Starting...
🔗 Connecting to Backend: http://127.0.0.1:5001
📊 Frontend running on port 5000
* Running on http://0.0.0.0:5000
```

### Step 4: Access Application
Open your browser and navigate to:
```
http://localhost:5000
```

**Login Credentials**:
- Username: `admin`
- Password: `metro2025`

---

## Testing All Features

### Option 1: Manual Testing
1. **Dashboard** (`/`) - View system overview
2. **Schedule** (`/schedule`) - Generate and lock schedules
3. **Inventory** (`/inventory`) - Manage fleet status
4. **Analytics** (`/analytics`) - View three-card analysis

### Option 2: Automated Testing
```bash
cd backend
python test_all_changes.py
```

---

## Feature Checklist

### ✅ Round Robin Preservation
- [ ] Generate schedule for Day 1
- [ ] Note the standby rake assigned
- [ ] Regenerate schedule
- [ ] Verify same standby rake is preserved for Day 1

### ✅ Three-Card Analysis
- [ ] Navigate to Analytics page
- [ ] Verify Card 1: Standby Rake History (blue border)
- [ ] Verify Card 2: PDF Archive (green border)
- [ ] Verify Card 3: Current Day Timetable (yellow border)
- [ ] Download PDF for a locked schedule

### ✅ Rake-to-Trip Synchronization
- [ ] Lock a schedule
- [ ] Click "Report change" button
- [ ] Select a rake from dropdown
- [ ] Verify trip options are filtered automatically
- [ ] Select trip and submit
- [ ] Verify UI updates immediately

### ✅ Inline Editing
- [ ] Generate new schedule
- [ ] Click on any Rake_No cell (yellow highlighted)
- [ ] Edit the value
- [ ] Lock the schedule
- [ ] Verify cells are no longer editable

### ✅ Immediate Lock Update
- [ ] Lock a schedule
- [ ] Watch for instant button change (no page refresh)
- [ ] Verify "Report change" button appears
- [ ] Verify LOCKED badge appears with timestamp

### ✅ Maintenance Auto-Update
- [ ] Report a rake change
- [ ] Check fleet inventory
- [ ] Verify reported rake shows "IN MAINTENANCE"
- [ ] Verify KM since service reset to 0

---

## Troubleshooting

### MongoDB Connection Error
```
pymongo.errors.ServerSelectionTimeoutError: localhost:27017
```
**Solution**: Start MongoDB service
```bash
# Windows (if MongoDB is installed as service)
net start MongoDB

# Or start manually
mongod --dbpath "C:\data\db"
```

### Port Already in Use
```
OSError: [WinError 10048] address already in use
```
**Solution**: Kill the process or use different port
```bash
# Find process using port 5001
netstat -ano | findstr :5001

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Backend Not Responding
**Solution**: 
1. Check if backend is running on port 5001
2. Verify `BACKEND_URL` in `frontend/app.py` matches
3. Check firewall settings

### Module Import Errors
```
ModuleNotFoundError: No module named 'pymongo'
```
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/main.py` | Main Flask backend server |
| `backend/database.py` | MongoDB connection config |
| `backend/init_db.py` | Database initialization |
| `backend/test_all_changes.py` | Automated test suite |
| `frontend/app.py` | Frontend Flask proxy server |
| `frontend/templates/schedule.html` | Schedule management UI |
| `frontend/templates/analysis.html` | Three-card analysis UI |
| `IMPLEMENTATION_SUMMARY.md` | Detailed implementation docs |

---

## Common Workflows

### Generate & Lock Schedule
1. Go to Schedule page
2. Click "GENERATE NEW SCHEDULE"
3. Review AI-generated timetable
4. Click "LOCK & SAVE" for each day
5. Schedule now appears in Analysis

### Report Rake Change
1. Lock a schedule first
2. Click "Report change" button
3. Select rake to replace
4. Trip options auto-filter
5. Select trip number
6. Click "Save"
7. UI updates instantly, rake sent to maintenance

### View Analysis
1. Navigate to Analytics (`/analytics`)
2. **Card 1**: Review standby rake history
3. **Card 2**: Download PDFs of locked schedules
4. **Card 3**: View today's detailed timetable

### Approve Fleet Status Changes
1. Go to Inventory page
2. Update rake statuses
3. Click "Approve Changes"
4. If status changed, timetable unlocks automatically
5. Regenerate and re-lock schedule

---

## Performance Benchmarks

| Operation | Expected Time |
|-----------|--------------|
| Login | < 1s |
| Generate Schedule (2 days) | < 2s |
| Lock Schedule | < 1s |
| Report Change | < 1s |
| PDF Download | < 2s |
| Analytics Page Load | < 1s |

---

## Support

If you encounter issues:
1. Check console/terminal for error messages
2. Verify MongoDB is running: `mongosh` or MongoDB Compass
3. Ensure both servers (backend & frontend) are running
4. Check `IMPLEMENTATION_SUMMARY.md` for detailed info
5. Run automated tests: `python test_all_changes.py`

---

## Next Steps After Setup

1. ✅ Verify database initialized correctly
   ```bash
   cd backend
   python check_fleet.py
   ```

2. ✅ Test basic functionality
   - Login
   - View dashboard
   - Generate schedule

3. ✅ Explore features
   - Try inline editing
   - Lock a schedule
   - Report a change
   - View analytics

4. ✅ Review implementation details
   - Read `IMPLEMENTATION_SUMMARY.md`
   - Check code comments in `main.py`

---

**Happy scheduling! 🚇✨**
