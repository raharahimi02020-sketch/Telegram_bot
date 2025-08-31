import telebot
from telebot import types
from tinydb import TinyDB, Query
import random

# ---------- توکن ----------
TOKEN = "8468902593:AAGqaP2sLbUaV-m2UpAoHzpuGAAi5M9FgIQ"
bot = telebot.TeleBot(TOKEN)

# ---------- پایگاه داده ----------
db = TinyDB('database.json')
users_table = db.table('users')
support_table = db.table('support')

# ---------- تنظیمات ----------
ADMIN_ID = 123456789  # شناسه تلگرام ادمین خودت

# ---------- متدهای کمک ----------
def get_user(user_id):
    return users_table.get(Query().id == user_id)

def update_user(user):
    users_table.update(user, Query().id == user['id'])

def create_profile(message):
    bot.send_message(message.chat.id, "برای شروع بازی لطفا پروفایل خود را تکمیل کنید.")

# ---------- دستور start ----------
@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    if not user:
        users_table.insert({
            'id': message.from_user.id,
            'username': message.from_user.username or "",
            'nickname': "",
            'age': 0,
            'city': "",
            'medals': [],
            'coins': 0,
            'games_played': 0,
            'wins': 0,
            'banned': False
        })
        create_profile(message)

    # ---------- منوی شیشه‌ای ----------
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row("🎲 بازی منچ", "👤 پروفایل")
    markup.row("💬 پشتیبانی", "📨 دعوت دوستان")
    markup.row("📊 آمار من", "🔧 تنظیمات")
    
    bot.send_message(message.chat.id,
                     "🎉 خوش آمدید به بات منچ آنلاین!\nاز منوی زیر می‌توانید کارها را شروع کنید:",
                     reply_markup=markup)

# ---------- دریافت پیام کاربران ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user = get_user(message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "لطفا ابتدا /start را بزنید.")
        return
    if user['banned']:
        bot.send_message(message.chat.id, "❌ شما بن شده‌اید و نمی‌توانید بازی کنید.")
        return

    text = message.text
    if text == "🎲 بازی منچ":
        if user['coins'] < 5:
            bot.send_message(message.chat.id, "⚠️ شما ۵ سکه نیاز دارید.")
            return
        user['coins'] -= 5
        user['games_played'] += 1
        update_user(user)
        dice = random.randint(1,6)
        bot.send_message(message.chat.id, f"🎲 شما تاس ریختید: {dice}\n(نسخه اولیه: حرکت مهره ثبت شد)")

    elif text == "👤 پروفایل":
        bot.send_message(message.chat.id,
                         f"👤 پروفایل شما:\nنام مستعار: {user['nickname']}\nسن: {user['age']}\nشهر: {user['city']}\nسکه‌ها: {user['coins']}\nمدال‌ها: {', '.join(user['medals']) if user['medals'] else 'ندارد'}\nتعداد بازی‌ها: {user['games_played']}\nبردها: {user['wins']}")

    elif text == "💬 پشتیبانی":
        bot.send_message(message.chat.id, "پیام خود را برای پشتیبانی ارسال کنید.")
        support_table.insert({'from': user['id'], 'text': "در انتظار پیام..."})  # آماده دریافت پیام بعدی

    elif text == "📨 دعوت دوستان":
        bot.send_message(message.chat.id, f"لینک دعوت شما: https://t.me/YourBotUsername?start={user['id']}\n🎁 با دعوت دوستان ۲۰ سکه دریافت می‌کنید!")

    elif text == "📊 آمار من":
        bot.send_message(message.chat.id, f"تعداد بازی‌ها: {user['games_played']}\nبردها: {user['wins']}\nسکه‌ها: {user['coins']}")

    elif text == "🔧 تنظیمات":
        bot.send_message(message.chat.id, "تنظیمات بات…")

    else:
        bot.send_message(message.chat.id, "⚠️ گزینه نامعتبر! لطفا از منوی شیشه‌ای انتخاب کنید.")

# ---------- دریافت پیام پشتیبانی ----------
@bot.message_handler(func=lambda m: True)
def handle_support_messages(message):
    user = get_user(message.from_user.id)
    if not user: return
    support_table.insert({'from': user['id'], 'text': message.text})
    bot.send_message(message.chat.id, "✅ پیام شما به ادمین ارسال شد.")

# ---------- ادمین: دادن سکه ----------
@bot.message_handler(commands=['addcoins'])
def addcoins(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        user = get_user(user_id)
        if not user:
            bot.reply_to(message, "کاربر پیدا نشد!")
            return
        user['coins'] += amount
        update_user(user)
        bot.reply_to(message, f"✅ {amount} سکه به {user['nickname']} اضافه شد.")
    except:
        bot.reply_to(message, "فرمت: /addcoins <user_id> <تعداد>")

@bot.message_handler(commands=['addcoinsall'])
def addcoinsall(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return
    try:
        amount = int(message.text.split()[1])
        all_users = users_table.all()
        for u in all_users:
            u['coins'] += amount
            update_user(u)
        bot.reply_to(message, f"✅ {amount} سکه به همه کاربران اضافه شد.")
    except:
        bot.reply_to(message, "فرمت: /addcoinsall <تعداد>")

# ---------- اجرای بات ----------
bot.polling()