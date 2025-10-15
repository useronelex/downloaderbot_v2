import os
import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import exceptions
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from downloader import extract_instagram_video

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен бота з Render environment
WEBHOOK_URL = "https://downloaderbot-v2.onrender.com"  # твій публічний URL на Render
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

# ================== KEYBOARD ==================
shutdown_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛑 Завершити роботу", callback_data="shutdown_bot")]
    ]
)

# ================== HANDLERS ==================
@router.message(F.text.contains("instagram.com"))
async def handle_video(message: types.Message):
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
        await message.answer("⚠️ Немає дозволу видаляти повідомлення.", reply_markup=shutdown_keyboard)

    if link:
        await message.answer_video(link, reply_markup=shutdown_keyboard)
    else:
        await message.answer("😵 Не вдалося знайти відео.", reply_markup=shutdown_keyboard)


@router.callback_query(F.data == "shutdown_bot")
async def shutdown_bot(callback: types.CallbackQuery):
    await callback.answer("🔻 Завершення роботи...")
    try:
        await callback.message.edit_text("🛑 Бот завершує роботу...")
    except exceptions.TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer("🛑 Бот завершує роботу...")

    # Завершення сервера
    asyncio.create_task(stop_server())


async def stop_server():
    await bot.session.close()
    print("🧹 Бот завершив роботу.")
    os._exit(0)  # Render "kill" process


# ================== WEBHOOK SERVER ==================
async def handle_webhook(request):
    """Обробка запитів від Telegram"""
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return web.Response(text="ok")


async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    dp.include_router(router)
    print("🤖 Бот запущено через webhook!")


async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()


app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
