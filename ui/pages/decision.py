import html

import streamlit as st

from engine.scenario_engine import compare_scenarios
from ui.state import ensure_calculation


def render() -> None:
    st.title("🛡️ AquaGuard Decision")
    st.caption("Compare the farm's planned irrigation with a modelled water-balanced option.")

    c = ensure_calculation()
    area = st.session_state.farm["area_ha"]

    baseline_mm = st.number_input(
        "Farmer planned irrigation (mm)",
        min_value=0.0,
        value=round(c["gross_irrigation_mm"] + 10, 1),
        step=1.0,
    )
    recommended_mm = round(c["gross_irrigation_mm"], 1)

    rows = compare_scenarios(
        [("Farmer plan", baseline_mm), ("AquaGuard", recommended_mm)], c, area
    )
    plan, aqua = rows

    x, y, z = st.columns(3)
    x.metric("Planned Groundwater", f"{plan['groundwater_m3']:,.0f} m³")
    y.metric("AquaGuard Groundwater", f"{aqua['groundwater_m3']:,.0f} m³")
    z.metric("Potential Saving", f"{aqua['difference_vs_baseline_m3']:,.0f} m³")

    if aqua["stress_risk"]:
        st.warning("The AquaGuard option is flagged for modelled crop-water stress risk.")
    if plan["stress_risk"]:
        st.warning("The farmer plan delivers less than the modelled crop need (stress risk).")

    st.html(
        f"""
        <div class="recommendation">
            <h3>💡 AquaGuard Recommendation</h3>
            <p>
                Modelled crop-water demand indicates approximately
                <b>{html.escape(f'{recommended_mm:.1f}')} mm</b> of gross irrigation for this period.
                The comparison estimates a potential groundwater difference of
                <b>{aqua['difference_vs_baseline_m3']:,.0f} m³</b> versus the entered plan.
            </p>
            <p class="small-muted">
                This is a modelled difference, not a measured reduction in pumping.
            </p>
        </div>
        """
    )
