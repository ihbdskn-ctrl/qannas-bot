from __future__ import annotations

import httpx


class Telegram:
    def __init__(self, token: str, chat_id: str):
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    async def call(self, method: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.base}/{method}", json=payload)
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                raise RuntimeError(data)
            return data["result"]

    async def send(self, text: str, buttons: bool = False) -> dict:
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": [[
                {"text": "✅ اعتماد الإشارة", "callback_data": "approve"},
                {"text": "❌ إلغاء الإشارة", "callback_data": "cancel"},
            ]]}
        return await self.call("sendMessage", payload)

    async def answer_callback(self, callback_id: str, text: str) -> None:
        await self.call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text, "show_alert": False})

    async def edit(self, message_id: int, text: str) -> None:
        await self.call("editMessageText", {"chat_id": self.chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"})

    async def set_webhook(self, url: str) -> None:
        await self.call("setWebhook", {"url": url, "allowed_updates": ["message", "callback_query"]})
