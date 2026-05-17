"""
Weather Service -- fetches real-time weather data.

Priority chain:
  1. OpenWeatherMap Current Weather API  (if OPENWEATHER_API_KEY is set)
  2. Open-Meteo (FREE, no API key needed)
  3. Static fallback message
"""

from __future__ import annotations

import os
import requests
from typing import Optional
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

OWM_API_KEY = os.getenv('OPENWEATHER_API_KEY', '').strip()
OWM_URL     = 'https://api.openweathermap.org/data/2.5/weather'
METEO_URL   = 'https://api.open-meteo.com/v1/forecast'


def get_weather_context(lat, lon):
    # type: (float, float) -> dict
    """
    Fetch weather for (lat, lon).

    Returns a dict with keys:
        summary, temperature, humidity, description,
        wind_speed, rain_mm, city, farming_advice, source
    """
    if OWM_API_KEY:
        result = _fetch_owm(lat, lon)
        if result:
            return result

    result = _fetch_open_meteo(lat, lon)
    if result:
        return result

    return _fallback_weather(lat, lon)


# ---------------------------------------------------------------------------
#  OpenWeatherMap
# ---------------------------------------------------------------------------

def _fetch_owm(lat, lon):
    # type: (float, float) -> Optional[dict]
    try:
        params = {
            'lat':   lat,
            'lon':   lon,
            'appid': OWM_API_KEY,
            'units': 'metric',
        }
        resp = requests.get(OWM_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        temp        = data['main']['temp']
        humidity    = data['main']['humidity']
        description = data['weather'][0]['description'].capitalize()
        wind        = data['wind']['speed']
        city        = data.get('name', '')
        rain_1h     = data.get('rain', {}).get('1h', 0)

        summary = '{0}, {1:.1f}C, humidity {2}%, wind {3} m/s'.format(
            description, temp, humidity, wind
        )
        if rain_1h:
            summary += ', rain {0} mm/h'.format(rain_1h)
        if city:
            summary += ' in {0}'.format(city)

        advice = _farming_advice(temp, humidity, description, rain_1h)

        return {
            'summary':        summary,
            'temperature':    temp,
            'humidity':       humidity,
            'description':    description,
            'wind_speed':     wind,
            'rain_mm':        rain_1h,
            'city':           city,
            'farming_advice': advice,
            'source':         'openweathermap',
        }
    except Exception as e:
        logger.error('OpenWeatherMap error: {0}'.format(e))
        return None


# ---------------------------------------------------------------------------
#  Open-Meteo (FREE fallback)
# ---------------------------------------------------------------------------

def _fetch_open_meteo(lat, lon):
    # type: (float, float) -> Optional[dict]
    try:
        params = {
            'latitude':  lat,
            'longitude': lon,
            'current':   'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code',
            'timezone':  'Asia/Kolkata',
        }
        resp = requests.get(METEO_URL, params=params, timeout=8)
        resp.raise_for_status()
        data    = resp.json()
        current = data.get('current', {})

        temp        = current.get('temperature_2m', 0)
        humidity    = current.get('relative_humidity_2m', 0)
        rain        = current.get('precipitation', 0)
        wind        = current.get('wind_speed_10m', 0)
        wmo_code    = current.get('weather_code', 0)
        description = _wmo_to_description(wmo_code)

        summary = '{0}, {1:.1f}C, humidity {2}%, wind {3:.1f} km/h'.format(
            description, temp, humidity, wind
        )
        if rain:
            summary += ', precipitation {0} mm'.format(rain)

        advice = _farming_advice(temp, humidity, description, rain)

        return {
            'summary':        summary,
            'temperature':    temp,
            'humidity':       humidity,
            'description':    description,
            'wind_speed':     wind,
            'rain_mm':        rain,
            'city':           '',
            'farming_advice': advice,
            'source':         'open-meteo',
        }
    except Exception as e:
        logger.error('Open-Meteo error: {0}'.format(e))
        return None


# ---------------------------------------------------------------------------
#  Fallback
# ---------------------------------------------------------------------------

def _fallback_weather(lat, lon):
    # type: (float, float) -> dict
    return {
        'summary':        'Weather data unavailable for ({0:.2f}, {1:.2f})'.format(lat, lon),
        'temperature':    None,
        'humidity':       None,
        'description':    'Unknown',
        'wind_speed':     None,
        'rain_mm':        0,
        'city':           '',
        'farming_advice': (
            'Weather data is currently unavailable. '
            'Please check local forecasts before irrigation or spraying operations.'
        ),
        'source':         'fallback',
    }


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _wmo_to_description(code):
    # type: (int) -> str
    """Convert WMO weather interpretation code to a human-readable string."""
    mapping = {
        0: 'Clear sky',
        1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
        45: 'Foggy', 48: 'Icy fog',
        51: 'Light drizzle', 53: 'Moderate drizzle', 55: 'Dense drizzle',
        61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
        71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
        80: 'Light showers', 81: 'Moderate showers', 82: 'Violent showers',
        95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail',
    }
    return mapping.get(code, 'Weather code {0}'.format(code))


def _farming_advice(temp, humidity, description, rain_mm):
    # type: (float, int, str, float) -> str
    """Generate concise farming advice from weather parameters."""
    desc_lower = description.lower() if description else ''
    advice_parts = []

    if temp is not None:
        if temp > 38:
            advice_parts.append(
                "Extreme heat: increase irrigation frequency and mulch soil to retain moisture."
            )
        elif temp > 32:
            advice_parts.append(
                "High temperature: irrigate early morning or evening to reduce crop stress."
            )
        elif temp < 5:
            advice_parts.append(
                "Near-freezing: protect sensitive crops with covers; avoid spraying today."
            )
        elif 20 <= temp <= 30:
            advice_parts.append("Ideal temperature for most crops.")

    if humidity is not None:
        if humidity > 80:
            advice_parts.append(
                "High humidity -- risk of fungal diseases (blight, mildew). "
                "Improve ventilation; apply preventive fungicide if needed."
            )
        elif humidity < 30:
            advice_parts.append(
                "Low humidity -- crops may wilt faster. Monitor soil moisture closely."
            )

    if rain_mm and float(rain_mm) > 5:
        advice_parts.append(
            "Significant rainfall expected -- postpone irrigation and spraying operations."
        )
    elif rain_mm and float(rain_mm) > 0:
        advice_parts.append("Light rain -- hold off on irrigation today.")

    if 'storm' in desc_lower or 'thunder' in desc_lower:
        advice_parts.append(
            "Storm conditions -- secure young plants and delay any field operations."
        )

    return (' '.join(advice_parts)
            if advice_parts
            else "Weather conditions are suitable for regular farm operations.")
