import os
import logging
import requests
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==============================================================
# কীগুলো সার্ভারের (Render/Koyeb) Environment Variables থেকে আসবে
# এই ফাইলে কোনো কী লিখতে হবে না — এরপরেই ঠাঁই করে নেই
# ==============================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini Setup (Fallback)
genai.configure(api_key=GEMINI_API_KEY)

# AI Agent: OpenRouter আগে, ফেইল করলে Gemini
async def get_ai_response(user_prompt: str) -> str:
    # 1. প্রথমে OpenRouter (Free Model)
    try:
        logging.info("Trying OpenRouter...")
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct:free",
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
