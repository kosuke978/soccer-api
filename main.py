from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from fastapi import FastAPI, Request, BackgroundTasks, Header
from dotenv import load_dotenv
from starlette.exceptions import HTTPException
import os

load_dotenv()

LINE_BOT_API=LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler=WebhookHandler(os.environ["CHANNEL_SECRET"])
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/callback")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature=Header(None),
):
    body = await request.body()

    try:
        background_tasks.add_task(
            handler.handle, body.decode("utf-8"), x_line_signature
        )
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "ok"

@handler.add(MessageEvent)
def handle_message(event):
    message_text = event.message.text.lower()
    
    if "こんにちは" in message_text:
        message = TextMessage(text="こんにちは！！")
        LINE_BOT_API.reply_message(event.reply_token, message)
    elif "ありがとう" in message_text:
        message = TextMessage(text="こちらこそー")
        LINE_BOT_API.reply_message(event.reply_token, message)
    else :
        message = TextMessage(text="いつも使ってくれてありがとう")
        LINE_BOT_API.reply_message(event.reply_token, message)