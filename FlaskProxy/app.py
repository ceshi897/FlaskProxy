import os
import logging
from flask import Flask, request, Response
import requests
from urllib.parse import urljoin

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Target API endpoint
TARGET_URL = "https://360seapi.ceshi897.cn"

# Headers that should not be forwarded to avoid connection issues
EXCLUDED_HEADERS = {
    'connection', 'keep-alive', 'transfer-encoding', 'te', 'trailer',
    'upgrade', 'proxy-authenticate', 'proxy-authorization', 'host'
}

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy(path):
    """
    Proxy all requests to the target API endpoint
    """
    try:
        # Construct the target URL
        target_url = urljoin(TARGET_URL, path)
        if request.query_string:
            target_url += '?' + request.query_string.decode('utf-8')
        
        logger.debug(f"Proxying {request.method} request to: {target_url}")
        
        # Prepare headers for forwarding
        headers = {}
        for key, value in request.headers:
            if key.lower() not in EXCLUDED_HEADERS:
                headers[key] = value
        
        # Set the host header to the target host
        #headers['Host'] = '360seapi.ceshi897.cn'
        
        # Prepare request data
        data = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json()
            else:
                data = request.get_data()
        
        # Make the proxy request
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=None,  # Already included in target_url
            allow_redirects=False,
            stream=True,
            timeout=30
        )
        
        logger.debug(f"Received response with status: {response.status_code}")
        
        # Prepare response headers
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in EXCLUDED_HEADERS:
                response_headers[key] = value
        
        # Create Flask response
        flask_response = Response(
            response.content,
            status=response.status_code,
            headers=response_headers
        )
        
        return flask_response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error: {str(e)}")
        error_message = f"Proxy error: {str(e)}"
        return Response(error_message, status=502, content_type='text/plain')
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        error_message = f"Unexpected proxy error: {str(e)}"
        return Response(error_message, status=500, content_type='text/plain')

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return Response("Endpoint not found on proxy server", status=404, content_type='text/plain')

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return Response("Internal proxy server error", status=500, content_type='text/plain')

if __name__ == '__main__':
    # Run the Flask app
    logger.info(f"Starting proxy server on port 5000, forwarding to {TARGET_URL}")
    app.run(host='0.0.0.0', port=5000, debug=True)
