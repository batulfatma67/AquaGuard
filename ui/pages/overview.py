import pandas as pd
import streamlit as st

from database.db import fetch_recent_accounts
from ui.components import metric_card, section_title
from ui.state import DB, ensure_calculation, go, recalculate


def render() -> None:
    st.html(
        """
        <div class="hero">
            <h1>Welcome to <span>AquaGuard</span></h1>
            <p>
                AI-powered farm water intelligence that connects crop-water demand,
                irrigation decisions and estimated groundwater use, helping farmers
                understand where water can potentially be saved.
            </p>
        </div>
        """
    )

    c = ensure_calculation()
    farm = st.session_state.farm

    recalculation_notice = st.session_state.pop("recalculation_notice", None)
    if recalculation_notice:
        st.success(recalculation_notice)

    first_metrics = st.columns(2)
    with first_metrics[0]:
        metric_card("Total Water Requirement", f"{c['gross_volume_m3']:,.0f} m³",
                    f"Modelled gross requirement, {c['period_days']:g}-day period")
    with first_metrics[1]:
        metric_card("Estimated Groundwater", f"{c['groundwater_m3']:,.0f} m³",
                    "Residual after surface-water contribution")

    second_metrics = st.columns(2)
    with second_metrics[0]:
        metric_card("Crop Water Demand", f"{c['etc_mm']:.1f} mm",
                    f"ETc = ETo × Kc ({c['crop_stage']}, Kc {c['kc']:.2f})")
    with second_metrics[1]:
        metric_card("Groundwater Dependency", f"{c['groundwater_dependency_pct']:.0f}%",
                    "Estimated share of gross irrigation")

    section_title("Farm Water Snapshot")
    left, right = st.columns([1.55, 1])

    with left:
        history = fetch_recent_accounts(DB, limit=12, farm_id=farm["farm_id"])
        with st.container(border=True):
            st.markdown("**Saved Water Accounts**")
            if len(history) >= 2:
                df = pd.DataFrame(history[::-1])
                df["created_at"] = pd.to_datetime(df["created_at"])
                st.caption("Gross requirement and groundwater from your saved accounts.")
                st.line_chart(
                    df.set_index("created_at")[["gross_volume_m3", "groundwater_m3"]]
                    .rename(columns={"gross_volume_m3": "Total water (m³)",
                                     "groundwater_m3": "Groundwater (m³)"})
                )
            else:
                st.caption("Save at least two water accounts on the Water Account page to see a trend.")

    with right:
        st.html(
            f"""
            <div class="card">
                <div class="metric-label">AquaGuard Insight</div>
                <div class="big-number">{c['groundwater_dependency_pct']:.0f}%</div>
                <p class="small-muted">
                    of the modelled gross irrigation requirement is estimated
                    to come from groundwater.
                </p>
                <span class="pill pill-green">Modelled estimate</span>
            </div>
            """
        )
        st.markdown("")
        st.html(
            """
            <div class="recommendation">
                <b>💡 Current recommendation</b>
                <p style="margin:8px 0 0;color:#5E5140">
                    Review the planned irrigation amount against the calculated crop
                    requirement before pumping. Use What-If Scenarios to test a lower
                    groundwater-dependent option that still meets crop needs.
                </p>
            </div>
            """
        )

    section_title("Quick Actions")
    if st.button("💧 Recalculate Water Account", width="stretch", type="primary"):
        result = recalculate()
        if result:
            st.session_state.recalculation_notice = (
                "Water account recalculated from the current farm profile and inputs "
                f"at {st.session_state.last_calculation_at}."
            )
        st.rerun()

    q2, q3 = st.columns(2)
    q2.button("📊 Run What-If Scenarios", width="stretch",
              on_click=go, args=("📊  What-If Scenarios",))
    q3.button("🌱 Farm Profiles", width="stretch",
              on_click=go, args=("🌱  Farm Profiles",))
