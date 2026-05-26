from __future__ import annotations

import os
from datetime import timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(
    os.getenv(
        "WORLD_CUP_DATA_DIR",
        BASE_DIR / "data" / "world_cup_2026",
    )
)
TOURNAMENT_YEAR = int(os.getenv("WORLD_CUP_YEAR", "2026"))
DISPLAY_TZ_OFFSET = int(os.getenv("DISPLAY_TZ_OFFSET", "9"))
DISPLAY_TIMEZONE = timezone(timedelta(hours=DISPLAY_TZ_OFFSET))
APP_TITLE = os.getenv("APP_TITLE", "World Cup 2026 Hub")
