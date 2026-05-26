from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.config import DATA_DIR
from app.data.repository import (
    WorldCupRepository,
    get_repository,
    parse_iso_datetime,
)

router = APIRouter(prefix="/api")
repository: WorldCupRepository = get_repository(DATA_DIR)


def slot_label(slot: str) -> str:
    if slot.startswith("Best3rd-"):
        _, ordinal = slot.split("-", maxsplit=1)
        return f"Best 3rd {ordinal}"
    if slot.startswith("W-"):
        return f"Winner {slot[2:]}"
    if slot.startswith("L-"):
        return f"Loser {slot[2:]}"
    if len(slot) == 2 and slot[0].isalpha() and slot[1].isdigit():
        group = slot[0].upper()
        rank = slot[1]
        suffix = "th"
        if rank == "1":
            suffix = "st"
        elif rank == "2":
            suffix = "nd"
        elif rank == "3":
            suffix = "rd"
        return f"Group {group} {rank}{suffix}"
    return slot


def resolve_team(match: dict[str, Any], side: str) -> dict[str, Any]:
    team_id = match.get(f"{side}_team_id")
    if team_id is not None:
        team = repository.get_team(int(team_id))
        if team:
            return {"id": team["id"], "name": team["name"]}
    slot = match.get(f"{side}_slot")
    if slot:
        return {"id": None, "name": slot_label(slot)}
    return {"id": None, "name": "TBD"}


def serialize_match(match: dict[str, Any]) -> dict[str, Any]:
    group_id = match.get("group")
    group_name = None
    if group_id:
        group = repository.get_group(group_id)
        group_name = group["name"] if group else None
    return {
        "id": match["id"],
        "stage": match.get("stage"),
        "group": group_id,
        "group_name": group_name,
        "matchday": match.get("matchday"),
        "date": match["date"],
        "venue": match.get("venue"),
        "status": match.get("status"),
        "home_goals": match.get("home_goals"),
        "away_goals": match.get("away_goals"),
        "home": resolve_team(match, "home"),
        "away": resolve_team(match, "away"),
    }


def serialize_team(team: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": team["id"],
        "name": team["name"],
        "confederation": team.get("confederation"),
    }


@router.get("/overview")
def get_overview() -> dict[str, Any]:
    tournament = repository.get_tournament()
    groups = []
    for group in repository.list_groups():
        teams = [repository.get_team(int(team_id)) for team_id in group["teams"]]
        groups.append(
            {
                "id": group["id"],
                "name": group["name"],
                "teams": [serialize_team(team) for team in teams if team],
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

    upcoming_sorted = sorted(
        upcoming,
        key=lambda match: parse_iso_datetime(match["date"]),
    )[:8]
    recent_sorted = sorted(
        recent,
        key=lambda match: parse_iso_datetime(match["date"]),
        reverse=True,
    )[:8]

    return {
        "tournament": tournament,
        "groups": groups,
        "upcoming_matches": [serialize_match(match) for match in upcoming_sorted],
        "recent_results": [serialize_match(match) for match in recent_sorted],
    }


@router.get("/teams")
def list_teams(
    query: str | None = Query(default=None, description="Team name or alias"),
    group: str | None = Query(default=None, description="Group id (A-L)"),
) -> dict[str, Any]:
    teams = repository.list_teams(query=query, group=group)
    return {"results": len(teams), "teams": [serialize_team(team) for team in teams]}


@router.get("/teams/{team_id}")
def get_team(team_id: int) -> dict[str, Any]:
    team = repository.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/teams/{team_id}/matches")
def get_team_matches(
    team_id: int,
    stage: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    if repository.get_team(team_id) is None:
        raise HTTPException(status_code=404, detail="Team not found")
    matches = repository.list_matches(team_id=team_id, stage=stage, status=status)
    return {
        "results": len(matches),
        "matches": [serialize_match(match) for match in matches],
    }


@router.get("/groups")
def list_groups() -> dict[str, Any]:
    groups = []
    for group in repository.list_groups():
        teams = [repository.get_team(int(team_id)) for team_id in group["teams"]]
        groups.append(
            {
                "id": group["id"],
                "name": group["name"],
                "teams": [serialize_team(team) for team in teams if team],
            }
        )
    return {"results": len(groups), "groups": groups}


@router.get("/matches")
def list_matches(
    stage: str | None = Query(default=None),
    group: str | None = Query(default=None),
    team_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
) -> dict[str, Any]:
    matches = repository.list_matches(
        team_id=team_id,
        group=group,
        stage=stage,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    return {
        "results": len(matches),
        "matches": [serialize_match(match) for match in matches],
    }
