import json
import pickle
import os

os.makedirs("documents", exist_ok=True)

# -------------------------
# Helper Function
# -------------------------

def save_documents(filename, documents):

    with open(f"documents/{filename}.pkl", "wb") as f:
        pickle.dump(documents, f)

    print(f"Saved {len(documents)} documents -> {filename}.pkl")


# -------------------------
# Advisory Documents
# -------------------------

advisory_docs = []

with open("datasets/mandya/advisory.json", "r") as f:
    data = json.load(f)

for item in data:

    text = f"""
    Crop: {item['crop']}

    Category: {item['category']}

    Symptoms:
    {", ".join(item['query_examples'])}

    Cause:
    {item['cause']}

    Solution:
    {item['solution']}
    """

    advisory_docs.append({
        "id": item["id"],
        "text": text.strip(),
        "metadata": item
    })

save_documents("advisory", advisory_docs)

# -------------------------
# Recommendation Documents
# -------------------------

recommendation_docs = []

with open("datasets/mandya/crops.json", "r") as f:
    data = json.load(f)

for idx, item in enumerate(data):

    text = f"""
    Crop: {item['crop']}

    Season:
    {item['season']}

    Water Requirement:
    {item['water_requirement']}

    Soil Types:
    {", ".join(item['soil_type'])}

    Suitable Conditions:
    {", ".join(item['suitable_conditions'])}
    """

    recommendation_docs.append({
        "id": idx,
        "text": text.strip(),
        "metadata": item
    })

save_documents("recommendation", recommendation_docs)

# -------------------------
# Weather Documents
# -------------------------

weather_docs = []

with open("datasets/mandya/weather.json", "r") as f:
    data = json.load(f)

for idx, item in enumerate(data):

    text = f"""
    Season:
    {item['season']}

    Condition:
    {item['condition']}

    Affected Crops:
    {", ".join(item['affected_crops'])}

    Advisory:
    {item['advisory']}
    """

    weather_docs.append({
        "id": idx,
        "text": text.strip(),
        "metadata": item
    })

save_documents("weather", weather_docs)

# -------------------------
# Fertilizer Documents
# -------------------------

fertilizer_docs = []

with open("datasets/mandya/fertilizer.json", "r") as f:
    data = json.load(f)

for idx, item in enumerate(data):

    text = f"""
    Crop:
    {item['crop']}

    Stage:
    {item['stage']}

    Fertilizer:
    {item['fertilizer']}

    Dosage:
    {item['dosage']}

    Method:
    {item['method']}
    """

    fertilizer_docs.append({
        "id": idx,
        "text": text.strip(),
        "metadata": item
    })

save_documents("fertilizer", fertilizer_docs)