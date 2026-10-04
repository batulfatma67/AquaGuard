import base64
import html
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from database.db import (
    init_db,from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import html
import pandas as pd
import streamlit as st

from database.db import init_db, save_farm, save_water_account, fetch_recent_accounts
from engine.water_engine import calculate_water_account, compare_scenarios
from rag.pipeline import build_knowledge_base, ask_rag, get_store_info

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "aquaguard.db"

st.set_page_config(page_title="AquaGuard AI | Irrigation Intelligence", page_icon="💧", layout="wide")
init_db(str(DB_PATH))

# ---------- Visual design ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family: Inter, sans-serif;}
.stApp {background:#f4f7f9;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#082b45,#104e59);}
[data-testid="stSidebar"] * {color:#f7fbfc;}
.block-container {padding-top:1.7rem; padding-bottom:3rem; max-width:1400px;}
.ag-hero {background:linear-gradient(115deg,#082b45,#12645e);padding:28px 32px;border-radius:18px;color:white;margin-bottom:22px;}
.ag-hero h1 {font-size:2.2rem;margin:0 0 8px 0;color:white;}
.ag-hero p {color:#e2f4f0;margin:0;max-width:850px;line-height:1.6;}
.ag-note {background:#edf6f3;border:1px solid #c9e5dc;border-radius:12px;padding:14px 16px;color:#174d43;}
.ag-warning {background:#fff7e6;border:1px solid #f0d9a4;border-radius:12px;padding:14px 16px;color:#76551b;}
div[data-testid="stMetric"] {background:white;border:1px solid #dce6e9;border-radius:12px;padding:14px;box-shadow:0 2px 8px rgba(8,43,69,.04);}
.stButton > button {border-radius:9px;font-weight:600;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Session state and transparent defaults ----------
DEFAULT_FARM = {
    "district": "Faisalabad",
    "tehsil": "Faisalabad City",
    "area_ha": 2.0,
    "crop": "Wheat",
    "sowing_date": date.today() - timedelta(days=85),
    "soil": "Loam",
    "irrigation_method": "Flood",
    "water_source": "Canal + Tubewell",
    "canal_water_m3": 250.0,
}
DEFAULT_ASSUMPTIONS = {
    "eto_mm": 5.2,
    "kc": 1.05,
    "effective_rain_mm": 0.8,
    "soil_water_contribution_mm": 2.0,
    "application_efficiency": 0.55,
}
if "farm" not in st.session_state:
    st.session_state.farm = DEFAULT_FARM.copy()
if "assumptions" not in st.session_state:
    st.session_state.assumptions = DEFAULT_ASSUMPTIONS.copy()
if "calculation" not in st.session_state:
    st.session_state.calculation = None
if "rag_messages" not in st.session_state:
    st.session_state.rag_messages = []


def calculate_current():
    """Run the deterministic water-account engine with visible user-editable assumptions."""
    f = st.session_state.farm
    a = st.session_state.assumptions
    return calculate_water_account(
        eto_mm=float(a["eto_mm"]),
        kc=float(a["kc"]),
        effective_rain_mm=float(a["effective_rain_mm"]),
        soil_water_contribution_mm=float(a["soil_water_contribution_mm"]),
        application_efficiency=float(a["application_efficiency"]),
        area_ha=float(f["area_ha"]),
        surface_water_m3=float(f["canal_water_m3"]),
    )


def get_calculation():
    if st.session_state.calculation is None:
        st.session_state.calculation = calculate_current()
    return st.session_state.calculation


def format_m3(value):
    return f"{float(value):,.1f} m³"


def render_method_note():
    st.caption("Prototype estimates only. Values depend on the assumptions shown in Water Account; they are not direct measurements of pumping, soil moisture, aquifer status, or actual field water use.")

# ---------- Navigation ----------
with st.sidebar:
    st.markdown("## 💧 AquaGuard AI")
    st.caption("Farm irrigation & groundwater decision support")
    page = st.radio("Workspace", [
        "Overview", "Farm Setup", "Water Account", "AquaGuard Decision",
        "What-If Scenarios", "Document RAG", "Reports"
    ], label_visibility="collapsed")
    st.divider()
    f_sidebar = st.session_state.farm
    st.markdown("**Active farm**")
    st.write(f"{f_sidebar['crop']} · {f_sidebar['area_ha']:.2f} ha")
    st.caption(f"{f_sidebar['tehsil']}, {f_sidebar['district']}")
    st.divider()
    st.caption("Calculations are deterministic; AI explanations must not replace the water engine.")

# ---------- Overview ----------
if page == "Overview":
    st.markdown("<div class='ag-hero'><h1>AquaGuard AI</h1><p>Understand the estimated irrigation requirement for a farm, account for a stated surface-water contribution, and compare irrigation plans before pumping.</p></div>", unsafe_allow_html=True)
    c = get_calculation()
    f = st.session_state.farm
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross irrigation requirement", f"{c['gross_irrigation_mm']:.1f} mm")
    m2.metric("Modelled water volume", format_m3(c["gross_volume_m3"]))
    m3.metric("Estimated groundwater", format_m3(c["groundwater_m3"]))
    m4.metric("Groundwater share", f"{c['groundwater_dependency_pct']:.1f}%")
    st.subheader("Current farm account")
    left, right = st.columns([1.25, 1])
    with left:
        chart_df = pd.DataFrame({
            "Water source": ["Surface water", "Groundwater"],
            "Estimated volume (m³)": [c["surface_water_m3"], c["groundwater_m3"]],
        }).set_index("Water source")
        st.bar_chart(chart_df, y_label="Estimated volume (m³)")
        st.caption("Chart: modelled irrigation volume by assumed water source; not a historical trend.")
    with right:
        st.markdown("### What this result means")
        st.write(f"For **{f['area_ha']:.2f} ha of {f['crop'].lower()}**, the current assumptions produce a gross irrigation estimate of **{c['gross_irrigation_mm']:.1f} mm**, equivalent to **{c['gross_volume_m3']:,.1f} m³**.")
        st.write(f"After applying the stated surface-water contribution of **{c['surface_water_m3']:,.1f} m³**, the remaining modelled groundwater requirement is **{c['groundwater_m3']:,.1f} m³**.")
        if c["groundwater_dependency_pct"] >= 70:
            st.warning("The model attributes a high share of this irrigation account to groundwater. Verify the water-source inputs before using this result for a real decision.")
        elif c["groundwater_dependency_pct"] > 0:
            st.info("The model estimates a mixed or groundwater-dependent supply. Verify actual canal delivery and pumping records where possible.")
        else:
            st.success("Under the current inputs, no groundwater contribution is estimated for this account.")
    st.markdown("<div class='ag-note'><b>Next step:</b> Confirm farm area, crop coefficient, reference ET, rainfall, soil-water contribution, application efficiency, and surface-water volume in Farm Setup and Water Account before interpreting the result.</div>", unsafe_allow_html=True)
    render_method_note()

# ---------- Farm Setup ----------
elif page == "Farm Setup":
    st.title("Farm Setup")
    st.write("Enter farm-specific information. Location does not automatically fetch weather or satellite data in this version.")
    f = st.session_state.farm
    with st.form("farm_setup_form"):
        col1, col2 = st.columns(2)
        with col1:
            district = st.text_input("District", value=f["district"])
            tehsil = st.text_input("Tehsil", value=f["tehsil"])
            area_ha = st.number_input("Farm area (hectares)", min_value=0.01, max_value=100000.0, value=float(f["area_ha"]), step=0.1)
            crop_options = ["Wheat", "Maize", "Rice", "Cotton", "Sugarcane", "Other"]
            crop = st.selectbox("Crop", crop_options, index=crop_options.index(f["crop"]) if f["crop"] in crop_options else 0)
            sowing_date = st.date_input("Sowing date", value=f["sowing_date"])
        with col2:
            soil_options = ["Loam", "Sandy Loam", "Clay Loam", "Clay", "Sandy", "Other/Unknown"]
            soil = st.selectbox("Soil type", soil_options, index=soil_options.index(f["soil"]) if f["soil"] in soil_options else 0)
            method_options = ["Flood", "Furrow", "Sprinkler", "Drip", "Other/Unknown"]
            irrigation_method = st.selectbox("Irrigation method", method_options, index=method_options.index(f["irrigation_method"]) if f["irrigation_method"] in method_options else 0)
            source_options = ["Tubewell only", "Canal only", "Canal + Tubewell", "Other/Unknown"]
            water_source = st.selectbox("Water source", source_options, index=source_options.index(f["water_source"]) if f["water_source"] in source_options else 0)
            surface_water_m3 = st.number_input("Surface-water contribution for this account (m³)", min_value=0.0, value=float(f["canal_water_m3"]), step=25.0, help="Enter the volume expected to contribute to this irrigation account, not a canal flow rate.")
        submitted = st.form_submit_button("Save Farm Profile & Recalculate", type="primary", use_container_width=True)
    if submitted:
        st.session_state.farm = {"district": district.strip(), "tehsil": tehsil.strip(), "area_ha": area_ha, "crop": crop, "sowing_date": sowing_date, "soil": soil, "irrigation_method": irrigation_method, "water_source": water_source, "canal_water_m3": surface_water_m3}
        try:
            save_farm(str(DB_PATH), st.session_state.farm)
            st.session_state.calculation = calculate_current()
            st.success("Farm profile saved and water account recalculated.")
        except Exception as exc:
            st.error(f"Could not save/recalculate farm profile: {exc}")
    st.subheader("Current profile")
    st.dataframe(pd.DataFrame([st.session_state.farm]), use_container_width=True, hide_index=True)

# ---------- Water Account ----------
elif page == "Water Account":
    st.title("Water Account")
    st.write("Edit the assumptions used by the calculation engine. These are not automatically retrieved from live weather or field sensors.")
    a = st.session_state.assumptions
    with st.form("water_assumptions_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            eto = st.number_input("Reference evapotranspiration ETo (mm/day)", min_value=0.0, max_value=20.0, value=float(a["eto_mm"]), step=0.1, help="Enter the ETo value for the period represented by this account.")
            kc = st.number_input("Crop coefficient Kc", min_value=0.0, max_value=2.0, value=float(a["kc"]), step=0.05)
        with c2:
            rain = st.number_input("Effective rainfall (mm)", min_value=0.0, max_value=500.0, value=float(a["effective_rain_mm"]), step=0.1)
            soil_water = st.number_input("Usable soil-water contribution (mm)", min_value=0.0, max_value=500.0, value=float(a["soil_water_contribution_mm"]), step=0.1)
        with c3:
            efficiency_pct = st.number_input("Application efficiency (%)", min_value=1.0, max_value=100.0, value=float(a["application_efficiency"] * 100), step=1.0, help="Illustrative efficiency should be replaced with a measured or locally justified value.")
            st.metric("Farm area", f"{st.session_state.farm['area_ha']:.2f} ha")
        update = st.form_submit_button("Calculate Water Account", type="primary", use_container_width=True)
    if update:
        st.session_state.assumptions = {"eto_mm": eto, "kc": kc, "effective_rain_mm": rain, "soil_water_contribution_mm": soil_water, "application_efficiency": efficiency_pct / 100.0}
        try:
            st.session_state.calculation = calculate_current()
            st.success("Water account recalculated from the assumptions above.")
        except Exception as exc:
            st.error(f"Calculation failed: {exc}")
    c = get_calculation()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Crop evapotranspiration (ETc)", f"{c['etc_mm']:.2f} mm")
    m2.metric("Net irrigation requirement", f"{c['net_irrigation_mm']:.2f} mm")
    m3.metric("Gross irrigation requirement", f"{c['gross_irrigation_mm']:.2f} mm")
    m4.metric("Gross farm volume", format_m3(c["gross_volume_m3"]))
    st.subheader("Calculation breakdown")
    rows = [
        ("Reference evapotranspiration (ETo)", f"{c['eto_mm']:.2f} mm"),
        ("Crop coefficient (Kc)", f"{c['kc']:.2f}"),
        ("Crop evapotranspiration (ETc = ETo × Kc)", f"{c['etc_mm']:.2f} mm"),
        ("Effective rainfall", f"{c['effective_rain_mm']:.2f} mm"),
        ("Usable soil-water contribution", f"{c['soil_water_contribution_mm']:.2f} mm"),
        ("Net irrigation requirement", f"{c['net_irrigation_mm']:.2f} mm"),
        ("Application efficiency", f"{c['application_efficiency'] * 100:.1f}%"),
        ("Gross irrigation requirement", f"{c['gross_irrigation_mm']:.2f} mm"),
        ("Gross farm volume", format_m3(c["gross_volume_m3"])),
        ("Surface-water contribution used in account", format_m3(c["surface_water_m3"])),
        ("Estimated groundwater contribution", format_m3(c["groundwater_m3"])),
        ("Groundwater share", f"{c['groundwater_dependency_pct']:.1f}%"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Component", "Calculated value"]), use_container_width=True, hide_index=True)
    st.subheader("Water source split")
    source_df = pd.DataFrame({"Water source": ["Surface water", "Groundwater"], "Estimated volume (m³)": [c["surface_water_m3"], c["groundwater_m3"]]}).set_index("Water source")
    st.bar_chart(source_df, y_label="Estimated volume (m³)")
    st.caption("Formula: ETc = ETo × Kc; net irrigation = max(0, ETc − effective rainfall − usable soil water); gross irrigation = net irrigation ÷ application efficiency; volume = depth × area × 10.")
    render_method_note()
    if st.button("Save this Water Account", type="primary"):
        try:
            save_water_account(str(DB_PATH), st.session_state.farm, c)
            st.success("Water account saved to the database.")
        except Exception as exc:
            st.error(f"Could not save account: {exc}")

# ---------- AquaGuard Decision ----------
elif page == "AquaGuard Decision":
    st.title("AquaGuard Decision")
    c = get_calculation()
    f = st.session_state.farm
    st.write("Compare the farmer's planned irrigation depth with the modelled gross irrigation requirement. The model does not recommend reducing water below crop need simply to show a saving.")
    planned = st.number_input("Planned irrigation depth (mm)", min_value=0.0, max_value=500.0, value=float(round(c["gross_irrigation_mm"] + 10, 1)), step=1.0)
    recommended = float(c["gross_irrigation_mm"])
    result = compare_scenarios(baseline_mm=planned, aquaguard_mm=recommended, area_ha=float(f["area_ha"]), groundwater_fraction=float(c["groundwater_fraction"]))
    x, y, z = st.columns(3)
    x.metric("Planned total volume", format_m3(result["baseline_volume_m3"]))
    y.metric("Modelled requirement volume", format_m3(result["aquaguard_volume_m3"]))
    z.metric("Potential groundwater difference", format_m3(result["potential_saving_m3"]), delta=f"{result['potential_saving_pct']:.1f}% of planned groundwater" if result["baseline_groundwater_m3"] > 0 else None)
    compare_df = pd.DataFrame({"Scenario": ["Farmer plan", "Modelled requirement"], "Total irrigation volume (m³)": [result["baseline_volume_m3"], result["aquaguard_volume_m3"]], "Estimated groundwater (m³)": [result["baseline_groundwater_m3"], result["aquaguard_groundwater_m3"]]}).set_index("Scenario")
    st.subheader("Scenario comparison")
    st.bar_chart(compare_df, y_label="Volume (m³)")
    if planned > recommended:
        st.success(f"The entered plan is {planned - recommended:.1f} mm above the modelled requirement. Under the same groundwater-share assumption, this corresponds to a potential groundwater difference of {result['potential_saving_m3']:,.1f} m³ if the modelled requirement is appropriate for the crop and period.")
    elif planned < recommended:
        st.warning(f"The entered plan is {recommended - planned:.1f} mm below the modelled requirement. This may under-supply crop water; do not treat the lower volume as a recommended saving without checking crop stage, soil moisture, rainfall and local advice.")
    else:
        st.info("The entered plan matches the modelled gross irrigation requirement under the current assumptions.")
    st.markdown("<div class='ag-warning'><b>Important limitation:</b> scenario groundwater is estimated using the current account's groundwater fraction. It assumes the same source mix in both scenarios; actual canal availability, pumping and field efficiency can differ.</div>", unsafe_allow_html=True)
    render_method_note()

# ---------- What-If Scenarios ----------
elif page == "What-If Scenarios":
    st.title("What-If Scenarios")
    c = get_calculation()
    f = st.session_state.farm
    st.write("Test alternative irrigation depths against the same farm area and current estimated groundwater share.")
    a, b, d = st.columns(3)
    with a:
        plan_a = st.number_input("Scenario A · Farmer plan (mm)", min_value=0.0, max_value=500.0, value=float(round(c["gross_irrigation_mm"] + 10, 1)), step=1.0)
    with b:
        plan_b = st.number_input("Scenario B · Modelled requirement (mm)", min_value=0.0, max_value=500.0, value=float(round(c["gross_irrigation_mm"], 1)), step=1.0)
    with d:
        plan_c = st.number_input("Scenario C · Custom alternative (mm)", min_value=0.0, max_value=500.0, value=float(round(max(0.0, c["gross_irrigation_mm"] + 5), 1)), step=1.0)
    scenarios = []
    for name, depth in [("Farmer plan", plan_a), ("Modelled requirement", plan_b), ("Custom alternative", plan_c)]:
        volume = depth * float(f["area_ha"]) * 10.0
        groundwater = volume * float(c["groundwater_fraction"])
        scenarios.append({"Scenario": name, "Irrigation depth (mm)": depth, "Total volume (m³)": volume, "Estimated groundwater (m³)": groundwater})
    df = pd.DataFrame(scenarios)
    st.dataframe(df.style.format({"Irrigation depth (mm)": "{:.1f}", "Total volume (m³)": "{:,.1f}", "Estimated groundwater (m³)": "{:,.1f}"}), use_container_width=True, hide_index=True)
    st.subheader("Total water volume by scenario")
    st.bar_chart(df.set_index("Scenario")[["Total volume (m³)"]], y_label="Volume (m³)")
    st.subheader("Estimated groundwater by scenario")
    st.bar_chart(df.set_index("Scenario")[["Estimated groundwater (m³)"]], y_label="Volume (m³)")
    if plan_c < c["gross_irrigation_mm"]:
        st.warning("The custom alternative is below the current modelled requirement. Lower application is not automatically better and may create crop water stress.")
    render_method_note()

# ---------- Document RAG ----------
elif page == "Document RAG":
    st.title("Document RAG — Ask Your Water & Agriculture PDFs")
    st.write("Upload reference PDFs, build the local vector index, then ask questions. Answers depend on the quality and coverage of the documents you upload.")
    left, right = st.columns([1.15, 1])
    with left:
        uploaded_files = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)
        chunk_size = st.slider("Chunk size (characters)", 400, 1800, 900, 100)
        chunk_overlap = st.slider("Chunk overlap (characters)", 50, 400, 150, 25)
        if st.button("Build / Replace Knowledge Base", type="primary", use_container_width=True):
            if not uploaded_files:
                st.warning("Upload at least one PDF first.")
            elif chunk_overlap >= chunk_size:
                st.error("Chunk overlap must be smaller than chunk size.")
            else:
                try:
                    with st.spinner("Extracting PDF text and building embeddings/index..."):
                        info = build_knowledge_base(uploaded_files, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                    st.session_state["rag_store_info"] = info
                    st.session_state.rag_messages = []
                    st.success(f"Knowledge base ready: {info.get('documents', '?')} document(s), {info.get('chunks', '?')} chunks.")
                except Exception as exc:
                    st.error(f"Knowledge-base build failed: {exc}")
    with right:
        st.subheader("Knowledge base status")
        try:
            info = get_store_info()
        except Exception as exc:
            info = None
            st.caption(f"Status unavailable: {exc}")
        if info:
            st.metric("Documents", info.get("documents", 0))
            st.metric("Indexed chunks", info.get("chunks", 0))
            st.caption(f"Embedding model: {info.get('embedding_model', 'Not reported')}")
        else:
            st.info("No knowledge base detected. Upload PDFs and build the index.")
        st.caption("Set GROQ_API_KEY in Streamlit Secrets. Never hard-code API keys in this file.")
    st.divider()
    st.subheader("Ask the knowledge base")
    top_k = st.slider("Retrieved passages per question", 2, 8, 4)
    for message in st.session_state.rag_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask about irrigation, crop water, groundwater, or a document passage...")
    if question:
        st.session_state.rag_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Retrieving passages and generating an answer..."):
                    answer, sources = ask_rag(question, top_k=top_k)
                st.markdown(answer)
                if sources:
                    with st.expander("Retrieved sources"):
                        for source in sources:
                            st.markdown(f"- **{source.get('source', 'Unknown document')}**, page {source.get('page', '?')} (similarity: {source.get('score', 0):.3f})")
                st.session_state.rag_messages.append({"role": "assistant", "content": answer})
            except Exception as exc:
                error = f"RAG query failed: {exc}"
                st.error(error)
                st.session_state.rag_messages.append({"role": "assistant", "content": error})

# ---------- Reports ----------
elif page == "Reports":
    st.title("Farm Water Report")
    c = get_calculation()
    f = st.session_state.farm
    a = st.session_state.assumptions
    st.markdown(f"### {html.escape(f['crop'])} · {f['area_ha']:.2f} ha")
    st.write(f"**Location:** {html.escape(f['tehsil'])}, {html.escape(f['district'])}  ")
    st.write(f"**Sowing date:** {f['sowing_date']} · **Soil:** {html.escape(f['soil'])} · **Irrigation method:** {html.escape(f['irrigation_method'])}")
    st.subheader("Water account summary")
    st.dataframe(pd.DataFrame([{
        "ETo (mm/day)": c["eto_mm"], "Kc": c["kc"], "ETc (mm)": c["etc_mm"],
        "Effective rainfall (mm)": c["effective_rain_mm"], "Soil-water contribution (mm)": c["soil_water_contribution_mm"],
        "Application efficiency (%)": c["application_efficiency"] * 100,
        "Net irrigation (mm)": c["net_irrigation_mm"], "Gross irrigation (mm)": c["gross_irrigation_mm"],
        "Gross volume (m³)": c["gross_volume_m3"], "Surface water (m³)": c["surface_water_m3"],
        "Estimated groundwater (m³)": c["groundwater_m3"], "Groundwater share (%)": c["groundwater_dependency_pct"]
    }]), use_container_width=True, hide_index=True)
    st.subheader("Inputs and assumptions")
    st.dataframe(pd.DataFrame([{"Farm area (ha)": f["area_ha"], "Crop": f["crop"], "Water source": f["water_source"], "Entered surface-water contribution (m³)": f["canal_water_m3"], **a}]), use_container_width=True, hide_index=True)
    report_df = pd.DataFrame([{**f, **c, **{f"assumption_{key}": value for key, value in a.items()}}])
    st.download_button("Download report as CSV", data=report_df.to_csv(index=False).encode("utf-8"), file_name="aquaguard_water_report.csv", mime="text/csv", type="primary")
    try:
        recent = fetch_recent_accounts(str(DB_PATH))
        if recent:
            st.subheader("Previously saved water accounts")
            st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.caption(f"Saved-account history unavailable: {exc}")
    st.markdown("<div class='ag-warning'><b>Interpretation boundary:</b> This report is based on user-entered or illustrative assumptions. It is not a field measurement, groundwater-level forecast, satellite observation, or agronomic prescription. Validate inputs with local measurements or an irrigation adviser before operational use.</div>", unsafe_allow_html=True)

st.divider()
st.caption("AquaGuard AI · Hackathon prototype · Transparent water accounting + scenario comparison + document-grounded answers")

    save_farm,
    save_water_account,
    fetch_recent_accounts,
)
from engine.water_engine import (
    calculate_water_account,
    compare_scenarios,
)

from rag.pipeline import build_knowledge_base, ask_rag

# ============================================================
# BASIC CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "aquaguard.db"
BG_PATH = BASE_DIR / "assets" / "aquaguard_landscape.svg"

st.set_page_config(
    page_title="AquaGuard AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db(str(DB_PATH))


# ============================================================
# BACKGROUND IMAGE
# ============================================================

def file_to_data_uri(path: Path) -> str:
    """Convert local image/SVG to a browser-readable data URI."""
    if not path.exists():
        return ""

    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    else:
        mime = "image/png"

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")

    return f"data:{mime};base64,{encoded}"

#Convert the background asset into a browser-compatible data URI
bg_uri = file_to_data_uri(BG_PATH)


# ============================================================
# CUSTOM CSS
# ============================================================

st.html(
    f"""
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {{
        --navy: #082A4A;
        --navy2: #0D3B66;
        --blue: #1479D1;
        --cyan: #36B8E8;
        --green: #20A66A;
        --mint: #EAF8F1;
        --bg: #F4F8FB;
        --text: #102A43;
        --muted: #60758A;
        --border: #DCE7EF;
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: var(--bg);
    }}

    /* SIDEBAR */

    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            #062847 0%,
            #0B3C63 65%,
            #082A4A 100%
        );

        border-right: 1px solid rgba(255,255,255,.08);
    }}

    [data-testid="stSidebar"] * {{
        color: #F7FBFF !important;
    }}

    .brand {{
        padding: 8px 6px 22px;
        border-bottom: 1px solid rgba(255,255,255,.13);
        margin-bottom: 18px;
    }}

    .brand-title {{
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -.8px;
    }}

    .brand-title span {{
        color: #41D89A;
    }}

    .brand-sub {{
        font-size: 11px;
        color: #C9DFED !important;
        margin-top: 2px;
    }}

    /* HERO */

    .hero {{
        min-height: 250px;

        border-radius: 20px;

        overflow: hidden;

        position: relative;

        background-image:
            linear-gradient(
                90deg,
                rgba(5,36,66,.94) 0%,
                rgba(7,54,83,.78) 46%,
                rgba(7,54,83,.18) 100%
            ),
            url("{bg_uri}");

        background-size: cover;

        background-position: center;

        padding: 42px 46px;

        margin-bottom: 22px;

        box-shadow:
            0 14px 35px rgba(8,42,74,.14);
    }}

    .hero h1 {{
        color: white;

        font-size: 42px;

        line-height: 1.05;

        margin: 0 0 10px;

        font-weight: 800;

        letter-spacing: -1.4px;
    }}

    .hero h1 span {{
        color: #43D79A;
    }}

    .hero p {{
        color: #E4F2FA;

        font-size: 16px;

        max-width: 650px;

        margin: 0;

        line-height: 1.55;
    }}

    /* CARDS */

    .section-title {{
        font-size: 20px;

        color: var(--text);

        font-weight: 800;

        margin: 12px 0 12px;
    }}

    .card {{
        background: white;

        border: 1px solid var(--border);

        border-radius: 16px;

        padding: 19px;

        box-shadow:
            0 7px 22px rgba(13,59,102,.06);
    }}

    .metric-label {{
        color: var(--muted);

        font-size: 13px;

        font-weight: 600;
    }}

    .metric-value {{
        color: var(--text);

        font-size: 29px;

        font-weight: 800;

        margin: 6px 0;
    }}

    .metric-help {{
        color: var(--muted);

        font-size: 11px;
    }}

    .pill {{
        display: inline-block;

        padding: 5px 10px;

        border-radius: 999px;

        font-size: 11px;

        font-weight: 700;
    }}

    .pill-green {{
        background: #E5F7EF;

        color: #118357;
    }}

    .pill-blue {{
        background: #E7F2FC;

        color: #1268AE;
    }}

    .pill-yellow {{
        background: #FFF5D9;

        color: #9A6A00;
    }}

    .callout {{
        background:
            linear-gradient(
                135deg,
                #F0FAF6,
                #EAF6FF
            );

        border: 1px solid #CDE9DD;

        border-radius: 16px;

        padding: 18px;
    }}

    .small-muted {{
        color: var(--muted);

        font-size: 12px;
    }}

    .big-number {{
        font-size: 38px;

        font-weight: 800;

        color: var(--navy);
    }}

    .recommendation {{
        background: #FFF8E6;

        border: 1px solid #F4D889;

        border-radius: 16px;

        padding: 20px;
    }}

    /* STREAMLIT METRICS */

    div[data-testid="stMetric"] {{
        background: white;

        border: 1px solid var(--border);

        border-radius: 14px;

        padding: 12px;
    }}

    /* BUTTONS */

    .stButton > button {{
        border-radius: 10px;

        font-weight: 700;

        border: 1px solid #CFE0EC;
    }}

    .stButton > button[kind="primary"] {{
        background:
            linear-gradient(
                90deg,
                #1479D1,
                #159A91
            );

        color: white;

        border: 0;
    }}

    footer {{
        visibility: hidden;
    }}

    </style>
    """
)


# ============================================================
# SESSION STATE
# ============================================================

if "farm" not in st.session_state:

    st.session_state.farm = {

        "district": "Faisalabad",

        "tehsil": "Faisalabad City",

        "area_ha": 2.02,

        "crop": "Wheat",

        "sowing_date":
            date.today() - timedelta(days=85),

        "soil": "Loam",

        "irrigation_method": "Flood",

        "water_source": "Canal + Tubewell",

        "canal_water_m3": 250.0,
    }


if "calculation" not in st.session_state:

    st.session_state.calculation = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.html(
        """
        <div class="brand">

            <div class="brand-title">
                💧 Aqua<span>Guard</span>
            </div>

            <div class="brand-sub">
                SMARTER WATER. HEALTHIER FARMS.
            </div>

        </div>
        """
    )


    pages = {

        "🏠  Overview":
            "Overview",

        "🌱  Farm Setup":
            "Farm Setup",

        "🛰️  Farm Intelligence":
            "Farm Intelligence",

        "💧  Water Account":
            "Water Account",

        "🛡️  AquaGuard Decision":
            "AquaGuard Decision",

        "📊  What-If Scenarios":
            "What-If Scenarios",

        "📄  Reports":
            "Reports",

        "📚  Document RAG":
            "Document RAG",
    }


    page_label = st.radio(
        "Navigation",
        list(pages.keys()),
        label_visibility="collapsed",
    )


    page = pages[page_label]


    st.markdown("---")

    st.markdown("**Current Farm**")

    st.caption(
        f"{st.session_state.farm['crop']} • "
        f"{st.session_state.farm['area_ha']:.2f} ha • "
        f"{st.session_state.farm['district']}"
    )


    st.markdown("---")

    st.caption("AquaGuard AI • Prototype")

    st.caption(
        "Potential water savings are model estimates, "
        "not measured pumping reductions."
    )


# ============================================================
# CALCULATION HELPERS
# ============================================================

def run_calculation(farm):

    """
    Temporary prototype inputs.

    These will later be replaced with
    actual weather/crop-stage inputs.
    """

    eto_mm = 5.2

    kc = 1.05

    effective_rain_mm = 0.8

    soil_contribution_mm = 2.0

    efficiency = 0.55


    return calculate_water_account(

        eto_mm=eto_mm,

        kc=kc,

        effective_rain_mm=
            effective_rain_mm,

        soil_water_contribution_mm=
            soil_contribution_mm,

        application_efficiency=
            efficiency,

        area_ha=farm["area_ha"],

        surface_water_m3=
            farm["canal_water_m3"],
    )


def ensure_calculation():

    if st.session_state.calculation is None:

        st.session_state.calculation = (
            run_calculation(
                st.session_state.farm
            )
        )

    return st.session_state.calculation


def metric_card(
    label,
    value,
    help_text,
    css_class=""
):

    st.html(

        f"""
        <div class="card {css_class}">

            <div class="metric-label">
                {html.escape(label)}
            </div>

            <div class="metric-value">
                {html.escape(value)}
            </div>

            <div class="metric-help">
                {html.escape(help_text)}
            </div>

        </div>
        """
    )


# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================

if page == "Overview":

    st.html(

        """
        <div class="hero">

            <h1>
                Welcome to <span>AquaGuard</span>
            </h1>

            <p>
                AI-powered farm water intelligence that connects
                crop-water demand, irrigation decisions and estimated
                groundwater use — helping farmers understand where
                water can potentially be saved.
            </p>

        </div>
        """
    )


    c = ensure_calculation()


    groundwater = c["groundwater_m3"]

    total = c["gross_volume_m3"]

    dependency = c[
        "groundwater_dependency_pct"
    ]


    cols = st.columns(4)


    with cols[0]:

        metric_card(
            "Total Water Requirement",
            f"{total:,.0f} m³",
            "Current modelled irrigation requirement",
        )


    with cols[1]:

        metric_card(
            "Estimated Groundwater",
            f"{groundwater:,.0f} m³",
            "Residual after surface-water contribution",
        )


    with cols[2]:

        metric_card(
            "Crop Water Demand",
            f"{c['etc_mm']:.1f} mm",
            "ETc = ETo × Kc",
        )


    with cols[3]:

        metric_card(
            "Groundwater Dependency",
            f"{dependency:.0f}%",
            "Estimated share of gross irrigation",
        )


    st.html(
        '<div class="section-title">'
        'Farm Water Snapshot'
        '</div>'
    )


    left, right = st.columns(
        [1.55, 1]
    )


    with left:

        chart = pd.DataFrame(

            {

                "Day":
                    pd.date_range(
                        end=date.today(),
                        periods=7,
                    ),

                "Total water (m³)": [
                    total * 0.72,
                    total * 0.78,
                    total * 0.83,
                    total,
                    total * 0.92,
                    total * 0.86,
                    total * 0.79,
                ],

                "Groundwater (m³)": [
                    groundwater * 0.72,
                    groundwater * 0.78,
                    groundwater * 0.83,
                    groundwater,
                    groundwater * 0.92,
                    groundwater * 0.86,
                    groundwater * 0.79,
                ],
            }

        ).set_index("Day")


        st.html(
            '<div class="card">'
        )

        st.markdown(
            "**Water Usage Trend**"
        )

        st.caption(
            "Illustrative prototype trend based "
            "on the current account."
        )

        st.line_chart(chart)

        st.html(
            '</div>'
        )


    with right:

        st.html(

            f"""
            <div class="card">

                <div class="metric-label">
                    AquaGuard Insight
                </div>

                <div class="big-number">
                    {dependency:.0f}%
                </div>

                <p class="small-muted">

                    of the modelled gross irrigation
                    requirement is currently estimated
                    to come from groundwater.

                </p>

                <span class="pill pill-green">
                    Decision-ready account
                </span>

            </div>
            """
        )


        st.markdown("")


        st.html(

            """
            <div class="recommendation">

                <b>
                    💡 Current recommendation
                </b>

                <p style="margin:8px 0 0;color:#5E5140">

                    Review the planned irrigation amount
                    against the calculated crop requirement
                    before pumping.

                    Use What-If Scenarios to test a lower
                    groundwater-dependent option.

                </p>

            </div>
            """
        )


    st.html(
        '<div class="section-title">'
        'Quick Actions'
        '</div>'
    )


    q1, q2, q3 = st.columns(3)


    with q1:

        if st.button(
            "💧 Recalculate Water Account",
            use_container_width=True,
            type="primary",
        ):

            st.session_state.calculation = (
                run_calculation(
                    st.session_state.farm
                )
            )

            st.rerun()


    with q2:

        if st.button(
            "📊 Run What-If Scenarios",
            use_container_width=True,
        ):

            st.info(
                "Open What-If Scenarios "
                "from the sidebar."
            )


    with q3:

        if st.button(
            "🌱 Update Farm Data",
            use_container_width=True,
        ):

            st.info(
                "Open Farm Setup "
                "from the sidebar."
            )


# ============================================================
# PAGE 2 — FARM SETUP
# ============================================================

elif page == "Farm Setup":

    st.title("🌱 Farm Setup")

    st.caption(
        "Create the farm profile used by "
        "the AquaGuard calculation engine."
    )


    f = st.session_state.farm


    with st.form("farm_setup"):

        a, b = st.columns(2)


        with a:

            district = st.text_input(
                "District",
                f["district"],
            )

            tehsil = st.text_input(
                "Tehsil",
                f["tehsil"],
            )

            area = st.number_input(
                "Farm area (hectares)",
                min_value=0.01,
                value=float(f["area_ha"]),
                step=0.01,
            )


            crops = [
                "Wheat",
                "Maize",
                "Rice",
                "Cotton",
                "Sugarcane",
            ]


            crop = st.selectbox(
                "Crop",
                crops,
                index=crops.index(
                    f["crop"]
                ),
            )


            sowing = st.date_input(
                "Sowing date",
                f["sowing_date"],
            )


        with b:

            soils = [
                "Loam",
                "Sandy Loam",
                "Clay Loam",
                "Clay",
            ]


            soil = st.selectbox(
                "Soil type",
                soils,
                index=soils.index(
                    f["soil"]
                ),
            )


            methods = [
                "Flood",
                "Drip",
                "Sprinkler",
            ]


            method = st.selectbox(
                "Irrigation method",
                methods,
                index=methods.index(
                    f["irrigation_method"]
                ),
            )


            sources = [
                "Tubewell only",
                "Canal only",
                "Canal + Tubewell",
            ]


            source = st.selectbox(
                "Water source",
                sources,
                index=sources.index(
                    f["water_source"]
                ),
            )


            canal = st.number_input(
                "Estimated surface/canal water used (m³)",
                min_value=0.0,
                value=float(
                    f["canal_water_m3"]
                ),
                step=10.0,
            )


        submitted = st.form_submit_button(
            "💾 Save Farm Profile",
            type="primary",
            use_container_width=True,
        )


    if submitted:

        st.session_state.farm = {

            "district": district,

            "tehsil": tehsil,

            "area_ha": area,

            "crop": crop,

            "sowing_date": sowing,

            "soil": soil,

            "irrigation_method":
                method,

            "water_source":
                source,

            "canal_water_m3":
                canal,
        }


        st.session_state.calculation = (
            run_calculation(
                st.session_state.farm
            )
        )


        save_farm(
            str(DB_PATH),
            st.session_state.farm,
        )


        st.success(
            "Farm profile saved and "
            "water account recalculated."
        )


    st.markdown(
        "### Current Profile"
    )


    st.json(
        st.session_state.farm
    )


# ============================================================
# PAGE 3 — FARM INTELLIGENCE
# ============================================================

elif page == "Farm Intelligence":

    st.title(
        "🛰️ Farm Intelligence"
    )

    st.caption(
        "Satellite-style crop condition signals "
        "and weather inputs used as decision evidence."
    )


    f = st.session_state.farm


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "NDVI",
        "0.68",
        "Healthy vegetation",
    )


    c2.metric(
        "Temperature",
        "27 °C",
        "Prototype weather input",
    )


    c3.metric(
        "Rainfall",
        "2.4 mm",
        "Recent rainfall",
    )


    c4.metric(
        "ETo",
        "5.2 mm/day",
        "Reference ET",
    )


    left, right = st.columns(
        [1.2, 1]
    )


    with left:

        st.html(

            """
            <div class="card">

                <h3>
                    🌿 Crop Condition
                </h3>

                <p class="small-muted">

                    NDVI is used as observed
                    crop-condition evidence.

                    It is not directly converted
                    into an irrigation volume.

                </p>

            </div>
            """
        )


        ndvi_df = pd.DataFrame(

            {
                "NDVI":
                    [
                        0.58,
                        0.61,
                        0.64,
                        0.67,
                        0.68,
                        0.68,
                        0.68,
                    ]
            },

            index=[
                "-6d",
                "-5d",
                "-4d",
                "-3d",
                "-2d",
                "-1d",
                "Today",
            ],
        )


        st.line_chart(
            ndvi_df
        )


    with right:

        st.html(

            """
            <div class="callout">

                <b>
                    Interpretation
                </b>

                <p>

                    Vegetation condition is currently
                    represented as healthy in this
                    prototype.

                    The water engine remains responsible
                    for estimating irrigation quantity.

                </p>

            </div>
            """
        )


    st.markdown(
        "### Current Crop"
    )


    st.info(
        f"{f['crop']} • "
        f"{f['area_ha']:.2f} ha • "
        f"{f['soil']} • "
        f"{f['irrigation_method']}"
    )


# ============================================================
# PAGE 4 — WATER ACCOUNT
# ============================================================

elif page == "Water Account":

    st.title(
        "💧 Water Account"
    )

    st.caption(
        "Transparent crop-water and groundwater "
        "accounting for the current farm."
    )


    c = ensure_calculation()


    a, b, c3, d = st.columns(4)


    a.metric(
        "ETo",
        f"{c['eto_mm']:.1f} mm",
    )


    b.metric(
        "ETc",
        f"{c['etc_mm']:.1f} mm",
    )


    c3.metric(
        "Gross Irrigation",
        f"{c['gross_irrigation_mm']:.1f} mm",
    )


    d.metric(
        "Groundwater",
        f"{c['groundwater_m3']:,.0f} m³",
    )


    st.markdown(
        "### Calculation Breakdown"
    )


    breakdown = pd.DataFrame(

        {

            "Component":

                [

                    "Reference evapotranspiration (ETo)",

                    "Crop coefficient (Kc)",

                    "Crop evapotranspiration (ETc)",

                    "Effective rainfall",

                    "Soil-water contribution",

                    "Net irrigation requirement",

                    "Application efficiency",

                    "Gross irrigation requirement",

                    "Gross farm volume",

                    "Surface-water contribution",

                    "Estimated groundwater",
                ],


            "Value":

                [

                    f"{c['eto_mm']:.2f} mm",

                    f"{c['kc']:.2f}",

                    f"{c['etc_mm']:.2f} mm",

                    f"{c['effective_rain_mm']:.2f} mm",

                    f"{c['soil_water_contribution_mm']:.2f} mm",

                    f"{c['net_irrigation_mm']:.2f} mm",

                    f"{c['application_efficiency']*100:.0f}%",

                    f"{c['gross_irrigation_mm']:.2f} mm",

                    f"{c['gross_volume_m3']:,.1f} m³",

                    f"{c['surface_water_m3']:,.1f} m³",

                    f"{c['groundwater_m3']:,.1f} m³",
                ],
        }
    )


    st.dataframe(
        breakdown,
        use_container_width=True,
        hide_index=True,
    )


    if st.button(
        "💾 Save Water Account",
        type="primary",
    ):

        save_water_account(
            str(DB_PATH),
            st.session_state.farm,
            c,
        )

        st.success(
            "Water account saved to SQLite."
        )


# ============================================================
# PAGE 5 — AQUAGUARD DECISION
# ============================================================

elif page == "AquaGuard Decision":

    st.title(
        "🛡️ AquaGuard Decision"
    )

    st.caption(
        "Compare the farm's planned irrigation "
        "with a modelled water-balanced option."
    )


    c = ensure_calculation()


    baseline_mm = st.number_input(

        "Farmer planned irrigation (mm)",

        min_value=0.0,

        value=max(
            5.0,
            round(
                c["gross_irrigation_mm"] + 10,
                1,
            ),
        ),

        step=1.0,
    )


    recommended_mm = (
        c["gross_irrigation_mm"]
    )


    result = compare_scenarios(

        baseline_mm=baseline_mm,

        aquaguard_mm=
            recommended_mm,

        area_ha=
            st.session_state.farm[
                "area_ha"
            ],

        groundwater_fraction=
            c["groundwater_fraction"],
    )


    x, y, z = st.columns(3)


    x.metric(
        "Planned Groundwater",
        f"{result['baseline_groundwater_m3']:,.0f} m³",
    )


    y.metric(
        "AquaGuard Groundwater",
        f"{result['aquaguard_groundwater_m3']:,.0f} m³",
    )


    z.metric(
        "Potential Saving",
        f"{result['potential_saving_m3']:,.0f} m³",
    )


    st.html(

        f"""
        <div class="recommendation">

            <h3>
                💡 AquaGuard Recommendation
            </h3>

            <p>

                Modelled crop-water demand indicates
                approximately

                <b>
                    {recommended_mm:.1f} mm
                </b>

                of gross irrigation for this period.

                The comparison estimates a potential
                groundwater saving of

                <b>
                    {result['potential_saving_m3']:,.0f} m³
                </b>

                versus the entered plan.

            </p>


            <p class="small-muted">

                This is a modelled potential saving,
                not a measured reduction in pumping.

            </p>

        </div>
        """
    )


# ============================================================
# PAGE 6 — WHAT-IF SCENARIOS
# ============================================================

elif page == "What-If Scenarios":

    st.title(
        "📊 What-If Scenarios"
    )

    st.caption(
        "Test irrigation choices before pumping."
    )


    c = ensure_calculation()

    f = st.session_state.farm


    baseline = st.number_input(

        "Scenario A — Farmer plan (mm)",

        min_value=0.0,

        max_value=200.0,

        value=float(
            round(
                c["gross_irrigation_mm"] + 10,
                1,
            )
        ),

        step=1.0,
    )


    aqua = st.number_input(

        "Scenario B — AquaGuard option (mm)",

        min_value=0.0,

        max_value=200.0,

        value=float(
            round(
                c["gross_irrigation_mm"],
                1,
            )
        ),

        step=1.0,
    )


    conservative = st.number_input(

        "Scenario C — Lower application (mm)",

        min_value=0.0,

        max_value=200.0,

        value=float(
            round(
                max(
                    0,
                    c["gross_irrigation_mm"] - 5,
                ),
                1,
            )
        ),

        step=1.0,
    )


    rows = []


    for name, mm in [

        ("Farmer plan", baseline),

        ("AquaGuard", aqua),

        ("Lower application", conservative),

    ]:

        volume = (
            mm *
            f["area_ha"] *
            10
        )


        groundwater = (
            volume *
            c["groundwater_fraction"]
        )


        rows.append(

            [
                name,
                mm,
                volume,
                groundwater,
            ]
        )


    df = pd.DataFrame(

        rows,

        columns=[
            "Scenario",
            "Irrigation (mm)",
            "Total water (m³)",
            "Estimated groundwater (m³)",
        ],
    )


    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


    st.bar_chart(

        df.set_index(
            "Scenario"
        )[

            [
                "Total water (m³)",
                "Estimated groundwater (m³)",
            ]
        ]
    )


    st.warning(

        "The lowest-water scenario is not automatically "
        "the best decision. AquaGuard's intended objective "
        "is to meet crop water needs while reducing "
        "unnecessary groundwater dependence."
    )


# ============================================================
# PAGE 7 — DOCUMENT RAG
# ============================================================

elif page == "Document RAG":

    st.title("📚 Document RAG")
    st.caption(
        "Upload PDF documents, build a local FAISS knowledge base, "
        "and ask questions using retrieval-augmented generation."
    )

    st.html(
        """
        <div class="callout">
            <b>How it works</b>
            <p style="margin:8px 0 0;">
                PDF extraction → text cleaning → overlapping chunks →
                local sentence-transformer embeddings → FAISS retrieval →
                Groq LLM answer with source/page references.
            </p>
        </div>
        """
    )

    left, right = st.columns([1.15, 1])

    with left:
        st.subheader("1. Build Knowledge Base")

        uploaded_files = st.file_uploader(
            "Upload one or more PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
            help="Text-based PDFs are supported. Scanned/image-only PDFs require OCR.",
        )

        chunk_size = st.slider(
            "Chunk size (characters)",
            min_value=400,
            max_value=1800,
            value=900,
            step=100,
        )

        chunk_overlap = st.slider(
            "Chunk overlap (characters)",
            min_value=50,
            max_value=400,
            value=150,
            step=25,
        )

        top_k = st.slider(
            "Retrieved chunks per question",
            min_value=2,
            max_value=8,
            value=4,
        )

        if st.button(
            "🔨 Build / Replace Knowledge Base",
            type="primary",
            use_container_width=True,
        ):
            if not uploaded_files:
                st.warning("Please upload at least one PDF.")
            elif chunk_overlap >= chunk_size:
                st.error("Chunk overlap must be smaller than chunk size.")
            else:
                with st.spinner(
                    "Extracting PDFs, creating chunks, embedding text, and building FAISS..."
                ):
                    try:
                        info = build_knowledge_base(
                            uploaded_files,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                        )
                        st.session_state["rag_store_info"] = info
                        st.session_state["rag_messages"] = []
                        st.success(
                            f"Knowledge base ready: {info['documents']} document(s), "
                            f"{info['chunks']} chunk(s)."
                        )
                    except Exception as exc:
                        st.error(f"Knowledge-base build failed: {exc}")

    with right:
        st.subheader("Knowledge Base Status")

        try:
            info = get_store_info()
        except Exception:
            info = None

        if info:
            st.metric("Documents", info.get("documents", 0))
            st.metric("Indexed chunks", info.get("chunks", 0))
            st.caption(
                f"Embedding model: {info.get('embedding_model', 'N/A')}"
            )
            st.caption(
                f"Vector dimension: {info.get('dimension', 'N/A')}"
            )
        else:
            st.info(
                "No FAISS knowledge base found yet. "
                "Upload PDFs and click Build / Replace Knowledge Base."
            )

        st.markdown("### API configuration")
        st.caption(
            "The Groq API key is read from GROQ_API_KEY. "
            "Do not hard-code the key in app.py or commit it to GitHub."
        )

    st.divider()

    st.subheader("2. Ask Your Documents")

    if "rag_messages" not in st.session_state:
        st.session_state["rag_messages"] = []

    for message in st.session_state["rag_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask a question about the uploaded documents..."
    )

    if question:
        st.session_state["rag_messages"].append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving relevant passages and generating answer..."):
                try:
                    answer, sources = ask_rag(
                        question,
                        top_k=top_k,
                    )

                    st.markdown(answer)

                    if sources:
                        with st.expander("📌 Retrieved sources"):
                            for source in sources:
                                st.markdown(
                                    f"- **{source['source']}**, "
                                    f"page {source['page']} "
                                    f"(similarity: {source['score']:.3f})"
                                )

                    st.session_state["rag_messages"].append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as exc:
                    error_message = f"RAG query failed: {exc}"
                    st.error(error_message)
                    st.session_state["rag_messages"].append(
                        {"role": "assistant", "content": error_message}
                    )


# ============================================================
# PAGE 8 — REPORTS
# ============================================================

elif page == "Reports":

    st.title(
        "📄 AquaGuard Report"
    )

    st.caption(
        "A concise prototype report for "
        "the current farm account."
    )


    c = ensure_calculation()

    f = st.session_state.farm


    st.html(

        f"""
        <div class="card">

            <h2 style="color:#082A4A;margin-top:0">

                Farm Water Intelligence Report

            </h2>


            <p>

                <b>Location:</b>

                {html.escape(f['district'])},
                {html.escape(f['tehsil'])}

            </p>


            <p>

                <b>Crop:</b>
                {html.escape(f['crop'])}

                &nbsp; | &nbsp;

                <b>Area:</b>
                {f['area_ha']:.2f} ha

                &nbsp; | &nbsp;

                <b>Soil:</b>
                {html.escape(f['soil'])}

            </p>


            <hr>


            <p>

                <b>Estimated crop demand:</b>
                {c['etc_mm']:.1f} mm

            </p>


            <p>

                <b>Gross irrigation requirement:</b>
                {c['gross_irrigation_mm']:.1f} mm

            </p>


            <p>

                <b>Total modelled irrigation volume:</b>
                {c['gross_volume_m3']:,.0f} m³

            </p>


            <p>

                <b>Estimated groundwater:</b>
                {c['groundwater_m3']:,.0f} m³

            </p>


            <p>

                <b>Groundwater dependency:</b>
                {c['groundwater_dependency_pct']:.0f}%

            </p>


            <hr>


            <p class="small-muted">

                AquaGuard is a prototype decision-support
                system.

                Values depend on assumptions and
                user-provided inputs.

                Potential savings are not direct measurements
                of groundwater extraction.

            </p>

        </div>
        """
    )


    st.download_button(

        "⬇️ Download Report Data (CSV)",

        data=pd.DataFrame(

            [
                {
                    **f,
                    **c,
                }
            ]

        ).to_csv(
            index=False
        ).encode("utf-8"),

        file_name=
            "aquaguard_water_report.csv",

        mime=
            "text/csv",

        use_container_width=True,
    )


    recent = fetch_recent_accounts(
        str(DB_PATH)
    )


    if recent:

        st.markdown(
            "### Saved Accounts"
        )

        st.dataframe(

            pd.DataFrame(
                recent
            ),

            use_container_width=True,

            hide_index=True,
        )
