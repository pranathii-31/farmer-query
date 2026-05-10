from flask import Blueprint, request, jsonify
from services.recommendation import get_full_recommendation
from utils.helpers import validate_image, format_response, validate_crop, validate_coordinates
from utils.logger import logger

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/full-recommendation', methods=['POST'])
def full_recommendation():
    """
    Full pipeline API: Image → Disease Detection → Advice → Yojna → Health Tips → Nearby Centers
    """
    logger.info("Received full recommendation request")

    # Validate image
    if 'image' not in request.files:
        logger.warning("No image provided in full recommendation request")
        return jsonify(format_response(None, 400, "No image provided")), 400

    file = request.files['image']
    if not validate_image(file):
        logger.warning("Invalid image file in full recommendation request")
        return jsonify(format_response(None, 400, "Invalid image file")), 400

    # Validate other parameters
    crop = request.form.get('crop')
    state = request.form.get('state')  # Optional
    lat = request.form.get('lat')
    lon = request.form.get('lon')

    if not validate_crop(crop):
        logger.warning("Missing or invalid crop parameter")
        return jsonify(format_response(None, 400, "Missing or invalid crop parameter")), 400

    # Location is optional for full recommendation. If either lat or lon is provided, require both.
    if (lat is not None or lon is not None) and not validate_coordinates(lat, lon):
        logger.warning("Missing or invalid coordinates")
        return jsonify(format_response(None, 400, "Missing or invalid lat/lon coordinates")), 400

    try:
        image_bytes = file.read()
        latitude = float(lat) if lat is not None and lat != '' else None
        longitude = float(lon) if lon is not None and lon != '' else None
        result = get_full_recommendation(image_bytes, crop, state, latitude, longitude)
        logger.info("Full recommendation completed successfully")
        return jsonify(format_response(result)), 200
    except Exception as e:
        logger.error(f"Error in full recommendation pipeline: {str(e)}")
        return jsonify(format_response(None, 500, "Internal server error")), 500