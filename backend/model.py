import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import logging

# Configure basic logging for ML metrics
logging.basicConfig(level=logging.INFO, format='%(asctime)s - ML Metrics - %(message)s')

def order_fleet_by_random_forest(active_rakes):
    """Use Random Forest ML Pipeline to order rakes based on operational health."""
    if not active_rakes:
        return []
        
    # Extract features: [km_since_service, total_distance_km]
    X = np.array([[r.get("km_since_last_service", 0), r.get("total_distance_km", 0)] for r in active_rakes])
    
    # Target: operational score (higher is healthier)
    y = np.array([max(0, 5000 - r.get("km_since_last_service", 0)) for r in active_rakes])
    
    # Handle edge case where all rakes require immediate maintenance
    if np.all(y == 0):
        y = np.array([1.0] * len(active_rakes))
        
    # ML Pipeline
    # 1. Feature Scaling (Standardization for better ML performance)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 2. Model Initialization (Scaled up n_estimators for variance reduction)
    model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    
    # 3. Model Training
    model.fit(X_scaled, y)
    
    # 4. Inference
    scores = model.predict(X_scaled)
    
    # 5. Measure Accuracy & Log dynamically
    if len(np.unique(y)) > 1:
        r2 = r2_score(y, scores)
        mse = mean_squared_error(y, scores)
        logging.info(f"Model trained on {len(active_rakes)} active rakes. R2 Score: {r2:.4f} | MSE: {mse:.2f}")
    
    # Sort descending: higher score = healthier = prioritized for operations
    indexed = list(zip(scores, active_rakes))
    indexed.sort(key=lambda x: -x[0])
    
    return [r for _, r in indexed]
