# Utility functions for the backend

import re
from utils.logger import logger


def validate_image(file):
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    filename = file.filename.lower()
    if '.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions:
        # Accept if content_type starts with image/ OR is the generic
        # octet-stream that some mobile clients send by default
        ct = getattr(file, 'content_type', '') or ''
        if ct.startswith('image/') or ct == 'application/octet-stream' or ct == '':
            return True
    return False


def format_response(data, status=200, error=None):
    """Standardized response format for all APIs."""
    return {
        "status": status,
        "data": data,
        "error": error,
    }


def validate_crop(crop):
    """Validate crop parameter — must be a non-empty string (letters/spaces only)."""
    if not crop or not isinstance(crop, str):
        return False
    sanitized = crop.strip()
    if len(sanitized) == 0:
        return False
    # Reject strings that are purely digits or contain suspicious characters
    if re.fullmatch(r"[\w\s\-]+", sanitized, flags=re.UNICODE) is None:
        return False
    return True


def validate_disease(disease):
    """Validate disease parameter — must be a non-empty string."""
    if not disease or not isinstance(disease, str):
        return False
    sanitized = disease.strip()
    if len(sanitized) == 0:
        return False
    if re.fullmatch(r"[\w\s\-]+", sanitized, flags=re.UNICODE) is None:
        return False
    return True


def validate_coordinates(lat, lon):
    """Validate latitude (-90..90) and longitude (-180..180)."""
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
            return True
    except (ValueError, TypeError):
        pass
    return False


def sanitize_string(value):
    """Strip characters that are not letters, digits, spaces, hyphens or underscores."""
    if not value:
        return ""
    return re.sub(r"[^\w\s\-]", "", value, flags=re.UNICODE).strip()


def normalize_string(value):
    """Normalize string: lowercase and strip surrounding whitespace."""
    if not value:
        return ""
    return value.lower().strip()


def canonicalize_crop(crop):
    """Map common crop names / synonyms to their canonical DB form."""
    crop_map = {
        # Gourds / cucurbits — squash and pumpkin are distinct crops
        "pumpkin": "pumpkin",
        "cucurbita maxima": "pumpkin",
        "squash": "squash",
        "zucchini": "zucchini",
        "cucumber": "cucumber",
        # Grains
        "wheat": "wheat",
        "rice": "rice",
        "maize": "maize",
        "corn": "maize",          # single, consistent alias
        # Fibre / cash crops
        "cotton": "cotton",
        "sugarcane": "sugarcane",
        "jute": "jute",
        "flax": "flax",
        "hemp": "hemp",
        # Vegetables
        "tomato": "tomato",
        "potato": "potato",
        "onion": "onion",
        "garlic": "garlic",
        "carrot": "carrot",
        "beet": "beet",
        "lettuce": "lettuce",
        "spinach": "spinach",
        "cabbage": "cabbage",
        "broccoli": "broccoli",
        "cauliflower": "cauliflower",
        "brussels sprouts": "brussels sprouts",
        "kale": "kale",
        "peas": "peas",
        "beans": "beans",
        "pepper": "pepper",
        "eggplant": "eggplant",
        "okra": "okra",
        "chili": "chili",
        # Spices / herbs
        "ginger": "ginger",
        "turmeric": "turmeric",
        # Fruits
        "banana": "banana",
        "mango": "mango",
        "orange": "orange",
        "apple": "apple",
        "grape": "grape",
        "strawberry": "strawberry",
        "blueberry": "blueberry",
        "raspberry": "raspberry",
        "blackberry": "blackberry",
        # Plantation crops
        "coffee": "coffee",
        "tea": "tea",
        "coconut": "coconut",
        # Nuts
        "cashew": "cashew",
        "almond": "almond",
        "walnut": "walnut",
        "pistachio": "pistachio",
        "peanut": "peanut",
        # Oil seeds / legumes
        "soybean": "soybean",
        "sunflower": "sunflower",
    }
    normalized = normalize_string(crop)
    return crop_map.get(normalized, normalized)


def canonicalize_disease(disease):
    """Map common disease names / synonyms to their canonical DB form."""
    disease_map = {
        "blight": "blight",
        "late blight": "late blight",
        "early blight": "early blight",
        "rust": "rust",
        "powdery mildew": "powdery mildew",
        "downy mildew": "downy mildew",
        "fusarium wilt": "fusarium wilt",
        "bacterial spot": "bacterial spot",
        "anthracnose": "anthracnose",
        "alternaria leaf spot": "alternaria leaf spot",
        "cercospora leaf spot": "cercospora leaf spot",
        "septoria leaf spot": "septoria leaf spot",
        "black spot": "black spot",
        "gray mold": "gray mold",
        "root rot": "root rot",
        "damping off": "damping off",
        "verticillium wilt": "verticillium wilt",
        "fungal leaf spot": "fungal leaf spot",
        "bacterial wilt": "bacterial wilt",
        "mosaic virus": "mosaic virus",
        "cucumber mosaic virus": "cucumber mosaic virus",
        "tobacco mosaic virus": "tobacco mosaic virus",
        "yellow mosaic virus": "yellow mosaic virus",
        "leaf curl virus": "leaf curl virus",
        "tomato yellow leaf curl virus": "tomato yellow leaf curl virus",
        "potato virus y": "potato virus y",
        "bean common mosaic virus": "bean common mosaic virus",
        "squash mosaic virus": "squash mosaic virus",
        "watermelon mosaic virus": "watermelon mosaic virus",
        "zucchini yellow mosaic virus": "zucchini yellow mosaic virus",
        "cabbage looper": "cabbage looper",
        "aphid": "aphid",
        "whitefly": "whitefly",
        "thrips": "thrips",
        "spider mite": "spider mite",
        "cutworm": "cutworm",
        "corn earworm": "corn earworm",
        "tomato hornworm": "tomato hornworm",
        "flea beetle": "flea beetle",
        "colorado potato beetle": "colorado potato beetle",
        "mexican bean beetle": "mexican bean beetle",
        "squash bug": "squash bug",
        "stink bug": "stink bug",
        "leafhopper": "leafhopper",
        "scale insect": "scale insect",
        "mealybug": "mealybug",
        "root knot nematode": "root knot nematode",
        "cyst nematode": "cyst nematode",
        "lesion nematode": "lesion nematode",
        "stubby root nematode": "stubby root nematode",
        "ditylenchus nematode": "ditylenchus nematode",
    }
    normalized = normalize_string(disease)
    return disease_map.get(normalized, normalized)


def canonicalize_state(state):
    """Map Indian state names and abbreviations to their canonical DB form."""
    state_map = {
        "karnataka": "karnataka",
        "maharashtra": "maharashtra",
        "punjab": "punjab",
        "uttar pradesh": "uttar pradesh",
        "up": "uttar pradesh",
        "andhra pradesh": "andhra pradesh",
        "ap": "andhra pradesh",
        "telangana": "telangana",
        "tamil nadu": "tamil nadu",
        "tn": "tamil nadu",
        "kerala": "kerala",
        "gujarat": "gujarat",
        "rajasthan": "rajasthan",
        "madhya pradesh": "madhya pradesh",
        "mp": "madhya pradesh",
        "west bengal": "west bengal",
        "wb": "west bengal",
        "bihar": "bihar",
        "odisha": "odisha",
        "haryana": "haryana",
        "himachal pradesh": "himachal pradesh",
        "hp": "himachal pradesh",
        "assam": "assam",
        "jharkhand": "jharkhand",
        "chhattisgarh": "chhattisgarh",
        "uttarakhand": "uttarakhand",
        "goa": "goa",
        "tripura": "tripura",
        "manipur": "manipur",
        "meghalaya": "meghalaya",
        "nagaland": "nagaland",
        "arunachal pradesh": "arunachal pradesh",
        "mizoram": "mizoram",
        "sikkim": "sikkim",
    }
    normalized = normalize_string(state)
    return state_map.get(normalized, normalized)
