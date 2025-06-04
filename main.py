from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageSendMessage,
)
from fastapi import FastAPI, Request, BackgroundTasks, Header
from starlette.exceptions import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# 環境変数からトークンを取得
LINE_BOT_API = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

@app.get("/")
def read_root():
    return {"message": "LINE Bot is running"}

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

@handler.add(MessageEvent)
def handle_message(event):
    if not isinstance(event.message, TextMessage):
        return

    message_text = event.message.text.lower()

    if message_text == "おはよう":
        reply = TextSendMessage(text="おはよう")
    elif message_text == "画像":
        image_url = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgz_KD4wcCk5Q0poPDsJhMGyFAT1FDHkRY5DdjxHriBddrGb7UmVyBFG4ox5Eg9DPD_t_qoP-nyuFwPQAe5wNBG9sK0XZgHnCma4sbDjsajU1uKYFCl_zYbTBjcCfcdWRmVfqlnkK7ICe6C/s876/sports_referee_var_pose.png"  # 必ずHTTPS URLにする
        reply = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    else:
        reply = TextSendMessage(text="「おはよう」または「画像」と送ってみてください。")

    try:
        LINE_BOT_API.reply_message(event.reply_token, reply)
    except Exception as e:
        print(f"Error sending message: {e}")
