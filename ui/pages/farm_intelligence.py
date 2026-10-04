import pandas as pd
import streamlit as st

from ui.state import ensure_calculation


def render() -> None:
    st.title("🛰️ Farm Intelligence")
    st.caption("Crop condition signals and weather inputs used as decision evidence.")

    f = st.session_state.farm
    inputs = st.session_state.inputs
    c = ensure_calculation()

    st.caption(
        f"Current crop: {f['crop']} · {f['area_ha']:.2f} ha · "
        f"{f['soil']} · {f['irrigation_method']}"
    )

    c1, c2 = st.columns(2)
    c1.metric("NDVI", "0.68", "Illustrative sample")
    c2.metric("Crop stage", c["crop_stage"], f"{c['days_after_sowing']} days after sowing")
    c3, c4 = st.columns(2)
    c3.metric("Rainfall (period)", f"{inputs['rain_mm']:.1f} mm", "User-entered")
    c4.metric("ETo", f"{inputs['eto_mm']:.1f} mm/day", "User-entered")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**🌿 Crop Condition**")
            st.caption(
                "NDVI is crop-condition evidence, not an irrigation volume. "
                "The displayed readings are illustrative until satellite data is connected."
            )

    with right:
        with st.container(border=True):
            st.markdown("**Interpretation**")
            st.caption(
                "Vegetation condition is represented as healthy in this prototype. "
                "The water engine estimates irrigation quantity. Edit ETo and rainfall "
                "on the Water Account page."
            )

    ndvi_df = pd.DataFrame(
        {"NDVI": [0.58, 0.61, 0.64, 0.67, 0.68, 0.68, 0.68]},
        index=["-6d", "-5d", "-4d", "-3d", "-2d", "-1d", "Today"],
    )
    st.line_chart(ndvi_df, height=240)
