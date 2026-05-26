# World Cup 2026 Hub

FastAPI and Jinja2 application for a trusted World Cup 2026 data hub.

The project separates raw official data from derived or experimental layers so
the UI and API do not present guesses as confirmed tournament facts.

## Data Model

`data/world_cup_2026/` contains:

- `tournament.json`: official tournament metadata and format.
- `teams.json`: 48 official group-stage teams.
- `groups.json`: official Group A-L membership.
- `matches.json`: 104-match catalog. Group/team membership is derived from
  official groups; unverified kickoff and venue fields remain `null`.
- `storylines.json`: derived editorial context for richer app experiences.

Each trusted record carries:

- `data_tier`: `official`, `derived`, or `experimental`
- `certainty`: `official`, `derived`, or `experimental`
- `source`
- `source_url`
- `last_verified_at`

## Configuration

Optional `.env` values:

```env
WORLD_CUP_DATA_DIR=./data/world_cup_2026
WORLD_CUP_YEAR=2026
DISPLAY_TZ_OFFSET=9
APP_TITLE=World Cup 2026 Hub
```

## Run

```powershell
pip install -r requirement.txt
uvicorn app.main:app --reload
```

or:

```powershell
python main.py
```

## Web UI

- `/`: tournament overview, official groups, and derived match catalog
- `/teams/{team_id}`: team detail
- `/matches/{match_id}`: match detail

## API

- `GET /api/tournament/overview`
- `GET /api/teams`
- `GET /api/groups`
- `GET /api/matches`
- `GET /api/matches/{match_id}`
- `GET /api/storylines`
- `GET /api/predictions`
- `GET /api/analytics/group-strength`

## Test

```powershell
python -m pytest
```
