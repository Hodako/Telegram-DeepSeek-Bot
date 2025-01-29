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

client = InferenceClient(
    provider="together",
    api_key="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"
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
    """Format bold text using HTML tags and clean unwanted markup"""
    # Convert **text** to <b>text</b>
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Remove other unsupported tags
    clean_text = re.sub(r'<\/?(think|rationale|step|context)[^>]*>', '', clean_text)
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
            
• Version: 2.0
• Model: <b>DeepSeek-R1</b>
• Provider: <b>Hugging Face</b>"""
            await update.message.reply_html(about_msg)
        elif user_input == "❓ Help":
            help_msg = """<b>🆘 Help</b>
            
Just type your question naturally like:
• <i>"Explain quantum computing"</i>
• <i>"Who is Bangabandhu?"</i>
• <i>"How to make biryani?"</i>"""
            await update.message.reply_html(help_msg)
        elif user_input == "🛠 Settings":
            settings_msg = """<b>⚙️ Settings</b>
            
• Max tokens: <b>500</b>
• Response style: <b>Detailed</b>
• Language: <b>English</b>"""
            await update.message.reply_html(settings_msg)
        return
    
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action="typing"
        )
        
        status_msg = await update.message.reply_html("<i>🧠 Processing...</i>")
        
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model="deepseek-ai/DeepSeek-R1",
                        messages=[{"role": "user", "content": user_input}],
                        max_tokens=500,
                        stream=False
                    )
                )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    await status_msg.edit_text(
                        f"<i>⏳ Retrying in {wait_time}s...</i>", 
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

        raw_response = response.choices[0].message.content
        clean_response = sanitize_html(raw_response)
        
        formatted_response = f"""
        <b>🤖 Answer:</b>
        
        {clean_response}
        """
        chunks = [formatted_response[i:i+4096] for i in range(0, len(formatted_response), 4096)]
        
        await status_msg.edit_text(chunks[0], parse_mode='HTML')
        
        for chunk in chunks[1:]:
            await update.message.reply_html(chunk)
            
    except Exception as e:
        error_msg = f"<b>❌ Error:</b>\n<code>{str(e)}</code>"
        await status_msg.edit_text(error_msg[:4096], parse_mode='HTML')

def main():
    app = Application.builder().token("7692733567:AAGuZfNs2tB29oG8cRFEat9zpbb9g_QItdg").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is starting...")
    app.run_polling()
    print("✅ Bot is running!")

if __name__ == "__main__":
    main()
