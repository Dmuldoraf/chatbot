from flask import Flask, render_template, render_template_string, request, jsonify
import os
import logging
import requests
from datetime import datetime
from database_maintainer import insert_chat_message
from database_maintainer import get_all_chat_requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
app = Flask(__name__)

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
                logger.info(f"Started convewrsation: {self.conversation_id}")
                return True
            else:
                logger.error(f"Failed to start conversation: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
            return False

    def send_message(self, message, user_id="user123"):
        def get_info_by_buzzword(sentence):
            buzzwords = [
            "Studiengänge",
            "Prüfungen",
            "Semester",
            "Stundenplan",
            "Rückmeldefrist",
            "Bibliothek",
            "Studienberatung",
            "Internationale Studierende",
            "International Office",
            "HISinOne"
            ]
            buzzword = next((word for word in buzzwords if word.lower() in sentence.lower()), None)
            faq = {
                "Studiengänge": "Die Hochschule bietet die Studiengänge Informatik, BWL, Maschinenbau u. v. m. an.",
                "Prüfungen": "Über das Online-Portal HISinOne. Die Fristen findest du unter „Prüfungsamt“.",
                "Semesterbeginn": "Das Sommersemester: 1. April, Wintersemester: 1. Oktober.",
                "Stundenplan": "Nach der Einschreibung findest du ihn im Campusportal unter „Mein Studium“.",
                "Rückmeldefrist": "Die Rückmeldung ist bis zum 15. März (SoSe) bzw. 15. September (WiSe) möglich.",
                "Bibliothek": "Unter THM.de/bibliothek findest du alle Infos.",
                "Studienberatung": "Per Mail an studienberatung@THM.de oder über die Terminbuchung online.",
                "Internationale Studierende": "Ja, z. B. das Buddy-Programm. Infos unter „International Office“."
            }
            if buzzword is None:
                return "Bitte stelle eine präzisere Frage oder nenne ein Stichwort."
            buzzword = buzzword.lower()
            for key in faq:
                if buzzword in key.lower():
                    return faq[key]
            return "Keine passende Information gefunden."
        if not self.conversation_id:
            if not self.start_conversation():
                return {'error': 'Failed to start conversation with bot'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "locale": "de-DE",
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
            def get_user_ip():
                ip = request.remote_addr
                res = requests.get(f'http://ip-api.com/json/{ip}').json()
                region = res.get('regionName', 'Unknown')
                country = res.get('country', 'Unknown')
                return f'{ip}-{region}-{country}'


            if response.status_code == 200:
                db_response = insert_chat_message(session_id=self.conversation_id, 
                    sender=get_user_ip(), 
                    message=message, 
                    is_error=False, pwd=os.environ.get('DB_PASSWORD', ''))
                if db_response:
                    logger.info(f"Message sent successfully: {message}")
                else:
                    logger.error("Failed database write ${db_response}")
                return self.get_messages()
            else:
                if insert_chat_message(session_id=self.conversation_id, 
                    sender=get_user_ip(), 
                    message=message, 
                    is_error=True,pwd=os.environ.get('DB_PASSWORD', '')):
                    logger.info(f"Message sent successfully: {message}")
                else:
                    logger.error("Failed to insert chat message into database")
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return 'Notbot: ' + get_info_by_buzzword(message)
                #return {'error': f'Bot returned error {response.status_code}'}
                
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
        
    

bot_connector = BotConnector()

@app.route('/api/test-action', methods=['POST'])
def test_action():
    session_id = "test_session_123"
    sender = "test_user"
    message = "This is a test message from the test button."
    is_error = False
    insert_chat_message(session_id, sender, message, is_error, pwd=os.environ.get('DB_PASSWORD', ''))
    print("Test button was clicked!")
    return jsonify({'status': 'success', 'message': 'Python method triggered!'})

@app.route('/')
def home():
    """Main chat page"""
    with open('homepage.html', encoding='utf-8') as f:
        html_content = f.read()
    return render_template_string(html_content)

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

        if not BOT_DIRECT_LINE_SECRET:
            return jsonify({
                'status': 'error',
                'message': 'Bot not correctly configured. Please set BOT_DIRECT_LINE_SECRET environment variable.',
                'bot_responses': [{
                    'text': f'Echo (bot not configured): {message}',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'message'
                }]
            })
        
        bot_response = bot_connector.send_message(message)

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
        elif isinstance(bot_response, str):
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

@app.route('/api/get_execute_requests', methods=['GET'])
def get_execute_requests():
    """Return all chat messages from the database"""
    return get_all_chat_requests(pwd=os.environ.get('DB_PASSWORD', ''))
    # try:
    #     messages = get_all_chat_requests()
    #     return messages
    # except Exception as e:
    #     logger.error(f"Error fetching chat messages: {str(e)}")
    #     return jsonify({
    #         'status': 'error',
    #         'message': f'Failed to fetch chat messages: {str(e)}'
    #     }), 500

@app.route('/dbview')
def db_view():
    """Render the database view page"""
    with open('db_view.html', encoding='utf-8') as f:
        html_content = f.read()

    return render_template_string(html_content)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )