import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import exceptions
from aiogram.client.default import DefaultBotProperties

from downloader import extract_instagram_video

# ================== CONFIG ==================
BOT_TOKEN = "7644549931:AAHJFUvF3SZe2Ig3izoBF2wj10IV_Vq5pQM"
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set")

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
    """Обробка натискання кнопки 'Завершити роботу'"""
    await callback.answer("🔻 Завершення роботи...")

    try:
        await callback.message.edit_text("🛑 Бот завершує роботу...")
    except exceptions.TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer("🛑 Бот завершує роботу...")

    # Коректне завершення polling
    asyncio.create_task(stop_polling())


async def stop_polling():
    """Акуратне завершення без RuntimeError"""
    await asyncio.sleep(1)
    await dp.stop_polling()
    await bot.session.close()


# ================== MAIN ==================
async def main():
    dp.include_router(router)
    print("🤖 Бот запущено і готовий до роботи!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🧹 Завершено вручну.")
