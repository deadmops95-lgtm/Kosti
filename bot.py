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

# Эмодзи для кубиков
DICE_EMOJI = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# Хранилище игр пользователей (пока в памяти)
user_games = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🎲 Начать игру в Покер на костях", callback_data="start_game"
          )
      ]]
  )
  await message.answer(
      "Привет! Это игра **Покер на костях**.\nЦель — собрать лучшие комбинации"
      " и набрать больше всего очков.",
      reply_markup=kb,
      parse_mode="Markdown",
  )


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
  dice_str = " ".join(
      [
          f"[{DICE_EMOJI[d]}]" if not game["locked"][i] else f"🔒{DICE_EMOJI[d]}"
          for i, d in enumerate(game["dice"])
      ]
  )

  text = (
      f"🎲 **Твои кубики:**\n{dice_str}\n\nОсталось перебросов:"
      f" {game['rolls_left']}\nНажми на кнопку кубика под сообщением, чтобы"
      " зафиксировать его (или снять фиксацию), затем сделай переброс."
  )

  buttons = []
  row1 = []
  for i in range(5):
    status = "✅" if game["locked"][i] else "❌"
    row1.append(
        InlineKeyboardButton(
            text=f"{i+1} {status}", callback_data=f"lock_{i}"
        )
    )
  buttons.append(row1)

  if game["rolls_left"] > 0:
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Перебросить выбранные", callback_data="reroll"
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
      "✅ Броски завершены! (Логику подсчета очков и таблицы мы добавим в"
      " следующем шаге).",
      parse_mode="Markdown",
  )
  await callback.answer()


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
