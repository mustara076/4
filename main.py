import os
import io
import logging
import sys
from threading import Thread
from flask import Flask
from dotenv import load_dotenv 

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

from database import init_db, update_chat_info, get_stats, get_all_chat_ids
from tools import get_current_time

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0)) 

app_server = Flask('')
@app_server.route('/')
def home(): return "I Know Bot is Live & Ready!"
def run_web(): app_server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

SYSTEM_INSTRUCTION = (
    "Aap ek digital vyakti hain jiska naam 'I Know' hai, West Bengal se. "
    "Aap real person hain, AI nahi. Tone witty aur confident rakhein. "
    "Doston ke naam: Princy, AZENDER, arya, piyush, tapash, Naruto. "
    "Short replies dein aur Hinglish use karein."
)

CHAT_SESSIONS = {} 
model = None

init_db()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # --- MODEL NAME FIX ---
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        tools=[get_current_time],
        system_instruction=SYSTEM_INSTRUCTION
    )
    print("✅ Gemini AI Connected!")
except Exception as e:
    logger.error(f"Gemini Error: {e}")

def get_gemini_session(chat_id, chat_type):
    if chat_id not in CHAT_SESSIONS and model:
        CHAT_SESSIONS[chat_id] = model.start_chat(history=[])
        update_chat_info(chat_id, chat_type, is_new=True)
    else:
        update_chat_info(chat_id, chat_type, is_new=False)
    return CHAT_SESSIONS.get(chat_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_gemini_session(update.effective_chat.id, update.effective_chat.type)
    msg = "Hello! Main **I Know** hoon, West Bengal se. Photo bhej ya kuch bhi pooch le! 😎"
    await update.message.reply_markdown(msg)

async def handle_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not model: return
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action='TYPING')
    
    session = get_gemini_session(chat_id, update.effective_chat.type)
    
    prompt = update.message.text or update.message.caption or "Describe this."
    contents = []

    if update.message.photo:
        photo = await update.message.photo[-1].get_file()
        img_bytes = io.BytesIO()
        await photo.download_to_memory(img_bytes)
        img_bytes.seek(0)
        contents.append({'mime_type': 'image/jpeg', 'data': img_bytes.read()})
    
    contents.append(prompt)

    try:
        response = session.send_message(contents)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        await update.message.reply_text("Kuch gadbad hui, firse try kar.")

if __name__ == '__main__':
    Thread(target=run_web).start()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_ai))
    
    print("🚀 Bot Polling Started...")
    application.run_polling(drop_pending_updates=True)
