import json
import os
import pickle
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer, util

class AdvisoryEngine:
    # Simple list of stop words to remove 'noise' from queries
    STOP_WORDS = {"the", "is", "are", "will", "be", "to", "for", "of", "a", "an", "this", "that", "it", "tomorrow", "yesterday", "can", "i", "you", "my"}

    def __init__(self, data_path="advisories.json", model_name='all-MiniLM-L6-v2', cache_path="embeddings.pkl"):
        self.data_path = data_path
        self.cache_path = cache_path
        self.advisories = self._load_data()
        
        print(f"Loading embedding model ({model_name})...")
        self.model = SentenceTransformer(model_name)
        
        # Indexing crops and symptoms separately
        self.index_data = []
        for item in self.advisories:
            self.index_data.append(item['crop'])
            self.index_data.append(item['symptom'])
            self.index_data.append(f"{item['crop']} {item['symptom']}")
        
        self.corpus_embeddings = self._get_embeddings()

    def _load_data(self):
        if not os.path.exists(self.data_path):
            return []
        with open(self.data_path, "r") as f:
            return json.load(f)

    def _get_data_hash(self):
        with open(self.data_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_embeddings(self):
        current_hash = self._get_data_hash()
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                cache = pickle.load(f)
                if cache.get("hash") == current_hash:
                    return cache["embeddings"]
        
        embeddings = self.model.encode(self.index_data, convert_to_tensor=True)
        with open(self.cache_path, "wb") as f:
            pickle.dump({"hash": current_hash, "embeddings": embeddings}, f)
        return embeddings

    def _clean_query(self, query):
        """Remove common stop words to focus on meaningful keywords."""
        words = query.lower().split()
        cleaned_words = [w for w in words if w not in self.STOP_WORDS]
        return " ".join(cleaned_words) if cleaned_words else query

    def search(self, query, threshold=0.35, top_k=3):
        if not query:
            return []

        # Remove noise words (e.g., 'will', 'be', 'tomorrow')
        cleaned_query = self._clean_query(query)
        
        query_embedding = self.model.encode(cleaned_query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        
        advisory_scores = []
        for i in range(len(self.advisories)):
            score = max(cos_scores[i*3], cos_scores[i*3+1], cos_scores[i*3+2]).item()
            advisory_scores.append(score)
        
        results = []
        sorted_indices = np.argsort(-np.array(advisory_scores))
        
        # Determine the top score to apply relative thresholding
        top_score = advisory_scores[sorted_indices[0]] if len(sorted_indices) > 0 else 0
        
        for idx in sorted_indices[:top_k]:
            score = advisory_scores[idx]
            
            # 1. Base threshold check
            if score < threshold:
                continue
                
            # 2. Relative threshold check:
            # If we have a very strong match (>85%), ignore anything that is much weaker.
            # This prevents 'rice' from showing 'coffee' just because they are both crops.
            if top_score > 0.85 and score < (top_score * 0.7):
                continue
                
            item = self.advisories[idx].copy()
            item['similarity_score'] = score
            results.append(item)
                    
        return results
