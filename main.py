from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, Query, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from starlette.exceptions import HTTPException

load_dotenv()

app = FastAPI(title="Soccer Results Bot")

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")
DEFAULT_SEASON = int(os.environ.get("SOCCER_SEASON", "2024"))
DATA_FILE = Path(__file__).with_name("soccer_data.json")
JST = timezone(timedelta(hours=9))

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET]):
    print("Error: CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET are required.")
    raise SystemExit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().strip().split())


class SoccerRepository:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self._data = self._load_data()
        self._teams_by_id = {
            int(team["id"]): team for team in self._data.get("teams", [])
        }

    def _load_data(self) -> dict[str, Any]:
        with self.data_file.open(encoding="utf-8") as file:
            return json.load(file)

    def list_teams(self, query: str | None = None) -> list[dict[str, Any]]:
        teams = self._data.get("teams", [])
        if not query:
            return teams

        normalized_query = normalize_text(query)
        return [
            team
            for team in teams
            if self._team_matches(team, normalized_query)
        ]

    def get_team(self, team_id: int) -> dict[str, Any] | None:
        return self._teams_by_id.get(team_id)

    def find_team(self, query: str) -> dict[str, Any] | None:
        normalized_query = normalize_text(query)
        exact_matches = [
            team
            for team in self._data.get("teams", [])
            if self._team_matches(team, normalized_query, exact=True)
        ]
        if exact_matches:
            return exact_matches[0]

        partial_matches = self.list_teams(query)
        return partial_matches[0] if partial_matches else None

    def list_fixtures(
        self,
        team_id: int,
        season: int | None = None,
    ) -> list[dict[str, Any]]:
        fixtures = []
        for fixture in self._data.get("fixtures", []):
            if season is not None and int(fixture["season"]) != season:
                continue
            if team_id in [int(fixture["home_team_id"]), int(fixture["away_team_id"])]:
                fixtures.append(fixture)

        return sorted(fixtures, key=lambda fixture: fixture["date"])

    def _team_matches(
        self,
        team: dict[str, Any],
        normalized_query: str,
        exact: bool = False,
    ) -> bool:
        candidates = [team["name"], *team.get("aliases", [])]
        normalized_candidates = [normalize_text(candidate) for candidate in candidates]
        if exact:
            return normalized_query in normalized_candidates

        return any(
            normalized_query in candidate or candidate in normalized_query
            for candidate in normalized_candidates
        )


repository = SoccerRepository(DATA_FILE)


def format_fixture(fixture: dict[str, Any]) -> str:
    fixture_date = datetime.fromisoformat(
        fixture["date"].replace("Z", "+00:00")
    ).astimezone(JST)
    formatted_date = fixture_date.strftime("%Y-%m-%d %H:%M")
    home_team = repository.get_team(int(fixture["home_team_id"]))
    away_team = repository.get_team(int(fixture["away_team_id"]))

    home_name = home_team["name"] if home_team else fixture["home_team_id"]
    away_name = away_team["name"] if away_team else fixture["away_team_id"]

    if fixture["status"] == "finished":
        return (
            f"{formatted_date}\n"
            f"{home_name} {fixture['home_goals']} - {fixture['away_goals']} {away_name}"
        )

    return f"{formatted_date}\n{home_name} vs {away_name}"


def format_fixtures_for_reply(team_name: str, fixtures: list[dict[str, Any]]) -> str:
    if not fixtures:
        return f"{team_name} の試合データは見つかりませんでした。"

    latest_fixtures = fixtures[-10:]
    fixture_text = "\n\n".join(format_fixture(fixture) for fixture in latest_fixtures)
    return f"【{team_name} 試合結果】\n\n{fixture_text}"


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Soccer Results Bot is running"}


@app.get("/api/teams")
def list_teams(
    query: str | None = Query(default=None, description="Team name or alias"),
) -> dict[str, Any]:
    teams = repository.list_teams(query)
    return {"results": len(teams), "teams": teams}


@app.get("/api/teams/{team_id}")
def get_team(team_id: int) -> dict[str, Any]:
    team = repository.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.get("/api/teams/{team_id}/fixtures")
def list_team_fixtures(
    team_id: int,
    season: int | None = Query(default=None),
) -> dict[str, Any]:
    if repository.get_team(team_id) is None:
        raise HTTPException(status_code=404, detail="Team not found")

    fixtures = repository.list_fixtures(team_id=team_id, season=season)
    return {"results": len(fixtures), "fixtures": fixtures}


@app.post("/callback")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None),
) -> dict[str, str]:
    body = await request.body()
    try:
        background_tasks.add_task(
            handler.handle,
            body.decode("utf-8"),
            x_line_signature,
        )
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return {"status": "ok"}


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent) -> None:
    user_text = event.message.text.strip()
    team = repository.find_team(user_text)

    if team:
        fixtures = repository.list_fixtures(
            team_id=int(team["id"]),
            season=DEFAULT_SEASON,
        )
        reply_text = format_fixtures_for_reply(team["name"], fixtures)
    else:
        reply_text = (
            f"「{user_text}」というチームは見つかりませんでした。\n"
            "英語名、正式名、またはよく使われる略称で試してください。"
        )

    try:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    except Exception as exc:
        print(f"Error while replying to LINE message: {exc}")
