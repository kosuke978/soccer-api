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

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")
SOCCER_API_KEY = os.environ.get("SOCCER_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN,CHANNEL_SECRET,SOCCER_API_KEY]):
    print("エラー：必要な環境変数が設定されていません。")
    exit()


# LINE BOT APIの初期化
LINE_BOT_API = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

TEAM_NAME_MAP = {
    "アーセナル": "Arsenal",
    "マンチェスターシティ": "Manchester City",
    "マンシティ": "Manchester City",
    "マンチェスターユナイテッド": "Manchester United",
    "マンU": "Manchester United",
    "リバプール": "Liverpool",
    "チェルシー": "Chelsea",
    "トッテナム": "Tottenham",
    "レアル": "Real Madrid",
    "レアルマドリード": "Real Madrid",
    "バルセロナ": "Barcelona",
    "バルサ": "Barcelona",
    "アトレティコ": "Atletico Madrid",
    "バイエルン": "Bayern Munich",
    "ドルトムント": "Dortmund",
    "psg": "PSG",
    "パリサンジェルマン": "PSG",
    "インテル": "Inter",
    "ミラン": "AC Milan",
    "ユベントス": "Juventus",
    "ガンバ大阪": "Gamba Osaka",
    "ヴィッセル神戸": "Vissel Kobe",
    "浦和レッズ": "Urawa Red Diamonds",
}

def get_team_id(team_name: str) -> int | None:
    
    url = "https://v3.football.api-sports.io/teams"
    headers = {'x-apisports-key': SOCCER_API_KEY}
    params = {'name': team_name}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['results'] > 0:
            team_id = data['response'][0]['team']['id']
            found_name =data['response'][0]['team']['name']
            print(f"チームが見つかりました: '{found_name}' (ID: {team_id})")
            return team_id
        return None
    except requests.exceptions.RequestException as e:
        print(f"チームID検索中にエラー: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"チームID検索中にエラー: {e}")
        return None
    
def get_fixtures_by_team(team_id: int, season: int) -> str:
    """
    指定されたチームIDとシーズンの試合結果を取得して、整形された文字列を返す
    """
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': SOCCER_API_KEY}
    # リーグIDを削除し、チームIDとシーズンだけで検索（全コンペティションが対象になる）
    params = {'season': season, 'team': team_id}
    
    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()

        if data['results'] == 0:
            return "このチームの試合データは見つかりませんでした。"
        
        fixtures = data['response']
        sorted_fixtures = sorted(fixtures, key=lambda x: x['fixture']['date'])
        
        # 返信用のメッセージリスト
        messages = []
        for fixture in sorted_fixtures:
            fixture_date_utc = datetime.fromisoformat(fixture['fixture']['date'].replace("Z", "+00:00"))
            fixture_date_jst = fixture_date_utc.strftime('%Y-%m-%d %H:%M')
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            
            if fixture['fixture']['status']['long'] == "Match Finished":
                home_goals = fixture['goals']['home']
                away_goals = fixture['goals']['away']
                result = f"{fixture_date_jst}\n{home_team} {home_goals} - {away_goals} {away_team}"
            else:
                result = f"{fixture_date_jst}\n{home_team} vs {away_team}"
            
            messages.append(result)
        
        # メッセージが長くなりすぎないように最新5件などに制限する
        if len(messages) > 10:
             return "【最近の試合結果】\n\n" + "\n\n".join(messages[-10:]) # 直近10件
        else:
             return "【試合結果】\n\n" + "\n\n".join(messages)

    except requests.exceptions.HTTPError as e:
        return f"APIエラーが発生しました (HTTP {e.response.status_code})。キーが有効か確認してください。"
    except Exception as e:
        return f"試合結果の取得中にエラーが発生しました: {e}"    
    

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
    user_text = event.message.text.strip()
    
    # ユーザー入力を小文字に変換して、辞書に存在するかチェック
    search_name_lower = user_text.lower()
    
    # 英語名に変換
    team_name_en = TEAM_NAME_MAP.get(search_name_lower, user_text) # 辞書になければ元のテキストを使用
    
    # チームIDを検索
    team_id = get_team_id(team_name_en)
    
    if team_id:
        # 2024年6月現在は、2023-24シーズンが直近なので2023を指定
        # 必要に応じて、現在の年を取得するように変更可能
        season = 2024
        reply_text = get_fixtures_by_team(team_id=team_id, season=season)
    else:
        reply_text = f"「{user_text}」というチームは見つかりませんでした。\n英語名（例: Arsenal）や、よく使われる通称でお試しください。"

    try:
        LINE_BOT_API.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    except Exception as e:
        print(f"メッセージの返信中にエラー: {e}")
