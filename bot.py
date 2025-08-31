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
ADMIN_ID = 8461153976  # آی‌دی تلگرام ادمین خودت

# ---------- متدهای کمک ----------
def get_user(user_id):
    return users_table.get(Query().id == user_id)

def update_user(user):
    users_table.update(user, Query().id == user['id'])

def is_admin(user_id):
    return user_id == ADMIN_ID

def send_main_menu(message):
    user = get_user(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    # منوی کاربران
    markup.row("🎲 بازی منچ", "👤 پروفایل")
    markup.row("💬 پشتیبانی", "📨 دعوت دوستان")
    markup.row("📊 آمار من", "🔧 تنظیمات")
    # منوی ادمین
    if is_admin(user['id']):
        markup.row("👥 مدیریت کاربران", "💰 مدیریت سکه")
        markup.row("🚫 بن کردن کاربر", "✉️ ارسال پیام به کاربران")
    bot.send_message(message.chat.id,
                     "📌 منو را انتخاب کنید:",
                     reply_markup=markup)

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
            'banned': False,
            'profile_step': 1
        })
        bot.send_message(message.chat.id, "🎉 خوش آمدید! ابتدا پروفایل خود را تکمیل کنید.")
        return bot.send_message(message.chat.id, "🎯 لطفا نام مستعار خود را وارد کنید:")

    if user['nickname'] == "":
        user['profile_step'] = 1
        update_user(user)
        bot.send_message(message.chat.id, "🎯 لطفا نام مستعار خود را وارد کنید:")
        return

    send_main_menu(message)

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

    # ---------- تکمیل پروفایل مرحله‌ای ----------
    if 'profile_step' in user and user['profile_step'] > 0:
        step = user['profile_step']
        if step == 1:
            user['nickname'] = message.text
            user['profile_step'] = 2
            update_user(user)
            bot.send_message(message.chat.id, "🎯 لطفا سن خود را وارد کنید:")
        elif step == 2:
            if not message.text.isdigit():
                return bot.send_message(message.chat.id, "⚠️ لطفا فقط عدد وارد کنید.")
            user['age'] = int(message.text)
            user['profile_step'] = 3
            update_user(user)
            bot.send_message(message.chat.id, "🎯 لطفا شهر و استان خود را وارد کنید:")
        elif step == 3:
            user['city'] = message.text
            user['profile_step'] = 0
            update_user(user)
            bot.send_message(message.chat.id, "✅ پروفایل شما تکمیل شد!")
            send_main_menu(message)
        return

    # ---------- دستورات کاربر ----------
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
        support_table.insert({'from': user['id'], 'text': message.text})

    elif text == "📨 دعوت دوستان":
        bot.send_message(message.chat.id, f"لینک دعوت شما: https://t.me/YourBotUsername?start={user['id']}\n🎁 با دعوت دوستان ۲۰ سکه دریافت می‌کنید!")

    elif text == "📊 آمار من":
        bot.send_message(message.chat.id, f"تعداد بازی‌ها: {user['games_played']}\nبردها: {user['wins']}\nسکه‌ها: {user['coins']}")

    elif text == "🔧 تنظیمات":
        bot.send_message(message.chat.id, "تنظیمات بات…")

    # ---------- منوی ادمین ----------
    elif is_admin(user['id']):
        if text == "👥 مدیریت کاربران":
            all_users = users_table.all()
            info = "\n".join([f"{u['id']}: {u['nickname']} ({u['coins']} سکه)" for u in all_users])
            bot.send_message(message.chat.id, f"لیست کاربران:\n{info}")
        elif text == "💰 مدیریت سکه":
            bot.send_message(message.chat.id, "برای دادن سکه به کاربر یا همه، از دستور /addcoins یا /addcoinsall استفاده کنید.")
        elif text == "🚫 بن کردن کاربر":
            bot.send_message(message.chat.id, "برای بن کردن کاربر از دستور /ban <user_id> استفاده کنید.")
        elif text == "✉️ ارسال پیام به کاربران":
            bot.send_message(message.chat.id, "برای ارسال پیام از دستور /send <user_id/all> <متن> استفاده کنید.")

    else:
        bot.send_message(message.chat.id, "⚠️ گزینه نامعتبر! لطفا از منوی شیشه‌ای انتخاب کنید.")

# ---------- ادمین: دادن سکه ----------
@bot.message_handler(commands=['addcoins'])
def addcoins(message):
    if not is_admin(message.from_user.id):
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
    if not is_admin(message.from_user.id):
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

# ---------- ادمین: بن کردن کاربر ----------
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return
    try:
        user_id = int(message.text.split()[1])
        user = get_user(user_id)
        if not user:
            bot.reply_to(message, "کاربر پیدا نشد!")
            return
        user['banned'] = True
        update_user(user)
        bot.reply_to(message, f"✅ کاربر {user['nickname']} بن شد.")
    except:
        bot.reply_to(message, "فرمت: /ban <user_id>")

# ---------- ادمین: ارسال پیام ----------
@bot.message_handler(commands=['send'])
def send_message_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return
    try:
        parts = message.text.split()
        target = parts[1]
        text = " ".join(parts[2:])
        if target == "all":
            for u in users_table.all():
                bot.send_message(u['id'], f"📢 پیام ادمین:\n{text}")
            bot.reply_to(message, "✅ پیام به همه کاربران ارسال شد.")
        else:
            user_id = int(target)
            u = get_user(user_id)
            if not u:
                bot.reply_to(message, "کاربر پیدا نشد!")
                return
            bot.send_message(user_id, f"📢 پیام ادمین:\n{text}")
            bot.reply_to(message, f"✅ پیام به {u['nickname']} ارسال شد.")
    except:
        bot.reply_to(message, "فرمت: /send <user_id/all> <متن>")

# ---------- اجرای بات ----------
bot.polling()