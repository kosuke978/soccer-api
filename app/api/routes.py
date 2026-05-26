from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import GroupSummary, MatchSummary, TeamSummary
from app.core.config import DATA_DIR
from app.data.repository import WorldCupRepository, get_repository

router = APIRouter(prefix="/api")
repository: WorldCupRepository = get_repository(DATA_DIR)


def serialize_match(match: dict[str, Any]) -> MatchSummary:
    home = repository.resolve_team_reference(match, "home")
    away = repository.resolve_team_reference(match, "away")
    return MatchSummary(
        id=int(match["id"]),
        stage=match.get("stage"),
        home_team=home["name"],
        away_team=away["name"],
        date=str(match["date"]),
        stadium=match.get("venue"),
    )


@router.get("/teams", response_model=list[TeamSummary])
def list_teams(
    query: str | None = Query(default=None, description="Team name or alias"),
    group: str | None = Query(default=None, description="Group id (A-L)"),
) -> list[TeamSummary]:
    teams = repository.list_teams(query=query, group=group)
    return [TeamSummary(id=team["id"], name=team["name"]) for team in teams]


@router.get("/groups", response_model=list[GroupSummary])
def list_groups() -> list[GroupSummary]:
    groups: list[GroupSummary] = []
    for group in repository.list_groups():
        team_names = []
        for team_id in group["teams"]:
            team = repository.get_team(int(team_id))
            if team:
                team_names.append(team["name"])
        groups.append(GroupSummary(group=group["id"], teams=team_names))
    return groups


@router.get("/matches", response_model=list[MatchSummary])
def list_matches(
    stage: str | None = Query(default=None),
    group: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
) -> list[MatchSummary]:
    matches = repository.list_matches(
        stage=stage,
        group=group,
        from_date=from_date,
        to_date=to_date,
    )
    return [serialize_match(match) for match in matches]


@router.get("/matches/{match_id}", response_model=MatchSummary)
def get_match(match_id: int) -> MatchSummary:
    match = repository.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return serialize_match(match)
