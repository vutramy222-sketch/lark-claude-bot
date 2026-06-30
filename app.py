import os
import json
from flask import Flask, request, jsonify
import anthropic
import requests

app = Flask(__name__)

LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

def get_lark_token():
      r = requests.post(
                "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
      )
      return r.json().get("tenant_access_token", "")

def send_reply(open_id, text):
      token = get_lark_token()
      requests.post(
          "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=open_id",
          headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
          json={"receive_id": open_id, "msg_type": "text", "content": json.dumps({"text": text})}
      )

@app.route("/webhook", methods=["POST"])
def webhook():
      data = request.json or {}
      if "challenge" in data:
                return jsonify({"challenge": data["challenge"]})
            event = data.get("event", {})
    message = event.get("message", {})
    sender = event.get("sender", {})
    open_id = sender.get("sender_id", {}).get("open_id", "")
    msg_type = message.get("message_type", "")
    if msg_type != "text":
              return jsonify({"status": "ignored"})
          content = json.loads(message.get("content", "{}"))
    user_text = content.get("text", "").strip()
    if user_text.startswith("@"):
              parts = user_text.split(" ", 1)
              user_text = parts[1].strip() if len(parts) > 1 else ""
          if not user_text or not open_id:
                    return jsonify({"status": "ignored"})
                client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
              model="claude-opus-4-5",
              max_tokens=1024,
              messages=[{"role": "user", "content": user_text}]
    )
    send_reply(open_id, response.content[0].text)
    return jsonify({"status": "ok"})

@app.route("/health", methods=["GET"])
def health():
      return jsonify({"status": "running"})

if __name__ == "__main__":
      port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
