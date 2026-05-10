# Geolocation and center lookup with fallback support
# Primary: Nominatim (OpenStreetMap) - FREE, no API key needed
# Fallback: Google Places API (if API key provided)
# Last fallback: Local SQLite database

import os
import math
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()

NOMINATIM_USER_AGENT = os.getenv('NOMINATIM_USER_AGENT', 'farmer-query-engine')
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '').strip()
geocoder = Nominatim(user_agent=NOMINATIM_USER_AGENT)

def find_nearby_centers(lat, lon, radius_km=50):
    """
    Find nearby Krishi centers using local SQLite database with distance calculation.
    Can be extended to use Google Places or other APIs in the future.
    """
    from database.db import get_db
    
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, name, latitude, longitude, address FROM centers')
    
    centers = []
    for row in cur.fetchall():
        center_lat, center_lon = row[2], row[3]
        if center_lat is not None and center_lon is not None:
            # Calculate distance using haversine
            distance = haversine(lat, lon, center_lat, center_lon)
            if distance <= radius_km:
                centers.append({
                    'name': row[1],
                    'latitude': center_lat,
                    'longitude': center_lon,
                    'address': row[4],
                    'distance_km': round(distance, 2)
                })
    
    return sorted(centers, key=lambda x: x['distance_km'])

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth using Haversine formula"""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def reverse_geocode(lat, lon):
    """
    Reverse geocode coordinates to get location name
    Uses FREE Nominatim API (rate limited to 1 request/second)
    """
    try:
        location = geocoder.reverse(f"{lat}, {lon}", language='en')
        return str(location)
    except Exception as e:
        return f"Location at {lat}, {lon}"
