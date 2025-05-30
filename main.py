from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv

load_dotenv()

LINE_BOT_API=LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler=WebhookHandler(os.environ["CHANNEL_SECRET"])
app = FastAPI()

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

print(CHANNEL_ACCESS_TOKEN)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(CHANNEL_SECRET)


@app.post("/webhook")
async def callback(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    try:
        events = parser.parse(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            reply_text = f"あなたのメッセージ: {event.message.text}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

    return {"status": "ok"}



@handler.add(MessageEvent)
def handle_message(event):
     message_text = event.message.text.lower()
     
     if "こんにちは" in message_text:
        message = TextMessage(text="こんにちは！！")
        LINE_BOT_API.reply_message(event.reply_token, message)