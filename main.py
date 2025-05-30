from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookParser,WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent,  TextSendMessage
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException




load_dotenv()

LINE_BOT_API=LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler=WebhookHandler(os.environ["CHANNEL_SECRET"])
app = FastAPI()
@app.get("/", response_class=PlainTextResponse)
async def root():
    return "LINE BOT is running"
@app.get("/")
def root():
    return {"message": "LINE BOT is running"}


CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

print(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.post("/webhook")
async def callback(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    try:
        events = handler.parse(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextSendMessage):
            reply_text = f"あなたのメッセージ: {event.message.text}"
            LINE_BOT_API.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

    return {"status": "ok"}



def handle_message(event):
     message_text = event.message.text.lower()
     
     if "こんにちは" in message_text:
        message = TextSendMessage(text="こんにちは！！")
        LINE_BOT_API.reply_message(event.reply_token, message)