from __future__ import annotations

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from .app import scan
from .telegram import Telegram

async def main():
    client = Telegram(os.environ["TELEGRAM_BOT_TOKEN"], os.getenv("TELEGRAM_CHAT_ID", "472883977"))
    offset = 0
    while True:
        try:
            updates = await client.call("getUpdates", {"timeout": 25, "offset": offset, "allowed_updates": ["callback_query", "message"]})
            for update in updates:
                offset = update["update_id"] + 1
                # Webhook handler logic is intentionally simple in polling mode:
                # signal scanning remains available; callback actions can be handled by webhook deployment.
            await scan()
        except Exception as exc:
            print(f"polling error: {exc}")
        await asyncio.sleep(int(os.getenv("SCAN_INTERVAL_SECONDS", "300")))

if __name__ == "__main__":
    asyncio.run(main())
