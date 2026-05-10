from flask import Blueprint, request, jsonify
from services.recommendation import get_crop_health_tips
from utils.helpers import format_response, validate_crop
from utils.logger import logger

health_bp = Blueprint('health', __name__)

@health_bp.route('/crop-health', methods=['GET'])
def crop_health():
    logger.info("Received crop health tips request")
    crop = request.args.get('crop')

    if not validate_crop(crop):
        logger.warning("Missing or invalid crop parameter")
        return jsonify(format_response(None, 400, "Missing or invalid crop parameter")), 400

    try:
        tips = get_crop_health_tips(crop)
        if tips:
            logger.info(f"Crop health tips retrieved for: {crop}")
            return jsonify(format_response({'tips': tips})), 200
        else:
            logger.warning(f"No health tips found for crop: {crop}")
            return jsonify(format_response(None, 404, "No tips found for this crop")), 404
    except Exception as e:
        logger.error(f"Error retrieving crop health tips: {str(e)}")
        return jsonify(format_response(None, 500, "Internal server error")), 500
