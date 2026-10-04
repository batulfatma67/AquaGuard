"""Builds the water-account report from structured results and cited evidence."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

DISCLAIMER = (
    "AquaGuard is a prototype decision-support tool. Values are modelled estimates built "
    "from user-entered assumptions, not measurements of actual pumping or aquifer response, "
    "and require field validation before operational use."
)


def build_report_markdown(
    farm: dict,
    account: dict,
    scenarios: list[dict] | None = None,
    evidence: list[dict] | None = None,
) -> str:
    """Report text: inputs, calculations, scenarios, evidence and limitations."""
    lines = [
        "# AquaGuard Farm Water Intelligence Report",
        f"_Generated {datetime.now():%Y-%m-%d %H:%M}_",
        "",
        "## 1. Farm profile (user-entered)",
        f"- Location: {farm['district']}, {farm['tehsil']}",
        f"- Crop: {farm['crop']} ({account.get('crop_stage', 'n/a')}, "
        f"{account.get('days_after_sowing', 'n/a')} days after sowing)",
        f"- Area: {farm['area_ha']:.2f} ha",
        f"- Soil: {farm['soil']}",
        f"- Irrigation method: {farm['irrigation_method']}",
        f"- Water source: {farm['water_source']}",
        f"- Surface/canal water entered: {farm['canal_water_m3']:,.0f} m3",
        "",
        f"## 2. Water account ({account['period_days']:g}-day period, modelled)",
        "| Component | Value | Basis |",
        "|---|---|---|",
        f"| ETo | {account['eto_mm']:.2f} mm/day | user-entered |",
        f"| Kc | {account['kc']:.2f} | crops.csv, stage-based |",
        f"| ETc | {account['etc_mm']:.1f} mm | ETo x Kc x days |",
        f"| Effective rainfall | {account['effective_rain_mm']:.1f} mm | rainfall x factor (assumed) |",
        f"| Soil-water contribution | {account['soil_water_contribution_mm']:.1f} mm | soils.csv + assumed moisture |",
        f"| Net irrigation requirement | {account['net_irrigation_mm']:.1f} mm | max(0, ETc - rain - soil) |",
        f"| Application efficiency | {account['application_efficiency'] * 100:.0f}% | method default or override |",
        f"| Gross irrigation requirement | {account['gross_irrigation_mm']:.1f} mm | net / efficiency |",
        f"| Gross field volume | {account['gross_volume_m3']:,.0f} m3 | mm x ha x 10 |",
        f"| Surface-water contribution | {account['surface_water_m3']:,.0f} m3 | user-entered estimate |",
        f"| Estimated groundwater | {account['groundwater_m3']:,.0f} m3 | max(0, gross - surface) |",
        f"| Groundwater dependency | {account['groundwater_dependency_pct']:.0f}% | groundwater / gross |",
    ]

    if scenarios:
        lines += [
            "",
            "## 3. Scenario comparison (modelled)",
            "| Scenario | Irrigation (mm) | Volume (m3) | Groundwater (m3) | Difference vs baseline (m3) | Stress risk |",
            "|---|---|---|---|---|---|",
        ]
        for r in scenarios:
            lines.append(
                f"| {r['name']} | {r['irrigation_mm']:.1f} | {r['volume_m3']:,.0f} | "
                f"{r['groundwater_m3']:,.0f} | {r['difference_vs_baseline_m3']:,.0f} | "
                f"{'Yes' if r['stress_risk'] else 'No'} |"
            )
        lines.append(
            "\nA scenario with stress risk delivers less net water than the modelled crop need "
            "and should not be recommended on groundwater savings alone."
        )

    if evidence:
        lines += ["", "## 4. Document evidence"]
        for e in evidence:
            snippet = " ".join(e["text"].split())[:300]
            lines.append(f"- [{e['source']}, p. {e['page']}] {snippet}...")

    lines += ["", "## Limitations", DISCLAIMER]
    return "\n".join(lines)


def build_report_csv(farm: dict, account: dict) -> bytes:
    row = {k: v for k, v in {**farm, **account}.items()}
    return pd.DataFrame([row]).to_csv(index=False).encode("utf-8")
