# World Cup 2026 Hub

FastAPI で動く World Cup 2026 向けの Web ページと API です。LINE Bot は廃止し、ローカル JSON データのみで大会情報・グループ・試合日程を提供します。

## データ

`data/world_cup_2026/` に以下の JSON を配置しています。

- `tournament.json`
- `teams.json` (48 teams)
- `groups.json` (A-L)
- `matches.json` (104 matches)

ノックアウトは `home_slot` / `away_slot` を使ってプレースホルダーで表現しています。

## 必要な環境変数

`.env` に以下を設定できます（任意）。

```env
WORLD_CUP_DATA_DIR=./data/world_cup_2026
WORLD_CUP_YEAR=2026
DISPLAY_TZ_OFFSET=9
```

## 起動

```powershell
pip install -r requirement.txt
uvicorn app.main:app --reload
```

## Web UI

`http://localhost:8000/` を開くと、グループ・今後の試合・検索が確認できます。

## API

- `GET /api/overview`
- `GET /api/teams`
- `GET /api/teams?query=Japan`
- `GET /api/teams?group=A`
- `GET /api/teams/{team_id}`
- `GET /api/teams/{team_id}/matches`
- `GET /api/groups`
- `GET /api/matches?stage=Group&group=A`
