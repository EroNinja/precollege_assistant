from app.utils.helpers import load_programs


def score_program(program, profile):
    score = 0
    reasons = []

    # ---------- CORE MATCH ----------
    user_interest = profile.get("interest_area")
    program_interests = str(program.get("interests", "")).lower().split(",")

    if user_interest and any(user_interest in i.strip() for i in program_interests):
        score += 4
        reasons.append("strong match with your interest")
    else:
        score -= 2

    user_goal = profile.get("program_goal")
    program_goals = str(program.get("goals", "")).lower().split(",")

    if user_goal and any(user_goal in g.strip() for g in program_goals):
        score += 3
        reasons.append("aligned with your goal")

    # ---------- PREFERENCES ----------
    user_budget = profile.get("budget")
    if user_budget and user_budget == program.get("budget"):
        score += 1
        reasons.append("fits your budget")

    user_format = profile.get("format")
    if user_format and user_format == program.get("format"):
        score += 1
        reasons.append("matches preferred format")

    user_location = profile.get("location")
    program_location = program.get("location_preference") or program.get("location")
    if user_location and program_location and user_location == program_location:
        score += 1
        reasons.append("matches location preference")

    # ---------- ACADEMIC FIT ----------
    user_gpa = profile.get("gpa_range")
    program_gpa = program.get("recommended_gpa_range")
    if user_gpa and program_gpa:
        if user_gpa == program_gpa:
            score += 2
            reasons.append("good academic fit")
        else:
            score -= 1

    user_coursework = profile.get("coursework_level")
    program_coursework = program.get("coursework_background_expected")
    if user_coursework and program_coursework and user_coursework == program_coursework:
        score += 1
        reasons.append("coursework level matches")

    user_experience = profile.get("prior_experience")
    program_experience = program.get("prior_experience_expected")
    if user_experience and program_experience and user_experience == program_experience:
        score += 1
        reasons.append("experience level matches")

    # ---------- REAL PROGRAM BOOST ----------
    if str(program.get("source_type", "")).lower() == "real":
        score += 0.5

    return score, reasons


def recommend_programs(profile):
    programs = load_programs()
    scored = []

    for program in programs:
        score, reasons = score_program(program, profile)

        scored.append(
            {
                "name": program.get("name")
                or program.get("Program Name")
                or program.get("program_name"),
                "score": score,
                "reasons": reasons,
                "reasons_text": ", ".join(reasons) if reasons else "No strong match reasons found",
                "description": program.get("description")
                or program.get("Description")
                or "",
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:3]