import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Твой токен бота
TOKEN = "7734913058:AAFWPIZl-cHsysCifXJsHj23oZD8QcAztvE"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Крупные и яркие символы для кубиков в кружках
DICE_EMOJI = {1: "➀", 2: "➁", 3: "➂", 4: "➃", 5: "➄", 6: "➅"}

# Хранилище игр пользователей
user_games = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Начать игру в Покер на костях",
                  callback_data="start_game",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📖 Правила игры", callback_data="show_rules"
              )
          ],
      ]
  )
  await message.answer(
      "Привет! Это игра **Покер на костях**.\nЦель — собрать лучшие комбинации"
      " и набрать больше всего очков.",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
  rules_text = (
      "📖 **Правила игры «Покер на костях»**:\n\n"
      "1. **Цель игры:** выбросить за 3 попытки лучшую комбинацию из 5"
      " кубиков.\n"
      "2. **Броски:**\n"
      "   • Сделай первый бросок.\n"
      "   • Нажми на кнопки кубиков (1–5), чтобы зафиксировать (🔒) те, которые"
      " тебе нравятся.\n"
      "   • Нажми «Перебросить незафиксированные», чтобы перекинуть"
      " остальные (у тебя есть 2 переброса).\n"
      "3. **Комбинации:**\n"
      "   • **Пара** — две одинаковые кости.\n"
      "   • **Тройка** — три одинаковые кости.\n"
      "   • **Каре** — четыре одинаковые кости.\n"
      "   • **Покер** — все 5 кубиков одинаковые! (Самая ценная комбинация).\n"
      "   • **Стрит** — последовательность (например, 1-2-3-4-5).\n"
  )

  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_home")
      ]]
  )
  await callback.message.edit_text(
      rules_text, reply_markup=kb, parse_mode="Markdown"
  )
  await callback.answer()


@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎲 Начать игру в Покер на костях",
                  callback_data="start_game",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📖 Правила игры", callback_data="show_rules"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      "Привет! Это игра **Покер на костях**.\nЦель — собрать лучшие комбинации"
      " и набрать больше всего очков.",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.data == "start_game")
async def start_game(callback: types.CallbackQuery):
  user_games[callback.from_user.id] = {
      "dice": [random.randint(1, 6) for _ in range(5)],
      "rolls_left": 2,  # осталось перебросов
      "locked": [False, False, False, False, False],
  }
  await show_desk(callback.message, callback.from_user.id, edit=False)
  await callback.answer()


async def show_desk(message: types.Message, user_id: int, edit: bool = True):
  game = user_games[user_id]

  dice_display = []
  for i, d in enumerate(game["dice"]):
    if game["locked"][i]:
      dice_display.append(f"🔒{DICE_EMOJI[d]}")
    else:
      dice_display.append(f"🎲 {DICE_EMOJI[d]}")

  dice_str = "   ".join(dice_display)

  text = (
      f"🎯 **Твой бросок:**\n\n"
      f"   {dice_str}\n\n"
      f"🔄 Осталось перебросов: **{game['rolls_left']}**\n\n"
      "*Инструкция:* нажми на кнопки ниже (1–5), чтобы зафиксировать нужные"
      " кости (появится 🔒), а затем нажми «Перебросить выбранные»."
  )

  buttons = []
  row1 = []
  for i in range(5):
    row1.append(
        InlineKeyboardButton(
            text=f"{i+1} {'✅' if game['locked'][i] else '❌'}",
            callback_data=f"lock_{i}",
        )
    )
  buttons.append(row1)

  if game["rolls_left"] > 0:
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Перебросить незафиксированные", callback_data="reroll"
        )
    ])

  buttons.append(
      [InlineKeyboardButton(text="📊 Выбрать комбинацию", callback_data="finish")]
  )
  kb = InlineKeyboardMarkup(inline_keyboard=buttons)

  if edit:
    await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  else:
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("lock_"))
async def process_lock(callback: types.CallbackQuery):
  user_id = callback.from_user.id
  idx = int(callback.data.split("_")[1])
  game = user_games[user_id]

  game["locked"][idx] = not game["locked"][idx]
  await show_desk(callback.message, user_id)
  await callback.answer()


@dp.callback_query(F.data == "reroll")
async def process_reroll(callback: types.CallbackQuery):
  user_id = callback.from_user.id
  game = user_games[user_id]

  if game["rolls_left"] > 0:
    game["rolls_left"] -= 1
    for i in range(5):
      if not game["locked"][i]:
        game["dice"][i] = random.randint(1, 6)

  await show_desk(callback.message, user_id)
  await callback.answer()


@dp.callback_query(F.data == "finish")
async def process_finish(callback: types.CallbackQuery):
  await callback.message.edit_text(
      "✅ Броски завершены! Скоро добавим сюда полноценную таблицу"
      " комбинаций (Пара, Стрит, Покер и т.д.).",
      parse_mode="Markdown",
  )
  await callback.answer()


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
