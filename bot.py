import asyncio
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Твой токен бота
TOKEN = "7734913058:AAFWPIZl-cHsysCifXJsHj23oZD8QcAztvE"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Крупные символы для вывода результатов
DICE_EMOJI = {1: "➀", 2: "➁", 3: "➂", 4: "➃", 5: "➄", 6: "➅"}

# --- РАБОТА С БАЗОЙ ДАННЫХ SQLite ---
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


def save_score(user_id: int, name: int, score: int):
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT score FROM records WHERE user_id = ?", (user_id,))
  row = cursor.fetchone()

  if row is None:
    cursor.execute(
        "INSERT INTO records (user_id, name, score) VALUES (?, ?, ?)",
        (user_id, name, score),
    )
  else:
    if score > row[0]:
      cursor.execute(
          "UPDATE records SET score = ?, name = ? WHERE user_id = ?",
          (score, name, user_id),
      )
  conn.commit()
  conn.close()


def get_top_players():
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT name, score FROM records ORDER BY score DESC LIMIT 10"
  )
  rows = cursor.fetchall()
  conn.close()
  return rows


# Хранилище активных партий в памяти
user_games = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  await show_main_menu(message, edit=False)


async def show_main_menu(message: types.Message, edit: bool = True):
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
                  text="🏆 Таблица лидеров", callback_data="show_top"
              ),
              InlineKeyboardButton(
                  text="📖 Правила игры", callback_data="show_rules"
              ),
          ],
      ]
  )
  text = (
      "Привет! Это игра **Покер на костях** 🎲\n\nБросай кубики, собирай"
      " комбинации, ставь рекорды и соревнуйся с другими игроками!"
  )

  if edit:
    await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  else:
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
  rules_text = (
      "📖 **Правила игры «Покер на костях»**:\n\n"
      "1. **Цель:** выбросить за попытки лучшую комбинацию из 5 кубиков.\n"
      "2. **Броски:**\n"
      "   • Бросай кубики и фиксируй (🔒) те, которые нравятся.\n"
      "   • Перебрасывай остальные.\n"
      "3. **Основные комбинации и очки:**\n"
      "   • 🔥 **Покер** (5 одинаковых) — 50 очков\n"
      "   • ⭐ **Каре** (4 одинаковых) — 40 очков\n"
      "   • 🏠 **Фулл Хаус** (3 + 2) — 30 очков\n"
      "   • 📊 **Стрит** (последовательность) — 25 очков\n"
      "   • 🎲 **Тройка** — 20 очков\n"
      "   • 👥 **Две пары** — 15 очков\n"
      "   • 🔹 **Пара** — 10 очков\n"
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


@dp.callback_query(F.data == "show_top")
async def show_top(callback: types.CallbackQuery):
  top_data = get_top_players()
  if not top_data:
    top_text = (
        "🏆 **Таблица лидеров**\n\nПока нет ни одного сохраненного рекорда."
        " Сыграй первым(-ой)!"
    )
  else:
    top_text = "🏆 **Топ-10 игроков (База данных):**\n\n"
    for idx, (name, score) in enumerate(top_data, start=1):
      medal = (
          "🥇"
          if idx == 1
          else "🥈"
          if idx == 2
          else "🥉"
          if idx == 3
          else f"{idx}."
      )
      top_text += f"{medal} **{name}** — {score} очков\n"

  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_home")
      ]]
  )
  await callback.message.edit_text(
      top_text, reply_markup=kb, parse_mode="Markdown"
  )
  await callback.answer()


@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
  await show_main_menu(callback.message, edit=True)
  await callback.answer()


@dp.callback_query(F.data == "start_game")
async def start_game(callback: types.CallbackQuery):
  # Красивая анимация броска кубиков от телеграма перед началом!
  msg = await callback.message.answer("🎲 Бросаем кости...")
  dice_msg = await callback.message.answer_dice(emoji="🎲")
  await asyncio.sleep(3)  # Ждем пока анимация проиграет в чате
  await msg.delete()

  user_games[callback.from_user.id] = {
      "dice": [random.randint(1, 6) for _ in range(5)],
      "rolls_left": 2,
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
      f"🎯 **Твой игровой стол:**\n\n"
      f"   {dice_str}\n\n"
      f"🔄 Осталось перебросов: **{game['rolls_left']}**\n\n"
      "Нажми на кнопки ниже (1–5), чтобы зафиксировать нужные кубики, а затем"
      " сделай переброс."
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
      [InlineKeyboardButton(text="📊 Подсчитать результат", callback_data="finish")]
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
    # Красивая анимация перед перебросом
    dice_anim = await callback.message.answer_dice(emoji="🎲")
    await asyncio.sleep(2.5)
    await dice_anim.delete()

    for i in range(5):
      if not game["locked"][i]:
        game["dice"][i] = random.randint(1, 6)

  await show_desk(callback.message, user_id)
  await callback.answer()


def evaluate_combination(dice: list):
  dice.sort()
  counts = {x: dice.count(x) for x in set(dice)}
  values = sorted(counts.values(), reverse=True)

  if values == [5]:
    return "🔥 Покер (5 одинаковых)", 50
  elif values == [4, 1]:
    return "⭐ Каре (4 одинаковых)", 40
  elif values == [3, 2]:
    return "🏠 Фулл Хаус (3 + 2)", 30
  elif set(dice) in [{1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}] or len(set(dice)) == 5:
    return "📊 Стрит", 25
  elif values == [3, 1, 1]:
    return "🎲 Тройка", 20
  elif values == [2, 2, 1]:
    return "👥 Две пары", 15
  elif values == [2, 1, 1, 1]:
    return "🔹 Пара", 10

  return "❌ Шанс (без комбинации)", sum(dice)


@dp.callback_query(F.data == "finish")
async def process_finish(callback: types.CallbackQuery):
  user_id = callback.from_user.id
  user_name = callback.from_user.first_name or "Игрок"
  game = user_games[user_id]
  dice = game["dice"]

  combo_name, score = evaluate_combination(dice)
  dice_display = " ".join([DICE_EMOJI[d] for d in dice])

  # Сохраняем результат в базу данных SQLite
  save_score(user_id, user_name, score)

  text = (
      f"🏁 **Итог броска!**\n\n"
      f"Кубики: {dice_display}\n\n"
      f"Комбинация: **{combo_name}**\n"
      f"Очки за раунд: **+{score}**\n\n"
      f"💾 *Результат успешно сохранен в базу данных!*"
  )

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔄 Сыграть еще раз", callback_data="start_game"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏆 Таблица лидеров", callback_data="show_top"
              ),
              InlineKeyboardButton(
                  text="🏠 Меню", callback_data="back_home"
              ),
          ],
      ]
  )

  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


async def main():
  # Инициализируем базу данных при запуске
  init_db()
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
