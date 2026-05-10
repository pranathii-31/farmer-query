from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from routes.disease import disease_bp
from routes.yojna import yojna_bp
from routes.health import health_bp
from routes.centers import centers_bp
from routes.recommendation import recommendation_bp

def create_app():
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization", "Accept"],
        methods=["GET", "POST", "OPTIONS"],
        supports_credentials=False,
    )

    # Register blueprints
    app.register_blueprint(disease_bp)
    app.register_blueprint(yojna_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(centers_bp)
    app.register_blueprint(recommendation_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
