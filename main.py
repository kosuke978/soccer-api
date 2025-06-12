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
import requests
import json
from datetime import datetime

load_dotenv()

app = FastAPI()

# 環境変数からトークンを取得
LINE_BOT_API = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

API_KEY=(os.environ["SOCCER_API_KEY"])
TEAM_ID=259
LEAGUE_ID=98
SEASON=2025
url="https://v3.football.api-sports.io/fixtures"
headers={'x-apisports':API_KEY}
params={'league':LEAGUE_ID,'season':SEASON,'team':TEAM_ID}

print(f"{SEASON}シーズン　ガンバ大阪の試合結果を取得")

try:
    r=requests.get(url,headers=headers,params=params)
    r.raise_for_status()
      # レスポンスをJSON形式で取得
    data = r.json()

    # 取得した試合結果をループで処理して表示
    if data['results'] > 0:
        fixtures = data['response']
        # 試合日でソートする
        sorted_fixtures = sorted(fixtures, key=lambda x: x['fixture']['date'])

        for fixture in sorted_fixtures:
            # 試合日と時間
            fixture_date_utc = datetime.fromisoformat(fixture['fixture']['date'])
            # 日本時間に変換 (UTC+9)
            fixture_date_jst = fixture_date_utc.strftime('%Y-%m-%d %H:%M')
            
            # チーム名
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            
            # スコア
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']

            # 試合ステータス
            status = fixture['fixture']['status']['long']

            print("-" * 40)
            print(f"試合日: {fixture_date_jst} JST")
            print(f"対戦: {home_team} vs {away_team}")

            # 試合が終わっている場合のみスコアを表示
            if status == "Match Finished":
                print(f"結果: {home_goals} - {away_goals}")
            else:
                print(f"ステータス: {status}")

    else:
        print("指定されたシーズンの試合データが見つかりませんでした。")
        if data.get('errors'):
            print("APIエラー:", data['errors'])

except requests.exceptions.RequestException as e:
    print(f"リクエストエラーが発生しました: {e}")
except json.JSONDecodeError:
    print("APIからのレスポンスがJSON形式ではありませんでした。")
except KeyError:
    print("APIからのレスポンスの形式が予期したものと異なります。")


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

