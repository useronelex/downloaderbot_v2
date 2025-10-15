import os
import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram import exceptions
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from downloader import extract_instagram_video

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен бота з Render environment
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # твій публічний URL на Render, наприклад: https://downloaderbot-v2.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"  # шлях для Telegram webhook
FULL_WEBHOOK_URL = WEBHOOK_URL + WEBHOOK_PATH  # повний URL, куди Telegram шле оновлення

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ BOT_TOKEN або WEBHOOK_URL не задано в environment variables")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()

# ================== HANDLERS ==================
@router.message(F.text.contains("instagram.com"))
async def handle_video(message: types.Message):
    print(f"🔹 Received message: {message.text}")  # лог повідомлення
    wait_msg = await message.answer("⏳ Завантажую відео...")

    try:
        link = await extract_instagram_video(message.text.strip())
    except Exception as e:
        await wait_msg.edit_text(f"⚠️ Помилка під час обробки: {e}")
        return

    await wait_msg.delete()

    try:
        if message.text.strip().startswith("http") and len(message.text.strip().split()) == 1:
            await message.delete()
    except exceptions.TelegramForbiddenError:
        await message.answer("⚠️ Немає дозволу видаляти повідомлення.")

    if link:
        await message.answer_video(link)
        print(f"✅ Video sent for link: {message.text}")
    else:
        await message.answer("😵 Не вдалося знайти відео.")
        print(f"⚠️ No video found for link: {message.text}")

# ================== WEBHOOK SERVER ==================
async def handle_webhook(request):
    """Обробка запитів від Telegram"""
    try:
        update_json = await request.json()
        print("🔹 Incoming update:", update_json)
        update = types.Update(**update_json)
        await dp.feed_update(update)  # в aiogram v3.x process_update → feed_update
    except Exception as e:
        print(f"❌ Error handling update: {e}")
        return web.Response(status=500, text="Internal Server Error")
    return web.Response(text="ok")


async def on_startup(app):
    await bot.set_webhook(FULL_WEBHOOK_URL)
    dp.include_router(router)
    print(f"🤖 Бот запущено через webhook на {FULL_WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    print("🧹 Бот завершив роботу")


# ================== AIOHTTP APP ==================
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
