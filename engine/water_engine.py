"""Transparent water-accounting engine. No language model is involved here.

Units: depths in mm, area in hectares, volumes in m3. 1 mm over 1 ha = 10 m3.
"""
from __future__ import annotations

from datetime import date

from engine.reference_data import (
    crop_kc,
    growth_stage,
    method_efficiency,
    soil_available_water_mm,
)

MM_HA_TO_M3 = 10.0


def calculate_water_account(
    eto_mm: float,
    kc: float,
    effective_rain_mm: float,
    soil_water_contribution_mm: float,
    application_efficiency: float,
    area_ha: float,
    surface_water_m3: float,
    period_days: float = 1.0,
) -> dict:
    """Water account for a period.

    eto_mm is daily reference ET; effective_rain_mm and soil_water_contribution_mm
    are totals for the period.
    """
    if eto_mm < 0:
        raise ValueError("ETo cannot be negative.")
    if kc < 0:
        raise ValueError("Kc cannot be negative.")
    if period_days <= 0:
        raise ValueError("Period must be at least one day.")
    if not 0 < application_efficiency <= 1:
        raise ValueError("Application efficiency must be between 0 and 1.")
    if area_ha <= 0:
        raise ValueError("Farm area must be greater than zero.")
    if surface_water_m3 < 0:
        raise ValueError("Surface-water contribution cannot be negative.")

    effective_rain_mm = max(0.0, effective_rain_mm)
    soil_water_contribution_mm = max(0.0, soil_water_contribution_mm)

    etc_mm = eto_mm * kc * period_days
    net_irrigation_mm = max(0.0, etc_mm - effective_rain_mm - soil_water_contribution_mm)
    gross_irrigation_mm = net_irrigation_mm / application_efficiency
    gross_volume_m3 = gross_irrigation_mm * area_ha * MM_HA_TO_M3

    surface_used_m3 = min(surface_water_m3, gross_volume_m3)
    groundwater_m3 = max(0.0, gross_volume_m3 - surface_used_m3)

    if gross_volume_m3 > 0:
        groundwater_fraction = groundwater_m3 / gross_volume_m3
    else:
        groundwater_fraction = 0.0

    return {
        "eto_mm": eto_mm,
        "period_days": period_days,
        "kc": kc,
        "etc_mm": etc_mm,
        "effective_rain_mm": effective_rain_mm,
        "soil_water_contribution_mm": soil_water_contribution_mm,
        "net_irrigation_mm": net_irrigation_mm,
        "application_efficiency": application_efficiency,
        "gross_irrigation_mm": gross_irrigation_mm,
        "gross_volume_m3": gross_volume_m3,
        "surface_water_m3": surface_used_m3,
        "groundwater_m3": groundwater_m3,
        "groundwater_dependency_pct": groundwater_fraction * 100.0,
        "groundwater_fraction": groundwater_fraction,
    }


def account_for_farm(farm: dict, inputs: dict, on: date | None = None) -> dict:
    """Derive Kc, soil water, efficiency and rain from the farm profile and user inputs."""
    sowing = farm["sowing_date"]
    if isinstance(sowing, str):
        sowing = date.fromisoformat(sowing)

    stage, days_after_sowing = growth_stage(farm["crop"], sowing, on)
    kc = crop_kc(farm["crop"], stage)

    soil_mm = soil_available_water_mm(farm["soil"]) * inputs["soil_moisture_pct"] / 100.0
    efficiency = inputs.get("efficiency_override") or method_efficiency(
        farm["irrigation_method"]
    )
    effective_rain_mm = inputs["rain_mm"] * inputs["rain_factor"]

    result = calculate_water_account(
        eto_mm=inputs["eto_mm"],
        kc=kc,
        effective_rain_mm=effective_rain_mm,
        soil_water_contribution_mm=soil_mm,
        application_efficiency=efficiency,
        area_ha=farm["area_ha"],
        surface_water_m3=farm["canal_water_m3"],
        period_days=inputs["period_days"],
    )
    result.update(
        {
            "crop_stage": stage,
            "days_after_sowing": days_after_sowing,
            "rain_mm_total": inputs["rain_mm"],
            "rain_factor": inputs["rain_factor"],
            "soil_moisture_pct": inputs["soil_moisture_pct"],
        }
    )
    return result
