"""
Unified Assistant Route — /assistant/query

Accepts any combination of:
  - text query
  - crop image
  - lat / lon (location)

Returns a single structured JSON response with:
  - ai_response   : main conversational answer
  - disease       : detected disease name (if image provided)
  - confidence    : disease confidence score
  - treatment     : treatment advice
  - fertilizer    : fertilizer advice
  - prevention    : prevention advice
  - health_tips   : crop health tips
  - weather       : weather info dict (if location provided)
  - yojnas        : list of government schemes
  - nearby_centers: list of nearby KVKs
  - input_summary : what inputs were received (for UI display)
"""

import base64
from flask import Blueprint, request, jsonify
from utils.helpers import (
    validate_image, validate_coordinates, format_response,
    canonicalize_crop, canonicalize_state,
)
from utils.logger import logger

assistant_bp = Blueprint('assistant', __name__, url_prefix='/assistant')


@assistant_bp.route('/query', methods=['POST'])
def unified_query():
    """
    Unified conversational endpoint.

    Multipart form fields:
        query   (str, optional)   — free-text farmer query
        image   (file, optional)  — crop / plant photo
        lat     (float, optional) — latitude
        lon     (float, optional) — longitude
        crop    (str, optional)   — crop name hint (may be inferred from image)
        state   (str, optional)   — Indian state name
    """
    logger.info("Received unified assistant query")

    # ── Parse inputs ───────────────────────────────────────────────────────────
    query     = (request.form.get('query', '') or '').strip()
    crop_hint = (request.form.get('crop',  '') or '').strip()
    state_raw = (request.form.get('state', '') or '').strip()
    lat_raw   = request.form.get('lat')
    lon_raw   = request.form.get('lon')
    image_file = request.files.get('image')
    # Conversation history sent as JSON string [{role, text}, ...]
    history_raw = (request.form.get('history', '') or '').strip()
    try:
        import json
        conv_history = json.loads(history_raw) if history_raw else []
    except Exception:
        conv_history = []

    # Require at least one input
    has_query  = bool(query)
    has_image  = image_file is not None and validate_image(image_file)
    has_location = (
        lat_raw is not None and lon_raw is not None
        and validate_coordinates(lat_raw, lon_raw)
    )

    if not has_query and not has_image and not has_location:
        return jsonify(format_response(
            None, 400,
            "Please provide at least one input: a text query, a crop image, or your location."
        )), 400

    # Canonicalise
    crop  = canonicalize_crop(crop_hint) if crop_hint else None
    state = canonicalize_state(state_raw) if state_raw else None
    lat   = float(lat_raw) if has_location else None
    lon   = float(lon_raw) if has_location else None

    # ── Disease detection (image) ───────────────────────────────────────────────
    disease_name  = None
    confidence    = None
    treatment     = None
    fertilizer    = None
    prevention    = None
    health_tips   = None
    image_b64     = None

    if has_image:
        try:
            image_bytes = image_file.read()
            image_b64   = base64.b64encode(image_bytes).decode('utf-8')

            from services.ml_model import detect_disease_from_image
            disease_result = detect_disease_from_image(image_bytes)
            disease_name   = disease_result.get('disease_name')
            confidence     = disease_result.get('confidence')

            # Pull advice from DB
            if disease_name and disease_name != 'Unable to detect disease':
                from services.recommendation import get_disease_advice
                advice = get_disease_advice(disease_name)
                if advice:
                    treatment  = advice.get('treatment')
                    fertilizer = advice.get('fertilizer')
                    prevention = advice.get('prevention')

            # Crop health tips
            if crop:
                from services.recommendation import get_crop_health_tips
                health_tips = get_crop_health_tips(crop)

            logger.info(f"Disease detection: {disease_name} ({confidence})")
        except Exception as e:
            logger.error(f"Image processing error: {e}")

    # ── Weather (fetch for AI context; only show card when user asks) ─────────────
    weather_data     = None
    weather_context  = None
    location_context = None
    nearby_centers   = []

    weather_asked_kws = ['weather', 'temperature', 'rain', 'forecast', 'climate',
                         'hot', 'cold', 'humidity', 'will it rain', 'sunny']
    user_wants_weather = any(kw in query.lower() for kw in weather_asked_kws)

    if has_location:
        try:
            from services.weather_service import get_weather_context
            weather_data    = get_weather_context(lat, lon)
            weather_context = weather_data.get('summary', '')
            logger.info(f"Weather: {weather_context}")
        except Exception as e:
            logger.error(f"Weather service error: {e}")

        try:
            from services.location_service import reverse_geocode, find_nearby_centers
            location_context = reverse_geocode(lat, lon)
            raw_centers      = find_nearby_centers(lat, lon, radius_km=50)
            nearby_centers   = [
                {
                    'name':        c.get('name', 'Unknown Centre'),
                    'distance_km': round(c.get('distance_km', 0.0), 2),
                    'address':     c.get('address', ''),
                }
                for c in raw_centers
            ]
            logger.info(f"Found {len(nearby_centers)} nearby centers")
        except Exception as e:
            logger.error(f"Location service error: {e}")

    # ── Government schemes (only when user asks) ───────────────────────────────
    yojnas = []
    scheme_keywords = ['scheme', 'yojna', 'yojana', 'subsidy', 'loan', 'pm-kisan',
                       'pmfby', 'insurance', 'benefit', 'kcc', 'kisan card']
    user_wants_schemes = any(kw in query.lower() for kw in scheme_keywords)
    if user_wants_schemes:
        try:
            from services.recommendation import get_yojna_recommendations
            yojnas = get_yojna_recommendations(crop, state, disease=disease_name)
        except Exception as e:
            logger.error(f"Yojna lookup error: {e}")

    # ── AI response ─────────────────────────────────────────────────────────────
    # Pass weather to AI for context (so it can answer weather-influenced questions)
    # but only show the weather CARD in UI when user explicitly asked about weather.
    weather_for_ai = None
    if weather_data:
        weather_for_ai = weather_data.get('summary', '')
        if weather_data.get('farming_advice'):
            weather_for_ai += '. ' + weather_data['farming_advice']

    try:
        from services.ai_service import get_ai_response
        ai_response = get_ai_response(
            query            = query,
            image_b64        = image_b64,
            crop             = crop,
            state            = state,
            disease          = disease_name,
            weather_context  = weather_for_ai,
            location_context = location_context,
            conv_history     = conv_history,
        )
    except Exception as e:
        logger.error(f"AI service error: {e}")
        ai_response = (
            "I'm here to help with your farming questions! "
            "I encountered a temporary issue. Please try again."
        )

    # ── Compose result ──────────────────────────────────────────────────────────
    input_summary = []
    if has_query:    input_summary.append('text')
    if has_image:    input_summary.append('image')
    if has_location: input_summary.append('location')

    # Apply fallback advice when disease was detected but no DB entry found
    if disease_name and disease_name != 'Unable to detect disease':
        treatment  = treatment  or 'Apply appropriate fungicide/bactericide based on local recommendations.'
        fertilizer = fertilizer or 'Maintain balanced NPK fertilization; avoid excess nitrogen during disease stress.'
        prevention = prevention or 'Practice crop rotation, use disease-resistant varieties and ensure good drainage.'
    
    if crop and not health_tips:
        health_tips = (
            f"General tips for {crop}: Ensure proper irrigation, monitor regularly for pests, "
            "rotate crops annually, and maintain soil health with organic matter."
        )

    result = {
        'ai_response':    ai_response,
        'disease':        disease_name,
        'confidence':     confidence,
        'treatment':      treatment,
        'fertilizer':     fertilizer,
        'prevention':     prevention,
        'health_tips':    health_tips,
        # Only send weather card when user asked about it
        'weather':        weather_data if user_wants_weather else None,
        'yojnas':         yojnas,
        'nearby_centers': nearby_centers,
        'input_summary':  input_summary,
    }

    logger.info("Unified assistant query completed successfully")
    return jsonify(format_response(result)), 200
