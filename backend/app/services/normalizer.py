import re
from difflib import SequenceMatcher

from app.utils.helpers import load_option_maps, load_questions

try:
    import ollama
except ImportError:
    ollama = None


OLLAMA_MODEL = "llama3.1:8b"


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9+\-/.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def get_question_config(question_id: str) -> dict:
    questions = load_questions()
    for q in questions:
        if q.get("id") == question_id:
            return q
    return {}


def llm_fallback(question_id: str, user_text: str) -> dict:
    question_config = get_question_config(question_id)
    question_text = question_config.get("text", "")
    allowed_options = question_config.get("options", [])
    option_maps = load_option_maps()
    question_map = option_maps.get(question_id, {})

    if not allowed_options or ollama is None:
        return {
            "normalized_value": None,
            "confidence": 0.20,
            "match_method": "llm_unavailable",
        }

    synonym_lines = []
    for option in allowed_options:
        synonyms = question_map.get(option, [])
        synonym_lines.append(f"{option}: {', '.join(synonyms) if synonyms else 'no synonyms'}")

    synonym_block = "\n".join(synonym_lines)
    options_block = "\n".join([f"- {opt}" for opt in allowed_options])

    system_prompt = """
You are a strict classifier for a pre-college recommendation system.

Choose exactly ONE best canonical option from the allowed options.
Use the synonym hints to understand misspellings and paraphrases.

Rules:
- Reply with only one line.
- That line must be exactly one of the allowed options, or exactly: null
- Do not explain anything.
- Do not use JSON.
"""

    user_prompt = f"""
Question ID: {question_id}
Question: {question_text}

Allowed options:
{options_block}

Synonym hints:
{synonym_block}

User answer:
{user_text}
"""

    try:
        print("LLM fallback triggered for:", question_id, "| input:", user_text)
        print("Using model:", OLLAMA_MODEL)

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0},
        )

        content = response["message"]["content"].strip()
        print("Raw LLM output:", content)

        if content == "null":
            return {
                "normalized_value": None,
                "confidence": 0.20,
                "match_method": "llm_null",
            }

        cleaned = content.strip().strip('"').strip("'")
        if cleaned in allowed_options:
            return {
                "normalized_value": cleaned,
                "confidence": 0.80,
                "match_method": "llm_fallback",
            }

        return {
            "normalized_value": None,
            "confidence": 0.20,
            "match_method": "llm_invalid_output",
        }

    except Exception as e:
        print("LLM fallback error:", str(e))
        return {
            "normalized_value": None,
            "confidence": 0.20,
            "match_method": "llm_error",
        }


def normalize_answer(question_id: str, user_text: str) -> dict:
    option_maps = load_option_maps()
    question_map = option_maps.get(question_id, {})

    raw_text = user_text.strip()
    clean_input = clean_text(raw_text)

    if not clean_input:
        return {
            "raw_text": raw_text,
            "cleaned_text": raw_text,
            "normalized_value": None,
            "confidence": 0.20,
            "match_method": "empty_input",
        }

    # 1. exact canonical match
    for canonical_option in question_map.keys():
        if clean_input == clean_text(canonical_option):
            return {
                "raw_text": raw_text,
                "cleaned_text": raw_text,
                "normalized_value": canonical_option,
                "confidence": 0.99,
                "match_method": "exact_canonical",
            }

    # 2. exact synonym / substring synonym
    for canonical_option, synonyms in question_map.items():
        for synonym in synonyms:
            clean_synonym = clean_text(synonym)

            if clean_input == clean_synonym:
                return {
                    "raw_text": raw_text,
                    "cleaned_text": raw_text,
                    "normalized_value": canonical_option,
                    "confidence": 0.95,
                    "match_method": "exact_synonym",
                }

            if clean_synonym in clean_input or clean_input in clean_synonym:
                return {
                    "raw_text": raw_text,
                    "cleaned_text": raw_text,
                    "normalized_value": canonical_option,
                    "confidence": 0.90,
                    "match_method": "substring_synonym",
                }

    # 3. fuzzy match FIRST
    best_option = None
    best_score = 0.0
    best_candidate = None

    for canonical_option, synonyms in question_map.items():
        candidates = [canonical_option] + synonyms
        for candidate in candidates:
            score = similarity(clean_input, clean_text(candidate))
            if score > best_score:
                best_score = score
                best_option = canonical_option
                best_candidate = candidate

    # Lower thresholds for short typo-style inputs
    fuzzy_threshold = 0.84
    if len(clean_input) <= 8:
        fuzzy_threshold = 0.72
    elif len(clean_input) <= 15:
        fuzzy_threshold = 0.78

    if best_option and best_score >= fuzzy_threshold:
        print(
            "Fuzzy match used for:",
            question_id,
            "| input:",
            user_text,
            "| candidate:",
            best_candidate,
            "| option:",
            best_option,
            "| score:",
            round(best_score, 2),
        )
        return {
            "raw_text": raw_text,
            "cleaned_text": raw_text,
            "normalized_value": best_option,
            "confidence": round(min(max(best_score, 0.75), 0.94), 2),
            "match_method": f"fuzzy:{best_candidate}",
        }

    # 4. only THEN use LLM fallback
    llm_result = llm_fallback(question_id, raw_text)

    return {
        "raw_text": raw_text,
        "cleaned_text": raw_text,
        "normalized_value": llm_result["normalized_value"],
        "confidence": llm_result["confidence"],
        "match_method": llm_result["match_method"],
    }