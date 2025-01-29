import asyncio
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from huggingface_hub import InferenceClient

# Initialize client with correct parameters
client = InferenceClient(
    model="deepseek-ai/DeepSeek-R1",
    token="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"  # Changed from api_key to token
)

MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        ["📝 Ask Question", "ℹ️ About"],
        ["🛠 Settings", "❓ Help"]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

def sanitize_html(text: str) -> str:
    """Remove unsupported HTML tags"""
    clean_text = re.sub(r'<\/?(think|rationale|step|context)[^>]*>', '', text)
    return clean_text.replace('\n\n', '\n').strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = """<b>🤖 DeepSeek AI Bot</b>
    
Welcome! I'm an AI-powered assistant using DeepSeek technology.
    
<i>Choose an option below or ask me anything!</i>"""
    await update.message.reply_html(welcome_msg, reply_markup=MENU_KEYBOARD)

# Keep rest of the handle_message function same as previous version
# ...

def main():
    app = Application.builder().token("7692733567:AAGuZfNs2tB29oG8cRFEat9zpbb9g_QItdg").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
