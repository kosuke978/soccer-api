from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from fastapi import FastAPI, Request, BackgroundTasks, Header
from starlette.exceptions import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()


app = FastAPI()

# 環境変数
LINE_BOT_API = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

@app.get("/")
def read_root():
    return {"message": "LINE Bot is running"}

# LINE Webhook用エンドポイント
@app.post("/callback")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None),
):
    body = await request.body()

    try:
        background_tasks.add_task(
            handler.handle, body.decode("utf-8"), x_line_signature
        )
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"status": "ok"}

# メッセージイベントの処理
@handler.add(MessageEvent)
def handle_message(event):
    message_text = event.message.text.lower()

    if message_text == "おはよう":
        reply = TextSendMessage(text="おはよう！")
        try:
            LINE_BOT_API.reply_message(event.reply_token, reply)
        except Exception as e:
            # ここでエラーをログに出力するなど、適切な処理を行u
            print(f"返信メッセージの送信中にエラーが発生しました: {e}")
            # エラー発生時でもLINE側に200 OKを返すために、基本的にはここで再送などを試みnai