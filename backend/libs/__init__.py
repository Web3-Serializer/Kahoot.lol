import re
import ast
import json
import time
import base64
import random
import operator
import threading
from typing import Callable
from urllib.parse import quote

import requests
import websocket
from fake_useragent import UserAgent

REACTIONS = {
    "thumbsup": "ThumbsUp",
    "clap": "Clap",
    "haha": "Haha",
    "thinking": "Thinking",
    "wow": "Wow",
    "heart": "Heart",
}

REACTION_KEYS = list(REACTIONS.keys())

LOOKUP = {
    1: "GET_READY",
    2: "START_QUESTION",
    3: "GAME_OVER",
    4: "TIME_UP",
    8: "REVEAL_ANSWER",
    9: "START_QUIZ",
    10: "RESET_CONTROLLER",
    13: "REVEAL_RANKING",
    14: "USERNAME_ACCEPTED",
    17: "SEND_RECOVERY_DATA_TO_CONTROLLER",
    45: "GAME_BLOCK_ANSWER",
    51: "TWO_FACTOR_AUTH_INCORRECT",
    52: "TWO_FACTOR_AUTH_CORRECT",
    53: "RESET_TWO_FACTOR_AUTH",
}

NAME_THEMES = {
    "hacker": ["Cipher", "Root", "Kernel", "Proxy", "Daemon", "Shell", "Null", "Byte", "Stack", "Heap", "Debug", "Cache", "Mutex", "Fork", "Ping", "Sudo"],
    "animal": ["Wolf", "Fox", "Bear", "Hawk", "Lynx", "Cobra", "Puma", "Viper", "Orca", "Raven", "Tiger", "Eagle", "Shark", "Falcon", "Panther", "Drake"],
    "space": ["Nova", "Nebula", "Comet", "Quasar", "Pulsar", "Vortex", "Photon", "Plasma", "Orbit", "Zenith", "Cosmos", "Lunar", "Solar", "Astro", "Meteor", "Eclipse"],
    "meme": ["Doge", "Pepe", "Amogus", "Sigma", "Rizz", "Skibidi", "Gyatt", "Blud", "Baka", "Uwu", "Bruh", "Yeet", "Pog", "Kek", "Based", "Chad"],
    "default": ["Shadow", "Phoenix", "Blaze", "Storm", "Frost", "Nova", "Viper", "Echo", "Raven", "Drift", "Pulse", "Cyber", "Ghost", "Neon", "Flux", "Omega"],
}


class KahootBot:
    def __init__(self, pin: str, nickname: str):
        self.pin = pin
        self.nickname = nickname
        self.cid = None
        self.client_id = None
        self.ws = None
        self.ua = UserAgent().random
        self.game_id = None
        self.score = 0
        self.rank = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self._msg_id = 0
        self._ack = 0
        self._sync_l = 0
        self._sync_o = 0
        self._listeners: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()
        self._running = False

    def _nid(self):
        with self._lock:
            self._msg_id += 1
            return str(self._msg_id)

    def _ts(self):
        return int(time.time() * 1000)

    def _tsync(self):
        return {"tc": self._ts(), "l": self._sync_l, "o": self._sync_o}

    def _send(self, payload):
        self.ws.send(json.dumps(payload))

    def _recv(self):
        raw = self.ws.recv()
        msgs = json.loads(raw)
        if not isinstance(msgs, list):
            msgs = [msgs]
        for msg in msgs:
            a = msg.get("ext", {}).get("ack")
            if a is not None:
                self._ack = a
        return msgs

    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)
        return self

    def _emit(self, event: str, data):
        for cb in self._listeners.get(event, []):
            try:
                cb(data)
            except Exception:
                pass

    @staticmethod
    def _safe_eval(expr):
        ops = {
            ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
            ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod, ast.Pow: operator.pow,
            ast.USub: operator.neg, ast.UAdd: operator.pos, ast.BitXor: operator.xor,
        }
        expr = re.sub(r'[^\d+\-*/%^&|~()<> ]', '', expr).strip()
        tree = ast.parse(expr, mode="eval")
        def walk(n):
            if isinstance(n, ast.Expression): return walk(n.body)
            if isinstance(n, ast.Constant): return n.value
            if isinstance(n, ast.UnaryOp): return ops[type(n.op)](walk(n.operand))
            if isinstance(n, ast.BinOp): return ops[type(n.op)](walk(n.left), walk(n.right))
            raise ValueError(type(n).__name__)
        return int(walk(tree))

    def _solve_challenge(self, js):
        js = re.sub(r'[^\x20-\x7E]', ' ', js)
        msg = re.search(r"decode\.call\(this,\s*'([^']+)'\)", js).group(1)
        offset = self._safe_eval(re.search(r"var\s+offset\s*=\s*(.+?)\s*;", js).group(1))
        out = ""
        for i, ch in enumerate(msg):
            out += chr(((ord(ch) * i + offset) % 77) + 48)
        return out

    def _reserve(self):
        url = f"https://kahoot.it/reserve/session/{self.pin}/?{self._ts()}"
        resp = requests.get(url, headers={"User-Agent": self.ua, "Accept": "application/json", "Referer": "https://kahoot.it/"}, timeout=15)
        resp.raise_for_status()
        token_b64 = resp.headers["x-kahoot-session-token"]
        challenge = resp.json()["challenge"]
        header = base64.b64decode(token_b64)
        mask = self._solve_challenge(challenge).encode()
        return bytes(h ^ m for h, m in zip(header, mask)).decode(errors="replace")

    def _handshake(self):
        self._send([{"id": self._nid(), "version": "1.0", "minimumVersion": "1.0", "channel": "/meta/handshake", "supportedConnectionTypes": ["websocket", "long-polling", "callback-polling"], "advice": {"timeout": 60000, "interval": 0}, "ext": {"ack": True, "timesync": {"tc": self._ts(), "l": 0, "o": 0}}}])
        msgs = self._recv()
        if not msgs[0].get("successful"):
            raise RuntimeError("handshake failed")
        self.client_id = msgs[0]["clientId"]
        srv_ts = msgs[0].get("ext", {}).get("timesync", {})
        if srv_ts.get("tc") and srv_ts.get("ts"):
            now = self._ts()
            self._sync_l = now - srv_ts["tc"]
            self._sync_o = int(srv_ts["ts"] - now + self._sync_l / 2)

    def _connect_meta(self, advice=None):
        msg = {"id": self._nid(), "channel": "/meta/connect", "connectionType": "websocket", "clientId": self.client_id, "ext": {"ack": self._ack, "timesync": self._tsync()}}
        if advice:
            msg["advice"] = advice
        self._send([msg])

    def _send_controller(self, msg_type, msg_id, content):
        self._send([{"id": self._nid(), "channel": "/service/controller", "data": {"gameid": self.pin, "type": msg_type, "host": "kahoot.it", "id": msg_id, "content": json.dumps(content) if isinstance(content, dict) else content}, "clientId": self.client_id, "ext": {}}])

    def join(self):
        token = self._reserve()
        self.ws = websocket.create_connection(f"wss://kahoot.it/cometd/{self.pin}/{token}", header=["Origin: https://kahoot.it"])
        self._handshake()
        self._connect_meta(advice={"timeout": 0})
        self._recv()
        self._connect_meta()
        self._send([{"id": self._nid(), "channel": "/service/controller", "data": {"type": "login", "gameid": self.pin, "host": "kahoot.it", "name": self.nickname, "content": "{}"}, "clientId": self.client_id, "ext": {}}])
        self._send([{"id": self._nid(), "channel": "/meta/subscribe", "subscription": f"/audience-questions/approved/{self.pin}", "clientId": self.client_id, "ext": {"timesync": self._tsync()}}])
        self._send_controller("message", 16, {"usingNamerator": False})
        self._emit("joined", {"pin": self.pin, "name": self.nickname})
        return self

    def react(self, reaction: str):
        key = reaction.lower().strip()
        if key == "random":
            key = random.choice(REACTION_KEYS)
        if key in REACTIONS:
            self._send_controller("message", 47, {"reactionType": REACTIONS[key]})
        return self

    def answer(self, choice: int, question_index: int = 0):
        self._send_controller("message", 45, {"type": "quiz", "choice": choice, "questionIndex": question_index})
        return self

    def submit_2fa(self, sequence: list):
        self._send_controller("message", 50, {"gameId": self.pin, "sequence": sequence})

    def send_raw(self, msg_type: str, msg_id: int, content: dict):
        self._send_controller(msg_type, msg_id, content)
        return self

    def _parse_content(self, data):
        content = data.get("content")
        if isinstance(content, str):
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass
        return content

    def _process_message(self, msg):
        ch = msg.get("channel", "")
        data = msg.get("data", {})
        if ch == "/meta/connect":
            self._connect_meta()
            return
        if ch == "/meta/disconnect":
            self._running = False
            self._emit("disconnect", {})
            return
        if ch.startswith("/meta/"):
            return
        msg_id = data.get("id")
        msg_type = data.get("type", "")
        content = self._parse_content(data)
        kind = LOOKUP.get(msg_id, "")
        if msg_type == "loginResponse":
            self.cid = data.get("cid")
            self._emit("login", {"cid": self.cid})
            return
        if msg_type == "status":
            self._emit("status", data)
            return
        if kind:
            self._emit(kind, content if content else data)

    def listen(self):
        self._running = True
        while self._running:
            try:
                for msg in self._recv():
                    self._process_message(msg)
            except Exception as e:
                self._emit("error", {"error": str(e)})
                break

    def disconnect(self):
        self._running = False
        if self.ws:
            try:
                self._send([{"id": self._nid(), "channel": "/meta/disconnect", "clientId": self.client_id}])
            except Exception:
                pass
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None


def search_quiz(query: str, limit: int = 50):
    resp = requests.get("https://create.kahoot.it/rest/kahoots/", params={"query": query, "cursor": 0, "limit": limit, "orderBy": "relevance", "searchCluster": 1, "includeExtendedCounters": False}, headers={"User-Agent": UserAgent().random}, timeout=15)
    if resp.status_code != 200:
        return []
    return [{"uuid": e["card"].get("uuid"), "title": e["card"].get("title"), "questions_count": e["card"].get("number_of_questions", 0), "creator": e["card"].get("creator_username", "")} for e in resp.json().get("entities", [])]


def fetch_quiz(uuid: str):
    resp = requests.get(f"https://create.kahoot.it/rest/kahoots/{uuid}", headers={"User-Agent": UserAgent().random}, timeout=15)
    if resp.status_code != 200:
        return None
    data = resp.json()
    answers = {}
    for qi, q in enumerate(data.get("questions", [])):
        for ci, c in enumerate(q.get("choices", [])):
            if c.get("correct"):
                answers[qi] = ci
                break
    return {"title": data.get("title", ""), "answers": answers, "questions": data.get("questions", [])}
