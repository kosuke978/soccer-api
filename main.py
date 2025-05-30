from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
from dotenv import load_dotenv
import os

# 環境変数を読み込む
load_dotenv()

# LINE API設定（.envから取得）
LINE_BOT_API = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

# FastAPI初期化
app = FastAPI()

# GETルート（ヘルスチェック）
@app.get("/")
def read_root():
    return {"message": "LINE BOT is running"}

# Webhookルート（LINEがPOSTする場所）
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

# メッセージイベントハンドラ
@handler.add(MessageEvent)
def handle_message(event):
    message_text = event.message.text.lower()

    if "こんにちは" in message_text:
        message = TextSendMessage(text="こんにちは！！")
    elif "ありがとう" in message_text:
        message = TextSendMessage(text="こちらこそー")
    else:
        message = TextSendMessage(text="いつも使ってくれてありがとう")

    LINE_BOT_API.reply_message(event.reply_token, message)
