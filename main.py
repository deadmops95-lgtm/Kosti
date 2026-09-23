import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    WebAppInfo,
)

# Твой токен бота
TOKEN = "7734913058:AAFWPIZl-cHsysCifXJsHj23oZD8QcAztvE"

# Ссылка на твое 3D мини-приложение на GitHub Pages
WEB_APP_URL = "https://deadmops95-lgtm.github.io/Kosti/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Инициализация базы данных SQLite для сохранения рекордов
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
  # Устанавливаем кнопку «Меню» (слева внизу возле ввода текста)
  try:
    await bot.set_chat_menu_button(
        chat_id=message.from_user.id,
        menu_button=MenuButtonWebApp(
            text="🎮 Играть", web_app=WebAppInfo(url=WEB_APP_URL)
        ),
    )
  except Exception as e:
    logging.error(f"Не удалось установить кнопку меню: {e}")

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
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
      "Привет! Добро пожаловать в мультиплеерный **Фэнтези 3D Покер на"
      " костях** 🎲✨\n\n🔮 Нажми кнопку **«🎮 Играть»** в левом нижнем углу"
      " экрана, чтобы открыть магическую арену!"
  )
  await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
  rules_text = (
      "📖 **Правила игры**:\n\n1. Нажми кнопку **«🎮 Играть»** слева внизу."
      "\n2. Зайди в 3D-комнату.\n3. Бросай рунические кубики, собирай"
      " комбинации и побеждай!"
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
        "🏆 **Таблица лидеров**\n\nПока пусто. Стань первым чемпионом!"
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
                  text="🏆 Таблица лидеров", callback_data="show_top"
              ),
              InlineKeyboardButton(
                  text="📖 Правила", callback_data="show_rules"
              ),
          ],
      ]
  )
  text = (
      "Привет! Добро пожаловать в мультиплеерный **Фэнтези 3D Покер на"
      " костях** 🎲✨\n\n🔮 Нажми кнопку **«🎮 Играть»** в левом нижнем углу"
      " экрана, чтобы открыть магическую арену!"
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


async def main():
  init_db()
  logging.info("Бот успешно запущен!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
