from flask import Blueprint, request, jsonify
from services.recommendation import get_yojna_recommendations
from utils.helpers import format_response, validate_crop
from utils.logger import logger

yojna_bp = Blueprint('yojna', __name__)

@yojna_bp.route('/yojna', methods=['GET'])
def yojna_recommendation():
    logger.info("Received yojna recommendation request")
    crop = request.args.get('crop')
    state = request.args.get('state')

    if not validate_crop(crop) or not state or not isinstance(state, str) or len(state.strip()) == 0:
        logger.warning("Missing or invalid crop/state parameters")
        return jsonify(format_response(None, 400, "Missing or invalid crop/state parameters")), 400

    try:
        recommendations = get_yojna_recommendations(crop, state)
        logger.info(f"Yojna recommendations retrieved: {len(recommendations)} for crop={crop}, state={state}")
        return jsonify(format_response(recommendations)), 200
    except Exception as e:
        logger.error(f"Error retrieving yojna recommendations: {str(e)}")
        return jsonify(format_response(None, 500, "Internal server error")), 500
