from flask import Flask, render_template_string, request, jsonify
import requests


app = Flask(__name__)
DIRECT_LINE_SECRET  = 'DiMtbOKGJsDu9LMXJJ0xNl7ZFADepHnOY6pvuMaGvrb4qb8KvjjpJQQJ99BFACi5YpzAArohAAABAZBS3EaP.11KA8GxYHjchRBFnph8d5YNSaKXNjeuNFFHtox34FdRdJ9L8FC7aJQQJ99BFACi5YpzAArohAAABAZBSAr3v'
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chatbot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fb; margin: 0; }
        .container { max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 24px; }
        .chat-area { height: 400px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; background: #fafbfc; margin-bottom: 16px; }
        .message { margin-bottom: 12px; }
        .user { color: #1976d2; font-weight: bold; }
        .bot { color: #388e3c; font-weight: bold; }
        .input-row { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 4px; border: 1px solid #ccc; }
        button { background: #1976d2; color: #fff; border: none; border-radius: 4px; padding: 10px 18px; cursor: pointer; }
        button:hover { background: #1565c0; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Chatbot</h2>
        <div class="chat-area" id="chat-area"></div>
        <form class="input-row" id="chat-form" autocomplete="off">
            <input type="text" id="user-input" placeholder="Type your message..." required autofocus>
            <button type="submit">Send</button>
        </form>
    </div>
    <script>
        const chatArea = document.getElementById('chat-area');
        const chatForm = document.getElementById('chat-form');
        const userInput = document.getElementById('user-input');

        function appendMessage(sender, message) {
            const div = document.createElement('div');
            div.className = 'message';
            div.innerHTML = `<span class="${sender === 'You' ? 'user' : 'bot'}">${sender}:</span> ${message}`;
            chatArea.appendChild(div);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        chatForm.onsubmit = async (e) => {
            e.preventDefault();
            const message = userInput.value.trim();
            if (!message) return;
            appendMessage('You', message);
            userInput.value = '';
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message})
            });
            const data = await res.json();
            appendMessage('Bot', data.response);
        };
    </script>
</body>
</html>
"""
def get_bot_response(message):
    res = requests.get(
        'https://directline.botframework.com/v3/directline/tokens/generate',
        headers={'Authorization': f'BotConnector {DIRECT_LINE_SECRET}'},)
    print(res)
    return res.status_code
    
@app.route('/')
def index(): 
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    bot_response = get_bot_response(user_message)
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
