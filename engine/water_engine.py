def calculate_water_account(
    eto_mm: float,
    kc: float,
    effective_rain_mm: float,
    soil_water_contribution_mm: float,
    application_efficiency: float,
    area_ha: float,
    surface_water_m3: float,
) -> dict:
    """
    Transparent prototype water-account calculation.

    Units:
      - depths: mm
      - area: hectares
      - volumes: m³

    1 mm over 1 hectare = 10 m³.
    """
    if eto_mm < 0:
        raise ValueError("ETo cannot be negative.")
    if kc < 0:
        raise ValueError("Kc cannot be negative.")
    if not 0 < application_efficiency <= 1:
        raise ValueError("Application efficiency must be between 0 and 1.")
    if area_ha <= 0:
        raise ValueError("Farm area must be greater than zero.")
    if surface_water_m3 < 0:
        raise ValueError("Surface-water contribution cannot be negative.")

    etc_mm = eto_mm * kc

    net_irrigation_mm = max(
        0.0,
        etc_mm - max(0.0, effective_rain_mm) - max(0.0, soil_water_contribution_mm),
    )

    gross_irrigation_mm = net_irrigation_mm / application_efficiency
    gross_volume_m3 = gross_irrigation_mm * area_ha * 10.0

    surface_water_m3 = min(surface_water_m3, gross_volume_m3)
    groundwater_m3 = max(0.0, gross_volume_m3 - surface_water_m3)

    groundwater_dependency_pct = (
        groundwater_m3 / gross_volume_m3 * 100.0
        if gross_volume_m3 > 0
        else 0.0
    )

    groundwater_fraction = (
        groundwater_m3 / gross_volume_m3
        if gross_volume_m3 > 0
        else 0.0
    )

    return {
        "eto_mm": eto_mm,
        "kc": kc,
        "etc_mm": etc_mm,
        "effective_rain_mm": effective_rain_mm,
        "soil_water_contribution_mm": soil_water_contribution_mm,
        "net_irrigation_mm": net_irrigation_mm,
        "application_efficiency": application_efficiency,
        "gross_irrigation_mm": gross_irrigation_mm,
        "gross_volume_m3": gross_volume_m3,
        "surface_water_m3": surface_water_m3,
        "groundwater_m3": groundwater_m3,
        "groundwater_dependency_pct": groundwater_dependency_pct,
        "groundwater_fraction": groundwater_fraction,
    }

def compare_scenarios(
    baseline_mm: float,
    aquaguard_mm: float,
    area_ha: float,
    groundwater_fraction: float,
) -> dict:
    """Compare two irrigation plans using the same groundwater fraction."""
    if min(baseline_mm, aquaguard_mm, area_ha, groundwater_fraction) < 0:
        raise ValueError("Scenario inputs cannot be negative.")
    if area_ha <= 0:
        raise ValueError("Area must be greater than zero.")
    if groundwater_fraction > 1:
        raise ValueError("Groundwater fraction must be between 0 and 1.")

    baseline_volume = baseline_mm * area_ha * 10.0
    aquaguard_volume = aquaguard_mm * area_ha * 10.0

    baseline_groundwater = baseline_volume * groundwater_fraction
    aquaguard_groundwater = aquaguard_volume * groundwater_fraction

    potential_saving = max(0.0, baseline_groundwater - aquaguard_groundwater)
    saving_pct = (
        potential_saving / baseline_groundwater * 100.0
        if baseline_groundwater > 0
        else 0.0
    )

    return {
        "baseline_mm": baseline_mm,
        "aquaguard_mm": aquaguard_mm,
        "baseline_volume_m3": baseline_volume,
        "aquaguard_volume_m3": aquaguard_volume,
        "baseline_groundwater_m3": baseline_groundwater,
        "aquaguard_groundwater_m3": aquaguard_groundwater,
        "potential_saving_m3": potential_saving,
        "potential_saving_pct": saving_pct,
    }
