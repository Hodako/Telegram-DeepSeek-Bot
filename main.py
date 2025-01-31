import os
import replicate
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Initialize Replicate client with API token
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN environment variable not set")
REPLICATE_CLIENT = replicate.Client(api_token=REPLICATE_API_TOKEN)

# HTML template with inline CSS and JavaScript for the chat interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Interface</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }

        .chat-container {
            width: 400px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }

        .chat-header {
            padding: 10px;
            background-color: #007bff;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 8px 8px 0 0;
        }

        .chat-window {
            padding: 10px;
            flex: 1;
            overflow-y: auto;
            border-bottom: 1px solid #ddd;
        }

        .chat-input {
            display: flex;
            padding: 10px;
            border-radius: 0 0 8px 8px;
        }

        .chat-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .chat-input button {
            padding: 10px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            margin-left: 10px;
        }

        .menu-bar {
            padding: 10px;
            background-color: #007bff;
            color: white;
            display: flex;
            justify-content: space-around;
            border-radius: 8px 8px 0 0;
        }

        .menu-bar button {
            background-color: white;
            color: #007bff;
            border: none;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
        }

        .about-info {
            display: none;
            margin-top: 10px;
            text-align: center;
            font-size: 14px;
        }

        .typing {
            animation: typing 1s steps(40, end) infinite;
        }

        @keyframes typing {
            0% {
                width: 0;
            }
            100% {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="menu-bar">
            <button onclick="showAbout()">About</button>
            <button onclick="toggleModelMenu()">Models</button>
        </div>
        <div class="chat-header">
            <h2>Chatbot</h2>
        </div>
        <div class="chat-window" id="chat-window"></div>
        <div class="chat-input">
            <input type="text" id="user-input" placeholder="Type a message...">
            <button id="send-btn">Send</button>
        </div>
    </div>
    <div class="model-switcher" id="model-switcher" style="display: none;">
        <label for="model-select">Choose a model:</label>
        <select id="model-select">
            <option value="deepseek-ai/deepseek-r1">DeepSeek-R1</option>
            <option value="another-model">Another Model</option>
        </select>
    </div>
    <div class="about-info" id="about-info">
        <p>Bot made by <a href="https://twitter.com/azizul17T">@azizul17T</a></p>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const sendBtn = document.getElementById("send-btn");
            const userInput = document.getElementById("user-input");
            const chatWindow = document.getElementById("chat-window");
            const aboutInfo = document.getElementById("about-info");
            const modelSelect = document.getElementById("model-select");

            sendBtn.addEventListener("click", function() {
                const message = userInput.value.trim();
                const model = modelSelect.value;
                if (message) {
                    addUserMessage(message);
                    userInput.value = "";
                    generateResponse(message, model);
                }
            });

            function addUserMessage(message) {
                const messageElem = document.createElement("div");
                messageElem.className = "user-message";
                messageElem.textContent = message;
                chatWindow.appendChild(messageElem);
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }

            function addBotMessage(message) {
                const messageElem = document.createElement("div");
                messageElem.className = "bot-message typing";
                messageElem.textContent = message;
                chatWindow.appendChild(messageElem);
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }

            function generateResponse(userMessage, model) {
                addBotMessage("Generating...");
                fetch('/webhook', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: { chat: { id: 1 }, text: userMessage }, model: model })
                })
                .then(response => response.json())
                .then(data => {
                    const botMessageElem = document.querySelector(".bot-message.typing");
                    botMessageElem.classList.remove("typing");
                    if (data.success) {
                        displayTypingAnimation(botMessageElem, data.response);
                    } else {
                        botMessageElem.textContent = "Error generating response";
                    }
                })
                .catch(error => {
                    const botMessageElem = document.querySelector(".bot-message.typing");
                    botMessageElem.classList.remove("typing");
                    botMessageElem.textContent = "Error: " + error.message;
                });
            }

            function displayTypingAnimation(element, text) {
                let index = 0;
                element.textContent = "";
                const interval = setInterval(() => {
                    if (index < text.length) {
                        element.textContent += text[index];
                        index++;
                    } else {
                        clearInterval(interval);
                    }
                }, 50);
            }
        });

        function showAbout() {
            const aboutInfo = document.getElementById("about-info");
            aboutInfo.style.display = aboutInfo.style.display === "none" ? "block" : "none";
        }

        function toggleModelMenu() {
            const modelSwitcher = document.getElementById("model-switcher");
            modelSwitcher.style.display = modelSwitcher.style.display === "none" ? "block" : "none";
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'message' not in data:
        return jsonify(success=False, error="Invalid request data"), 400

    chat_id = data['message']['chat']['id']
    user_input = data['message']['text']
    model = data.get('model', 'deepseek-ai/deepseek-r1')

    if user_input.lower() == '/start':
        response_text = "Hey, This is DeepSeek AI. How can I help you?"
    elif user_input.lower() in ['exit', 'quit']:
        response_text = "Goodbye!"
    else:
        response_text = get_deepseek_response(user_input, model)

    send_message(chat_id, response_text)
    return jsonify(success=True, response=response_text)

def get_deepseek_response(prompt, model):
    full_response = []
    try:
        for event in REPLICATE_CLIENT.stream(model, input={"prompt": prompt}):
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
