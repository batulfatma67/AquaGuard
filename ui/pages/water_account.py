import pandas as pd
import streamlit as st

from database.db import fetch_recent_accounts, save_water_account
from ui.state import DB, ensure_calculation, recalculate


def render() -> None:
    st.title("💧 Water Account")
    st.caption("Transparent crop-water and groundwater accounting for the current farm.")

    inputs = st.session_state.inputs

    with st.expander("Calculation inputs and assumptions (user-entered)", expanded=False):
        with st.form("water_inputs"):
            a, b, c3 = st.columns(3)
            eto = a.number_input("ETo (mm/day)", 0.0, 20.0, float(inputs["eto_mm"]), 0.1)
            days = b.number_input("Period (days)", 1, 60, int(inputs["period_days"]))
            rain = c3.number_input("Rainfall over period (mm)", 0.0, 500.0,
                                   float(inputs["rain_mm"]), 0.5)
            d, e, f = st.columns(3)
            factor = d.slider("Effective rainfall factor", 0.0, 1.0, float(inputs["rain_factor"]), 0.05)
            moisture = e.slider("Usable soil water at start (% of readily available)", 0, 100,
                                int(inputs["soil_moisture_pct"]))
            use_eff = f.checkbox("Override application efficiency",
                                 value=inputs["efficiency_override"] is not None)
            eff = f.slider("Application efficiency", 0.10, 1.0,
                           float(inputs["efficiency_override"] or 0.55), 0.05)
            if st.form_submit_button("Apply inputs", type="primary"):
                st.session_state.inputs = {
                    "eto_mm": eto, "period_days": days, "rain_mm": rain,
                    "rain_factor": factor, "soil_moisture_pct": float(moisture),
                    "efficiency_override": eff if use_eff else None,
                }
                st.session_state.scenario_rows = None
                recalculate()
                st.rerun()

    c = ensure_calculation()

    a, b = st.columns(2)
    a.metric("ETo", f"{c['eto_mm']:.1f} mm/day")
    b.metric("ETc (period)", f"{c['etc_mm']:.1f} mm")
    c3, d = st.columns(2)
    c3.metric("Gross Irrigation", f"{c['gross_irrigation_mm']:.1f} mm")
    d.metric("Groundwater", f"{c['groundwater_m3']:,.0f} m³")

    st.markdown("### Calculation Breakdown")
    rows = [
        ("Crop stage", f"{c['crop_stage']} ({c['days_after_sowing']} days after sowing)", "Derived from sowing date"),
        ("Reference evapotranspiration (ETo)", f"{c['eto_mm']:.2f} mm/day", "User-entered"),
        ("Crop coefficient (Kc)", f"{c['kc']:.2f}", "crops.csv"),
        ("Crop evapotranspiration (ETc)", f"{c['etc_mm']:.2f} mm", f"ETo × Kc × {c['period_days']:g} days"),
        ("Effective rainfall", f"{c['effective_rain_mm']:.2f} mm", "Rainfall × effective factor (assumed)"),
        ("Soil-water contribution", f"{c['soil_water_contribution_mm']:.2f} mm", "soils.csv × assumed moisture"),
        ("Net irrigation requirement", f"{c['net_irrigation_mm']:.2f} mm", "max(0, ETc − rain − soil)"),
        ("Application efficiency", f"{c['application_efficiency'] * 100:.0f}%", "Method default or override"),
        ("Gross irrigation requirement", f"{c['gross_irrigation_mm']:.2f} mm", "Net ÷ efficiency"),
        ("Gross farm volume", f"{c['gross_volume_m3']:,.1f} m³", "mm × ha × 10"),
        ("Surface-water contribution", f"{c['surface_water_m3']:,.1f} m³", "User-entered estimate"),
        ("Estimated groundwater", f"{c['groundwater_m3']:,.1f} m³", "max(0, gross − surface)"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Component", "Value", "Basis"]),
                 width="stretch", hide_index=True)

    if st.button("💾 Save Water Account", type="primary"):
        save_water_account(DB, st.session_state.farm["farm_id"], c, st.session_state.inputs)
        st.success("Water account saved to SQLite.")

    history = fetch_recent_accounts(DB, farm_id=st.session_state.farm["farm_id"])
    if history:
        st.markdown("### Saved Accounts")
        st.dataframe(pd.DataFrame(history), width="stretch", hide_index=True)
