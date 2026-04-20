from flask import Blueprint, request, jsonify
from services.analyzer import generate_advisory
from services.qa_engine import answer_question
from database.db import get_history, get_faqs

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    required_fields = ['crop', 'temperature', 'humidity', 'market_price']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
            
    try:
        response = generate_advisory(
            crop=data['crop'],
            temp=float(data['temperature']),
            humidity=float(data['humidity']),
            market_price=float(data['market_price'])
        )
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({"error": "Please provide a 'question' in the JSON payload"}), 400
        
    try:
        answer = answer_question(data['question'])
        return jsonify({
            "question": data['question'],
            "answer": answer
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/history', methods=['GET'])
def history():
    try:
        limit = request.args.get('limit', default=10, type=int)
        logs = get_history(limit)
        return jsonify({"history": logs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/faqs', methods=['GET'])
def faqs():
    try:
        faqs_data = get_faqs()
        return jsonify({"faqs": faqs_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
