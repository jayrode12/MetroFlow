from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'mumbai_metro_frontend_secret_2025'

# Backend API URL
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:5001')

# ====================
# Helper Functions
# ====================
def get_backend_session():
    """Create a session object for backend requests"""
    session_obj = requests.Session()
    # Copy cookies from Flask session if needed
    return session_obj

@app.route('/')
def index():
    """Render dashboard - fetches data from backend"""
    try:
        # Fetch data from backend
        response = requests.get(f'{BACKEND_URL}/', timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 302:
            # Redirected to login
            return redirect(f'{BACKEND_URL}/login')
        else:
            # Fallback to local rendering
            return render_template('index.html', 
                                 temp=30, 
                                 cond='Sunny', 
                                 alerts=[], 
                                 logs=['System initialized'],
                                 now=datetime.now())
    except Exception as e:
        print(f"Backend connection error: {e}")
        return render_template('index.html', 
                             temp=30, 
                             cond='Sunny', 
                             alerts=[], 
                             logs=['Backend unavailable - running in standalone mode'],
                             now=datetime.now())

@app.route('/inventory')
def inventory():
    """Render inventory page - fetches data from backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/inventory', timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            return render_template('inventory.html')
    except Exception as e:
        print(f"Backend connection error: {e}")
        return render_template('inventory.html')

@app.route('/schedule')
def schedule():
    """Render schedule page - fetches data from backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/schedule', timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            return render_template('schedule.html')
    except Exception as e:
        print(f"Backend connection error: {e}")
        return render_template('schedule.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login through backend"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            # Forward login request to backend
            response = requests.post(
                f'{BACKEND_URL}/login',
                data={'username': username, 'password': password},
                timeout=10,
                allow_redirects=False
            )
            
            # Check for successful login (redirect or dashboard content)
            if response.status_code in [200, 302]:
                if response.status_code == 302 or 'Dashboard' in response.text or 'Operations Hub' in response.text:
                    # Login successful, redirect to backend home
                    return redirect(f'{BACKEND_URL}/')
            
            # If we get here with 405 or other error, use fallback auth
            if response.status_code != 200:
                raise Exception(f"Backend returned status {response.status_code}")
                
            return render_template('login.html', error='Invalid credentials')
            
        except Exception as e:
            print(f"Backend login error: {e}")
            # Fallback to simple local auth
            if username == 'admin' and password == 'metro2025':
                session['logged_in'] = True
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='Invalid credentials')
    
    # GET request - just show login form
    try:
        response = requests.get(f'{BACKEND_URL}/login', timeout=10)
        if response.status_code == 200:
            return response.content
    except:
        pass
    
    return render_template('login.html')

@app.route('/generate')
def generate():
    """Generate schedule - proxy to backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/generate', timeout=15)
        return response.json()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Backend unavailable: {str(e)}'})

@app.route('/approve_inventory', methods=['POST'])
def approve_inventory():
    """Approve inventory changes - proxy to backend"""
    try:
        data = request.json
        response = requests.post(
            f'{BACKEND_URL}/approve_inventory',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Backend unavailable: {str(e)}'})

@app.route('/commit_schedule', methods=['POST'])
def commit_schedule():
    """Commit schedule - proxy to backend"""
    try:
        data = request.json
        response = requests.post(
            f'{BACKEND_URL}/commit_schedule',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Backend unavailable: {str(e)}'})

@app.route('/logout')
def logout():
    """Logout - clear sessions"""
    try:
        requests.get(f'{BACKEND_URL}/logout', timeout=5)
    except:
        pass
    session.clear()
    return redirect(url_for('login'))

# API Proxy Endpoints
@app.route('/api/fleet')
def api_fleet():
    """Proxy fleet API to backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/api/fleet', timeout=10)
        return response.json()
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/weather')
def api_weather():
    """Proxy weather API to backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/api/weather', timeout=10)
        return response.json()
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/logs')
def api_logs():
    """Proxy logs API to backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/api/logs', timeout=10)
        return response.json()
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🚇 Mumbai Metro Frontend Server Starting...")
    print(f"🔗 Connecting to Backend: {BACKEND_URL}")
    print("📊 Frontend running on port 5000")
    app.run(debug=True, port=5000, host="0.0.0.0")
