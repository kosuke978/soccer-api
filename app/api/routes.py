from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    FeatureStatus,
    GroupStrengthSummary,
    GroupSummary,
    MatchSummary,
    SourceMeta,
    StorylineSummary,
    TeamSummary,
    TournamentOverview,
)
from app.core.config import DATA_DIR
from app.data.repository import WorldCupRepository, get_repository

router = APIRouter(prefix="/api")
repository: WorldCupRepository = get_repository(DATA_DIR)


def serialize_meta(entry: dict[str, Any]) -> SourceMeta:
    return SourceMeta(
        data_tier=entry.get("data_tier"),
        certainty=entry.get("certainty"),
        source=entry.get("source"),
        source_url=entry.get("source_url"),
        last_verified_at=entry.get("last_verified_at"),
    )


def serialize_team(team: dict[str, Any]) -> TeamSummary:
    return TeamSummary(
        id=int(team["id"]),
        code=team.get("code"),
        name=team["name"],
        confederation=team.get("confederation"),
        meta=serialize_meta(team),
    )


def serialize_match(match: dict[str, Any]) -> MatchSummary:
    home = repository.resolve_team_reference(match, "home")
    away = repository.resolve_team_reference(match, "away")
    return MatchSummary(
        id=int(match["id"]),
        stage=match.get("stage"),
        group=match.get("group"),
        home_team=home["name"],
        away_team=away["name"],
        date=match.get("date"),
        stadium=match.get("venue"),
        city=match.get("city"),
        status=match.get("status"),
        meta=serialize_meta(match),
    )


@router.get("/tournament/overview", response_model=TournamentOverview)
def tournament_overview() -> TournamentOverview:
    overview = repository.get_tournament_overview()
    return TournamentOverview(
        name=overview["name"],
        year=int(overview["year"]),
        host_countries=overview["host_countries"],
        start_date=overview["start_date"],
        end_date=overview["end_date"],
        description=overview.get("description"),
        format=overview.get("format", {}),
        counts=overview["counts"],
        meta=serialize_meta(overview),
    )


@router.get("/teams", response_model=list[TeamSummary])
def list_teams(
    query: str | None = Query(default=None, description="Team name or alias"),
    group: str | None = Query(default=None, description="Group id (A-L)"),
) -> list[TeamSummary]:
    teams = repository.list_teams(query=query, group=group)
    return [serialize_team(team) for team in teams]


@router.get("/groups", response_model=list[GroupSummary])
def list_groups() -> list[GroupSummary]:
    groups: list[GroupSummary] = []
    for group in repository.list_groups():
        teams = []
        for team_id in group["teams"]:
            team = repository.get_team(int(team_id))
            if team:
                teams.append(serialize_team(team))
        groups.append(
            GroupSummary(
                group=group["id"],
                teams=teams,
                meta=serialize_meta(group),
            )
        )
    return groups


@router.get("/matches", response_model=list[MatchSummary])
def list_matches(
    stage: str | None = Query(default=None),
    group: str | None = Query(default=None),
    team: int | None = Query(default=None, description="Team id"),
    city: str | None = Query(default=None),
    date: str | None = Query(default=None, description="Single-day ISO date"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
) -> list[MatchSummary]:
    matches = repository.list_matches(
        team_id=team,
        stage=stage,
        group=group,
        city=city,
        from_date=date or from_date,
        to_date=date or to_date,
    )
    return [serialize_match(match) for match in matches]


@router.get("/matches/{match_id}", response_model=MatchSummary)
def get_match(match_id: int) -> MatchSummary:
    match = repository.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return serialize_match(match)


@router.get("/storylines", response_model=list[StorylineSummary])
def list_storylines() -> list[StorylineSummary]:
    return [
        StorylineSummary(
            id=storyline["id"],
            title=storyline["title"],
            summary=storyline["summary"],
            related_groups=storyline.get("related_groups", []),
            related_team_codes=storyline.get("related_team_codes", []),
            meta=serialize_meta(storyline),
        )
        for storyline in repository.list_storylines()
    ]


@router.get("/predictions", response_model=FeatureStatus)
def predictions_status() -> FeatureStatus:
    return FeatureStatus(
        status="planned",
        data_tier="experimental",
        certainty="experimental",
        message=(
            "Prediction models are intentionally not enabled until a transparent "
            "input dataset and evaluation method are added."
        ),
    )


@router.get(
    "/analytics/group-strength",
    response_model=list[GroupStrengthSummary],
)
def group_strength() -> list[GroupStrengthSummary]:
    return [
        GroupStrengthSummary(
            group=item["group"],
            teams=item["teams"],
            confederations=item["confederations"],
            confederation_count=int(item["confederation_count"]),
            meta=serialize_meta(item),
        )
        for item in repository.list_group_strength()
    ]
