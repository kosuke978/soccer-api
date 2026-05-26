from __future__ import annotations

from pydantic import BaseModel


class SourceMeta(BaseModel):
    data_tier: str | None = None
    certainty: str | None = None
    source: str | None = None
    source_url: str | None = None
    last_verified_at: str | None = None


class TeamSummary(BaseModel):
    id: int
    code: str | None = None
    name: str
    confederation: str | None = None
    meta: SourceMeta | None = None


class GroupSummary(BaseModel):
    group: str
    teams: list[TeamSummary]
    meta: SourceMeta | None = None


class MatchSummary(BaseModel):
    id: int
    stage: str | None = None
    group: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    date: str | None = None
    stadium: str | None = None
    city: str | None = None
    status: str | None = None
    meta: SourceMeta | None = None


class TournamentOverview(BaseModel):
    name: str
    year: int
    host_countries: list[str]
    start_date: str
    end_date: str
    description: str | None = None
    format: dict
    counts: dict
    meta: SourceMeta | None = None


class StorylineSummary(BaseModel):
    id: str
    title: str
    summary: str
    related_groups: list[str] = []
    related_team_codes: list[str] = []
    meta: SourceMeta | None = None


class GroupStrengthSummary(BaseModel):
    group: str
    teams: list[str]
    confederations: list[str]
    confederation_count: int
    meta: SourceMeta | None = None


class FeatureStatus(BaseModel):
    status: str
    data_tier: str
    certainty: str
    message: str
