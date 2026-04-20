import pandas as pd
import joblib
import os
from database.db import log_advisory

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

# Load models at module level to keep it fast
try:
    disease_model = joblib.load(os.path.join(MODEL_DIR, 'disease_model.pkl'))
    water_model = joblib.load(os.path.join(MODEL_DIR, 'water_model.pkl'))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))
except FileNotFoundError:
    disease_model = None
    water_model = None
    label_encoder = None

def generate_advisory(crop, temp, humidity, market_price):
    if not disease_model:
        return {
            "error": "Models not loaded. Please run model training first."
        }
        
    try:
        # Encode crop
        crop_encoded = label_encoder.transform([crop])[0]
    except ValueError:
        # Unknown crop
        crop_encoded = -1
        
    # Model inputs
    features = pd.DataFrame([[crop_encoded, temp, humidity]], columns=['crop_encoded', 'temperature', 'humidity'])
    
    # Predict Disease Risk (0: Low, 1: Medium, 2: High)
    disease_pred = int(disease_model.predict(features)[0])
    disease_prob = disease_model.predict_proba(features).max()
    
    # Predict Water Need (0: Normal, 1: High)
    water_pred = int(water_model.predict(features)[0])
    
    alert = "Optimal Conditions"
    action = "Continue regular monitoring."
    priority = "LOW"
    confidence = round(float(disease_prob), 2)
    sms_reply = f"{crop} conditions normal. Keep monitoring."
    
    if disease_pred == 2:
        alert = f"High Risk of Fungal/Blast Disease in {crop}"
        action = "Apply appropriate fungicide immediately and avoid excess moisture."
        priority = "HIGH"
        sms_reply = f"ALERT: High disease risk for {crop}. Apply fungicide immediately."
    elif disease_pred == 1:
        alert = f"Moderate Disease Risk in {crop}"
        action = "Monitor closely for symptoms. Apply preventive sprays if needed."
        priority = "MEDIUM"
        sms_reply = f"Warning: Moderate disease risk for {crop}. Monitor closely."
    elif water_pred == 1:
        alert = f"High Temperature Stress on {crop}"
        action = "Increase irrigation to prevent drying."
        priority = "MEDIUM"
        sms_reply = f"Weather Alert: High temp. Increase irrigation for {crop}."
        
    # Price logic
    if crop == 'Sugarcane' and market_price < 2200:
        if priority == "LOW":
            alert = "Low Market Price"
            action = "Consider delaying harvest or finding alternative buyers."
            priority = "MEDIUM"
            confidence = 0.8
            sms_reply = "Market Alert: Sugarcane prices are low. Consider holding."
            
    # Save to SQLite
    log_advisory(crop, temp, humidity, market_price, alert, action, priority, confidence)
    
    return {
        "alert": alert,
        "action": action,
        "priority": priority,
        "confidence": confidence,
        "sms_reply": sms_reply
    }
