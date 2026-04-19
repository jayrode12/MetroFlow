import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Mocking the fleet data based on typical values
active_rakes = [
    {"km_since_last_service": np.random.randint(0, 4500), "total_distance_km": np.random.randint(10000, 50000)}
    for _ in range(16)
]

def evaluate_model(active_rakes):
    X = np.array([[r.get("km_since_last_service", 0), r.get("total_distance_km", 0)] for r in active_rakes])
    y = np.array([max(0, 5000 - r.get("km_since_last_service", 0)) for r in active_rakes])
    
    if np.all(y == 0):
        y = np.array([1.0] * len(active_rakes))
        
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    predictions = model.predict(X)
    
    mse = mean_squared_error(y, predictions)
    r2 = r2_score(y, predictions) if len(np.unique(y)) > 1 else 0
    print(f"MSE: {mse:.2f}")
    print(f"R2 Score: {r2:.4f}")
    
    # Let's see if the ranking order is 100% correct
    actual_ranks = np.argsort(-y)
    pred_ranks = np.argsort(-predictions)
    
    exact_match = np.array_equal(actual_ranks, pred_ranks)
    print(f"Does the model correctly rank the exact same way as a simple sort? {exact_match}")
    print(set(actual_ranks) == set(pred_ranks))

evaluate_model(active_rakes)
