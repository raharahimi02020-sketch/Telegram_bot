import telebot
from telebot import types
from tinydb import TinyDB, Query
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

db = TinyDB('database.json')
users_table = db.table('users')
games_table = db.table('games')

ADMIN_ID = 123456789  # شناسه تلگرام ادمین

# ---------- دستورات کاربران ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = users_table.get(Query().id == message.from_user.id)
    if not user:
        users_table.insert({
            'id': message.from_user.id,
            'username': message.from_user.username or "",
            'games_played': 0,
            'wins': 0
        })
    bot.send_message(message.chat.id, "سلام! 👋 خوش اومدی به ربات منچ آنلاین!")

@bot.message_handler(commands=['profile'])
def profile(message):
    user = users_table.get(Query().id == message.from_user.id)
    if user:
        text = f"👤 پروفایل شما:\n"
        text += f"نام کاربری: @{user['username']}\n"
        text += f"تعداد بازی‌ها: {user['games_played']}\n"
        text += f"بردها: {user['wins']}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "شما هنوز ثبت‌نام نکردید، /start بزنید.")

# ---------- منو بازی ----------
@bot.message_handler(commands=['play'])
def play(message):
    # نسخه ساده: فقط اعلام می‌کنیم کاربر آماده بازیه
    bot.send_message(message.chat.id, "✅ شما برای بازی منچ آماده شدید! منتظر بازیکن دیگر...")

# ---------- دستورات ادمین ----------
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "دسترسی ندارید!")
        return
    total_users = len(users_table)
    total_games = len(games_table)
    bot.send_message(message.chat.id, f"📊 آمار بات:\nتعداد کاربران: {total_users}\nتعداد بازی‌ها: {total_games}")

@bot.message_handler(commands=['messageall'])
def messageall(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "دسترسی ندارید!")
        return
    text = message.text.replace("/messageall", "").strip()
    if not text:
        bot.reply_to(message, "متن پیام را بعد از /messageall بنویسید")
        return
    for u in users_table:
        try:
            bot.send_message(u['id'], f"📢 پیام ادمین:\n{text}")
        except:
            continue
    bot.reply_to(message, "پیام به همه کاربران ارسال شد ✅")

# ---------- اجرای بات ----------
bot.polling()