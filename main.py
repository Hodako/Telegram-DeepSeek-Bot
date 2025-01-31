import os
import replicate
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize Replicate client with API token
REPLICATE_CLIENT = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        user_input = data['message']['text']
        
        if user_input.startswith('/'):
            command = user_input.lower()
            if command in ['/start', '/help']:
                menu_text = """🤖 Welcome to DeepSeek Chat Bot!
                
Available commands:
/start - Start the bot
/help - Show this help menu
/exit - Exit the conversation

You can send unlimited messages! I'll respond to anything you ask."""
                send_message(chat_id, menu_text)
            elif command in ['/exit', '/quit']:
                send_message(chat_id, "Goodbye! Feel free to start again anytime. 👋")
            else:
                send_message(chat_id, "⚠️ Unknown command. Type /help for available options.")
        else:
            # Send processing message and get its ID
            processing_msg_id = send_message(chat_id, "⏳ Processing your request...")
            try:
                response_text = get_deepseek_response(user_input)
                edit_message(chat_id, processing_msg_id, response_text)
            except Exception as e:
                edit_message(chat_id, processing_msg_id, f"⚠️ Error processing request: {str(e)}")
        
        return jsonify(success=True)
    return jsonify(success=False)

def get_deepseek_response(prompt):
    full_response = []
    try:
        for event in REPLICATE_CLIENT.stream("deepseek-ai/deepseek-r1", input={"prompt": prompt}):
            full_response.append(str(event))
        return ''.join(full_response)
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def send_message(chat_id, text):
    TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(TELEGRAM_API_URL, json=payload)
    response_json = response.json()
    return response_json.get('result', {}).get('message_id') if response_json.get('ok') else None

def edit_message(chat_id, message_id, text):
    TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text
    }
    requests.post(TELEGRAM_API_URL, json=payload)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
