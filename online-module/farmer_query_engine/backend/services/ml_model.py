# ML model inference with fallback support
# Primary: Plant.id API (if API key provided)
# Fallback 1: Hugging Face Inference API (FREE, rate limited)
# Fallback 2: Local database placeholder

import base64
import os
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

PLANT_ID_API_KEY = os.getenv('PLANT_ID_API_KEY', '').strip()
PLANT_ID_URL = 'https://api.plant.id/v2/health_assessment'
HF_MODEL_ID = os.getenv('HUGGINGFACE_MODEL_ID', 'nateraw/vit-base-beans').strip()
HF_API_URL = f'https://api-inference.huggingface.co/models/{HF_MODEL_ID}'
HF_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN', '').strip()
HUGGINGFACE_ENABLED = os.getenv('HUGGINGFACE_ENABLED', 'true').lower() == 'true'

def detect_disease_from_image(image_bytes):
    """
    Detect disease from image bytes using API fallbacks.
    Returns standardized format: {"disease_name": str, "confidence": float}
    """
    logger.info("Starting disease detection for image")

    # Try Plant.id first (if API key available)
    if PLANT_ID_API_KEY:
        result = _detect_with_plantid(image_bytes)
        if result:
            logger.info(f"Disease detected via Plant.id: {result['disease_name']} ({result['confidence']})")
            return result

    # Fallback to Hugging Face
    if HUGGINGFACE_ENABLED:
        result = _detect_with_huggingface(image_bytes)
        if result:
            logger.info(f"Disease detected via Hugging Face: {result['disease_name']} ({result['confidence']})")
            return result

    # Fallback: return placeholder
    logger.warning("All disease detection APIs failed, returning placeholder")
    return {'disease_name': 'Unable to detect disease', 'confidence': 0.0}

def _detect_with_plantid(image_bytes):
    """Detect disease using Plant.id API"""
    try:
        logger.debug("Attempting Plant.id API call")
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            'images': [encoded_image],
            'modifiers': ['crops_fast', 'similar_images'],
            'plant_details': ['common_names', 'url', 'wiki_description', 'taxonomy']
        }
        headers = {
            'Api-Key': PLANT_ID_API_KEY,
            'Content-Type': 'application/json'
        }

        response = requests.post(PLANT_ID_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get('health_assessment') and result['health_assessment'].get('diseases') and len(result['health_assessment']['diseases']) > 0:
            top_disease = result['health_assessment']['diseases'][0]
            disease_name = top_disease.get('name', 'Unknown Disease')
            confidence = round(top_disease.get('probability', 0.0), 3)
            return {'disease_name': disease_name, 'confidence': confidence}
        elif result.get('suggestions') and len(result['suggestions']) > 0:
            # Fallback to plant identification if health assessment fails
            top_suggestion = result['suggestions'][0]
            disease_name = f"Healthy {top_suggestion.get('plant_name', 'Unknown Plant')}"
            confidence = round(top_suggestion.get('probability', 0.0), 3)
            return {'disease_name': disease_name, 'confidence': confidence}
    except requests.RequestException as e:
        logger.error(f"Plant.id API error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Plant.id parsing error: {str(e)}")
        return None

    return None

def _detect_with_huggingface(image_bytes):
    """Detect disease using Hugging Face Inference API (FREE fallback)"""
    try:
        logger.debug("Attempting Hugging Face API call")
        headers = {'Content-Type': 'image/jpeg'}
        if HF_API_TOKEN:
            headers['Authorization'] = f'Bearer {HF_API_TOKEN}'

        response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=10)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            top_result = result[0]
            disease_name = top_result.get('label', 'Unknown Disease')
            confidence = round(top_result.get('score', 0.0), 3)
            return {'disease_name': disease_name, 'confidence': confidence}
    except requests.RequestException as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Hugging Face parsing error: {str(e)}")
        return None
