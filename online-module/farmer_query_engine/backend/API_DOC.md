# Farmer Query Engine API Documentation

## Endpoints

### 1. Disease Detection
- **POST /detect-disease**
- Input: Multipart form-data, key=image (file)
- Output: `{ "status": 200, "data": { "disease_name": str, "confidence": float }, "error": null }`
- **Backend**: Plant.id API (image is Base64-encoded into JSON if key available) → Hugging Face `nateraw/vit-base-beans` → Placeholder

### 2. Disease Advice
- **GET /disease-advice?disease=NAME**
- Output: `{ "status": 200, "data": { "treatment": str, "fertilizer": str, "prevention": str }, "error": null }`
- **Backend**: SQLite database

### 3. Yojna Recommendation
- **GET /yojna?crop=CROP&state=STATE**
- Output: `{ "status": 200, "data": [ { "name": str, "description": str }, ... ], "error": null }`
- **Backend**: SQLite database

### 4. Crop Health Tips
- **GET /crop-health?crop=CROP**
- Output: `{ "status": 200, "data": { "tips": str }, "error": null }`
- **Backend**: SQLite database

### 5. Nearby Krishi Centers
- **GET /nearby-centers?lat=LAT&lon=LON&radius=50**
- Output: `{ "data": [ { "name": str, "latitude": float, "longitude": float, "address": str, "distance_km": float }, ... ], "status": 200 }`
- **Backend**: SQLite database with haversine distance calculation
- Optional: radius parameter (default 50km)

### 6. Full Recommendation Pipeline (NEW)
- **POST /full-recommendation**
- Input: Multipart form-data with:
  - image (file): Crop image
  - crop (string): Crop type (e.g., "wheat", "pumpkin", "tomato")
  - state (string, optional): State for yojna recommendations (e.g., "karnataka"). Defaults to "karnataka" if not provided.
  - lat (float, optional): Latitude
  - lon (float, optional): Longitude
- Output: `{ "status": 200, "data": { "disease": str, "confidence": float, "treatment": str, "fertilizer": str, "prevention": str, "health_tips": str, "yojna": [str, ...], "nearby_centers": [{"name": str, "distance_km": float}, ...] }, "error": null }`
- **Backend**: Combines all services in one API call. Disease detection uses Plant.id Health Assessment or Hugging Face. Queries use normalized and canonicalized values for resilience to casing and synonyms. Fallbacks provide actionable advice even when exact matches fail. Nearby center results are returned only when valid lat/lon are provided, so the endpoint works even without location input.

### Hybrid Architecture (Free + Premium)
- **FREE**: Nominatim (OpenStreetMap), Hugging Face, Local Database
- **PREMIUM** (Optional): Plant.id, Google Places
- **Fallback Chain**: Tries primary service, falls back if API key missing or request fails
- **Image Handling**: Incoming multipart image uploads are converted to bytes in the backend; Plant.id receives the image as a Base64 string because JSON APIs cannot carry raw binary directly.

### Notes
- All endpoints return JSON with a `status` field, `data` field, and `error` field (null on success).
- Errors return appropriate status codes with error messages in the `error` field.
- **Normalization and Mapping**: Inputs are normalized (lowercased, trimmed) and canonicalized to handle synonyms (e.g., "corn" → "maize", "late blight" → "blight"). This ensures database lookups succeed despite minor variations in user input or ML outputs.
- **Fallback Behavior**: When exact matches fail, endpoints provide general advice or default messages to ensure actionable responses.
- No API keys required to run the system - all services have free fallbacks.
- For production, consider caching external API responses to reduce costs.
