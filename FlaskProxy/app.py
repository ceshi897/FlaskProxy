from flask import Flask, request, Response
import requests

app = Flask(__name__)

TARGET_API = "https://360seapi.ceshi897.cn"

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy(path):
    # 获取客户端真实 IP
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # 构建转发的 headers
    headers = {key: value for key, value in request.headers if key.lower() != "host"}
    headers["CF-Connecting-IP"] = client_ip   # Worker 可直接识别
    headers["X-Forwarded-For"] = client_ip    # 备用，方便日志追踪

    # 转发请求
    resp = requests.request(
        method=request.method,
        url=f"{TARGET_API}/{path}",
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        params=request.args
    )

    # 返回响应
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    response_headers = [(name, value) for name, value in resp.headers.items() if name.lower() not in excluded_headers]
    return Response(resp.content, resp.status_code, response_headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
