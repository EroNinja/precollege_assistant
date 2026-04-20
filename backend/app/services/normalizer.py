from app.utils.helpers import load_option_maps


def normalize_answer(question_id: str, user_text: str) -> dict:
    option_maps = load_option_maps()
    normalized_value = None
    confidence = 0.0

    clean_text = user_text.strip().lower()

    question_map = option_maps.get(question_id, {})

    for canonical_option, synonyms in question_map.items():
        for synonym in synonyms:
            if synonym.lower() in clean_text:
                normalized_value = canonical_option
                confidence = 0.9
                break
        if normalized_value:
            break

    if not normalized_value:
        confidence = 0.2

    return {
        "raw_text": user_text,
        "cleaned_text": user_text.strip(),
        "normalized_value": normalized_value,
        "confidence": confidence
    }