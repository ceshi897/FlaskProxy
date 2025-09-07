import os
import logging
from flask import Flask, request, Response
import requests
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Target API endpoint
TARGET_URL = "https://360seapi.ceshi897.cn"

# Excluded headers
EXCLUDED_HEADERS = {
    'connection', 'keep-alive', 'transfer-encoding', 'te', 'trailer',
    'upgrade', 'proxy-authenticate', 'proxy-authorization', 'host'
}

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy(path):
    try:
        # Construct target URL
        target_url = urljoin(TARGET_URL, path)
        if request.query_string:
            target_url += '?' + request.query_string.decode('utf-8')

        logger.debug(f"Proxying {request.method} request to: {target_url}")

        # Prepare headers
        headers = {}
        for key, value in request.headers:
            if key.lower() not in EXCLUDED_HEADERS:
                headers[key] = value

        # Set Host header for target
        headers['Host'] = '360seapi.ceshi897.cn'

        # 关键：传递真实客户端 IP
        real_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        headers['X-Real-IP'] = real_ip

        # Prepare body
        data = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json()
            else:
                data = request.get_data()

        # Forward request
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            allow_redirects=False,
            stream=True,
            timeout=30
        )

        # Response headers
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in EXCLUDED_HEADERS:
                response_headers[key] = value

        return Response(response.content, status=response.status_code, headers=response_headers)

    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error: {str(e)}")
        return Response(f"Proxy error: {str(e)}", status=502, content_type='text/plain')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response(f"Unexpected proxy error: {str(e)}", status=500, content_type='text/plain')


if __name__ == '__main__':
    logger.info(f"Starting proxy server on port 5000, forwarding to {TARGET_URL}")
    app.run(host='0.0.0.0', port=5000, debug=True)
