import numpy as np
import pickle

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from query_classifier import classify_query

model = SentenceTransformer('all-MiniLM-L6-v2')

THRESHOLD = 0.45

# -------------------------
# Load Embeddings
# -------------------------

embedding_cache = {}
document_cache = {}

DOCUMENT_TYPES = [
    "advisory",
    "recommendation",
    "weather",
    "fertilizer"
]

for doc_type in DOCUMENT_TYPES:

    embedding_cache[doc_type] = np.load(
        f"embeddings/{doc_type}_embeddings.npy"
    )

    with open(
        f"embeddings/{doc_type}_mapping.pkl",
        "rb"
    ) as f:
        document_cache[doc_type] = pickle.load(f)

print("System Ready")

# -------------------------
# Query Loop
# -------------------------

while True:

    query = input("\nFarmer Query: ")

    if query.lower() == "exit":
        break

    query_type = classify_query(query)

    embeddings = embedding_cache[query_type]
    documents = document_cache[query_type]

    query_embedding = model.encode([query])

    similarities = cosine_similarity(
        query_embedding,
        embeddings
    )[0]

    best_idx = np.argmax(similarities)

    best_score = similarities[best_idx]

    if best_score < THRESHOLD:

        print("\nLow confidence.")
        print("Escalate to online/SMS support.")

        continue

    result = documents[best_idx]

    metadata = result["metadata"]

    print("\n--- Advisory Response ---")

    for key, value in metadata.items():
        print(f"{key}: {value}")

    print(f"\nSimilarity Score: {best_score:.2f}")