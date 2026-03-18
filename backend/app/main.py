import os
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db, User, GameSession
from app.auth import create_jwt, get_current_user, require_admin
from libs.manager import BotManager
from libs import ollama as llm

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

active_sessions: dict[str, BotManager] = {}
CREDIT_PER_BOT = 1.0

class RegisterReq(BaseModel):
    username: str
class LoginReq(BaseModel):
    token: str
class StartReq(BaseModel):
    pin: str
    bot_count: int = 1
    mode: str = "random"
    spectator: bool = False
    name_mode: str = "theme"
    name_theme: str = "default"
    name_prefix: str = "Bot"
    custom_names: list[str] = []
    answer_delay_min: int = 0
    answer_delay_max: int = 0
    join_delay: int = 500
    flood_react: bool = False
    flood_reaction: str = "random"
    flood_speed: int = 500
    react_on_win: bool = False
    win_reaction: str = "random"
    react_on_lose: bool = False
    lose_reaction: str = "random"
    celebrate: bool = False
    celebrate_reaction: str = "random"
    celebrate_count: int = 10
    auto_reconnect: bool = False
    ollama_model: str = "llama3.2"
class TfaReq(BaseModel):
    sequence: list[int]
class CreditReq(BaseModel):
    user_id: str
    amount: float
class UserIdReq(BaseModel):
    user_id: str

@app.get("/api/ollama/status")
def ollama_status(model: str = "llama3.2"):
    available = llm.is_available(model)
    models = []
    try:
        import requests
        resp = requests.get(f"{llm.OLLAMA_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return {"available": available, "model": model, "models": models}

@app.post("/api/auth/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "username taken")
    user = User(username=req.username, credits=5.0)
    db.add(user); db.commit(); db.refresh(user)
    return {"token": user.token, "jwt": create_jwt(user.id, False), "user": _u(user)}

@app.post("/api/auth/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == req.token).first()
    if not user: raise HTTPException(401, "invalid token")
    return {"jwt": create_jwt(user.id, user.is_admin), "user": _u(user)}

@app.get("/api/user/me")
def me(user: User = Depends(get_current_user)):
    return _u(user)

@app.post("/api/game/start")
def start(req: StartReq, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cost = req.bot_count * CREDIT_PER_BOT
    if user.credits < cost: raise HTTPException(402, f"need {cost} credits")
    user.credits -= cost
    s = GameSession(user_id=user.id, pin=req.pin, bot_count=req.bot_count, mode=req.mode, status="running", config=json.dumps(req.model_dump()))
    db.add(s); db.commit(); db.refresh(s)
    mgr = BotManager(pin=req.pin, bot_count=req.bot_count, config=req.model_dump())
    active_sessions[s.id] = mgr
    mgr.start()
    return {"session_id": s.id, "cost": cost, "credits": user.credits}

@app.post("/api/game/{sid}/stop")
def stop(sid: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mgr = active_sessions.get(sid)
    if not mgr: raise HTTPException(404)
    s = db.query(GameSession).filter(GameSession.id == sid).first()
    if s and s.user_id != user.id and not user.is_admin: raise HTTPException(403)
    mgr.stop()
    if s: s.status = "stopped"; db.commit()
    active_sessions.pop(sid, None)
    return {"ok": True}

@app.get("/api/game/{sid}/status")
def status(sid: str, user: User = Depends(get_current_user)):
    mgr = active_sessions.get(sid)
    if not mgr: raise HTTPException(404)
    return mgr.get_status()

@app.post("/api/game/{sid}/2fa")
def submit_2fa(sid: str, req: TfaReq, user: User = Depends(get_current_user)):
    mgr = active_sessions.get(sid)
    if not mgr: raise HTTPException(404)
    mgr.submit_2fa(req.sequence)
    return {"ok": True}

@app.get("/api/game/sessions")
def sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(GameSession).filter(GameSession.user_id == user.id).order_by(GameSession.created_at.desc()).limit(20).all()
    return [{"id": s.id, "pin": s.pin, "bot_count": s.bot_count, "mode": s.mode, "status": s.status} for s in rows]

@app.get("/api/admin/users")
def admin_users(a: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [{"id": u.id, "username": u.username, "credits": u.credits, "is_admin": u.is_admin, "token": u.token} for u in db.query(User).all()]

@app.post("/api/admin/credits/add")
def admin_add(req: CreditReq, a: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == req.user_id).first()
    if not u: raise HTTPException(404)
    u.credits += req.amount; db.commit()
    return {"credits": u.credits}

@app.post("/api/admin/delete")
def admin_del(req: UserIdReq, a: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == req.user_id).first()
    if not u: raise HTTPException(404)
    db.delete(u); db.commit()
    return {"ok": True}

@app.post("/api/admin/promote")
def admin_promo(req: UserIdReq, a: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == req.user_id).first()
    if not u: raise HTTPException(404)
    u.is_admin = True; db.commit()
    return {"ok": True}

@app.post("/api/admin/init")
def admin_init(db: Session = Depends(get_db)):
    if db.query(User).filter(User.is_admin == True).first(): raise HTTPException(400, "admin exists")
    u = User(username="admin", is_admin=True, credits=999999)
    db.add(u); db.commit(); db.refresh(u)
    return {"token": u.token, "jwt": create_jwt(u.id, True)}

def _u(u): return {"id": u.id, "username": u.username, "credits": u.credits, "is_admin": u.is_admin}
