import pandas as pd
import numpy as np
import os

def generate_mandya_dataset(num_samples=1000):
    np.random.seed(42)
    crops = ['Sugarcane', 'Paddy', 'Ragi']
    
    data = []
    for _ in range(num_samples):
        crop = np.random.choice(crops)
        
        # Mandya specific weather approximations
        if crop == 'Sugarcane':
            temp = np.random.uniform(25, 40)
            humidity = np.random.uniform(40, 80)
            market_price = np.random.uniform(2000, 3500) # per ton
        elif crop == 'Paddy':
            temp = np.random.uniform(22, 35)
            humidity = np.random.uniform(60, 95)
            market_price = np.random.uniform(1800, 2500) # per quintal
        else: # Ragi
            temp = np.random.uniform(20, 35)
            humidity = np.random.uniform(30, 70)
            market_price = np.random.uniform(2500, 3800) # per quintal
            
        # Target logic for synthetic data (Disease Risk)
        disease_risk = 0 # 0: Low, 1: Medium, 2: High
        if crop == 'Paddy' and humidity > 85 and temp > 28:
            disease_risk = 2 # Blast disease risk
        elif crop == 'Sugarcane' and humidity > 70 and temp > 35:
            disease_risk = 1 # Red rot / fungal risk
        elif crop == 'Ragi' and humidity > 65:
            disease_risk = 1 # Blast risk
            
        # Water Need logic (0: Normal, 1: High)
        water_need = 1 if temp > 33 else 0
            
        data.append({
            'crop': crop,
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'market_price': round(market_price, 2),
            'disease_risk': disease_risk,
            'water_need': water_need
        })
        
    df = pd.DataFrame(data)
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'data'), exist_ok=True)
    df.to_csv(os.path.join(os.path.dirname(__file__), '..', 'data', 'mandya_crop_data.csv'), index=False)
    print("Dataset generated at data/mandya_crop_data.csv")

if __name__ == '__main__':
    generate_mandya_dataset()
