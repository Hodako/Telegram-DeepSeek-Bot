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
        user_input = data['message']['text'].lower()
        
        if user_input in ['/start', 'menu']:
            response_text = show_menu()
        elif user_input == 'exit':
            response_text = "Goodbye!"
        elif user_input == '/help':
            response_text = show_help()
        elif user_input == '/about':
            response_text = about_bot()
        elif user_input == '/developer':
            response_text = developer_info()
        else:
            response_text = get_deepseek_response(user_input)
        
        send_message(chat_id, response_text)
        return jsonify(success=True)
    return jsonify(success=False)

def show_menu():
    return """
Choose an option:
/start or /menu - Show this menu
/exit - Exit the chat
/help - Get help
/about - About the bot
/developer - Developer information
Anything else - Get a response from the AI
"""

def show_help():
    return """
This bot uses AI to respond to your queries. You can use the following commands:
/start or /menu - Show the menu options
/exit - Exit the chat
/help - Get help about using the bot
/about - Information about the bot
/developer - Information about the developer
"""

def about_bot():
    return """
DeepSeek Bot:
- This bot uses advanced AI to respond to user queries.
- It leverages the DeepSeek AI model for generating responses.
- Version: 1.0.0
"""

def developer_info():
    return """
Developer Information:
- Name: Hodako
- Contact: example@example.com
- GitHub: https://github.com/Hodako
"""

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
    return response.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
