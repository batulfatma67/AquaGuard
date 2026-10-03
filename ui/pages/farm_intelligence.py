import pandas as pd
import streamlit as st

from ui.state import ensure_calculation


def render() -> None:
    st.title("🛰️ Farm Intelligence")
    st.caption("Crop condition signals and weather inputs used as decision evidence.")

    f = st.session_state.farm
    inputs = st.session_state.inputs
    c = ensure_calculation()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NDVI", "0.68", "Illustrative sample")
    c2.metric("Crop stage", c["crop_stage"], f"{c['days_after_sowing']} days after sowing")
    c3.metric("Rainfall (period)", f"{inputs['rain_mm']:.1f} mm", "User-entered")
    c4.metric("ETo", f"{inputs['eto_mm']:.1f} mm/day", "User-entered")

    left, right = st.columns([1.2, 1])
    with left:
        st.html(
            """
            <div class="card">
                <h3>🌿 Crop Condition</h3>
                <p class="small-muted">
                    NDVI is shown as observed crop-condition evidence only. It is not
                    converted into an irrigation volume. Values below are illustrative
                    samples until a satellite data source is connected.
                </p>
            </div>
            """
        )
        ndvi_df = pd.DataFrame(
            {"NDVI": [0.58, 0.61, 0.64, 0.67, 0.68, 0.68, 0.68]},
            index=["-6d", "-5d", "-4d", "-3d", "-2d", "-1d", "Today"],
        )
        st.line_chart(ndvi_df)

    with right:
        st.html(
            """
            <div class="callout">
                <b>Interpretation</b>
                <p>
                    Vegetation condition is represented as healthy in this prototype.
                    The water engine remains responsible for estimating irrigation quantity.
                    Edit ETo and rainfall on the Water Account page.
                </p>
            </div>
            """
        )

    st.markdown("### Current Crop")
    st.info(f"{f['crop']} • {f['area_ha']:.2f} ha • {f['soil']} • {f['irrigation_method']}")
