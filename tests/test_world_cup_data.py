from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import DATA_DIR
from app.data.repository import get_repository
from app.main import app


repository = get_repository(DATA_DIR)
client = TestClient(app)


def test_official_group_field_is_complete() -> None:
    teams = repository.list_teams()
    groups = repository.list_groups()

    assert len(teams) == 48
    assert len(groups) == 12
    assert {group["id"] for group in groups} == set("ABCDEFGHIJKL")
    assert all(len(group["teams"]) == 4 for group in groups)
    assert all(team["data_tier"] == "official" for team in teams)
    assert all(group["certainty"] == "official" for group in groups)


def test_match_catalog_counts_and_references_are_valid() -> None:
    teams = {team["id"] for team in repository.list_teams()}
    matches = repository.list_matches()
    group_matches = [match for match in matches if match["stage"] == "Group"]

    assert len(matches) == 104
    assert len(group_matches) == 72
    assert len([match for match in matches if match["stage"] != "Group"]) == 32

    for match in group_matches:
        assert match["home_team_id"] in teams
        assert match["away_team_id"] in teams
        assert match["data_tier"] == "derived"
        assert match["certainty"] == "derived"


def test_source_metadata_exists_for_trusted_records() -> None:
    records = [
        repository.get_tournament(),
        *repository.list_teams(),
        *repository.list_groups(),
        *repository.list_matches(),
    ]

    for record in records:
        assert record["source_url"].startswith("https://www.fifa.com/")
        assert record["last_verified_at"]
        assert record["certainty"] in {"official", "derived", "experimental"}


def test_groups_api_returns_nested_team_metadata() -> None:
    response = client.get("/api/groups")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 12
    assert payload[0]["group"] == "A"
    assert payload[0]["meta"]["certainty"] == "official"
    assert payload[0]["teams"][0]["name"] == "Mexico"


def test_matches_api_filters_by_group_and_team() -> None:
    group_response = client.get("/api/matches?group=F")
    team_response = client.get("/api/matches?team=22")

    assert group_response.status_code == 200
    assert len(group_response.json()) == 6
    assert all(match["group"] == "F" for match in group_response.json())

    assert team_response.status_code == 200
    assert len(team_response.json()) == 3
    assert all(
        "Japan" in {match["home_team"], match["away_team"]}
        for match in team_response.json()
    )


def test_experimental_predictions_are_not_returned_as_official() -> None:
    response = client.get("/api/predictions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "planned"
    assert payload["data_tier"] == "experimental"
    assert payload["certainty"] == "experimental"
