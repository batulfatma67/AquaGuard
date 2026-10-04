import pandas as pd
import streamlit as st

from database.db import fetch_recent_accounts, fetch_reports, save_report
from services.report_service import build_report_csv, build_report_markdown
from ui.state import DB, ensure_calculation


def render() -> None:
    st.title("📄 AquaGuard Report")
    st.caption("Inputs, calculations, scenarios, evidence and limitations for the current farm.")

    c = ensure_calculation()
    f = st.session_state.farm
    scenarios = st.session_state.scenario_rows
    evidence = st.session_state.rag_evidence

    include_scenarios = st.checkbox("Include scenario comparison", value=bool(scenarios),
                                    disabled=not scenarios)
    include_evidence = st.checkbox("Include last retrieved document evidence",
                                   value=bool(evidence), disabled=not evidence)
    if not scenarios:
        st.caption("Open What-If Scenarios to generate a comparison for the report.")

    report_md = build_report_markdown(
        f, c,
        scenarios if include_scenarios else None,
        evidence if include_evidence else None,
    )

    with st.container(border=True):
        st.markdown(report_md)

    a, b, d = st.columns(3)
    a.download_button("⬇️ Download Report (Markdown)", report_md.encode("utf-8"),
                      "aquaguard_report.md", "text/markdown", width="stretch")
    b.download_button("⬇️ Download Data (CSV)", build_report_csv(f, c),
                      "aquaguard_water_report.csv", "text/csv", width="stretch")
    if d.button("💾 Save Report to Database", type="primary", width="stretch"):
        save_report(DB, f["farm_id"], f"{f['crop']} report - {f['district']}", report_md)
        st.success("Report saved.")

    reports = fetch_reports(DB, farm_id=f["farm_id"])
    if reports:
        st.markdown("### Saved Reports")
        for r in reports:
            with st.expander(f"{r['title']} — {r['created_at']}"):
                st.markdown(r["content_md"])

    accounts = fetch_recent_accounts(DB, farm_id=f["farm_id"])
    if accounts:
        st.markdown("### Saved Accounts")
        st.dataframe(pd.DataFrame(accounts), width="stretch", hide_index=True)
