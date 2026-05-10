from flask import Blueprint, request, jsonify
from utils.helpers import format_response, validate_coordinates
from services.location_service import find_nearby_centers
from utils.logger import logger

centers_bp = Blueprint('centers', __name__)

@centers_bp.route('/nearby-centers', methods=['GET'])
def nearby_centers():
    logger.info("Received nearby centers request")
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radius = float(request.args.get('radius', 50))  # default 50km
    except (TypeError, ValueError):
        logger.warning("Invalid lat/lon/radius parameters")
        return jsonify(format_response(None, 400, "Missing or invalid lat/lon parameters")), 400

    if not validate_coordinates(lat, lon):
        logger.warning("Invalid coordinate values")
        return jsonify(format_response(None, 400, "Invalid coordinate values")), 400

    try:
        centers = find_nearby_centers(float(lat), float(lon), radius_km=radius)
        logger.info(f"Nearby centers retrieved: {len(centers)} centers")
        return jsonify(format_response(centers)), 200
    except Exception as e:
        logger.error(f"Error retrieving nearby centers: {str(e)}")
        return jsonify(format_response(None, 500, "Internal server error")), 500
