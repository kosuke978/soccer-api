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

API_KEY=os.environ["SOCCER_API_KEY"]

TEAM_ID=42
LEAGUE_ID=39
SEASON=2022

def fetch_and_display_fixtures(team_id, league_id, season):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_KEY}
    params = {'league': league_id, 'season': season, 'team': team_id}
    messages = []

    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()

        if data['results'] > 0:
            fixtures = data['response']
            sorted_fixtures = sorted(fixtures, key=lambda x: x['fixture']['date'])

            for fixture in sorted_fixtures:
                fixture_date_utc = datetime.fromisoformat(fixture['fixture']['date'].replace("Z", "+00:00"))
                fixture_date_jst = fixture_date_utc.strftime('%Y-%m-%d %H:%M')

                home_team = fixture['teams']['home']['name']
                away_team = fixture['teams']['away']['name']
                home_goals = fixture['goals']['home']
                away_goals = fixture['goals']['away']
                status = fixture['fixture']['status']['long']

                if status == "Match Finished":
                    result = f"{fixture_date_jst} JST\n{home_team} {home_goals} - {away_goals} {away_team}"
                else:
                    result = f"{fixture_date_jst} JST\n{home_team} vs {away_team}（{status}）"

                messages.append(result)

        else:
            messages.append("指定されたシーズンの試合データが見つかりませんでした。")
            if data.get('errors'):
                messages.append(f"APIエラー: {data['errors']}")

    except requests.exceptions.RequestException as e:
        messages.append(f"リクエストエラー: {e}")
    except json.JSONDecodeError:
        messages.append("APIからのレスポンスがJSON形式ではありませんでした。")
    except KeyError:
        messages.append("APIからのレスポンスの形式が予期したものと異なります。")

    return "\n\n".join(messages[:5])  # 直近5試合だけ返す（多すぎ防止）

        
fetch_and_display_fixtures(team_id=42, league_id=39, season=2022)


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
        image_url = "https://blogger.googleusercontent.com/img/sports_referee_var_pose.png"
        reply = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    elif message_text in ["試合", "試合結果", "fixture", "results"]:
        fixture_text = fetch_and_display_fixtures(team_id=TEAM_ID, league_id=LEAGUE_ID, season=SEASON)
        reply = TextSendMessage(text=fixture_text)
    else:
        reply = TextSendMessage(text="「おはよう」「画像」「試合」などを送ってみてください。")

    try:
        LINE_BOT_API.reply_message(event.reply_token, reply)
    except Exception as e:
        print(f"Error sending message: {e}")


