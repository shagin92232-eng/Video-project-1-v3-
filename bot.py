import os
import logging
import threading
import requests
import google.generativeai as genai
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ================= CONFIGURATION (Railway Variables থেকে আসবে) =================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY")
# ================================================================================

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup check - Variable ঠিকমতো লোড হয়েছে কিনা যাচাই
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN পাওয়া যায়নি! Railway Variables চেক করুন।")
if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY পাওয়া যায়নি।")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY পাওয়া যায়নি।")

# Gemini Setup (Fallback)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ============ Dummy Web Server (Railway health check pass করার জন্য) ============
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)
# =================================================================================

# AI Agent: OpenRouter with Gemini Fallback
async def get_ai_response(user_prompt: str) -> str:
    # 1. Try OpenRouter First
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are an AI assistant for 'long to shorts clip' project."},
                    {"role": "user", "content": user_prompt}
                ]
            },
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            logger.warning(f"OpenRouter failed: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"OpenRouter Error: {e}")

    # 2. Fallback to Google Gemini
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        gemini_response = model.generate_content(user_prompt)
        return gemini_response.text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return f"দুঃখিত, AI সার্ভিস এই মুহূর্তে কাজ করছে না।"

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 'long to shorts clip' বটে স্বাগতম! আমাকে কিছু লিখুন।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("🤖 AI প্রসেস করছে...")
    reply = await get_ai_response(user_text)
    await update.message.reply_text(reply)

# Main Application
if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN নেই! Railway Variables-এ গিয়ে যোগ করুন।")

    # Dummy web server আলাদা thread-এ চালু করা (Railway crash আটকাতে)
    threading.Thread(target=run_web_server, daemon=True).start()

    # Telegram bot চালু
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Bot is running...")
    app.run_polling()                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are an AI assistant for the 'long to shorts clip' project."},
                    {"role": "user", "content": user_prompt}
                ]
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            logging.warning(f"OpenRouter failed: {response.status_code}. Gemini-তে যাচ্ছি...")
    except Exception as e:
        logging.error(f"OpenRouter Error: {e}. Gemini-তে যাচ্ছি...")

    # 2. Fallback: Google Gemini
    try:
        logging.info("Using Fallback: Google Gemini...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        gemini_response = model.generate_content(user_prompt)
        return gemini_response.text
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return "দুঃখিত, দুই AI সার্ভারেই সমস্যা হচ্ছে। কিছুক্ষণ পর আবার চেষ্টা করুন।"

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 স্বাগতম long to shorts clip বটে!\n\nআমাকে টেক্সট পাঠান, AI প্রসেস করে উত্তর দেবে।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    wait_msg = await update.message.reply_text("🤖 AI প্রসেস করছে, অপেক্ষা করুন...")

    reply = await get_ai_response(user_prompt=user_text)
    await update.message.reply_text(reply)

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is running...")
    app.run_polling()
