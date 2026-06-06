import asyncio
import os
import threading
import bot as bot_module
from aiohttp import web
from server import create_app
from telegram.ext import Application, CommandHandler, MessageHandler, filters

async def run_bot():
    TOKEN = os.getenv("BOT_TOKEN", "8643925833:AAGlky5L6iytMziWdd65QTcGQjPPExuMiw0")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.railway.app")
    bot_module.WEBAPP_URL = WEBAPP_URL
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", bot_module.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_module.handle_message))
    async with app:
        await app.start()
        await app.updater.start_polling()
        print("Бот запущен...")
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()

async def run_web():
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(create_app())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Веб-сервер на порту {port}")

async def main():
    await asyncio.gather(run_web(), run_bot())

if __name__ == "__main__":
    asyncio.run(main())