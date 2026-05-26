from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import BASE_DIR, DATA_DIR, DISPLAY_TIMEZONE
from app.core.utils import format_datetime, parse_iso_datetime
from app.data.repository import WorldCupRepository, get_repository

templates = Jinja2Templates(
    directory=str(BASE_DIR / "app" / "web" / "templates")
)
router = APIRouter()
repository: WorldCupRepository = get_repository(DATA_DIR)


def build_match_view(match: dict[str, Any]) -> dict[str, Any]:
    home = repository.resolve_team_reference(match, "home")
    away = repository.resolve_team_reference(match, "away")
    return {
        "id": match["id"],
        "stage": match.get("stage"),
        "group": match.get("group"),
        "matchday": match.get("matchday"),
        "date": format_datetime(match.get("date"), DISPLAY_TIMEZONE),
        "raw_date": match.get("date"),
        "venue": match.get("venue"),
        "status": match.get("status") or "scheduled",
        "home_goals": match.get("home_goals"),
        "away_goals": match.get("away_goals"),
        "home": home,
        "away": away,
    }


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    tournament = repository.get_tournament()
    groups = []
    for group in repository.list_groups():
        teams = []
        for team_id in group["teams"]:
            team = repository.get_team(int(team_id))
            if team:
                teams.append({"id": team["id"], "name": team["name"]})
        groups.append(
            {
                "id": group["id"],
                "name": group["name"],
                "teams": teams,
            }
        )

    matches = repository.list_matches()
    now = datetime.now(timezone.utc)
    upcoming = [
        match
        for match in matches
        if parse_iso_datetime(match["date"]) >= now
    ]
    recent = [
        match
        for match in matches
        if match.get("status") == "finished"
        and parse_iso_datetime(match["date"]) < now
    ]

    featured_matches = [build_match_view(match) for match in upcoming[:3]]
    upcoming_matches = [build_match_view(match) for match in upcoming[:8]]
    recent_matches = [
        build_match_view(match) for match in sorted(
            recent,
            key=lambda item: parse_iso_datetime(item["date"]),
            reverse=True,
        )[:8]
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tournament": tournament,
            "groups": groups,
            "featured_matches": featured_matches,
            "upcoming_matches": upcoming_matches,
            "recent_matches": recent_matches,
        },
    )


@router.get("/teams/{team_id}", response_class=HTMLResponse)
def team_detail(request: Request, team_id: int) -> HTMLResponse:
    team = repository.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    group = repository.get_group_for_team(team_id)
    matches = repository.list_matches(team_id=team_id)
    match_cards = [build_match_view(match) for match in matches]

    team_view = {
        "id": team["id"],
        "name": team["name"],
        "confederation": team.get("confederation"),
        "flag": team.get("flag_emoji", "FLAG"),
        "fifa_rank": team.get("fifa_rank"),
        "group": group["name"] if group else "未定",
    }

    return templates.TemplateResponse(
        "team.html",
        {
            "request": request,
            "team": team_view,
            "matches": match_cards,
        },
    )


@router.get("/matches/{match_id}", response_class=HTMLResponse)
def match_detail(request: Request, match_id: int) -> HTMLResponse:
    match = repository.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    match_view = build_match_view(match)
    return templates.TemplateResponse(
        "match.html",
        {
            "request": request,
            "match": match_view,
        },
    )
