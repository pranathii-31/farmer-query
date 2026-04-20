import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mandya_crop_data.csv')
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

def train_models():
    if not os.path.exists(DATA_PATH):
        print("Data file not found. Run dataset_generator.py first.")
        return
        
    df = pd.read_csv(DATA_PATH)
    
    # Preprocessing
    le = LabelEncoder()
    df['crop_encoded'] = le.fit_transform(df['crop'])
    
    X = df[['crop_encoded', 'temperature', 'humidity']]
    y_disease = df['disease_risk']
    y_water = df['water_need']
    
    # Train Disease Risk Model
    disease_rf = RandomForestClassifier(n_estimators=50, random_state=42)
    disease_rf.fit(X, y_disease)
    
    # Train Water Need Model
    water_rf = RandomForestClassifier(n_estimators=50, random_state=42)
    water_rf.fit(X, y_water)
    
    # Save models and encoder
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(disease_rf, os.path.join(MODEL_DIR, 'disease_model.pkl'))
    joblib.dump(water_rf, os.path.join(MODEL_DIR, 'water_model.pkl'))
    joblib.dump(le, os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    
    print("Models trained and saved in models/ directory.")

if __name__ == '__main__':
    train_models()
