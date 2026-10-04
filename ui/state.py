"""Session state and shared calculation helpers for the Streamlit UI."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

from config import DB_PATH, DEFAULT_INPUTS
from database.db import get_farm, get_latest_farm, init_db, save_farm
from engine.water_engine import account_for_farm

DB = str(DB_PATH)


def _default_farm() -> dict:
    return {
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


def _hydrate(farm: dict) -> dict:
    if isinstance(farm["sowing_date"], str):
        farm["sowing_date"] = date.fromisoformat(farm["sowing_date"])
    return farm


def init_state() -> None:
    init_db(DB)

    if "farm" not in st.session_state:
        farm = get_latest_farm(DB)
        if farm is None:
            farm = _default_farm()
            farm["farm_id"] = save_farm(DB, farm)
        st.session_state.farm = _hydrate(farm)

    st.session_state.setdefault("inputs", dict(DEFAULT_INPUTS))
    st.session_state.setdefault("farm_mode", "list")
    st.session_state.setdefault("form_nonce", 0)
    st.session_state.setdefault("calculation", None)
    st.session_state.setdefault("scenario_rows", None)
    st.session_state.setdefault("rag_evidence", [])
    st.session_state.setdefault("rag_messages", [])


def select_farm(farm_id: int) -> None:
    farm = get_farm(DB, farm_id)
    if farm:
        st.session_state.farm = _hydrate(farm)
        st.session_state.farm_mode = "list"
        st.session_state.form_nonce += 1
        st.session_state.calculation = None
        st.session_state.scenario_rows = None


def set_farm_mode(mode: str) -> None:
    """Farm Profiles view: list | pick | new | edit. Use as a button callback."""
    st.session_state.farm_mode = mode
    st.session_state.form_nonce += 1


def start_new_farm() -> None:
    """Open a blank form; nothing is saved until the user clicks Save."""
    set_farm_mode("new")
    st.session_state["nav"] = "🌱  Farm Profiles"  # safe only because this runs as a button callback


def view_farm(farm_id: int) -> None:
    """Show the detail table for one farm without changing the active farm."""
    st.session_state.view_farm_id = farm_id
    set_farm_mode("view")


def edit_viewed_farm() -> None:
    select_farm(st.session_state.view_farm_id)
    set_farm_mode("edit")


def activate_viewed_farm() -> None:
    select_farm(st.session_state.view_farm_id)
    set_farm_mode("view")


def activate_picked_farm() -> None:
    """Make the farm chosen in the picker the active farm for all pages."""
    select_farm(st.session_state["pick_farm_id"])


def open_picked_farm() -> None:
    """Load the farm chosen in the picker into the edit form."""
    select_farm(st.session_state["pick_farm_id"])
    set_farm_mode("edit")


def recalculate() -> dict | None:
    try:
        st.session_state.calculation = account_for_farm(
            st.session_state.farm, st.session_state.inputs
        )
        st.session_state.last_calculation_at = datetime.now().strftime("%H:%M:%S")
    except ValueError as exc:
        st.session_state.calculation = None
        st.error(f"Calculation failed: {exc}")
    return st.session_state.calculation


def ensure_calculation() -> dict:
    """Current account; stops the page with a clear message if inputs are invalid."""
    if st.session_state.calculation is None:
        recalculate()
    if st.session_state.calculation is None:
        st.stop()
    return st.session_state.calculation


def go(page_label: str) -> None:
    st.session_state["nav"] = page_label
