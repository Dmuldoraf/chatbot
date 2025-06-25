from flask import Flask, render_template_string, request, jsonify
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Azure Flask Web App</h1>
        
        <div class="status">
            <h3>✅ Application Status: Running</h3>
            <p>Deployed on Microsoft Azure Web App Service</p>
            <p>Server Time: {{ current_time }}</p>
        </div>

        <div class="info-grid">
            <div class="card">
                <h3>📊 App Info</h3>
                <p><strong>Python Version:</strong> {{ python_version }}</p>
                <p><strong>Flask Version:</strong> {{ flask_version }}</p>
                <p><strong>Environment:</strong> {{ environment }}</p>
            </div>
            
            <div class="card">
                <h3>🌐 Request Details</h3>
                <p><strong>Your IP:</strong> {{ user_ip }}</p>
                <p><strong>User Agent:</strong> {{ user_agent[:50] }}...</p>
                <p><strong>Method:</strong> {{ method }}</p>
            </div>
        </div>

        <div class="card">
            <h3>💬 Test API Endpoint</h3>
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
            <h3>🔗 Available Endpoints</h3>
            <ul>
                <li><strong>GET /</strong> - This home page</li>
                <li><strong>GET /health</strong> - Health check endpoint</li>
                <li><strong>POST /api/echo</strong> - Echo API for testing</li>
                <li><strong>GET /info</strong> - System information</li>
            </ul>
        </div>
    </div>

    <script>
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

@app.route('/api/echo', methods=['POST'])
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

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )