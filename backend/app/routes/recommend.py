from flask import Blueprint, request, jsonify
from app.services.recommender import recommend_programs

recommend_bp = Blueprint("recommend", __name__)


@recommend_bp.post("/")
def recommend():
    data = request.get_json() or {}

    profile = data.get("profile", {})

    results = recommend_programs(profile)

    return jsonify({
        "recommendations": results
    })