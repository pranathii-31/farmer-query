from flask import Flask, jsonify
from routes.api import api_blueprint
from database.db import init_db

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(api_blueprint, url_prefix='/api')

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the Farmer Advisory Backend API",
        "endpoints": {
            "/api/analyze": "POST - Analyze crop data",
            "/api/ask": "POST - Ask a question",
            "/api/history": "GET - View analysis history",
            "/api/faqs": "GET - View FAQs"
        }
    })

# Initialize SQLite database
with app.app_context():
    init_db()

if __name__ == '__main__':
    # Run the Flask app on localhost (offline constraint)
    app.run(host='127.0.0.1', port=5001, debug=True)
