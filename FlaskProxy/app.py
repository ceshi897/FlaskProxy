import os
import logging
from flask import Flask, request, Response, render_template, jsonify
import requests
from urllib.parse import urljoin, urlparse
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Target API configuration
TARGET_API = "https://360seapi.ceshi897.cn"

@app.route('/')
def index():
    """Serve the main proxy interface"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test connection to target API
        response = requests.get(TARGET_API, timeout=5)
        return jsonify({
            "status": "healthy",
            "target_api": TARGET_API,
            "target_status": response.status_code
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "target_api": TARGET_API,
            "error": str(e)
        }), 502

@app.route('/proxy', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    """Main proxy endpoint that forwards requests to the target API"""
    try:
        # Construct target URL
        if path:
            target_url = f"{TARGET_API}/{path}"
        else:
            target_url = TARGET_API
        
        # Add query parameters if present
        if request.query_string:
            target_url += f"?{request.query_string.decode('utf-8')}"
        
        logger.info(f"Proxying {request.method} request to: {target_url}")
        
        # Prepare headers - exclude hop-by-hop headers
        headers = {}
        excluded_headers = [
            'host', 'connection', 'keep-alive', 'transfer-encoding',
            'upgrade', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers'
        ]
        
        for key, value in request.headers:
            if key.lower() not in excluded_headers:
                headers[key] = value
        
        # Set the correct host header for the target
        headers['Host'] = urlparse(TARGET_API).netloc
        
        # Prepare request data
        data = None
        if request.method in ['POST', 'PUT', 'PATCH'] and request.data:
            data = request.data
        
        # Make the proxy request
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=None,  # Already included in target_url
            allow_redirects=False,
            timeout=30,
            stream=True
        )
        
        logger.info(f"Target API responded with status: {response.status_code}")
        
        # Prepare response headers - exclude hop-by-hop headers
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in excluded_headers:
                response_headers[key] = value
        
        # Create Flask response
        flask_response = Response(
            response.content,
            status=response.status_code,
            headers=response_headers
        )
        
        return flask_response
        
    except requests.exceptions.Timeout:
        logger.error("Request to target API timed out")
        return jsonify({"error": "Target API request timed out"}), 504
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to target API: {str(e)}")
        return jsonify({"error": f"Unable to connect to target API: {str(e)}"}), 502
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({"error": f"Proxy request failed: {str(e)}"}), 502
    
    except Exception as e:
        logger.error(f"Unexpected error in proxy: {str(e)}")
        return jsonify({"error": f"Internal proxy error: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found. Use /proxy/<path> to access the target API"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
