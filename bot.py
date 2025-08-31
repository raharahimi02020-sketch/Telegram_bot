import telebot
from telebot import types
from tinydb import TinyDB, Query
import random

# ---------- توکن ----------
TOKEN = "توکن_ربات_تو_اینجا"
bot = telebot.TeleBot(TOKEN)

# ---------- پایگاه داده ----------
db = TinyDB('database.json')
users_table = db.table('users')
games_table = db.table('games')
support_table = db.table('support')

# ---------- تنظیمات ----------
ADMIN_ID = 123456789

# ---------- متدهای کمک ----------
def get_user(user_id):
    return users_table.get(Query().id == user_id)

def update_user(user):
    users_table.update(user, Query().id == user['id'])

def create_profile(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("شروع ثبت پروفایل")
    bot.send_message(message.chat.id, "برای بازی ابتدا پروفایل خود را تکمیل کنید.", reply_markup=markup)

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
    else:
        if user['banned']:
            bot.send_message(message.chat.id, "❌ شما بن شده‌اید.")
        else:
            bot.send_message(message.chat.id, "سلام دوباره! برای شروع بازی /menu را بزنید.")

# ---------- منوی اصلی ----------
@bot.message_handler(commands=['menu'])
def menu(message):
    user = get_user(message.from_user.id)
    if not user or user['nickname']=="":
        create_profile(message)
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎲 بازی منچ", callback_data="play"))
    markup.add(types.InlineKeyboardButton("👤 پروفایل", callback_data="profile"))
    markup.add(types.InlineKeyboardButton("💬 پشتیبانی", callback_data="support"))
    markup.add(types.InlineKeyboardButton("📨 دعوت دوستان", callback_data="invite"))
    bot.send_message(message.chat.id, "منوی اصلی:", reply_markup=markup)

# ---------- callback منو ----------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user = get_user(call.from_user.id)
    if user['banned']:
        bot.answer_callback_query(call.id, "❌ شما بن شده‌اید.")
        return

    if call.data == "play":
        if user['coins'] < 5:
            bot.send_message(call.message.chat.id, "⚠️ شما ۵ سکه نیاز دارید.")
        else:
            user['coins'] -= 5
            users_table.update({'coins': user['coins']}, Query().id == user['id'])
            # شروع بازی ساده: نوبت اول تاس
            dice = random.randint(1,6)
            bot.send_message(call.message.chat.id, f"🎲 شما تاس ریختید: {dice}\n(نسخه اولیه: حرکت مهره ثبت شد)")

    elif call.data == "profile":
        text = f"👤 پروفایل شما:\n"
        text += f"نام مستعار: {user['nickname']}\nسن: {user['age']}\nشهر: {user['city']}\n"
        text += f"سکه‌ها: {user['coins']}\nمدال‌ها: {', '.join(user['medals']) if user['medals'] else 'ندارد'}\n"
        text += f"تعداد بازی‌ها: {user['games_played']}\nبردها: {user['wins']}"
        bot.send_message(call.message.chat.id, text)

    elif call.data == "support":
        bot.send_message(call.message.chat.id, "پیام خود را برای پشتیبانی ارسال کنید.")

    elif call.data == "invite":
        bot.send_message(call.message.chat.id, f"لینک دعوت شما: https://t.me/YourBotUsername?start={user['id']}\n🎁 با دعوت دوستان ۲۰ سکه دریافت می‌کنید!")

# ---------- دریافت پیام پشتیبانی ----------
@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    user = get_user(message.from_user.id)
    if not user:
        return
    support_table.insert({'from': message.from_user.id, 'text': message.text})
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