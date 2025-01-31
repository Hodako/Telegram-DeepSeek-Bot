import os
import replicate
import requests
from flask import Flask, request, jsonify
from urllib.parse import unquote

app = Flask(__name__)

# Initialize Replicate client
REPLICATE_CLIENT = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

# Store user preferences (volatile, consider database for production)
USER_MODELS = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    send_chat_action(data, 'typing')  # Show typing indicator
    
    if 'message' in data:
        return handle_message(data)
    elif 'callback_query' in data:
        return handle_callback(data)
    return jsonify(success=False)

def handle_message(data):
    message = data['message']
    chat_id = message['chat']['id']
    text = message.get('text', '')
    
    # Handle commands
    if text.startswith('/'):
        if text.startswith('/imagine'):
            prompt = text[8:].strip()
            return handle_image_generation(chat_id, prompt)
        elif text.startswith('/settings'):
            return show_settings(chat_id)
        elif text.startswith('/start'):
            return send_welcome(chat_id)
        elif text.startswith('/help'):
            return show_help(chat_id)
    
    # Handle file uploads
    if 'document' in message:
        return handle_file_upload(chat_id, message['document'])
    
    # Text processing
    user_input = text
    if user_input.lower() in ['exit', 'quit']:
        response_text = "👋 Goodbye!"
    else:
        response_text = get_ai_response(chat_id, user_input)
    
    send_message(chat_id, response_text)
    return jsonify(success=True)

def handle_callback(data):
    query = data['callback_query']
    chat_id = query['message']['chat']['id']
    model_name = unquote(query['data'])
    
    USER_MODELS[chat_id] = model_name
    send_message(chat_id, f"⚙️ Model switched to: <b>{model_name}</b>")
    return jsonify(success=True)

def get_ai_response(chat_id, prompt):
    model = USER_MODELS.get(chat_id, "deepseek-r1")
    try:
        if model == "deepseek-r1":
            return get_deepseek_response(prompt)
        elif model == "llama2":
            return get_llama_response(prompt)
        # Add more models as needed
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def get_deepseek_response(prompt):
    full_response = []
    for event in REPLICATE_CLIENT.stream(
        "deepseek-ai/deepseek-r1",
        input={"prompt": f"{prompt}\n\nAssistant: "}
    ):
        full_response.append(str(event))
    return format_response(''.join(full_response))

def get_llama_response(prompt):
    output = REPLICATE_CLIENT.run(
        "meta/llama-2-70b-chat",
        input={"prompt": f"{prompt}\n\nAssistant: "}
    )
    return format_response(''.join(output))

def handle_image_generation(chat_id, prompt):
    try:
        output = REPLICATE_CLIENT.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={"prompt": prompt}
        )
        send_photo(chat_id, output[0])
        return jsonify(success=True)
    except Exception as e:
        send_message(chat_id, f"🚫 Image generation failed: {str(e)}")
        return jsonify(success=False)

def handle_file_upload(chat_id, document):
    file_info = requests.get(
        f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/getFile",
        params={"file_id": document['file_id']}
    ).json()
    
    if file_info['result']['mime_type'].startswith('text/'):
        file_url = f"https://api.telegram.org/file/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/{file_info['result']['file_path']}"
        content = requests.get(file_url).text
        response = get_ai_response(chat_id, f"Analyze this document:\n{content}")
        send_message(chat_id, f"📄 Document analysis:\n{response}")
    else:
        send_message(chat_id, "❌ Unsupported file type. Please upload text files only.")
    
    return jsonify(success=True)

def format_response(text):
    return f"<b>🤖 AI Response:</b>\n\n{text}\n\n<code>End of response</code>"

def send_message(chat_id, text, reply_markup=None):
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = {'inline_keyboard': reply_markup}
    
    requests.post(
        f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
        json=payload
    )

def send_photo(chat_id, photo_url):
    requests.post(
        f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendPhoto",
        json={
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': "🖼 Here's your generated image!"
        }
    )

def send_chat_action(data, action):
    chat_id = data['message']['chat']['id'] if 'message' in data else data['callback_query']['message']['chat']['id']
    requests.post(
        f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendChatAction",
        json={'chat_id': chat_id, 'action': action}
    )

def send_welcome(chat_id):
    welcome_text = """
    🌟 <b>Welcome to AI Assistant Bot!</b> 🌟

    Available commands:
    /start - Show this welcome message
    /help - List available commands
    /imagine [prompt] - Generate images from text
    /settings - Change AI model preferences

    🧠 Current features:
    - Text generation with multiple AI models
    - Image generation from text prompts
    - Document analysis
    - Interactive settings
    """
    send_message(chat_id, welcome_text)
    return jsonify(success=True)

def show_help(chat_id):
    help_text = """
    📚 <b>Available Commands:</b>

    <b>Basic Commands:</b>
    /start - Show welcome message
    /help - Display this help
    /settings - Configure bot preferences

    <b>AI Features:</b>
    /imagine [prompt] - Generate images from text
    Send any text message for AI conversation
    Upload text files for document analysis

    <b>Technical:</b>
    'exit' or 'quit' - End conversation
    """
    send_message(chat_id, help_text)
    return jsonify(success=True)

def show_settings(chat_id):
    buttons = [
        [{"text": "DeepSeek-R1", "callback_data": "deepseek-r1"}],
        [{"text": "Llama2-70B", "callback_data": "llama2"}]
    ]
    send_message(chat_id, "⚙️ <b>Choose AI Model:</b>", buttons)
    return jsonify(success=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
