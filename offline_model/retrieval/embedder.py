from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

os.makedirs("embeddings", exist_ok=True)

DOCUMENT_TYPES = [
    "advisory",
    "recommendation",
    "weather",
    "fertilizer"
]

for doc_type in DOCUMENT_TYPES:

    with open(f"documents/{doc_type}.pkl", "rb") as f:
        documents = pickle.load(f)

    texts = [doc["text"] for doc in documents]

    embeddings = model.encode(texts)

    np.save(
        f"embeddings/{doc_type}_embeddings.npy",
        embeddings
    )

    with open(
        f"embeddings/{doc_type}_mapping.pkl",
        "wb"
    ) as f:
        pickle.dump(documents, f)

    print(f"{doc_type} embeddings generated")