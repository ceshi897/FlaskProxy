import os
import logging
from flask import Flask, request, Response
import requests
from urllib.parse import urljoin

# 日志配置
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# 修改这里，换成你的 Cloudflare Worker 边缘域名
TARGET_URL = "https://360seapi.ceshi897.cn"

# 不转发的头
EXCLUDED_HEADERS = {
    'connection', 'keep-alive', 'transfer-encoding', 'te', 'trailer',
    'upgrade', 'proxy-authenticate', 'proxy-authorization', 'host'
}

@app.route('/', defaults={'path': ''}, methods=[
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=[
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy(path):
    try:
        # 拼接目标 URL
        target_url = urljoin(TARGET_URL, path)
        if request.query_string:
            target_url += '?' + request.query_string.decode('utf-8')

        logger.debug(f"Proxying {request.method} request to: {target_url}")

        # 构造头部
        headers = {}
        for key, value in request.headers:
            if key.lower() not in EXCLUDED_HEADERS:
                headers[key] = value

        headers['Host'] = urljoin(TARGET_URL, '/').split('/')[2]

        # ⭐️ 关键：附加真实客户端 IP
        # request.remote_addr 是直接访问 Flask 的客户端 IP
        headers["X-Forwarded-For"] = real_ip

        # 构造请求体
        data = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json()
            else:
                data = request.get_data()

        # 转发请求
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            allow_redirects=False,
            stream=True,
            timeout=30
        )

        # 构造响应
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in EXCLUDED_HEADERS:
                response_headers[key] = value

        return Response(response.content, status=response.status_code, headers=response_headers)

    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return Response(f"Proxy error: {str(e)}", status=502, content_type='text/plain')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask proxy on port {port}, forwarding to {TARGET_URL}")
    app.run(host='0.0.0.0', port=port, debug=True)
