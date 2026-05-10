# Services for recommendations and advice
# Handles yojna, crop health tips, and disease advice

from database.db import get_db
from utils.logger import logger
import os
from dotenv import load_dotenv
from utils.helpers import canonicalize_crop, canonicalize_disease, canonicalize_state, normalize_string

load_dotenv()


def get_disease_advice(disease_name):
    """Return treatment/fertilizer/prevention for a disease from the local DB."""
    try:
        canonical = canonicalize_disease(disease_name)
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            'SELECT treatment, fertilizer, prevention FROM diseases WHERE LOWER(name) = LOWER(?)',
            (canonical,)
        )
        row = cur.fetchone()
        if row:
            return {'treatment': row[0], 'fertilizer': row[1], 'prevention': row[2]}
        return None
    except Exception as e:
        logger.error(f"Error getting disease advice: {e}")
        return None


def get_yojna_recommendations(crop, state, disease=None):
    """
    Return a de-duplicated list of relevant government schemes.

    Matching priority (all matching rows are collected, then de-duplicated by name):
      1. Disease-specific match  (crop/state/disease all match)
      2. Crop + state match      (disease=NULL in DB)
      3. Crop-only match         (state=NULL & disease=NULL)
      4. State-only match        (crop=NULL & disease=NULL)
      5. National schemes        (crop=NULL & state=NULL & disease=NULL)

    Returns: list of dicts with keys: name, description, link
    """
    try:
        canonical_crop    = canonicalize_crop(crop) if crop else None
        canonical_state   = canonicalize_state(state) if state else None
        canonical_disease = canonicalize_disease(disease) if disease else None

        db  = get_db()
        cur = db.cursor()

        # Build a UNION query that pulls all potentially matching rows and
        # tags each with a priority so we can rank them later.
        # Priority 1 = most specific, 5 = least specific (national catch-all).

        params = []
        queries = []

        # 1. Disease + crop + state specific
        if canonical_disease and canonical_crop and canonical_state:
            queries.append("""
                SELECT 1 AS priority, name, description, link
                FROM yojnas
                WHERE LOWER(COALESCE(disease,'')) = LOWER(?)
                  AND LOWER(COALESCE(crop,''))    = LOWER(?)
                  AND LOWER(COALESCE(state,''))   = LOWER(?)
            """)
            params += [canonical_disease, canonical_crop, canonical_state]

        # 2. Disease + crop (any state)
        if canonical_disease and canonical_crop:
            queries.append("""
                SELECT 2 AS priority, name, description, link
                FROM yojnas
                WHERE LOWER(COALESCE(disease,'')) = LOWER(?)
                  AND LOWER(COALESCE(crop,''))    = LOWER(?)
                  AND state IS NULL
            """)
            params += [canonical_disease, canonical_crop]

        # 3. Disease only (any crop / state)
        if canonical_disease:
            queries.append("""
                SELECT 3 AS priority, name, description, link
                FROM yojnas
                WHERE LOWER(COALESCE(disease,'')) = LOWER(?)
                  AND crop  IS NULL
                  AND state IS NULL
            """)
            params += [canonical_disease]

        # 4. Crop + state specific (no disease restriction)
        if canonical_crop and canonical_state:
            queries.append("""
                SELECT 4 AS priority, name, description, link
                FROM yojnas
                WHERE LOWER(COALESCE(crop,''))  = LOWER(?)
                  AND LOWER(COALESCE(state,'')) = LOWER(?)
                  AND disease IS NULL
            """)
            params += [canonical_crop, canonical_state]

        # 5. Crop only (any state, no disease restriction)
        if canonical_crop:
            queries.append("""
                SELECT 5 AS priority, name, description, link
                FROM yojnas
                WHERE LOWER(COALESCE(crop,'')) = LOWER(?)
                  AND state   IS NULL
                  AND disease IS NULL
            """)
            params += [canonical_crop]

        # 6. State only (any crop, no disease restriction)
        if canonical_state:
            queries.append("""
                SELECT 6 AS priority, name, description, link
                FROM yojnas
                WHERE LOWER(COALESCE(state,'')) = LOWER(?)
                  AND crop    IS NULL
                  AND disease IS NULL
            """)
            params += [canonical_state]

        # 7. National / all-crop schemes
        queries.append("""
            SELECT 7 AS priority, name, description, link
            FROM yojnas
            WHERE crop    IS NULL
              AND state   IS NULL
              AND disease IS NULL
        """)

        full_query = " UNION ALL ".join(queries) + " ORDER BY priority ASC"
        cur.execute(full_query, params)
        rows = cur.fetchall()

        # De-duplicate: keep the first occurrence of each scheme name
        # (which will be the highest-priority match)
        seen = set()
        results = []
        for _, name, description, link in rows:
            key = name.strip().lower()
            if key not in seen:
                seen.add(key)
                results.append({
                    'name':        name,
                    'description': description or '',
                    'link':        link or '',
                })

        return results

    except Exception as e:
        logger.error(f"Error getting yojna recommendations: {e}")
        return []


def get_crop_health_tips(crop):
    """Return crop-specific health tips from the local DB."""
    try:
        canonical = canonicalize_crop(crop)
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            'SELECT tips FROM crop_health_tips WHERE LOWER(crop) = LOWER(?)',
            (canonical,)
        )
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error getting crop health tips: {e}")
        return None


def get_full_recommendation(image_bytes, crop, state, lat=None, lon=None):
    """
    Full pipeline:
      image → disease detection → advice → yojna → health tips → nearby centres

    Returns a single flat dict ready to be JSON-serialised.
    """
    from services.ml_model import detect_disease_from_image
    from services.location_service import find_nearby_centers

    logger.info("Starting full recommendation pipeline")

    canonical_crop  = canonicalize_crop(crop)
    canonical_state = canonicalize_state(state) if state else 'karnataka'

    # 1. Detect disease
    disease_result   = detect_disease_from_image(image_bytes)
    disease_name     = disease_result['disease_name']
    canonical_disease = canonicalize_disease(disease_name)

    # 2. Disease advice
    advice = get_disease_advice(canonical_disease)

    # 3. Yojna — pass detected disease so disease-specific schemes are included
    yojna_list = get_yojna_recommendations(
        canonical_crop, canonical_state, disease=canonical_disease
    )

    # 4. Crop health tips
    health_tips = get_crop_health_tips(canonical_crop)

    # 5. Nearby centres (only when coordinates provided)
    centers = []
    if lat is not None and lon is not None:
        centers = find_nearby_centers(lat, lon, radius_km=50)

    # Format nearby centres
    formatted_centers = [
        {
            'name':        c.get('name', 'Unknown Centre'),
            'distance_km': round(c.get('distance_km', 0.0), 2),
        }
        for c in centers
    ]

    result = {
        'disease':        disease_name,
        'confidence':     disease_result['confidence'],
        'treatment':      advice.get('treatment', 'Apply appropriate fungicide based on local recommendations') if advice else 'Consult local agricultural extension for treatment options',
        'fertilizer':     advice.get('fertilizer', 'Use balanced NPK fertilizer suitable for the crop') if advice else 'Apply balanced NPK fertilizer',
        'prevention':     advice.get('prevention', 'Practice good agricultural management') if advice else 'Ensure proper crop management and monitoring',
        'health_tips':    health_tips or f"General tips for {canonical_crop}: Ensure proper irrigation, monitor for pests, rotate crops annually.",
        'yojna':          yojna_list,          # list of {name, description, link}
        'nearby_centers': formatted_centers,
    }

    logger.info("Full recommendation pipeline completed")
    return result
