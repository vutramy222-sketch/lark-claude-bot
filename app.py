import os
import json
import logging
import anthropic
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

logging.basicConfig(level=logging.INFO)

LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def send_reply(client, open_id, text):
          request = CreateMessageRequest.builder() \
              .receive_id_type("open_id") \
              .request_body(CreateMessageRequestBody.builder()
                                                  .receive_id(open_id)
                                                  .msg_type("text")
                                                  .content(json.dumps({"text": text}))
                                                  .build()) \
              .build()
          client.im.v1.message.create(request)


def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
          msg = data.event.message
          sender = data.event.sender
          open_id = sender.sender_id.open_id
          msg_type = msg.message_type

    if msg_type != "text":
                  return

    content = json.loads(msg.content)
    user_text = content.get("text", "").strip()

    if user_text.startswith("@"):
                  parts = user_text.split(" ", 1)
                  user_text = parts[1].strip() if len(parts) > 1 else ""

    if not user_text:
                  return

    response = claude_client.messages.create(
                  model="claude-opus-4-5",
                  max_tokens=1024,
                  messages=[{"role": "user", "content": user_text}]
    )
    reply_text = response.content[0].text

    lark_client = lark.Client.builder() \
        .app_id(LARK_APP_ID) \
        .app_secret(LARK_APP_SECRET) \
        .build()
    send_reply(lark_client, open_id, reply_text)


def main():
          event_handler = lark.EventDispatcherHandler.builder(
                        lark.DECRYPT_KEY, lark.VERIFICATION_TOKEN, lark.LogLevel.DEBUG
          ).register_p2_im_message_receive_v1(do_p2_im_message_receive_v1).build()

    cli = lark.Client.builder() \
        .app_id(LARK_APP_ID) \
        .app_secret(LARK_APP_SECRET) \
        .build()

    wsClient = lark.ws.Client(
                  LARK_APP_ID,
                  LARK_APP_SECRET,
                  event_handler=event_handler,
                  log_level=lark.LogLevel.DEBUG
    )
    wsClient.start()


if __name__ == "__main__":
          main()
      
