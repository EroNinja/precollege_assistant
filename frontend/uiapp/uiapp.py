import reflex as rx
import requests

BACKEND_URL = "http://127.0.0.1:5000"


class State(rx.State):
    questions: list[dict] = []
    current_question_index: int = 0
    user_input: str = ""
    chat_history: list[dict] = []
    loading_questions: bool = False
    profile: dict = {}
    recommendations: list[dict] = []

    featured_biomed: list[dict] = [
        {
            "name": "Stanford AIMI Summer Research Internship",
            "tag": "Medicine + AI",
            "desc": "Selective research experience at the intersection of medicine and artificial intelligence."
        },
        {
            "name": "Evergreen Future Lab Elite Bootcamp in Biomedical Engineering",
            "tag": "Biomedical Engineering",
            "desc": "Hands-on biomedical engineering and research-oriented summer learning."
        },
        {
            "name": "Meridian Scholars Collective Applied Summer Academy in Pre-Med",
            "tag": "Pre-Med",
            "desc": "A strong option for students exploring medicine, research, and healthcare exposure."
        },
    ]

    featured_cs: list[dict] = [
        {
            "name": "MIT Introduction to Deep Learning",
            "tag": "AI / ML",
            "desc": "A strong option for students interested in machine learning and practical projects."
        },
        {
            "name": "Arizona State University Online Coding Camp",
            "tag": "Coding",
            "desc": "Accessible online coding experience for students exploring software and CS."
        },
        {
            "name": "Future Systems Youth Academy in Computer Science",
            "tag": "Computer Science",
            "desc": "A broad CS-focused program with applied projects and problem-solving."
        },
    ]

    featured_business: list[dict] = [
        {
            "name": "Berkeley Business Academy for Youth",
            "tag": "Business",
            "desc": "Leadership, entrepreneurship, and business strategy exposure."
        },
        {
            "name": "Summit Edge Young Founders Lab",
            "tag": "Entrepreneurship",
            "desc": "For students interested in startups, innovation, and venture thinking."
        },
        {
            "name": "Northbridge Finance Scholars Program",
            "tag": "Finance",
            "desc": "A strong fit for students interested in markets, finance, and business careers."
        },
    ]

    def set_user_input(self, value: str):
        self.user_input = value

    def load_questions(self):
        self.loading_questions = True
        self.current_question_index = 0
        self.user_input = ""
        self.profile = {}
        self.recommendations = []

        try:
            response = requests.get(f"{BACKEND_URL}/api/chat/questions", timeout=30)
            data = response.json()
            self.questions = data.get("questions", [])

            if self.questions:
                first_question = self.questions[0]["text"]
                self.chat_history = [
                    {
                        "role": "assistant",
                        "text": "Hi! I’ll help match you to pre-college programs.",
                    },
                    {
                        "role": "assistant",
                        "text": first_question,
                    },
                ]
            else:
                self.chat_history = [
                    {
                        "role": "assistant",
                        "text": "I couldn't load the question flow.",
                    }
                ]
        except Exception as e:
            self.questions = []
            self.chat_history = [
                {
                    "role": "assistant",
                    "text": f"Sorry, I couldn't load the questions. Error: {str(e)}",
                }
            ]

        self.loading_questions = False

    @rx.var
    def has_questions(self) -> bool:
        return len(self.questions) > 0

    @rx.var
    def is_finished(self) -> bool:
        return self.has_questions and self.current_question_index >= len(self.questions)

    @rx.var
    def progress_text(self) -> str:
        if not self.questions:
            return "0 / 0"
        completed = min(self.current_question_index + 1, len(self.questions))
        return f"{completed} / {len(self.questions)}"

    @rx.var
    def profile_summary(self) -> str:
        if not self.profile:
            return "Your answers will be converted into a structured student profile."

        parts = []

        if self.profile.get("interest_area"):
            parts.append(f"Interest: {self.profile['interest_area']}")
        if self.profile.get("program_goal"):
            parts.append(f"Goal: {self.profile['program_goal']}")
        if self.profile.get("budget"):
            parts.append(f"Budget: {self.profile['budget']}")
        if self.profile.get("format"):
            parts.append(f"Format: {self.profile['format']}")
        if self.profile.get("location"):
            parts.append(f"Location: {self.profile['location']}")
        if self.profile.get("gpa_range"):
            parts.append(f"GPA: {self.profile['gpa_range']}")
        if self.profile.get("coursework_level"):
            parts.append(f"Coursework: {self.profile['coursework_level']}")
        if self.profile.get("prior_experience"):
            parts.append(f"Experience: {self.profile['prior_experience']}")

        return " | ".join(parts)

    def send_answer(self):
        if not self.questions:
            return
        if self.current_question_index >= len(self.questions):
            return
        if self.user_input.strip() == "":
            return

        question_index = self.current_question_index
        current_question = self.questions[question_index]
        question_id = current_question["id"]
        raw_input = self.user_input.strip()

        self.chat_history.append({"role": "user", "text": raw_input})

        payload = {
            "question_id": question_id,
            "user_text": raw_input,
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chat/answer",
                json=payload,
                timeout=10,
            )
            data = response.json()
        except Exception as e:
            self.chat_history.append(
                {
                    "role": "assistant",
                    "text": f"Sorry, I hit an error while processing that answer: {str(e)}",
                }
            )
            self.user_input = ""
            return

        normalized_value = data.get("structured_fields", {}).get("normalized_value")

        if normalized_value:
            self.profile[question_id] = normalized_value

        self.user_input = ""
        self.current_question_index += 1

        if self.current_question_index < len(self.questions):
            next_question = self.questions[self.current_question_index]["text"]
            self.chat_history.append({"role": "assistant", "text": next_question})
        else:
            self.chat_history.append(
                {
                    "role": "assistant",
                    "text": "Thanks — I have enough information now. Click below to get your program recommendations.",
                }
            )

    def use_sample_prompt_1(self):
        self.user_input = "Provide a list of biomedical engineering or medicine-related pre-college programs for a strong high school student."

    def use_sample_prompt_2(self):
        self.user_input = "How do research-focused pre-college programs compare with hands-on project-based ones?"

    def use_sample_prompt_3(self):
        self.user_input = "What computer science or AI pre-college programs would suit a student with strong academics and some project experience?"

    def get_recommendations(self):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/recommend/",
                json={"profile": self.profile},
                timeout=15,
            )
            data = response.json()
            self.recommendations = data.get("recommendations", [])
        except Exception as e:
            self.recommendations = [
                {
                    "name": "Unable to load recommendations",
                    "description": str(e),
                    "score_text": "Unavailable",
                    "fit_label": "Error",
                    "reasons_text": "Request failed",
                }
            ]


def navbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.box(
                "V",
                bg="#f27c2b",
                color="white",
                font_weight="bold",
                border_radius="9999px",
                width="46px",
                height="46px",
                display="flex",
                align_items="center",
                justify_content="center",
                font_size="26px",
            ),
            rx.text("Pre-college recommendation app", font_size="2em", font_weight="700", color="#1f1b16"),
            spacing="3",
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            rx.box(
                "Home",
                bg="#ddd0bd",
                padding="10px 18px",
                border_radius="9999px",
                font_weight="600",
            ),
            rx.text("Pricing", font_size="1.2em"),
            rx.text("Insights", font_size="1.2em"),
            rx.text("About Us", font_size="1.2em"),
            spacing="6",
            align="center",
            color="#2b2118",
        ),
        rx.spacer(),
        rx.box(
            "◉",
            border="1px solid #cdbfae",
            border_radius="9999px",
            width="48px",
            height="48px",
            display="flex",
            align_items="center",
            justify_content="center",
            color="#2b2118",
            bg="#f6f1e8",
            box_shadow="0 4px 16px rgba(0,0,0,0.08)",
        ),
        width="100%",
        padding="18px 24px",
        border_radius="9999px",
        bg="#f6f1e8",
        box_shadow="0 6px 20px rgba(0,0,0,0.08)",
        align="center",
    )


def hero_section() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Your personal AI counselor for college planning, prep, and applications",
            font_size="2.3em",
            font_weight="500",
            color="#1f1b16",
        ),
        rx.hstack(
            rx.text("Act on", font_size="3.4em", font_weight="700", color="#1f1b16"),
            rx.box(
                rx.text(
                    "careers",
                    font_size="1em",
                    font_weight="700",
                    color="#5f462c",
                ),
                bg="#e8dfd2",
                padding="6px 14px",
                border_radius="12px",
            ),
            align="center",
            spacing="4",
        ),
        spacing="4",
        align="start",
        width="100%",
        padding_top="16px",
        padding_bottom="18px",
    )


def chat_bubble(msg) -> rx.Component:
    return rx.box(
        rx.text(msg["text"], font_size="1.05em", color="#2b2118"),
        bg=rx.cond(msg["role"] == "user", "#f8dcc6", "#ece5da"),
        padding="14px 18px",
        border_radius="18px",
        width="100%",
    )


def sample_question_card(text: str, on_click) -> rx.Component:
    return rx.box(
        rx.text(text, font_size="1.05em", font_weight="600", color="#2d241c"),
        bg="#ece5da",
        padding="18px 22px",
        border_radius="24px",
        width="100%",
        cursor="pointer",
        on_click=on_click,
        _hover={"bg": "#e3dacd"},
    )


def chat_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("Try sample questions:", font_size="1.05em", color="#6b5a4a"),
            sample_question_card(
                "Provide a list of biomedical engineering or medicine-related pre-college programs for a strong high school student.",
                State.use_sample_prompt_1,
            ),
            sample_question_card(
                "How do research-focused pre-college programs compare with hands-on project-based ones?",
                State.use_sample_prompt_2,
            ),
            sample_question_card(
                "What computer science or AI pre-college programs would suit a student with strong academics and some project experience?",
                State.use_sample_prompt_3,
            ),
            rx.button(
                "Load Questions",
                on_click=State.load_questions,
                bg="#ddd0bd",
                color="#2b2118",
                border_radius="9999px",
                padding="10px 18px",
                font_weight="700",
            ),
            rx.cond(
                State.has_questions,
                rx.text(f"Progress: {State.progress_text}", color="#6b5a4a"),
                rx.fragment(),
            ),
            rx.cond(
                State.chat_history != [],
                rx.vstack(
                    rx.foreach(State.chat_history, chat_bubble),
                    spacing="3",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.cond(
                State.is_finished,
                rx.button(
                    "Get Recommendations",
                    on_click=State.get_recommendations,
                    bg="#f27c2b",
                    color="white",
                    border_radius="9999px",
                    padding="12px 22px",
                    align_self="end",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.input(
                    value=State.user_input,
                    on_change=State.set_user_input,
                    placeholder="Type your own question...",
                    width="100%",
                    border_radius="9999px",
                    bg="#f8f3eb",
                    border="1px solid #d8cdbc",
                    padding="14px 18px",
                ),
                rx.button(
                    "Send",
                    on_click=State.send_answer,
                    bg="#f27c2b",
                    color="white",
                    border_radius="9999px",
                    padding="12px 22px",
                    font_weight="700",
                ),
                width="100%",
                align="center",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
        bg="#f6f1e8",
        border_radius="28px",
        padding="26px",
        box_shadow="0 12px 30px rgba(0,0,0,0.10)",
    )


def featured_program_card(item) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                item["name"],
                font_weight="700",
                font_size="1.05em",
                color="#1f1b16",
            ),
            rx.box(
                rx.text(
                    item["tag"],
                    font_size="0.9em",
                    font_weight="600",
                    color="#7a542f",
                ),
                bg="#ece2d2",
                padding="4px 10px",
                border_radius="9999px",
                width="fit-content",
            ),
            rx.text(item["desc"], color="#5d4c3b", font_size="0.98em"),
            spacing="3",
            align="start",
        ),
        bg="#f6f1e8",
        border_radius="20px",
        padding="18px",
        box_shadow="0 8px 20px rgba(0,0,0,0.06)",
        width="100%",
    )


def featured_section(title: str, items) -> rx.Component:
    return rx.vstack(
        rx.text(title, font_size="1.8em", font_weight="700", color="#1f1b16"),
        rx.grid(
            rx.foreach(items, featured_program_card),
            columns="3",
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
        align="start",
    )


def recommendation_card(rec) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    rec.get("name", "Unknown Program"),
                    font_weight="700",
                    font_size="1.1em",
                    color="#1f1b16",
                ),
                rx.spacer(),
                rx.box(
                    rx.text(
                        rec.get("fit_label", "Recommended"),
                        font_size="0.9em",
                        font_weight="700",
                        color="#7a542f",
                    ),
                    bg="#ece2d2",
                    padding="6px 12px",
                    border_radius="9999px",
                ),
                width="100%",
                align="center",
            ),
            rx.text(rec.get("description", ""), color="#5d4c3b", font_size="1em"),
            rx.text(
                rec.get("score_text", ""),
                color="#6b5a4a",
                font_size="0.95em",
            ),
            rx.text("Why this fits you", font_weight="700", color="#2b2118"),
            rx.text(rec.get("reasons_text", "No explanation available"), color="#5d4c3b"),
            spacing="3",
            align="start",
            width="100%",
        ),
        bg="#f6f1e8",
        border_radius="20px",
        padding="20px",
        box_shadow="0 8px 20px rgba(0,0,0,0.06)",
        width="100%",
    )


def recommendations_panel() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Recommended programs for you",
            font_size="2em",
            font_weight="700",
            color="#1f1b16",
        ),
        rx.text(State.profile_summary, color="#5d4c3b", font_size="1em"),
        rx.vstack(
            rx.foreach(State.recommendations, recommendation_card),
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
        align="start",
    )


def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            navbar(),
            hero_section(),
            chat_panel(),
            rx.cond(
                State.recommendations != [],
                recommendations_panel(),
                rx.fragment(),
            ),
            featured_section(
                "Top recommended programs for Biomedical / Pre-Health",
                State.featured_biomed,
            ),
            featured_section(
                "Top recommended programs for Computer Science / AI",
                State.featured_cs,
            ),
            featured_section(
                "Top recommended programs for Business / Entrepreneurship",
                State.featured_business,
            ),
            spacing="8",
            width="100%",
            max_width="1280px",
            margin="0 auto",
            padding="24px",
            padding_bottom="60px",
        ),
        bg="#efe9df",
        min_height="100vh",
        width="100%",
    )


app = rx.App()
app.add_page(index, route="/")