import os
import json
import asyncio
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from flask import Flask

# 🔐 TOKEN (Render ENV dan olinadi)
TOKEN = os.getenv("BOT_TOKEN")

# 💾 MA'LUMOTLARNI FAYLDA SAQLASH
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# 👤 USER DATA
data = load_data()

def get_user_data(user_id):
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "video": [],
            "image": [],
            "link": []
        }
    return data[user_id]

# 🏠 START MENU
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📺 VIDEOLAR", callback_data="video")],
        [InlineKeyboardButton("🖼 RASMLAR", callback_data="image")],
        [InlineKeyboardButton("🔗 LINKLAR", callback_data="link")]
    ]
    await update.message.reply_text(
        "📂 Kategoriya tanla:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📩 SAQLASH
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.message.from_user.id
    user_data = get_user_data(user_id)
    msg = update.message

    if msg.video:
        user_data["video"].append(msg.video.file_id)
        save_data()
    elif msg.photo:
        user_data["image"].append(msg.photo[-1].file_id)
        save_data()
    elif msg.text and msg.text.startswith("http"):
        user_data["link"].append(msg.text)
        save_data()

# 🔘 KO'RISH
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    cat = query.data
    items = user_data.get(cat, [])

    if not items:
        await query.edit_message_text("❌ Hech narsa yo'q")
        return

    if cat == "video":
        for v in items:
            await query.message.reply_video(v)
    elif cat == "image":
        for i in items:
            await query.message.reply_photo(i)
    elif cat == "link":
        await query.message.reply_text("\n".join(items))

# =========================
# 🌐 FLASK (Render Web Service uchun)
# =========================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot ishlayapti ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# =========================
# 🤖 ASOSIY (har qanday Python versiyada ishlaydi)
# =========================
def main():
    # Yangi event loop yaratish (Python 3.14 himoyasi)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except Exception:
        pass

    # Flask serverni alohida thread'da ishga tushirish
    Thread(target=run_web, daemon=True).start()

    # Telegram bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
