from flask import Blueprint, request, jsonify
from app.utils.helpers import load_questions
from app.services.normalizer import normalize_answer

chat_bp = Blueprint("chat", __name__)


@chat_bp.get("/questions")
def get_questions():
    questions = load_questions()
    return jsonify({"questions": questions})


@chat_bp.post("/answer")
def process_answer():
    data = request.get_json() or {}

    question_id = data.get("question_id")
    user_text = data.get("user_text", "").strip()

    normalized = normalize_answer(question_id, user_text)

    return jsonify({
        "question_id": question_id,
        "raw_text": normalized["raw_text"],
        "cleaned_text": normalized["cleaned_text"],
        "structured_fields": {
            "normalized_value": normalized["normalized_value"],
            "confidence": normalized["confidence"]
        },
        "next_step": "placeholder"
    })