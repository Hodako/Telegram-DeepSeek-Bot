import os
import replicate
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize Replicate client with API token
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN environment variable not set")
REPLICATE_CLIENT = replicate.Client(api_token=REPLICATE_API_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'message' not in data:
        return jsonify(success=False, error="Invalid request data"), 400
    
    chat_id = data['message']['chat']['id']
    user_input = data['message']['text']
    
    if user_input.lower() in ['exit', 'quit']:
        response_text = "Goodbye!"
    else:
        response_text = get_deepseek_response(user_input)
    
    send_message(chat_id, response_text)
    return jsonify(success=True)

def get_deepseek_response(prompt):
    full_response = []
    try:
        for event in REPLICATE_CLIENT.stream("deepseek-ai/deepseek-r1", input={"prompt": prompt}):
            chunk = str(event)
            full_response.append(chunk)
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
    if not response.ok:
        raise ValueError(f"Failed to send message: {response.text}")
    return response.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
