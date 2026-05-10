import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# -----------------------------
# Load Dataset
# -----------------------------
with open("dataset.json", "r") as f:
    dataset = json.load(f)

# -----------------------------
# Load Embedding Model
# -----------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')

# -----------------------------
# Prepare Training Sentences
# -----------------------------
all_sentences = []
sentence_to_entry = []

for entry in dataset:
    for sentence in entry["query_examples"]:
        all_sentences.append(sentence)
        sentence_to_entry.append(entry)

# -----------------------------
# Generate Embeddings
# -----------------------------
embeddings = model.encode(all_sentences)

print("System Ready")
print("Type 'exit' to stop")

# -----------------------------
# Query Loop
# -----------------------------
while True:
    user_query = input("\nFarmer Query: ")

    if user_query.lower() == "exit":
        break

    # Convert query to embedding
    query_embedding = model.encode([user_query])

    # Calculate similarity
    similarities = cosine_similarity(query_embedding, embeddings)[0]

    # Find best match
    best_match_index = np.argmax(similarities)

    matched_entry = sentence_to_entry[best_match_index]

    # Display response
    print("\n--- Advisory Response ---")
    print(f"Crop: {matched_entry['crop']}")
    print(f"Category: {matched_entry['category']}")
    print(f"Possible Cause: {matched_entry['cause']}")
    print(f"Recommended Action: {matched_entry['solution']}")
    print(f"Similarity Score: {similarities[best_match_index]:.2f}")