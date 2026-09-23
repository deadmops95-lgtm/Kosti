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

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Инициализация базы данных для рекордов и комнат
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
  # Ссылка на наше веб-приложение (пока поставим заглушку, позже заменим на реальный адрес с Bothost)
  web_app_url = "https://example.com"

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Играть в 3D Покер (Лобби)",
                  web_app=WebAppInfo(url=web_app_url),
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
  web_app_url = "https://example.com"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Играть в 3D Покер (Лобби)",
                  web_app=WebAppInfo(url=web_app_url),
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
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
