import json
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


def load_questions():
    questions_path = DATA_DIR / "questions" / "questions.json"
    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_option_maps():
    maps_path = DATA_DIR / "mappings" / "option_maps.json"
    with open(maps_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_programs():
    programs_path = DATA_DIR / "programs" / "programs.csv"
    df = pd.read_csv(programs_path)
    return df.to_dict(orient="records")