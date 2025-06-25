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
BOT_APP_ID = os.environ.get('BOT_APP_ID', '')
BOT_APP_PASSWORD = os.environ.get('BOT_APP_PASSWORD', '')
BOT_DIRECT_LINE_SECRET = os.environ.get('BOT_DIRECT_LINE_SECRET', '')
BOT_SERVICE_URL = os.environ.get('BOT_SERVICE_URL', 'https://directline.botframework.com')

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
                time.sleep(2)  # Increased wait time
                return self.get_messages()
            elif response.status_code == 502:
                logger.error(f"Bot service error (502): {response.text}")
                return {'error': 'Bot service is not responding. Please check if your bot is deployed and running.'}
            elif response.status_code == 401:
                logger.error(f"Authentication error (401): {response.text}")
                return {'error': 'Bot authentication failed. Please check your Direct Line secret.'}
            elif response.status_code == 403:
                logger.error(f"Forbidden error (403): {response.text}")
                return {'error': 'Access denied. Please check your bot permissions and Direct Line configuration.'}
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return {'error': f'Bot returned error {response.status_code}: {response.text}'}
                
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return {'error': 'Request to bot service timed out'}
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            return {'error': 'Could not connect to bot service'}
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
                logger.error(f"Failed to get messages: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return None

# Global bot connector instance
bot_connector = BotConnector()

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Flask App</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .card {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .form-group {
            margin: 15px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 16px;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        button:hover {
            background: #45a049;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            background: rgba(76, 175, 80, 0.3);
            border: 1px solid #4CAF50;
        }
        #response {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            min-height: 20px;
        }
        .chat-message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
        }
        .user-message {
            background: rgba(0, 123, 255, 0.3);
            margin-left: 20px;
        }
        .bot-message {
            background: rgba(40, 167, 69, 0.3);
            margin-right: 20px;
        }
        .error-message {
            background: rgba(220, 53, 69, 0.3);
            color: #ffcccc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Azure Flask Web App</h1>

        <div class="card">
            <h3>🤖 Chat with Azure Bot</h3>
            <div id="chatContainer">
                <div id="chatMessages" style="height: 300px; overflow-y: auto; border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; padding: 15px; margin-bottom: 15px; background: rgba(0,0,0,0.2);">
                    <div class="chat-message bot-message">
                        <strong>Bot:</strong> Hello! I'm ready to chat. Send me a message!
                    </div>
                </div>
                <form id="chatForm">
                    <div class="form-group" style="display: flex; gap: 10px;">
                        <input type="text" id="chatInput" name="message" placeholder="Type your message..." style="flex: 1;" required>
                        <button type="submit" style="width: auto; padding: 12px 20px;">Send</button>
                    </div>
                </form>
            </div>
            <div id="botStatus" style="margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">
                Bot Status: <span id="statusText">Ready</span>
            </div>
        </div>

        <div class="card">
            <h3>💬 Test Echo API</h3>
            <form id="testForm">
                <div class="form-group">
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name" placeholder="Enter your name" required>
                </div>
                <div class="form-group">
                    <label for="message">Message:</label>
                    <textarea id="message" name="message" rows="3" placeholder="Enter a message"></textarea>
                </div>
                <button type="submit">Send Test Request</button>
            </form>
            <div id="response"></div>
        </div>

        <div class="card">
            <h3>🔧 Bot Diagnostics</h3>
            <button onclick="runDiagnostics()" style="margin-bottom: 15px;">Run Bot Diagnostics</button>
            <div id="diagnosticsResult" style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; min-height: 100px;">
                Click "Run Bot Diagnostics" to check bot configuration and connectivity.
            </div>
        </div>

        <div class="card">
            <h3>🔗 Available Endpoints</h3>
            <ul>
                <li><strong>GET /</strong> - This home page with bot chat</li>
                <li><strong>GET /health</strong> - Health check endpoint</li>
                <li><strong>POST /api/chat</strong> - Send message to Azure Bot</li>
                <li><strong>GET /api/bot-diagnostics</strong> - Bot configuration diagnostics</li>
                <li><strong>POST /api/echo</strong> - Echo API for testing</li>
                <li><strong>GET /info</strong> - System information</li>
            </ul>
        </div>
    </div>

    <script>
        // Chat functionality
        document.getElementById('chatForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const chatInput = document.getElementById('chatInput');
            const message = chatInput.value.trim();
            if (!message) return;
            
            const chatMessages = document.getElementById('chatMessages');
            const statusText = document.getElementById('statusText');
            
            // Add user message to chat
            const userMessageDiv = document.createElement('div');
            userMessageDiv.className = 'chat-message user-message';
            userMessageDiv.innerHTML = `<strong>You:</strong> ${message}`;
            chatMessages.appendChild(userMessageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Clear input and show loading
            chatInput.value = '';
            statusText.textContent = 'Sending message...';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const result = await response.json();
                
                if (result.status === 'success' && result.bot_responses) {
                    // Add bot responses to chat
                    result.bot_responses.forEach(botMessage => {
                        if (botMessage.text) {
                            const botMessageDiv = document.createElement('div');
                            botMessageDiv.className = 'chat-message bot-message';
                            botMessageDiv.innerHTML = `<strong>Bot:</strong> ${botMessage.text}`;
                            chatMessages.appendChild(botMessageDiv);
                        }
                    });
                    statusText.textContent = 'Ready';
                } else {
                    // Show error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'chat-message error-message';
                    errorDiv.innerHTML = `<strong>Error:</strong> ${result.message || 'Failed to get bot response'}`;
                    chatMessages.appendChild(errorDiv);
                    statusText.textContent = 'Error occurred';
                }
                
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
            } catch (error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'chat-message error-message';
                errorDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
                chatMessages.appendChild(errorDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                statusText.textContent = 'Connection error';
            }
        });

        // Bot diagnostics functionality
        async function runDiagnostics() {
            const diagnosticsResult = document.getElementById('diagnosticsResult');
            diagnosticsResult.textContent = 'Running diagnostics...';
            
            try {
                const response = await fetch('/api/bot-diagnostics');
                const result = await response.json();
                
                diagnosticsResult.textContent = JSON.stringify(result, null, 2);
                
                // Add interpretation
                let interpretation = '\n\n=== INTERPRETATION ===\n';
                if (!result.bot_configured) {
                    interpretation += '❌ Bot not configured - set BOT_DIRECT_LINE_SECRET\n';
                } else if (result.direct_line_test && !result.direct_line_test.success) {
                    interpretation += '❌ Direct Line connection failed\n';
                    interpretation += `   Status: ${result.direct_line_test.status_code || 'Connection error'}\n`;
                    interpretation += `   Error: ${result.direct_line_test.error || result.direct_line_test.response_text}\n`;
                } else {
                    interpretation += '✅ Direct Line connection successful\n';
                    interpretation += '   If bot still not responding, check:\n';
                    interpretation += '   1. Bot service is deployed and running\n';
                    interpretation += '   2. Bot endpoint URL is correct\n';
                    interpretation += '   3. Bot authentication is properly configured\n';
                }
                
                diagnosticsResult.textContent += interpretation;
                
            } catch (error) {
                diagnosticsResult.textContent = `Error running diagnostics: ${error.message}`;
            }
        }

        // Test form functionality
        document.getElementById('testForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                name: formData.get('name'),
                message: formData.get('message')
            };
            
            try {
                const response = await fetch('/api/echo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                document.getElementById('response').innerHTML = `
                    <h4>✅ API Response:</h4>
                    <pre>${JSON.stringify(result, null, 2)}</pre>
                `;
            } catch (error) {
                document.getElementById('response').innerHTML = `
                    <h4>❌ Error:</h4>
                    <p>${error.message}</p>
                `;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Main page with app information and testing interface"""
    import sys
    import flask
    
    return render_template_string(HTML_TEMPLATE, 
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        python_version=sys.version.split()[0],
        flask_version=flask.__version__,
        environment=os.environ.get('FLASK_ENV', 'production'),
        user_ip=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
        user_agent=request.headers.get('User-Agent', 'Unknown'),
        method=request.method
    )

@app.route('/health')
def health_check():
    """Health check endpoint for Azure monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/chat', methods=['POST'])
def chat_with_bot():
    """Send message to Azure Bot and get response"""
    try:
        data = request.get_json()
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
                    'text': 'Bot simulation: Echo - ' + message,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'message'
                }]
            })
        
        # Send message to bot
        bot_response = bot_connector.send_message(message)
        
        # Handle different response types
        if isinstance(bot_response, dict) and 'error' in bot_response:
            # Bot returned an error
            return jsonify({
                'status': 'error',
                'message': bot_response['error'],
                'user_message': message,
                'bot_responses': [{
                    'text': f"❌ Bot Error: {bot_response['error']}",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'error'
                }],
                'debug_info': {
                    'conversation_id': bot_connector.conversation_id,
                    'has_token': bool(bot_connector.token),
                    'bot_service_url': BOT_SERVICE_URL
                },
                'timestamp': datetime.now().isoformat()
            })
        
        elif isinstance(bot_response, list) and len(bot_response) > 0:
            # Bot returned messages
            return jsonify({
                'status': 'success',
                'message': 'Message sent successfully',
                'user_message': message,
                'bot_responses': bot_response,
                'timestamp': datetime.now().isoformat()
            })
        
        else:
            # No response from bot (empty or None)
            return jsonify({
                'status': 'partial_success',
                'message': 'Message sent but no bot response received',
                'user_message': message,
                'bot_responses': [{
                    'text': '🤖 Bot received your message but didn\'t respond. This might be normal depending on your bot\'s logic.',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'info'
                }],
                'debug_info': {
                    'conversation_id': bot_connector.conversation_id,
                    'response_type': str(type(bot_response)),
                    'response_length': len(bot_response) if isinstance(bot_response, list) else 0
                },
                'timestamp': datetime.now().isoformat()
            })
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Chat error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/bot-diagnostics')
def bot_diagnostics():
    """Diagnostic endpoint to check bot configuration"""
    try:
        diagnostics = {
            'bot_configured': bool(BOT_DIRECT_LINE_SECRET),
            'direct_line_secret_set': bool(BOT_DIRECT_LINE_SECRET),
            'app_id_set': bool(BOT_APP_ID),
            'app_password_set': bool(BOT_APP_PASSWORD),
            'bot_service_url': BOT_SERVICE_URL,
            'current_conversation_id': bot_connector.conversation_id,
            'has_token': bool(bot_connector.token),
            'watermark': bot_connector.watermark,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test connection to Direct Line API
        if BOT_DIRECT_LINE_SECRET:
            try:
                headers = {
                    'Authorization': f'Bearer {BOT_DIRECT_LINE_SECRET}',
                    'Content-Type': 'application/json'
                }
                
                # Test creating a conversation
                response = requests.post(
                    f'{BOT_SERVICE_URL}/v3/directline/conversations',
                    headers=headers,
                    timeout=10
                )
                
                diagnostics['direct_line_test'] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 201,
                    'response_text': response.text[:200] if response.text else 'No response text'
                }
                
            except Exception as e:
                diagnostics['direct_line_test'] = {
                    'error': str(e),
                    'success': False
                }
        else:
            diagnostics['direct_line_test'] = {
                'error': 'No Direct Line secret configured',
                'success': False
            }
        
        return jsonify(diagnostics)
        
    except Exception as e:
        logger.error(f"Error in bot diagnostics: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
def echo_api():
    """Echo API endpoint for testing"""
    try:
        data = request.get_json()
        
        response = {
            'status': 'success',
            'received_data': data,
            'timestamp': datetime.now().isoformat(),
            'message': f"Hello {data.get('name', 'Anonymous')}! Your message was received.",
            'echo': data.get('message', 'No message provided')
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in echo API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 400

@app.route('/info')
def system_info():
    """System information endpoint"""
    import sys
    import platform
    
    info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'flask_version': getattr(__import__('flask'), '__version__', 'Unknown'),
        'environment_variables': {
            key: value for key, value in os.environ.items() 
            if not key.startswith(('SECRET', 'PASSWORD', 'KEY', 'TOKEN'))
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(info)

@app.errorhandler(404)
def not_found(error):
    """Custom 404 error handler"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found on this server.',
        'status_code': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error handler"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal server error occurred.',
        'status_code': 500
    }), 500

#########################################################
# Add this to your existing Flask app, after the other route definitions

@app.route('/api/messages', methods=['POST'])
def bot_messages():
    """
    Endpoint that receives messages from Azure Bot Framework
    This is where your bot sends messages to your web app
    """
    try:
        # Get the activity (message) from Azure Bot Framework
        activity = request.get_json()
        
        logger.info(f"Received activity from bot: {activity}")
        
        # Validate the activity
        if not activity:
            return jsonify({'error': 'No activity received'}), 400
        
        # Process different types of activities
        activity_type = activity.get('type', '')
        
        if activity_type == 'message':
            # Handle incoming message from bot
            text = activity.get('text', '')
            from_user = activity.get('from', {})
            conversation = activity.get('conversation', {})
            
            logger.info(f"Message from bot: {text}")
            
            # Here you can process the message and send a response back
            # For now, let's just echo it back
            response_activity = {
                'type': 'message',
                'text': f"Web app received: {text}",
                'from': {
                    'id': 'webapp',
                    'name': 'Web App'
                },
                'conversation': conversation,
                'replyToId': activity.get('id')
            }
            
            # You can also store the message in a database or process it however you need
            # For example, update UI state, trigger notifications, etc.
            
            return jsonify(response_activity)
            
        elif activity_type == 'conversationUpdate':
            # Handle conversation updates (like bot/user joining)
            logger.info("Conversation update received")
            return jsonify({'status': 'ok'})
            
        else:
            # Handle other activity types
            logger.info(f"Received activity type: {activity_type}")
            return jsonify({'status': 'ok'})
    
    except Exception as e:
        logger.error(f"Error in bot messages endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Add authentication middleware if needed (recommended for production)
def verify_bot_request(request):
    """
    Verify that the request is actually coming from Azure Bot Framework
    This is important for security in production
    """
    # In production, you should verify the JWT token from Azure
    # For now, we'll just check if it looks like a bot request
    
    # Check for required headers
    if not request.headers.get('Authorization'):
        return False
    
    # Additional verification logic can be added here
    # See: https://docs.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-connector-authentication
    
    return True


# Optional: Add a webhook verification endpoint
@app.route('/api/webhook-verify', methods=['GET'])
def webhook_verify():
    """
    Endpoint for webhook verification during bot setup
    """
    return jsonify({
        'status': 'verified',
        'timestamp': datetime.now().isoformat(),
        'endpoint': '/api/messages'
    })


# Update your existing chat endpoint to work bidirectionally
@app.route('/api/send-to-bot', methods=['POST'])
def send_to_bot():
    """
    Send a message from web app to bot (using Direct Line)
    This is your existing functionality, just renamed for clarity
    """
    try:
        data = request.get_json()
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
                'message': 'Bot not configured. Please set BOT_DIRECT_LINE_SECRET environment variable.'
            })
        
        # Send message to bot via Direct Line
        bot_response = bot_connector.send_message(message)
        
        # Handle response (your existing logic)
        if isinstance(bot_response, dict) and 'error' in bot_response:
            return jsonify({
                'status': 'error',
                'message': bot_response['error'],
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Message sent to bot',
            'bot_responses': bot_response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error sending to bot: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500



if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )