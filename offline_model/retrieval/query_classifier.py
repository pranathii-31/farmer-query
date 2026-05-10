def classify_query(query):

    query = query.lower()

    recommendation_keywords = [
        "what crop",
        "what can i grow",
        "best crop",
        "suitable crop",
        "grow in",
        "low water",
        "dry land"
    ]

    weather_keywords = [
        "rain",
        "flood",
        "weather",
        "drought",
        "monsoon",
        "humidity",
        "heat wave"
    ]

    fertilizer_keywords = [
        "fertilizer",
        "urea",
        "npk",
        "dosage",
        "top dressing",
        "nutrient"
    ]

    for keyword in recommendation_keywords:
        if keyword in query:
            return "recommendation"

    for keyword in weather_keywords:
        if keyword in query:
            return "weather"

    for keyword in fertilizer_keywords:
        if keyword in query:
            return "fertilizer"

    return "advisory"