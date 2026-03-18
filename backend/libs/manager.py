import json
import time
import random
import threading

from libs import KahootBot, search_quiz, fetch_quiz, REACTION_KEYS, NAME_THEMES
from libs import ollama as llm


def _try_match(results: list, qqa: list):
    for r in results:
        if qqa and r["questions_count"] != len(qqa):
            continue
        quiz = fetch_quiz(r["uuid"])
        if not quiz:
            continue
        questions = quiz.get("questions", [])
        match = True
        for qi, exp in enumerate(qqa):
            if qi >= len(questions) or len(questions[qi].get("choices", [])) != exp:
                match = False
                break
        if match:
            return quiz
    return None


class BotManager:
    def __init__(self, pin: str, bot_count: int, config: dict):
        self.pin = pin
        self.bot_count = bot_count
        self.config = config
        self.bots: list[KahootBot] = []
        self.threads: list[threading.Thread] = []
        self.answers: dict[int, int] = {}
        self.quiz_found = False
        self.quiz_title = ""
        self.running = False
        self.logs: list[str] = []
        self.needs_2fa = False
        self._2fa_submitted = False
        self.ollama_model = config.get("ollama_model", "llama3.2")
        self.ollama_available = False

        self.mode = config.get("mode", "random")
        self.spectator = config.get("spectator", False)
        self.name_mode = config.get("name_mode", "theme")
        self.name_theme = config.get("name_theme", "default")
        self.name_prefix = config.get("name_prefix", "Bot")
        self.custom_names = config.get("custom_names", [])
        self.answer_delay_min = config.get("answer_delay_min", 0)
        self.answer_delay_max = config.get("answer_delay_max", 0)
        self.join_delay = config.get("join_delay", 500)
        self.flood_react = config.get("flood_react", False)
        self.flood_reaction = config.get("flood_reaction", "random")
        self.flood_speed = config.get("flood_speed", 500)
        self.react_on_win = config.get("react_on_win", False)
        self.win_reaction = config.get("win_reaction", "random")
        self.react_on_lose = config.get("react_on_lose", False)
        self.lose_reaction = config.get("lose_reaction", "random")
        self.celebrate = config.get("celebrate", False)
        self.celebrate_reaction = config.get("celebrate_reaction", "random")
        self.celebrate_count = config.get("celebrate_count", 10)
        self.auto_reconnect = config.get("auto_reconnect", False)

        self.total_correct = 0
        self.total_wrong = 0
        self.total_points = 0
        self.questions_seen = 0

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {msg}")
        if len(self.logs) > 300:
            self.logs = self.logs[-300:]

    def _gen_name(self, index: int):
        if self.name_mode == "custom" and index < len(self.custom_names):
            return self.custom_names[index]
        if self.name_mode == "prefix":
            return f"{self.name_prefix}{random.randint(10, 999)}"
        theme = NAME_THEMES.get(self.name_theme, NAME_THEMES["default"])
        return f"{theme[index % len(theme)]}{random.randint(10, 99)}"

    def _get_delay(self):
        if self.answer_delay_max <= 0:
            return 0
        return random.randint(self.answer_delay_min, self.answer_delay_max) / 1000.0

    def _flood_loop(self, bot: KahootBot):
        time.sleep(1)
        while self.running and bot._running:
            try:
                bot.react(self.flood_reaction)
            except Exception:
                break
            time.sleep(max(0.2, self.flood_speed / 1000.0))

    def _celebrate_burst(self, bot: KahootBot):
        for _ in range(self.celebrate_count):
            if not bot._running:
                break
            try:
                bot.react(self.celebrate_reaction)
            except Exception:
                break
            time.sleep(0.3)

    def _setup_bot(self, bot: KahootBot, is_primary: bool):

        def on_joined(d):
            self.log(f"+ {bot.nickname} joined")
            if self.flood_react:
                threading.Thread(target=self._flood_loop, args=(bot,), daemon=True).start()

        def on_login(d):
            pass

        def on_2fa_reset(d):
            self.needs_2fa = True
            if is_primary:
                self.log("! 2FA required")

        def on_2fa_correct(d):
            self.needs_2fa = False
            self._2fa_submitted = False
            self.log("+ 2FA accepted")

        def on_2fa_incorrect(d):
            self._2fa_submitted = False
            self.log("- 2FA wrong")

        def on_start_quiz(d):
            if not is_primary or self.quiz_found:
                return
            if not isinstance(d, dict):
                return
            qqa = d.get("quizQuestionAnswers", [])
            q1 = d.get("firstGameBlockData", {})
            if not isinstance(q1, dict):
                q1 = {}
            q1_title = q1.get("question", "")
            q1_choices = q1.get("choices", [])
            self.log(f"i Q1: {q1_title[:60]} ({len(qqa)}q)")

            if self.mode == "ai":
                threading.Thread(target=self._ai_find_quiz, args=(q1_title, q1_choices, qqa), daemon=True).start()

        def on_start_question(d):
            if self.spectator:
                return
            if not isinstance(d, dict):
                return
            q_idx = d.get("gameBlockIndex", d.get("questionIndex", 0))
            n_choices = d.get("numberOfChoices", 4)
            self.questions_seen = max(self.questions_seen, q_idx + 1)
            delay = self._get_delay()

            def do_answer():
                if delay > 0:
                    time.sleep(delay)
                if not bot._running:
                    return
                if q_idx in self.answers:
                    choice = self.answers[q_idx]
                    self.log(f"> {bot.nickname} Q{q_idx+1} -> {choice}")
                elif self.mode == "first":
                    choice = 0
                    self.log(f"> {bot.nickname} Q{q_idx+1} -> 0")
                elif self.mode == "last":
                    choice = max(0, n_choices - 1)
                    self.log(f"> {bot.nickname} Q{q_idx+1} -> {choice}")
                else:
                    choice = random.randint(0, max(0, n_choices - 1))
                    self.log(f"> {bot.nickname} Q{q_idx+1} -> {choice} (rng)")
                bot.answer(choice, q_idx)

            threading.Thread(target=do_answer, daemon=True).start()

        def on_reveal_answer(d):
            if not isinstance(d, dict):
                return
            correct = d.get("isCorrect", False)
            pts = d.get("points", 0)
            rank = d.get("rank", "?")
            streak = d.get("pointsData", {}).get("answerStreakPoints", {}).get("streakLevel", 0)
            bot.score = d.get("totalScore", bot.score)
            bot.rank = rank
            bot.streak = streak
            if correct:
                self.total_correct += 1
                self.total_points += pts
                bot.correct_count += 1
                if self.react_on_win:
                    try: bot.react(self.win_reaction)
                    except: pass
            else:
                self.total_wrong += 1
                bot.wrong_count += 1
                if self.react_on_lose:
                    try: bot.react(self.lose_reaction)
                    except: pass
            mark = "+" if correct else "-"
            self.log(f"{mark} {bot.nickname} {pts}pts #{rank}")

        def on_game_over(d):
            self.log(f"* {bot.nickname} GAME OVER {bot.score}pts #{bot.rank}")
            if self.celebrate:
                threading.Thread(target=self._celebrate_burst, args=(bot,), daemon=True).start()

        def on_error(d):
            self.log(f"! {bot.nickname} disconnected")
            if self.auto_reconnect and self.running:
                self.log(f"~ reconnecting {bot.nickname}...")
                time.sleep(2)
                threading.Thread(target=self._run_bot, args=(bot,), daemon=True).start()

        bot.on("joined", on_joined)
        bot.on("login", on_login)
        bot.on("RESET_TWO_FACTOR_AUTH", on_2fa_reset)
        bot.on("TWO_FACTOR_AUTH_CORRECT", on_2fa_correct)
        bot.on("TWO_FACTOR_AUTH_INCORRECT", on_2fa_incorrect)
        bot.on("START_QUIZ", on_start_quiz)
        bot.on("START_QUESTION", on_start_question)
        bot.on("REVEAL_ANSWER", on_reveal_answer)
        bot.on("GAME_OVER", on_game_over)
        bot.on("error", on_error)

    def _ai_find_quiz(self, q1_text: str, q1_choices: list, qqa: list):
        # extract Q1 answer from game data (always available)
        for ci, c in enumerate(q1_choices):
            if isinstance(c, dict) and c.get("correct"):
                self.answers[0] = ci
                break

        # ask ollama to guess quiz titles from Q1 data
        self.ollama_available = llm.is_available(self.ollama_model)
        if not self.ollama_available:
            self.log("~ ollama offline, Q1 only")
            return

        choice_texts = [c.get("answer", "") for c in q1_choices if isinstance(c, dict)]
        self.log(f"* asking {self.ollama_model} to guess quiz title...")
        guesses = llm.guess_quiz_titles(q1_text, choice_texts, len(qqa))

        if not guesses:
            self.log("- ollama returned no guesses")
            return

        self.log(f"i guesses: {guesses}")

        # search each guessed title on Kahoot API
        for title in guesses:
            self.log(f"* searching: \"{title}\"")
            results = search_quiz(title)
            if not results:
                continue

            self.log(f"i {len(results)} results for \"{title}\"")
            quiz = _try_match(results, qqa)
            if quiz:
                self.answers = quiz["answers"]
                self.quiz_found = True
                self.quiz_title = quiz["title"]
                self.log(f"+ FOUND: \"{quiz['title']}\" ({len(self.answers)} answers)")
                return

        self.log("- quiz not found after all guesses, Q1 only + random")

    def submit_2fa(self, sequence: list):
        if self._2fa_submitted:
            return
        self._2fa_submitted = True
        self.log(f"~ 2FA: {sequence}")
        for bot in self.bots:
            if bot._running:
                try:
                    bot.submit_2fa(sequence)
                except Exception:
                    pass

    def _run_bot(self, bot: KahootBot):
        try:
            bot.join()
            bot.listen()
        except Exception as e:
            self.log(f"! {bot.nickname}: {e}")
        finally:
            bot.disconnect()

    def start(self):
        self.running = True
        label = "spectator" if self.spectator else self.mode
        self.log(f"* {self.bot_count} bot(s) -> {self.pin} [{label}]")

        if self.mode == "ai":
            llm.DEFAULT_MODEL = self.ollama_model
            self.ollama_available = llm.is_available(self.ollama_model)
            if self.ollama_available:
                self.log(f"+ ollama ready ({self.ollama_model})")
            else:
                self.log("~ ollama not detected — will use Q1 answer only")

        for i in range(self.bot_count):
            name = self._gen_name(i)
            bot = KahootBot(self.pin, name)
            self._setup_bot(bot, is_primary=(i == 0))
            self.bots.append(bot)
            t = threading.Thread(target=self._run_bot, args=(bot,), daemon=True)
            self.threads.append(t)
            t.start()
            if self.bot_count > 1 and self.join_delay > 0:
                time.sleep(self.join_delay / 1000.0)

    def stop(self):
        self.running = False
        for bot in self.bots:
            try:
                bot.disconnect()
            except Exception:
                pass
        self.bots.clear()
        self.threads.clear()
        self.log("x stopped")

    def get_status(self):
        return {
            "running": self.running,
            "bot_count": len(self.bots),
            "quiz_found": self.quiz_found,
            "quiz_title": self.quiz_title,
            "answers_count": len(self.answers),
            "connected": sum(1 for b in self.bots if b._running),
            "correct": self.total_correct,
            "wrong": self.total_wrong,
            "points": self.total_points,
            "questions_seen": self.questions_seen,
            "needs_2fa": self.needs_2fa,
            "ollama": self.ollama_available,
            "bots": [{"name": b.nickname, "connected": b._running, "score": b.score, "rank": b.rank, "correct": b.correct_count, "wrong": b.wrong_count, "streak": b.streak} for b in self.bots],
            "logs": self.logs[-80:],
        }
