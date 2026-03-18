import requests

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"


def is_available(model: str = DEFAULT_MODEL) -> bool:
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if resp.status_code != 200:
            return False
        models = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
        return model in models or any(model in m for m in models)
    except Exception:
        return False


def list_models() -> list[str]:
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []


def ask(prompt: str, model: str = DEFAULT_MODEL) -> str:
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 150},
        }, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""


def guess_quiz_titles(question: str, choices: list[str], num_questions: int = 0) -> list[str]:
    choices_str = ", ".join(choices[:6])
    count_hint = f"The quiz has {num_questions} questions." if num_questions else ""

    prompt = f"""A Kahoot quiz is being played. I need to find this quiz by its TITLE on the Kahoot platform.
The Kahoot search works like a catalog — users create quizzes with titles like "English A1", "Math Grade 5", "History WW2", "Biology Cells", etc.

Here is the first question of the quiz:
Question: {question}
Answer choices: {choices_str}
{count_hint}

Based on this question, guess what the quiz title could be. Think about:
- What subject/topic is this? (English, Math, Science, History, Geography...)
- What level? (A1, A2, beginner, grade 5...)
- What specific topic? (nouns, verbs, fractions, animals...)

Give me 5 possible quiz titles, short (2-5 words each), one per line.
Most likely first. No numbers, no bullets, no explanation."""

    raw = ask(prompt, model=DEFAULT_MODEL)
    if not raw:
        return []
    titles = []
    for line in raw.split("\n"):
        t = line.strip().strip("-").strip("•").strip("*").strip("0123456789.").strip()
        if t and 2 <= len(t) <= 50:
            titles.append(t)
    return titles[:5]
