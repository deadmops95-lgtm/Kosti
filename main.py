import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

# Твой токен бота
TOKEN = "7734913058:AAFWPIZl-cHsysCifXJsHj23oZD8QcAztvE"

# Ссылка на твое веб-приложение (3D Фэнтези арена на Bothost)
WEB_APP_URL = "https://dice-poker-bot.bothost.ru"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Инициализация базы данных для рекордов
def init_db():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER
        )
    """)
  conn.commit()
  conn.close()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Играть в 3D Покер (Лобби)",
                  web_app=WebAppInfo(url=WEB_APP_URL),
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏆 Таблица лидеров", callback_data="show_top"
              ),
              InlineKeyboardButton(
                  text="📖 Правила", callback_data="show_rules"
              ),
          ],
      ]
  )

  text = (
      "Привет! Добро пожаловать в мультиплеерный **3D Покер на костях** 🎲✨\n\n"
      "Нажми кнопку ниже, чтобы открыть трехмерную игровую комнату на 2–4"
      " человека!"
  )
  await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
  rules_text = (
      "📖 **Правила 3D Покера на костях**:\n\n"
      "1. Зайди в 3D-комнату (от 2 до 4 игроков).\n"
      "2. Бросай кубики в реальном времени с крутой 3D-физикой.\n"
      "3. Собирай комбинации (Покер, Каре, Стрит, Фулл-Хаус) и побеждай"
      " соперников!"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")
      ]]
  )
  await callback.message.edit_text(
      rules_text, reply_markup=kb, parse_mode="Markdown"
  )
  await callback.answer()


@dp.callback_query(F.data == "show_top")
async def show_top(callback: types.CallbackQuery):
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT name, score FROM records ORDER BY score DESC LIMIT 10"
  )
  rows = cursor.fetchall()
  conn.close()

  if not rows:
    top_text = (
        "🏆 **Таблица лидеров**\n\nПока пусто. Стань первым чемпионом в 3D!"
    )
  else:
    top_text = "🏆 **Топ-10 игроков:**\n\n"
    for idx, (name, score) in enumerate(rows, start=1):
      top_text += f"{idx}. **{name}** — {score} очков\n"

  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")
      ]]
  )
  await callback.message.edit_text(
      top_text, reply_markup=kb, parse_mode="Markdown"
  )
  await callback.answer()


@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Играть в 3D Покер (Лобби)",
                  web_app=WebAppInfo(url=WEB_APP_URL),
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏆 Таблица лидеров", callback_data="show_top"
              ),
              InlineKeyboardButton(
                  text="📖 Правила", callback_data="show_rules"
              ),
          ],
      ]
  )
  text = (
      "Привет! Добро пожаловать в мультиплеерный **3D Покер на костях** 🎲✨\n\n"
      "Нажми кнопку ниже, чтобы открыть трехмерную игровую комнату на 2–4"
      " человека!"
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


async def main():
  init_db()
  # Запускаем локальный HTTP-сервер для Bothost, чтобы отдавать index.html
  from aiohttp import web

  async def handle(request):
    return web.FileResponse("index.html")

  app = web.Application()
  app.router.add_get("/", handle)

  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "0.0.0.0", 3000)
  await site.start()
  logging.info("HTTP сервер с 3D ареной запущен на порту 3000")

  # Запуск бота
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
