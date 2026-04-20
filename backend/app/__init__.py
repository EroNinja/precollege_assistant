from flask import Flask
from flask_cors import CORS

from app.routes.chat import chat_bp
from app.routes.recommend import recommend_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(recommend_bp, url_prefix="/api/recommend")

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "message": "Backend is running"}

    return app