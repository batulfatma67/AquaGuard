import pandas as pd
import streamlit as st

from agent.agent_router import run_agent
from database.db import save_report
from engine.scenario_engine import compare_scenarios
from rag.groq_client import get_groq_api_key
from rag.pipeline import ask_rag
from services.report_service import build_report_markdown
from ui.state import DB, ensure_calculation


def _render_calculation() -> None:
    farm = st.session_state.farm
    account = ensure_calculation()

    st.subheader(f"{farm['crop']} water account")
    st.caption(
        f"{account['crop_stage']} stage · {account['period_days']:g}-day period · "
        "modelled estimates"
    )

    water, groundwater = st.columns(2)
    water.metric("Gross water requirement", f"{account['gross_volume_m3']:,.0f} m³")
    groundwater.metric(
        "Estimated groundwater",
        f"{account['groundwater_m3']:,.0f} m³",
        f"{account['groundwater_dependency_pct']:.0f}% of gross requirement",
    )

    rows = [
        ("Reference evapotranspiration (ETo)", f"{account['eto_mm']:.2f} mm/day", "User-entered"),
        ("Crop coefficient (Kc)", f"{account['kc']:.2f}", "Crop and growth-stage reference"),
        ("Crop evapotranspiration (ETc)", f"{account['etc_mm']:.2f} mm", "ETo × Kc × period"),
        ("Effective rainfall", f"{account['effective_rain_mm']:.2f} mm", "Rainfall × effective factor"),
        ("Soil-water contribution", f"{account['soil_water_contribution_mm']:.2f} mm", "Soil reference × assumed moisture"),
        ("Net irrigation requirement", f"{account['net_irrigation_mm']:.2f} mm", "max(0, ETc − rain − soil water)"),
        ("Application efficiency", f"{account['application_efficiency'] * 100:.0f}%", "Irrigation-method default or override"),
        ("Gross irrigation requirement", f"{account['gross_irrigation_mm']:.2f} mm", "Net requirement ÷ efficiency"),
        ("Surface-water contribution", f"{account['surface_water_m3']:,.0f} m³", "User-entered estimate"),
        ("Estimated groundwater", f"{account['groundwater_m3']:,.0f} m³", "Gross volume − surface water"),
    ]
    st.dataframe(
        pd.DataFrame(rows, columns=["Calculation", "Result", "Basis"]),
        width="stretch",
        hide_index=True,
    )

    st.markdown("**Water-source split**")
    split = pd.DataFrame(
        {"Volume (m³)": [account["surface_water_m3"], account["groundwater_m3"]]},
        index=["Surface water", "Groundwater"],
    )
    st.bar_chart(split, height=220)
    st.caption("These are modelled estimates, not measured pumping volumes.")


def _render_comparison() -> None:
    rows = st.session_state.get("scenario_rows") or []
    if not rows:
        st.markdown("The scenario comparison was prepared, but no rows are available.")
        return

    st.subheader("Scenario comparison")
    st.caption("All volumes are modelled estimates. Scenario A is the baseline.")
    table = pd.DataFrame(
        [
            {
                "Scenario": row["name"],
                "Irrigation (mm)": row["irrigation_mm"],
                "Total water (m³)": row["volume_m3"],
                "Groundwater (m³)": row["groundwater_m3"],
                "Difference vs baseline (m³)": row["difference_vs_baseline_m3"],
                "Stress risk": "Yes" if row["stress_risk"] else "No",
            }
            for row in rows
        ]
    )
    st.dataframe(table, width="stretch", hide_index=True)
    st.bar_chart(
        table.set_index("Scenario")[["Total water (m³)", "Groundwater (m³)"]],
        height=260,
    )
    if any(row["stress_risk"] for row in rows):
        st.warning("At least one scenario is flagged for modelled crop-water stress risk.")


def _tools() -> dict:
    farm = st.session_state.farm
    account = ensure_calculation()

    def calculate(_msg: str) -> str:
        return (
            f"For {farm['crop']} ({account['crop_stage']}) over {account['period_days']:g} days: "
            f"ETc {account['etc_mm']:.1f} mm, net need {account['net_irrigation_mm']:.1f} mm, "
            f"gross {account['gross_irrigation_mm']:.1f} mm = {account['gross_volume_m3']:,.0f} m³, "
            f"of which about {account['groundwater_m3']:,.0f} m³ "
            f"({account['groundwater_dependency_pct']:.0f}%) is estimated groundwater. "
            "These are modelled estimates."
        )

    def compare(_msg: str) -> str:
        gross = account["gross_irrigation_mm"]
        rows = compare_scenarios(
            [("Farmer plan (+10 mm)", gross + 10), ("AquaGuard", gross)], account, farm["area_ha"]
        )
        st.session_state.scenario_rows = rows
        return (
            f"Moving from {rows[0]['irrigation_mm']:.1f} mm to {rows[1]['irrigation_mm']:.1f} mm "
            f"changes estimated groundwater by {rows[1]['difference_vs_baseline_m3']:,.0f} m³ "
            "(modelled, not measured)."
        )

    def search(message: str) -> str:
        answer, sources = ask_rag(message)
        if sources:
            st.session_state.rag_evidence = sources
        return answer

    def report(_msg: str) -> str:
        return build_report_markdown(
            farm, account, st.session_state.scenario_rows, st.session_state.rag_evidence
        )

    return {"CALCULATE": calculate, "COMPARE": compare, "SEARCH": search, "REPORT": report}


def render() -> None:
    st.title("🤖 Assistant (experimental)")
    st.caption(
        "Routes a request to one tool: water calculation, scenario comparison, "
        "document search or report draft. Reports need your confirmation."
    )

    message = st.chat_input("e.g. How much water does my wheat need?")
    if message:
        try:
            st.session_state.agent_result = run_agent(message, _tools(), get_groq_api_key())
            st.session_state.agent_message = message
        except Exception as exc:
            st.session_state.agent_result = None
            st.error(f"Assistant failed: {exc}")

    result = st.session_state.get("agent_result")
    if not result:
        st.info("Ask a question to begin.")
        return

    with st.chat_message("user"):
        st.markdown(st.session_state.agent_message)
    with st.chat_message("assistant"):
        st.caption(f"Tool selected: {result['intent']}")
        if result["needs_confirmation"]:
            st.markdown("Draft report prepared. Review it, then confirm to save.")
            with st.expander("Draft report", expanded=True):
                st.markdown(result["output"])
            if st.button("✅ Confirm and save report", type="primary"):
                farm = st.session_state.farm
                save_report(DB, farm["farm_id"], f"{farm['crop']} report - {farm['district']}",
                            result["output"])
                st.session_state.agent_result = None
                st.success("Report saved.")
        elif result["intent"] == "CALCULATE":
            _render_calculation()
        elif result["intent"] == "COMPARE":
            _render_comparison()
        else:
            st.markdown(result["output"])
