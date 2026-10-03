"""Scenario engine: compares irrigation plans against one water account."""
from __future__ import annotations

from engine.water_engine import MM_HA_TO_M3

# A plan delivering less than this share of net need is flagged as stress risk.
STRESS_TOLERANCE = 0.95


def evaluate_scenario(name: str, irrigation_mm: float, account: dict, area_ha: float) -> dict:
    """Gross irrigation applied (mm) -> volume, groundwater share and stress check."""
    if irrigation_mm < 0:
        raise ValueError("Irrigation depth cannot be negative.")
    if area_ha <= 0:
        raise ValueError("Area must be greater than zero.")

    volume_m3 = irrigation_mm * area_ha * MM_HA_TO_M3
    surface_m3 = min(account["surface_water_m3"], volume_m3)
    groundwater_m3 = max(0.0, volume_m3 - surface_m3)

    delivered_net_mm = irrigation_mm * account["application_efficiency"]
    needed_net_mm = account["net_irrigation_mm"]
    deficit_mm = max(0.0, needed_net_mm - delivered_net_mm)
    stress_risk = delivered_net_mm < needed_net_mm * STRESS_TOLERANCE

    return {
        "name": name,
        "irrigation_mm": irrigation_mm,
        "volume_m3": volume_m3,
        "surface_water_m3": surface_m3,
        "groundwater_m3": groundwater_m3,
        "groundwater_dependency_pct": (groundwater_m3 / volume_m3 * 100.0) if volume_m3 > 0 else 0.0,
        "delivered_net_mm": delivered_net_mm,
        "deficit_mm": deficit_mm,
        "stress_risk": stress_risk,
    }


def compare_scenarios(scenarios: list[tuple[str, float]], account: dict, area_ha: float) -> list[dict]:
    """Evaluate scenarios; the first is the baseline for differences."""
    if not scenarios:
        raise ValueError("At least one scenario is required.")

    rows = [evaluate_scenario(n, mm, account, area_ha) for n, mm in scenarios]
    base = rows[0]
    for row in rows:
        diff = base["groundwater_m3"] - row["groundwater_m3"]
        row["difference_vs_baseline_m3"] = diff
        row["difference_vs_baseline_pct"] = (
            diff / base["groundwater_m3"] * 100.0 if base["groundwater_m3"] > 0 else 0.0
        )
    return rows


def recommend(rows: list[dict]) -> dict | None:
    """Lowest-groundwater scenario that avoids modelled crop-water stress."""
    safe = [r for r in rows if not r["stress_risk"]]
    return min(safe, key=lambda r: r["groundwater_m3"]) if safe else None
