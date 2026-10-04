import pandas as pd
import streamlit as st

from database.db import fetch_recent_scenarios, save_scenarios
from engine.scenario_engine import compare_scenarios, recommend
from ui.state import DB, ensure_calculation


def render() -> None:
    st.title("📊 What-If Scenarios")
    st.caption("Test irrigation choices before pumping. Scenario A is the baseline.")

    c = ensure_calculation()
    f = st.session_state.farm
    gross = c["gross_irrigation_mm"]

    a, b, d = st.columns(3)
    baseline = a.number_input("Scenario A — Farmer plan (mm)", 0.0, 200.0,
                              float(round(gross + 10, 1)), 1.0)
    aqua = b.number_input("Scenario B — AquaGuard option (mm)", 0.0, 200.0,
                          float(round(gross, 1)), 1.0)
    lower = d.number_input("Scenario C — Lower application (mm)", 0.0, 200.0,
                           float(round(max(0.0, gross - 5), 1)), 1.0)

    rows = compare_scenarios(
        [("Farmer plan", baseline), ("AquaGuard", aqua), ("Lower application", lower)],
        c, f["area_ha"],
    )
    st.session_state.scenario_rows = rows

    df = pd.DataFrame(
        [
            {
                "Scenario": r["name"],
                "Irrigation (mm)": r["irrigation_mm"],
                "Total water (m³)": r["volume_m3"],
                "Estimated groundwater (m³)": r["groundwater_m3"],
                "Difference vs baseline (m³)": r["difference_vs_baseline_m3"],
                "Crop-water stress risk": "Yes" if r["stress_risk"] else "No",
            }
            for r in rows
        ]
    )
    st.dataframe(df, width="stretch", hide_index=True)
    st.bar_chart(df.set_index("Scenario")[["Total water (m³)", "Estimated groundwater (m³)"]])

    best = recommend(rows)
    if best:
        st.success(
            f"Lowest-groundwater option without modelled stress: **{best['name']}** "
            f"({best['irrigation_mm']:.1f} mm, {best['groundwater_m3']:,.0f} m³ groundwater)."
        )
    else:
        st.error("Every scenario is flagged for modelled crop-water stress.")

    st.warning(
        "The lowest-water scenario is not automatically the best decision. AquaGuard aims "
        "to meet crop water needs while reducing unnecessary groundwater dependence. "
        "Differences are modelled, not measured."
    )

    if st.button("💾 Save Scenarios", type="primary"):
        save_scenarios(DB, f["farm_id"], rows)
        st.success("Scenarios saved to SQLite.")

    saved = fetch_recent_scenarios(DB, farm_id=f["farm_id"])
    if saved:
        st.markdown("### Saved Scenarios")
        st.dataframe(pd.DataFrame(saved), width="stretch", hide_index=True)
