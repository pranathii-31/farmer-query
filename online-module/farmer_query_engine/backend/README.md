# To run the Flask app, change directory to backend and run:
#
#   pip install -r requirements.txt
#   python database/init_db.py
#   python app.py
#
# Endpoints:
#   POST   /detect-disease
#   GET    /disease-advice?disease=xyz
#   GET    /yojna?crop=wheat&state=karnataka
#   GET    /crop-health?crop=rice
#   GET    /nearby-centers?lat=..&lon=..
#   POST   /full-recommendation (NEW - Unified API)
#
# API Architecture - Hybrid with Fallbacks:
#
# 1. DISEASE DETECTION:
#    Primary:   Plant.id Health Assessment API (if PLANT_ID_API_KEY provided, detects diseases from image)
#    Fallback:  Hugging Face Inference using nateraw/vit-base-beans (FREE, rate limited)
#    Last:      Placeholder response
#
# 2. LOCATION SERVICE:
#    Primary:   Nominatim / OpenStreetMap (FREE, no API key)
#    Fallback:  Google Places API (if GOOGLE_PLACES_API_KEY provided)
#    Last:      Local SQLite database
#
# 3. ADVICE & TIPS:
#    Primary:   Local SQLite database with normalization and canonicalization for resilience
#    Future:    External API integration for dynamic data
#
# Key Features:
# - Normalization: Inputs are lowercased and mapped to canonical forms (e.g., "corn" -> "maize")
# - Fallbacks: Provides actionable advice even when exact matches fail
# - Expanded Data: Includes more diseases, crops, and schemes for better coverage
# - Optional Location: `/full-recommendation` will work without lat/lon; nearby centers are returned only when location is provided
#
# Setup:
# 1. Copy .envexample to .env
# 2. (Optional) Add API keys for premium services
# 3. Run database/init_db.py for sample data
# 4. Run app.py
