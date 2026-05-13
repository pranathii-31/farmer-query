# ML model inference with fallback support
# Primary: Plant.id API (if API key provided)
# Fallback 1: Hugging Face Inference API (FREE, rate limited)
# Fallback 2: Local database placeholder

import base64
import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

PLANT_ID_API_KEY = os.getenv('PLANT_ID_API_KEY', '').strip()
PLANT_ID_URL = 'https://api.plant.id/v2/health_assessment'
DEFAULT_HF_MODEL_ID = 'nateraw/vit-base-beans'

def _get_hf_config():
    """
    Read Hugging Face config from environment.
    We re-load `.env` with override so changes apply without a full server restart
    in debug mode.
    """
    load_dotenv(override=True)
    model_id = (os.getenv('HUGGINGFACE_MODEL_ID', DEFAULT_HF_MODEL_ID) or DEFAULT_HF_MODEL_ID).strip()
    # Legacy `api-inference.huggingface.co` has been deprecated; use the router endpoint.
    api_url = f'https://router.huggingface.co/hf-inference/models/{quote(model_id, safe="")}'
    api_token = (os.getenv('HUGGINGFACE_API_TOKEN', '') or '').strip()
    enabled = (os.getenv('HUGGINGFACE_ENABLED', 'true') or 'true').lower() == 'true'
    return enabled, api_token, model_id, api_url

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
    hf_enabled, _, _, _ = _get_hf_config()
    if hf_enabled:
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
            try:
                confidence = float(top_disease.get('probability', 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            return {'disease_name': disease_name, 'confidence': confidence}
        elif result.get('suggestions') and len(result['suggestions']) > 0:
            # Fallback to plant identification if health assessment fails
            top_suggestion = result['suggestions'][0]
            disease_name = f"Healthy {top_suggestion.get('plant_name', 'Unknown Plant')}"
            try:
                confidence = float(top_suggestion.get('probability', 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
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
        _, hf_api_token, hf_model_id, hf_api_url = _get_hf_config()
        logger.debug("Attempting Hugging Face API call")
        # Use octet-stream since uploads may be PNG/JPEG/etc.
        base_headers = {'Content-Type': 'application/octet-stream'}
        authed_headers = dict(base_headers)
        if hf_api_token:
            authed_headers['Authorization'] = f'Bearer {hf_api_token}'

        def _post(url: str):
            return requests.post(
                url,
                headers=authed_headers if hf_api_token else base_headers,
                data=image_bytes,
                timeout=10,
            )

        # Try with auth (if present). If token is invalid/mis-scoped, HF may return 401/403.
        # In that case, retry anonymously so the free fallback still works.
        response = _post(hf_api_url)
        if response.status_code in (401, 403) and hf_api_token:
            logger.warning(
                f"Hugging Face returned {response.status_code} with token; retrying without Authorization header"
            )
            response = requests.post(hf_api_url, headers=base_headers, data=image_bytes, timeout=10)

        # If the configured model isn't available via the Inference API, retry with a known-good default.
        if response.status_code == 404 and hf_model_id != DEFAULT_HF_MODEL_ID:
            fallback_url = f'https://router.huggingface.co/hf-inference/models/{quote(DEFAULT_HF_MODEL_ID, safe="")}'
            logger.warning(
                f"Hugging Face model '{hf_model_id}' returned 404; retrying with default model '{DEFAULT_HF_MODEL_ID}'"
            )
            response = _post(fallback_url)
            if response.status_code in (401, 403) and hf_api_token:
                response = requests.post(fallback_url, headers=base_headers, data=image_bytes, timeout=10)

        response.raise_for_status()
        result = response.json()

        # HF can return:
        # - list[{"label": str, "score": float}, ...] on success
        # - {"error": "...", ...} on failure (e.g., loading/rate limit)
        if isinstance(result, dict):
            if result.get('error'):
                logger.error(f"Hugging Face API returned error JSON: {result.get('error')}")
                return None
            # Some deployments return {"label": "...", "score": ...}
            if 'label' in result and 'score' in result:
                top_result = result
                try:
                    confidence = float(top_result.get('score', 0.0))
                except (TypeError, ValueError):
                    confidence = 0.0
                return {'disease_name': top_result.get('label', 'Unknown Disease'), 'confidence': confidence}

        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            top_result = result[0]
            disease_name = top_result.get('label', 'Unknown Disease')
            try:
                confidence = float(top_result.get('score', 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            # Keep more precision; callers can round for UI if needed.
            return {'disease_name': disease_name, 'confidence': confidence}
    except requests.RequestException as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Hugging Face parsing error: {str(e)}")
        return None
