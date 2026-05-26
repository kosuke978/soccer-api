from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.utils import normalize_text, parse_iso_datetime, slot_label
from app.data.loader import load_json


class WorldCupRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._tournament = load_json(data_dir, "tournament.json")
        self._teams = load_json(data_dir, "teams.json")
        self._groups = load_json(data_dir, "groups.json")
        self._matches = load_json(data_dir, "matches.json")
        self._teams_by_id = {int(team["id"]): team for team in self._teams}
        self._groups_by_id = {
            group["id"].upper(): group for group in self._groups
        }
        self._matches_by_id = {
            int(match["id"]): match for match in self._matches
        }

    def get_tournament(self) -> dict[str, Any]:
        return self._tournament

    def list_teams(
        self,
        query: str | None = None,
        group: str | None = None,
    ) -> list[dict[str, Any]]:
        teams = self._teams
        if group:
            group_entry = self._groups_by_id.get(group.upper())
            if not group_entry:
                return []
            allowed_ids = {int(team_id) for team_id in group_entry["teams"]}
            teams = [team for team in teams if int(team["id"]) in allowed_ids]

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

    def list_groups(self) -> list[dict[str, Any]]:
        return self._groups

    def get_group(self, group_id: str) -> dict[str, Any] | None:
        return self._groups_by_id.get(group_id.upper())

    def get_group_for_team(self, team_id: int) -> dict[str, Any] | None:
        for group in self._groups:
            if int(team_id) in {int(team) for team in group["teams"]}:
                return group
        return None

    def list_matches(
        self,
        *,
        team_id: int | None = None,
        group: str | None = None,
        stage: str | None = None,
        status: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[dict[str, Any]]:
        matches = self._matches
        if team_id is not None:
            matches = [
                match
                for match in matches
                if team_id
                in [match.get("home_team_id"), match.get("away_team_id")]
            ]
        if group:
            matches = [
                match
                for match in matches
                if match.get("group") == group.upper()
            ]
        if stage:
            normalized_stage = stage.casefold()
            matches = [
                match
                for match in matches
                if match.get("stage", "").casefold() == normalized_stage
            ]
        if status:
            normalized_status = status.casefold()
            matches = [
                match
                for match in matches
                if match.get("status", "").casefold() == normalized_status
            ]

        if from_date or to_date:
            from_dt = parse_iso_datetime(from_date) if from_date else None
            to_dt = parse_iso_datetime(to_date) if to_date else None

            def within_range(match: dict[str, Any]) -> bool:
                match_dt = parse_iso_datetime(match["date"])
                if from_dt and match_dt < from_dt:
                    return False
                if to_dt and match_dt > to_dt:
                    return False
                return True

            matches = [match for match in matches if within_range(match)]

        return sorted(matches, key=lambda match: parse_iso_datetime(match["date"]))

    def get_match(self, match_id: int) -> dict[str, Any] | None:
        return self._matches_by_id.get(match_id)

    def resolve_team_reference(self, match: dict[str, Any], side: str) -> dict[str, Any]:
        team_id = match.get(f"{side}_team_id")
        if team_id is not None:
            team = self.get_team(int(team_id))
            if team:
                return {"id": team["id"], "name": team["name"]}
        slot = match.get(f"{side}_slot")
        if slot:
            return {"id": None, "name": slot_label(slot)}
        return {"id": None, "name": "TBD"}

    def _team_matches(
        self,
        team: dict[str, Any],
        normalized_query: str,
    ) -> bool:
        candidates = [team["name"], *team.get("aliases", [])]
        normalized_candidates = [normalize_text(candidate) for candidate in candidates]
        return any(
            normalized_query in candidate or candidate in normalized_query
            for candidate in normalized_candidates
        )


_repository: WorldCupRepository | None = None


def get_repository(data_dir: Path) -> WorldCupRepository:
    global _repository
    if _repository is None or _repository.data_dir != data_dir:
        _repository = WorldCupRepository(data_dir)
    return _repository
