from flask import Flask, render_template_string, request, jsonify
import os
import logging
import requests
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Azure Bot Configuration
BOT_DIRECT_LINE_SECRET = os.environ.get('BOT_DIRECT_LINE_SECRET', '')
BOT_SERVICE_URL = os.environ.get('BOT_SERVICE_URL', 'https://directline.botframework.com')
if not BOT_DIRECT_LINE_SECRET:
    logger.warning("BOT_DIRECT_LINE_SECRET is not set. Bot functionality will be limited.")
class BotConnector:
    def __init__(self):
        self.conversation_id = None
        self.token = None
        self.watermark = None
    
    def start_conversation(self):

        """Start a new conversation with the bot"""
        try:
            headers = {
                'Authorization': f'Bearer {BOT_DIRECT_LINE_SECRET}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{BOT_SERVICE_URL}/v3/directline/conversations',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.conversation_id = data['conversationId']
                self.token = data.get('token', BOT_DIRECT_LINE_SECRET)
                logger.info(f"Started conversation: {self.conversation_id}")
                return True
            else:
                logger.error(f"Failed to start conversation: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
            return False
    
    def send_message(self, message, user_id="user123"):
        """Send a message to the bot"""
        if not self.conversation_id:
            if not self.start_conversation():
                return {'error': 'Failed to start conversation with bot'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'type': 'message',
                'from': {'id': user_id},
                'text': message
            }
            
            response = requests.post(
                f'{BOT_SERVICE_URL}/v3/directline/conversations/{self.conversation_id}/activities',
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                # Wait for bot to process and respond
                import time
                time.sleep(2)
                return self.get_messages()
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return {'error': f'Bot returned error {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}'}
    
    def get_messages(self):
        """Get messages from the bot"""
        if not self.conversation_id:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}'
            }
            
            url = f'{BOT_SERVICE_URL}/v3/directline/conversations/{self.conversation_id}/activities'
            if self.watermark:
                url += f'?watermark={self.watermark}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.watermark = data.get('watermark')
                
                # Filter for bot messages
                bot_messages = []
                for activity in data.get('activities', []):
                    if activity.get('from', {}).get('id') != 'user123':
                        bot_messages.append({
                            'text': activity.get('text', ''),
                            'timestamp': activity.get('timestamp', ''),
                            'type': activity.get('type', 'message')
                        })
                
                return bot_messages
            else:
                logger.error(f"Failed to get messages: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return None

# Global bot connector instance
bot_connector = BotConnector()

# Minimal HTML template - CHAT ONLY
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Bot Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .chat-container {
            width: 90%;
            max-width: 600px;
            height: 80vh;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .bot-message {
            background: #e9ecef;
            color: #333;
            margin-right: auto;
        }
        
        .error-message {
            background: #dc3545;
            color: white;
            margin-right: auto;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input input:focus {
            border-color: #007bff;
        }
        
        .chat-input button {
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        
        .chat-input button:hover {
            background: #0056b3;
        }
        
        .chat-input button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .status {
            padding: 5px 15px;
            font-size: 12px;
            color: #6c757d;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px 15px;
            background: #e9ecef;
            border-radius: 15px;
            margin-bottom: 15px;
            max-width: 80%;
            color: #6c757d;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            🤖 Azure Bot Chat
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                Hello! I'm your Azure Bot. Send me a message to start chatting!
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            Bot is typing...
        </div>
        
        <form class="chat-input" id="chatForm">
            <input 
                type="text" 
                id="messageInput" 
                placeholder="Type your message here..." 
                required
                autocomplete="off"
            >
            <button type="submit" id="sendButton">Send</button>
        </form>
        
        <div class="status" id="statusBar">
            Ready to chat
        </div>
    </div>

    <script>
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const chatMessages = document.getElementById('chatMessages');
        const statusBar = document.getElementById('statusBar');
        const typingIndicator = document.getElementById('typingIndicator');

        // Add message to chat
        function addMessage(text, isUser = false, isError = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : (isError ? 'error-message' : 'bot-message')}`;
            messageDiv.textContent = text;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Show/hide typing indicator
        function showTyping(show = true) {
            typingIndicator.style.display = show ? 'block' : 'none';
            if (show) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        // Update status
        function updateStatus(text) {
            statusBar.textContent = text;
        }

        // Handle form submission
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent page reload
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage(message, true);
            
            // Clear input and disable button
            messageInput.value = '';
            sendButton.disabled = true;
            updateStatus('Sending message...');
            showTyping(true);
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                
                showTyping(false);
                
                if (result.status === 'success' && result.bot_responses) {
                    // Add bot responses
                    result.bot_responses.forEach(botMessage => {
                        if (botMessage.text) {
                            addMessage(botMessage.text, false, botMessage.type === 'error');
                        }
                    });
                    updateStatus('Ready to chat');
                } else {
                    // Show error
                    const errorText = result.message || 'Failed to get bot response';
                    addMessage(`Error: ${errorText}`, false, true);
                    updateStatus('Error occurred');
                }
                
            } catch (error) {
                showTyping(false);
                addMessage(`Connection Error: ${error.message}`, false, true);
                updateStatus('Connection failed');
                console.error('Chat error:', error);
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        });

        // Focus input on load
        messageInput.focus();
        
        // Handle Enter key
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Main chat page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat_with_bot():
    """Send message to Azure Bot and get response"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data received'
            }), 400
            
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Check if bot credentials are configured
        if not BOT_DIRECT_LINE_SECRET:
            return jsonify({
                'status': 'error',
                'message': 'Bot not configured. Please set BOT_DIRECT_LINE_SECRET environment variable.',
                'bot_responses': [{
                    'text': f'Echo (bot not configured): {message}',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'message'
                }]
            })
        
        # Send message to bot
        bot_response = bot_connector.send_message(message)
        
        # Handle different response types
        if isinstance(bot_response, dict) and 'error' in bot_response:
            return jsonify({
                'status': 'error',
                'message': bot_response['error'],
                'bot_responses': [{
                    'text': f"Bot Error: {bot_response['error']}",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'error'
                }]
            })
        
        elif isinstance(bot_response, list) and len(bot_response) > 0:
            return jsonify({
                'status': 'success',
                'message': 'Message sent successfully',
                'bot_responses': bot_response
            })
        
        else:
            return jsonify({
                'status': 'success',
                'message': 'Message sent but no response received',
                'bot_responses': [{
                    'text': 'Message sent to bot, but no response received.',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'info'
                }]
            })
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}',
            'bot_responses': [{
                'text': f'Server Error: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'type': 'error'
            }]
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )