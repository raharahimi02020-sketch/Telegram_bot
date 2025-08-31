import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام 👋 ربات روشن شد ✅")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "گفتی: " + message.text)

bot.polling()
