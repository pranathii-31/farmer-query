from flask import Blueprint, request, jsonify
from services.ml_model import detect_disease_from_image
from services.recommendation import get_disease_advice
from utils.helpers import validate_image, format_response, validate_disease
from utils.logger import logger

disease_bp = Blueprint('disease', __name__)

@disease_bp.route('/detect-disease', methods=['POST'])
def detect_disease():
    logger.info("Received disease detection request")
    if 'image' not in request.files:
        logger.warning("No image provided in request")
        return jsonify(format_response(None, 400, "No image provided")), 400

    file = request.files['image']
    if not validate_image(file):
        logger.warning("Invalid image file provided")
        return jsonify(format_response(None, 400, "Invalid image file")), 400

    try:
        image_bytes = file.read()
        result = detect_disease_from_image(image_bytes)
        logger.info(f"Disease detection completed: {result}")
        return jsonify(format_response(result)), 200
    except Exception as e:
        logger.error(f"Error in disease detection: {str(e)}")
        return jsonify(format_response(None, 500, "Internal server error")), 500

@disease_bp.route('/disease-advice', methods=['GET'])
def disease_advice():
    logger.info("Received disease advice request")
    disease_name = request.args.get('disease')
    if not validate_disease(disease_name):
        logger.warning("Invalid or missing disease parameter")
        return jsonify(format_response(None, 400, "Missing or invalid disease parameter")), 400

    try:
        advice = get_disease_advice(disease_name)
        if advice:
            logger.info(f"Disease advice retrieved for: {disease_name}")
            return jsonify(format_response(advice)), 200
        else:
            logger.warning(f"Disease not found in database: {disease_name}")
            return jsonify(format_response(None, 404, "Disease not found")), 404
    except Exception as e:
        logger.error(f"Error retrieving disease advice: {str(e)}")
        return jsonify(format_response(None, 500, "Internal server error")), 500
