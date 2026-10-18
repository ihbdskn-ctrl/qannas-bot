from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .data import fetch_data
from .strategy import analyze
from .telegram import Telegram

app = FastAPI(title="Qannas Phone Signals Bot")
scheduler = AsyncIOScheduler(timezone="UTC")
DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "state.json"
DATA_DIR.mkdir(exist_ok=True)

def state() -> dict:
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except Exception: pass
    return {"last_signal_key": None, "last_action": None}

def save_state(s: dict):
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2))

def tg() -> Telegram:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token or "ضع_توكن" in token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")
    return Telegram(token, os.getenv("TELEGRAM_CHAT_ID", "472883977"))

def format_signal(sig) -> str:
    icon = "🟢 شراء" if sig.side == "BUY" else "🔴 بيع"
    reasons = "\n".join(f"• {x}" for x in sig.reasons)
    return (f"<b>Qannas — إشارة {icon}</b>\n\n"
            f"الأداة: XAUUSD\nالاتجاه: <b>{sig.side}</b>\n"
            f"الدخول التقريبي: <code>{sig.entry:.2f}</code>\n"
            f"وقف الخسارة: <code>{sig.stop:.2f}</code>\n"
            f"الهدف: <code>{sig.target:.2f}</code>\n"
            f"الثقة: <b>{sig.confidence}%</b>\n\n<b>الأسباب:</b>\n{reasons}\n\n"
            "تحقق من سعر Exness والسبريد قبل التنفيذ اليدوي. هذه ليست توصية مالية.")

async def scan():
    try:
        df = fetch_data()
        sig = analyze(df, float(os.getenv("PIP_SIZE", "0.10")), float(os.getenv("RISK_REWARD", "2.0")), float(os.getenv("ATR_STOP_MULTIPLIER", "1.5")), int(os.getenv("MIN_CONFIDENCE", "60")))
        if not sig:
            return
        key = f"{sig.side}:{sig.candle_time}:{sig.entry}:{sig.stop}:{sig.target}"
        s = state()
        if s.get("last_signal_key") == key:
            return
        await tg().send(format_signal(sig), buttons=True)
        s.update({"last_signal_key": key, "last_action": "pending", "last_sent_at": datetime.now(timezone.utc).isoformat()})
        save_state(s)
    except Exception as exc:
        print(f"scan error: {exc}")

@app.on_event("startup")
async def startup():
    scheduler.add_job(scan, "interval", seconds=int(os.getenv("SCAN_INTERVAL_SECONDS", "300")), id="scan", max_instances=1, coalesce=True)
    scheduler.start()
    base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if base:
        try: await tg().set_webhook(f"{base}/telegram/webhook")
        except Exception as exc: print(f"webhook setup error: {exc}")
    await scan()

@app.on_event("shutdown")
def shutdown():
    if scheduler.running: scheduler.shutdown(wait=False)

@app.get("/health")
def health():
    return {"ok": True, "service": "qannas-phone-bot", "mt5_dependency": False}

@app.post("/telegram/webhook")
async def webhook(request: Request):
    update = await request.json()
    chat_id = str(update.get("message", {}).get("chat", {}).get("id", update.get("callback_query", {}).get("message", {}).get("chat", {}).get("id", "")))
    if chat_id != os.getenv("TELEGRAM_CHAT_ID", "472883977"):
        return {"ok": True}
    client = tg()
    if "callback_query" in update:
        cb = update["callback_query"]
        action = "اعتماد الإشارة" if cb.get("data") == "approve" else "إلغاء الإشارة"
        s = state(); s["last_action"] = cb.get("data"); save_state(s)
        await client.answer_callback(cb["id"], action)
        old = cb.get("message", {}).get("text", "")
        await client.edit(cb["message"]["message_id"], old + f"\n\n<b>الحالة:</b> {action}")
    elif update.get("message", {}).get("text", "").startswith("/start"):
        await client.send("أهلاً بك في Qannas. سيتم إرسال إشارات XAUUSD هنا، والتنفيذ يدوي من تطبيق Exness.")
    return {"ok": True}
