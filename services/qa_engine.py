import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.db import get_faqs

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

# Load Models
try:
    disease_model = joblib.load(os.path.join(MODEL_DIR, 'disease_model.pkl'))
    water_model = joblib.load(os.path.join(MODEL_DIR, 'water_model.pkl'))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))
except FileNotFoundError:
    disease_model = None
    water_model = None
    label_encoder = None

def load_qa_corpus():
    faqs = get_faqs()
    if not faqs:
        return [], []
    questions = [faq['question'] for faq in faqs]
    answers = [faq['answer'] for faq in faqs]
    return questions, answers

def answer_question(query):
    questions, answers = load_qa_corpus()
    if not questions:
        return "I'm sorry, I don't have enough data to answer that right now."
        
    # Basic intent matching for water supply logic based on today's weather
    if "water supply" in query.lower() and "tomorrow" in query.lower():
        # Ideally, we would parse parameters, but as a fallback/FAQ match:
        pass
        
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(questions + [query])
    
    # Calculate similarity between the query (last item) and all questions
    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    best_match_idx = cosine_similarities.argmax()
    
    if cosine_similarities[best_match_idx] > 0.3:
        return answers[best_match_idx]
    
    return "I couldn't find a precise answer. Please consult the nearest agricultural office for specific details."
