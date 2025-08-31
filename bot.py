import telebot
from telebot import types
from tinydb import TinyDB, Query
import random
import time
import threading

# ------------------- تنظیمات -------------------
TOKEN = "8468902593:AAGqaP2sLbUaV-m2UpAoHzpuGAAi5M9FgIQ"
ADMIN_ID = 8461153976
bot = telebot.TeleBot(TOKEN)
db = TinyDB("database.json")
users_table = db.table("users")
support_table = db.table("support")
games_table = db.table("games")

# ------------------- لیست استان‌ها و شهرها (پیش‌فرض) -------------------
provinces = {
    "تهران": ["تهران", "ری", "شهریار"],
    "اصفهان": ["اصفهان", "کاشان", "نجف‌آباد"],
    "فارس": ["شیراز", "کازرون", "مرودشت"]
}

# ------------------- متدهای کمکی -------------------
def get_user(user_id):
    return users_table.get(Query().id == user_id)

def update_user(user):
    users_table.update(user, Query().id == user['id'])

def is_admin(user_id):
    return user_id == ADMIN_ID

def send_main_menu(user_id):
    user = get_user(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎲 بازی منچ", "👤 پروفایل")
    markup.row("💬 پشتیبانی", "📨 دعوت دوستان")
    markup.row("📊 آمار من", "⚙️ تنظیمات")
    if is_admin(user_id):
        markup.row("👥 مدیریت کاربران", "💰 مدیریت سکه")
        markup.row("🚫 بن کردن کاربر", "✉️ ارسال پیام به کاربران")
    bot.send_message(user_id, "📌 منو را انتخاب کنید:", reply_markup=markup)

# ------------------- تکمیل پروفایل -------------------
@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    if not user:
        users_table.insert({
            'id': message.from_user.id,
            'username': message.from_user.username or "",
            'nickname': "",
            'age': 0,
            'province': "",
            'city': "",
            'medals': [],
            'coins': 20,
            'games_played': 0,
            'wins': 0,
            'banned': False,
            'profile_step': 1
        })
        bot.send_message(message.chat.id, "🎉 خوش آمدید! ابتدا پروفایل خود را تکمیل کنید.")
        bot.send_message(message.chat.id, "🎯 لطفا نام مستعار خود را وارد کنید:")
        return
    if user['nickname'] == "":
        user['profile_step'] = 1
        update_user(user)
        bot.send_message(message.chat.id, "🎯 لطفا نام مستعار خود را وارد کنید:")
        return
    send_main_menu(message.from_user.id)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user = get_user(message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "لطفا ابتدا /start را بزنید.")
        return
    if user['banned']:
        bot.send_message(message.chat.id, "❌ شما بن شده‌اید و نمی‌توانید بازی کنید.")
        return

    # تکمیل پروفایل مرحله‌ای
    if user.get('profile_step', 0) > 0:
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
            # انتخاب استان
            markup = types.InlineKeyboardMarkup()
            for p in provinces.keys():
                markup.add(types.InlineKeyboardButton(p, callback_data=f"province:{p}"))
            bot.send_message(message.chat.id, "🏙 استان خود را انتخاب کنید:", reply_markup=markup)
        update_user(user)
        return

    # منوی اصلی کاربران
    text = message.text
    if text == "🎲 بازی منچ":
        if user['coins'] < 5:
            bot.send_message(message.chat.id, "⚠️ شما ۵ سکه نیاز دارید.")
            return
        # اضافه شدن به لیست بازی
        join_game(user['id'])
    elif text == "👤 پروفایل":
        bot.send_message(message.chat.id,
                         f"👤 پروفایل شما:\nنام مستعار: {user['nickname']}\nسن: {user['age']}\nاستان: {user['province']}\nشهر: {user['city']}\nسکه‌ها: {user['coins']}\nمدال‌ها: {', '.join(user['medals']) if user['medals'] else 'ندارد'}\nتعداد بازی‌ها: {user['games_played']}\nبردها: {user['wins']}")
    elif text == "💬 پشتیبانی":
        bot.send_message(message.chat.id, "پیام خود را برای پشتیبانی ارسال کنید.")
        support_table.insert({'from': user['id'], 'text': message.text})
    elif text == "📨 دعوت دوستان":
        bot.send_message(message.chat.id, f"لینک دعوت شما: https://t.me/YourBotUsername?start={user['id']}\n🎁 با دعوت دوستان ۲۰ سکه دریافت می‌کنید!")
    elif text == "📊 آمار من":
        bot.send_message(message.chat.id, f"تعداد بازی‌ها: {user['games_played']}\nبردها: {user['wins']}\nسکه‌ها: {user['coins']}")
    elif text == "⚙️ تنظیمات":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("👤 پروفایل", "💰 سکه‌های من")
        markup.row("🔙 برگشت")
        bot.send_message(message.chat.id, "تنظیمات شما:", reply_markup=markup)
    elif is_admin(user['id']):
        handle_admin_menu(user, text)
    else:
        bot.send_message(message.chat.id, "⚠️ گزینه نامعتبر! لطفا از منوی شیشه‌ای انتخاب کنید.")

# ------------------- انتخاب استان و شهر -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user = get_user(call.from_user.id)
    if call.data.startswith("province:"):
        prov = call.data.split(":")[1]
        user['province'] = prov
        user['profile_step'] = 4
        update_user(user)
        markup = types.InlineKeyboardMarkup()
        for c in provinces[prov]:
            markup.add(types.InlineKeyboardButton(c, callback_data=f"city:{c}"))
        bot.edit_message_text("🏙 حالا شهر خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("city:"):
        city = call.data.split(":")[1]
        user['city'] = city
        user['profile_step'] = 0
        update_user(user)
        bot.edit_message_text("✅ پروفایل شما تکمیل شد!", call.message.chat.id, call.message.message_id)
        send_main_menu(user['id'])

# ------------------- لیست بازی -------------------
game_queue = []

def join_game(user_id):
    user = get_user(user_id)
    user['coins'] -= 5
    update_user(user)
    bot.send_message(user_id, "🎲 شما به لیست بازی اضافه شدید. منتظر بازیکن دیگر...")
    game_queue.append(user_id)
    if len(game_queue) >= 2:
        players = [game_queue.pop(0), game_queue.pop(0)]
        start_game(players)

# ------------------- شروع بازی -------------------
def start_game(player_ids):
    for uid in player_ids:
        bot.send_message(uid, f"🎮 بازی شروع شد! شما با {len(player_ids)} نفر بازی می‌کنید.")
    # مثال ساده: هر بازیکن تاس می‌ریزد
    rolls = {}
    for uid in player_ids:
        rolls[uid] = random.randint(1,6)
    winner_id = max(rolls, key=rolls.get)
    winner = get_user(winner_id)
    winner['coins'] += 10
    winner['wins'] += 1
    update_user(winner)
    for uid in player_ids:
        bot.send_message(uid, f"🎲 نتایج تاس‌ها:\n" + "\n".join([f"{get_user(pid)['nickname']}: {rolls[pid]}" for pid in player_ids]) + f"\n🏆 برنده: {winner['nickname']} (+10 سکه)")

# ------------------- منوی ادمین -------------------
def handle_admin_menu(user, text):
    if text == "👥 مدیریت کاربران":
        all_users = users_table.all()
        info = "\n".join([f"{u['id']}: {u['nickname']} ({u['coins']} سکه)" for u in all_users])
        bot.send_message(user['id'], f"لیست کاربران:\n{info}")
    elif text == "💰 مدیریت سکه":
        bot.send_message(user['id'], "از دستور /addcoins <user_id> <تعداد> یا /addcoinsall <تعداد> استفاده کنید.")
    elif text == "🚫 بن کردن کاربر":
        bot.send_message(user['id'], "از دستور /ban <user_id> استفاده کنید.")
    elif text == "✉️ ارسال پیام به کاربران":
        bot.send_message(user['id'], "از دستور /send <user_id/all> <متن> استفاده کنید.")

@bot.message_handler(commands=['addcoins'])
def addcoins(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ دسترسی ندارید.")
        return
    try:
        parts = message.text