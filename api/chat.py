import os
import requests
import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # --- 1. ブラウザからのリクエストを受け取る ---
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            
            user_query = body.get('query')
            conversation_id = body.get('conversation_id')

            if not user_query:
                self._send_response(400, {"error": "Query is missing"})
                return

        except (json.JSONDecodeError, TypeError, ValueError):
            self._send_response(400, {"error": "Invalid JSON format"})
            return

        # --- 2. 環境変数からAPIキーを安全に読み込む ---
        API_KEY = os.environ.get('DIFY_API_KEY')
        API_URL = os.environ.get('DIFY_API_URL')

        if not API_KEY or not API_URL:
            self._send_response(500, {"error": "Server configuration error: API key or URL is not set."})
            return

        # --- 3. Dify APIにリクエストを送信する ---
        dify_payload = {
            "inputs": {},  # inputsは空にする
            "query": user_query,  # queryをトップレベルに移動
            "response_mode": "blocking",
            "user": "secure-web-user",
            "conversation_id": conversation_id or ""
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(API_URL, headers=headers, json=dify_payload, timeout=30)
            response.raise_for_status()  # HTTPエラーがあれば例外を発生
            dify_data = response.json()
            
            # --- 4. Difyからの応答をブラウザに返す ---
            self._send_response(200, dify_data)

        except requests.exceptions.Timeout:
            self._send_response(504, {"error": "The request to Dify API timed out."})
        except requests.exceptions.RequestException as e:
            self._send_response(502, {"error": f"Failed to communicate with Dify API: {e}"})

        return

    def _send_response(self, status_code, data):
        """レスポンスを送信するためのヘルパー関数"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))