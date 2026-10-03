from datetime import date

import pandas as pd
import streamlit as st

from config import CROPS, IRRIGATION_METHODS, SOILS, WATER_SOURCES
from database.db import get_farm, list_farms, save_farm
from engine.reference_data import load_locations
from ui.state import (
    DB,
    activate_picked_farm,
    activate_viewed_farm,
    edit_viewed_farm,
    open_picked_farm,
    recalculate,
    set_farm_mode,
    start_new_farm,
    view_farm,
)

NO_TEHSIL_DATA = "Entire district"
AREA_OPTIONS = list(range(1, 1001))
REQUIRED = ["District", "Tehsil", "Farm area", "Crop", "Soil type", "Irrigation method", "Water source"]


def _with_current(options: list, current) -> list:
    """Keep a previously saved value selectable even if it is not in the list."""
    return options if current in options else sorted(options + [current])


def _idx(options: list, value):
    return options.index(value) if value in options else None


def render() -> None:
    st.title("🌱 Farm Profiles")
    mode = st.session_state.farm_mode
    if mode == "pick":
        _render_picker()
    elif mode == "view":
        _render_detail()
    elif mode in ("new", "edit"):
        _render_form(is_new=mode == "new")
    else:
        _render_list()


def _render_list() -> None:
    st.caption("Saved farm profiles used by the AquaGuard calculation engine. "
               "Click Open to see all details of a farm.")
    farms = list_farms(DB)
    active = st.session_state.farm["farm_id"]

    widths = [0.7, 0.8, 1.5, 1.6, 0.9, 1.0, 1.6, 0.9]
    with st.container(border=True):
        header = st.columns(widths)
        for col, title in zip(header, ["Active", "Farm ID", "District", "Tehsil", "Area (ha)",
                                       "Crop", "Water source", ""]):
            col.markdown(f"**{title}**")
        for f in farms:
            c = st.columns(widths, vertical_alignment="center")
            c[0].write("✔" if f["farm_id"] == active else "")
            c[1].write(f"#{f['farm_id']}")
            c[2].write(f["district"])
            c[3].write(f["tehsil"])
            c[4].write(f"{f['area_ha']:g}")
            c[5].write(f["crop"])
            c[6].write(f["water_source"])
            c[7].button("Open", key=f"open_farm_{f['farm_id']}", width="stretch",
                        on_click=view_farm, args=(f["farm_id"],))

    st.caption(f"{len(farms)} saved farm(s). The active farm (✔) is used on all other pages; "
               "open a farm and click Set as active farm to change it.")

    a, b = st.columns(2)
    a.button("✏️ Edit Existing Farm Profile", width="stretch",
             on_click=set_farm_mode, args=("pick",))
    b.button("➕ New Farm Profile", type="primary", width="stretch", on_click=start_new_farm)


def _render_detail() -> None:
    farm = get_farm(DB, st.session_state.view_farm_id)
    if farm is None:
        set_farm_mode("list")
        st.rerun()

    is_active = farm["farm_id"] == st.session_state.farm["farm_id"]
    st.subheader(f"Farm #{farm['farm_id']} • {farm['crop']} • {farm['district']}")
    st.caption("Active farm ✔" if is_active else "Not the active farm.")

    details = [
        ("Farm ID", f"#{farm['farm_id']}"),
        ("District", farm["district"]),
        ("Tehsil", farm["tehsil"]),
        ("Farm area", f"{farm['area_ha']:g} ha"),
        ("Crop", farm["crop"]),
        ("Sowing date", date.fromisoformat(farm["sowing_date"]).strftime("%d %b %Y")),
        ("Soil type", farm["soil"]),
        ("Irrigation method", farm["irrigation_method"]),
        ("Water source", farm["water_source"]),
        ("Surface/canal water used", f"{farm['canal_water_m3']:,.0f} m³"),
    ]
    st.dataframe(pd.DataFrame(details, columns=["Field", "Value"]), width="stretch", hide_index=True)

    a, b, c = st.columns(3)
    a.button("← Back to Farm Profiles", width="stretch", on_click=set_farm_mode, args=("list",))
    b.button("✏️ Edit this profile", width="stretch", on_click=edit_viewed_farm)
    c.button("Active farm ✔" if is_active else "Set as active farm", type="primary",
             width="stretch", disabled=is_active, on_click=activate_viewed_farm)


def _render_picker() -> None:
    st.caption("Choose the farm profile you want to edit.")
    farms = list_farms(DB)
    labels = {
        f["farm_id"]: f"#{f['farm_id']} • {f['crop']} • {f['area_ha']:g} ha • "
                      f"{f['district']}, {f['tehsil']}"
        for f in farms
    }
    ids = list(labels)
    st.selectbox("Existing farm profiles", ids, format_func=labels.get,
                 index=ids.index(st.session_state.farm["farm_id"]), key="pick_farm_id")

    a, b, c = st.columns(3)
    a.button("Open for editing", type="primary", width="stretch", on_click=open_picked_farm)
    b.button("Set as active farm", width="stretch", on_click=activate_picked_farm)
    c.button("Cancel", width="stretch", on_click=set_farm_mode, args=("list",))


def _render_form(is_new: bool) -> None:
    saved = st.session_state.farm
    # Blank draft for a new farm; otherwise the selected saved farm.
    f = {} if is_new else saved
    k = f"fs_{'new' if is_new else saved['farm_id']}_{st.session_state.form_nonce}"
    locations = load_locations()

    if is_new:
        st.info("Creating a new farm. Fill in every field and click Save Farm Profile.")
    else:
        st.info(f"Editing saved farm #{saved['farm_id']}.")

    # Not in a form: Tehsil options must update immediately when District changes.
    a, b = st.columns(2)
    with a:
        districts = sorted(locations)
        if f:
            districts = _with_current(districts, f["district"])
        district = st.selectbox("District", districts, index=_idx(districts, f.get("district")),
                                placeholder="Select district", key=f"{k}_district")

        tehsils = (locations.get(district) or [NO_TEHSIL_DATA]) if district else []
        saved_tehsil = f.get("tehsil") if f.get("district") == district else None
        if saved_tehsil:
            tehsils = _with_current(tehsils, saved_tehsil)
        tehsil = st.selectbox("Tehsil", tehsils, index=_idx(tehsils, saved_tehsil),
                              placeholder="Select district first" if not district else "Select tehsil",
                              disabled=not district, key=f"{k}_tehsil_{district}")
        if tehsils == [NO_TEHSIL_DATA]:
            st.caption("Tehsil list is not available for this district yet.")

        # Saved decimal areas (e.g. 2.02) snap to the nearest whole hectare until re-saved.
        saved_area = min(max(round(float(f["area_ha"])), 1), 1000) if f else None
        area = st.selectbox("Farm area (hectares)", AREA_OPTIONS, index=_idx(AREA_OPTIONS, saved_area),
                            placeholder="Select area", key=f"{k}_area")
        crop = st.selectbox("Crop", CROPS, index=_idx(CROPS, f.get("crop")),
                            placeholder="Select crop", key=f"{k}_crop")
        sowing = st.date_input("Sowing date", f.get("sowing_date", date.today()), key=f"{k}_sowing")

    with b:
        soil = st.selectbox("Soil type", SOILS, index=_idx(SOILS, f.get("soil")),
                            placeholder="Select soil type", key=f"{k}_soil")
        method = st.selectbox("Irrigation method", IRRIGATION_METHODS,
                              index=_idx(IRRIGATION_METHODS, f.get("irrigation_method")),
                              placeholder="Select method", key=f"{k}_method")
        source = st.selectbox("Water source", WATER_SOURCES,
                              index=_idx(WATER_SOURCES, f.get("water_source")),
                              placeholder="Select water source", key=f"{k}_source")
        canal = st.number_input("Estimated surface/canal water used (m³)", min_value=0.0,
                                value=float(f.get("canal_water_m3", 0.0)), step=10.0, key=f"{k}_canal")

    save_col, cancel_col = st.columns(2)
    save_clicked = save_col.button("💾 Save Farm Profile", type="primary", width="stretch")
    cancel_col.button("Cancel", width="stretch", on_click=set_farm_mode, args=("list",))

    if not save_clicked:
        return

    values = [district, tehsil, area, crop, soil, method, source]
    missing = [name for name, v in zip(REQUIRED, values) if v is None]
    if missing:
        st.error("Please complete: " + ", ".join(missing) + ".")
        return

    farm = {
        "farm_id": None if is_new else saved["farm_id"],
        "district": district,
        "tehsil": tehsil,
        "area_ha": float(area),
        "crop": crop,
        "sowing_date": sowing,
        "soil": soil,
        "irrigation_method": method,
        "water_source": source,
        "canal_water_m3": canal,
    }
    farm["farm_id"] = save_farm(DB, farm)
    st.session_state.farm = farm
    st.session_state.scenario_rows = None
    set_farm_mode("list")
    recalculate()
    st.toast(("New farm saved" if is_new else "Farm profile updated")
             + " and water account recalculated.", icon="✅")
    st.rerun()
