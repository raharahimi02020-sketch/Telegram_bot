import telebot
from tinydb import TinyDB, Query

# توکن مستقیم گذاشته شده برای تست
TOKEN = "8468902593:AAGqaP2sLbUaV-m2UpAoHzpuGAAi5M9FgIQ"
bot = telebot.TeleBot(TOKEN)

# پایگاه داده سبک برای کاربران
db = TinyDB('database.json')
users_table = db.table('users')

# ---------- دستور start ----------
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
    bot.send_message(message.chat.id, "سلام! 👋 ربات روشن شد ✅")

# ---------- دستور profile ----------
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

# ---------- اجرای بات ----------
bot.polling()