import os
import re
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Dispatcher
)
from huggingface_hub import InferenceClient

app = Flask(__name__)

# Initialize clients with environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7692733567:AAGuZfNs2tB29oG8cRFEat9zpbb9g_QItdg')
HF_TOKEN = os.environ.get('HF_TOKEN', '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')

client = InferenceClient(token=HF_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)

# Webhook setup
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://your-render-app.onrender.com/webhook')

MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        ["📝 Ask Question", "ℹ️ About"],
        ["🛠 Settings", "❓ Help"]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

def sanitize_html(text: str) -> str:
    """Remove unsupported HTML tags from DeepSeek responses"""
    clean_text = re.sub(r'<\/?(think|rationale|step|context)[^>]*>', '', text)
    return clean_text.replace('\n\n', '\n').strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = """
    <b>🤖 DeepSeek AI Bot</b>
    
    Welcome! I'm an AI-powered assistant using DeepSeek technology.
    
    <i>Choose an option below or ask me anything!</i>
    """
    await update.message.reply_html(
        welcome_msg,
        reply_markup=MENU_KEYBOARD
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    
    if user_input in ["ℹ️ About", "❓ Help", "🛠 Settings"]:
        if user_input == "ℹ️ About":
            about_msg = """<b>🔍 About This Bot</b>
            Version: 2.0
            Model: <b>DeepSeek-R1</b>"""
            await update.message.reply_html(about_msg)
        elif user_input == "❓ Help":
            help_msg = """<b>🆘 Help</b>
            Just ask your question!"""
            await update.message.reply_html(help_msg)
        elif user_input == "🛠 Settings":
            settings_msg = """<b>⚙️ Settings</b>
            Max tokens: 500"""
            await update.message.reply_html(settings_msg)
        return
    
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action="typing"
        )
        
        status_msg = await update.message.reply_html("<i>🧠 Processing...</i>")
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1",
                messages=[{"role": "user", "content": user_input}],
                max_tokens=500,
                stream=False
            )
        )

        raw_response = response.choices[0].message.content
        clean_response = sanitize_html(raw_response)
        
        formatted_response = f"<b>🤖 Answer:</b>\n\n{clean_response}"
        chunks = [formatted_response[i:i+4096] for i in range(0, len(formatted_response), 4096)]
        
        await status_msg.edit_text(chunks[0], parse_mode='HTML')
        
        for chunk in chunks[1:]:
            await update.message.reply_html(chunk)
            
    except Exception as e:
        error_msg = f"<b>❌ Error:</b>\n<code>{str(e)}</code>"
        await status_msg.edit_text(error_msg[:4096], parse_mode='HTML')

# Initialize Flask app with Telegram webhook
@app.route('/webhook', methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(), bot)
        
        # Create dispatcher
        dispatcher = Dispatcher(bot, None, workers=0)
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await dispatcher.process_update(update)
        return jsonify(success=True)

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/set_webhook')
def set_webhook():
    # Set webhook on Render deployment
    webhook_url = f"{WEBHOOK_URL}/webhook"
    s = bot.set_webhook(webhook_url)
    if s:
        return f"Webhook setup OK: {webhook_url}"
    return "Webhook setup failed"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
