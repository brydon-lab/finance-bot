import asyncio
import os
import threading
from aiohttp import web
from server import create_app
import bot as bot_module
from telegram.ext import Application, CommandHandler, MessageHandler, filters

def run_web():
    port = int(os.getenv("PORT", 8080))
    app = create_app()
    web.run_app(app, port=port)

async def run_bot():
    TOKEN = os.getenv("BOT_TOKEN", "8643925833:AAGlky5L6iytMziWdd65QTcGQjPPExuMiw0")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.railway.app")
    bot_module.WEBAPP_URL = WEBAPP_URL
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", bot_module.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_module.handle_message))
    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print(f"Веб-сервер запущен на порту {os.getenv('PORT', 8080)}")
    asyncio.run(run_bot())