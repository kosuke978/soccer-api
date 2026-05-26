from __future__ import annotations

from pydantic import BaseModel


class TeamSummary(BaseModel):
    id: int
    name: str


class GroupSummary(BaseModel):
    group: str
    teams: list[str]


class MatchSummary(BaseModel):
    id: int
    stage: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    date: str
    stadium: str | None = None
