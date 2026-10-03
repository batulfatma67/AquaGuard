"""Crop, soil and method reference data used to derive calculation inputs."""
from __future__ import annotations

from datetime import date
from functools import lru_cache
import json

import pandas as pd

from config import DATA_DIR

# Approximate stage lengths in days (FAO-56 style); illustrative, adjustable.
STAGE_DAYS = {
    "Wheat": [("Initial", 20), ("Development", 40), ("Mid-season", 40), ("Late-season", 30)],
    "Maize": [("Initial", 20), ("Development", 35), ("Mid-season", 40), ("Late-season", 30)],
    "Rice": [("Initial", 30), ("Development", 30), ("Mid-season", 60), ("Late-season", 30)],
    "Cotton": [("Initial", 30), ("Development", 50), ("Mid-season", 55), ("Late-season", 45)],
    "Sugarcane": [("Initial", 35), ("Development", 60), ("Mid-season", 190), ("Late-season", 120)],
}

# Typical application efficiencies by method (assumptions, not measurements).
METHOD_EFFICIENCY = {"Flood": 0.55, "Sprinkler": 0.75, "Drip": 0.90}

# Fraction of total available water that can be depleted before stress.
DEPLETION_FRACTION = 0.5


@lru_cache(maxsize=1)
def load_crops() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "crops.csv")


@lru_cache(maxsize=1)
def load_soils() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "soils.csv")


@lru_cache(maxsize=1)
def load_locations() -> dict[str, list[str]]:
    """District -> tehsils (empty list when tehsil data is not available)."""
    raw = json.loads((DATA_DIR / "pakistan_locations.json").read_text(encoding="utf-8"))
    return {d: t for districts in raw.values() for d, t in districts.items()}


def growth_stage(crop: str, sowing_date: date, on: date | None = None) -> tuple[str, int]:
    """Return (stage name, days after sowing) for the crop on a given date."""
    on = on or date.today()
    days = max(0, (on - sowing_date).days)
    stages = STAGE_DAYS.get(crop)
    if not stages:
        raise ValueError(f"No stage schedule for crop '{crop}'.")
    elapsed = 0
    for name, length in stages:
        elapsed += length
        if days < elapsed:
            return name, days
    return stages[-1][0], days


def crop_kc(crop: str, stage: str) -> float:
    """Kc for crop/stage; falls back to the nearest listed stage if the CSV omits it."""
    df = load_crops()
    rows = df[df["crop"] == crop]
    if rows.empty:
        raise ValueError(f"Crop '{crop}' is not in crops.csv.")
    exact = rows[rows["stage"] == stage]
    if not exact.empty:
        return float(exact.iloc[0]["kc"])
    order = [s for s, _ in STAGE_DAYS[crop]]
    target = order.index(stage)
    listed = [s for s in order if s in set(rows["stage"])]
    nearest = min(listed, key=lambda s: abs(order.index(s) - target))
    return float(rows[rows["stage"] == nearest].iloc[0]["kc"])


def soil_available_water_mm(soil: str) -> float:
    """Readily available soil water in the root zone (mm)."""
    df = load_soils()
    rows = df[df["soil_type"] == soil]
    if rows.empty:
        raise ValueError(f"Soil '{soil}' is not in soils.csv.")
    r = rows.iloc[0]
    taw = (r["field_capacity"] - r["wilting_point"]) * r["root_zone_depth_m"] * 1000.0
    return float(taw * DEPLETION_FRACTION)


def method_efficiency(method: str) -> float:
    return METHOD_EFFICIENCY.get(method, 0.55)
