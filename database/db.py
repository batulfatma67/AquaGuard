"""SQLite persistence for farms, water accounts, scenarios and reports."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS farms (
    farm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT NOT NULL,
    tehsil TEXT,
    area_ha REAL NOT NULL,
    crop TEXT NOT NULL,
    sowing_date TEXT,
    soil_type TEXT,
    irrigation_method TEXT,
    water_source TEXT,
    canal_water_m3 REAL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS water_accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER,
    eto_mm REAL,
    kc REAL,
    etc_mm REAL,
    effective_rain_mm REAL,
    soil_water_contribution_mm REAL,
    net_irrigation_mm REAL,
    application_efficiency REAL,
    gross_irrigation_mm REAL,
    gross_volume_m3 REAL,
    surface_water_m3 REAL,
    groundwater_m3 REAL,
    groundwater_dependency_pct REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(farm_id) REFERENCES farms(farm_id)
);

CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER,
    scenario_name TEXT,
    irrigation_mm REAL,
    groundwater_m3 REAL,
    potential_saving_m3 REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(farm_id) REFERENCES farms(farm_id)
);

CREATE TABLE IF NOT EXISTS reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER,
    title TEXT,
    content_md TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(farm_id) REFERENCES farms(farm_id)
);
"""

# Columns added after the first prototype; applied to existing databases.
MIGRATIONS = {
    "water_accounts": {
        "period_days": "REAL",
        "crop_stage": "TEXT",
        "assumptions_json": "TEXT",
    },
    "scenarios": {
        "account_id": "INTEGER",
        "volume_m3": "REAL",
        "stress_risk": "INTEGER",
    },
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def get_connection(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
        for table, columns in MIGRATIONS.items():
            existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            for name, ctype in columns.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ctype}")


# ---------------------------------------------------------------- farms

def _farm_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "farm_id": row["farm_id"],
        "district": row["district"],
        "tehsil": row["tehsil"] or "",
        "area_ha": row["area_ha"],
        "crop": row["crop"],
        "sowing_date": row["sowing_date"],
        "soil": row["soil_type"],
        "irrigation_method": row["irrigation_method"],
        "water_source": row["water_source"],
        "canal_water_m3": row["canal_water_m3"] or 0.0,
    }


def save_farm(db_path: str, farm: dict) -> int:
    """Insert the farm, or update it when farm_id is present."""
    values = (
        farm["district"], farm["tehsil"], farm["area_ha"], farm["crop"],
        str(farm["sowing_date"]), farm["soil"], farm["irrigation_method"],
        farm["water_source"], farm["canal_water_m3"],
    )
    with get_connection(db_path) as conn:
        if farm.get("farm_id"):
            conn.execute(
                """UPDATE farms SET district=?, tehsil=?, area_ha=?, crop=?, sowing_date=?,
                   soil_type=?, irrigation_method=?, water_source=?, canal_water_m3=?
                   WHERE farm_id=?""",
                values + (farm["farm_id"],),
            )
            return int(farm["farm_id"])
        cur = conn.execute(
            """INSERT INTO farms (district, tehsil, area_ha, crop, sowing_date, soil_type,
               irrigation_method, water_source, canal_water_m3, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values + (_now(),),
        )
        return int(cur.lastrowid)


def get_farm(db_path: str, farm_id: int) -> dict | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM farms WHERE farm_id=?", (farm_id,)).fetchone()
    return _farm_row_to_dict(row) if row else None


def get_latest_farm(db_path: str) -> dict | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM farms ORDER BY farm_id DESC LIMIT 1").fetchone()
    return _farm_row_to_dict(row) if row else None


def list_farms(db_path: str) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM farms ORDER BY farm_id DESC").fetchall()
    return [_farm_row_to_dict(r) for r in rows]


# ------------------------------------------------------------- accounts

def save_water_account(db_path: str, farm_id: int, result: dict, inputs: dict | None = None) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO water_accounts
               (farm_id, eto_mm, kc, etc_mm, effective_rain_mm, soil_water_contribution_mm,
                net_irrigation_mm, application_efficiency, gross_irrigation_mm, gross_volume_m3,
                surface_water_m3, groundwater_m3, groundwater_dependency_pct, created_at,
                period_days, crop_stage, assumptions_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                farm_id, result["eto_mm"], result["kc"], result["etc_mm"],
                result["effective_rain_mm"], result["soil_water_contribution_mm"],
                result["net_irrigation_mm"], result["application_efficiency"],
                result["gross_irrigation_mm"], result["gross_volume_m3"],
                result["surface_water_m3"], result["groundwater_m3"],
                result["groundwater_dependency_pct"], _now(),
                result.get("period_days"), result.get("crop_stage"),
                json.dumps(inputs, default=str) if inputs else None,
            ),
        )
        return int(cur.lastrowid)


def fetch_recent_accounts(db_path: str, limit: int = 10, farm_id: int | None = None) -> list[dict]:
    query = """SELECT account_id, farm_id, crop_stage, period_days, eto_mm, etc_mm,
                      gross_volume_m3, groundwater_m3, groundwater_dependency_pct, created_at
               FROM water_accounts"""
    params: list = []
    if farm_id is not None:
        query += " WHERE farm_id = ?"
        params.append(farm_id)
    query += " ORDER BY account_id DESC LIMIT ?"
    params.append(limit)
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(query, params)]


# ------------------------------------------------------------ scenarios

def save_scenarios(db_path: str, farm_id: int, rows: list[dict], account_id: int | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.executemany(
            """INSERT INTO scenarios
               (farm_id, scenario_name, irrigation_mm, groundwater_m3, potential_saving_m3,
                created_at, account_id, volume_m3, stress_risk)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    farm_id, r["name"], r["irrigation_mm"], r["groundwater_m3"],
                    r["difference_vs_baseline_m3"], _now(), account_id,
                    r["volume_m3"], int(r["stress_risk"]),
                )
                for r in rows
            ],
        )


def fetch_recent_scenarios(db_path: str, limit: int = 20, farm_id: int | None = None) -> list[dict]:
    query = """SELECT scenario_id, scenario_name, irrigation_mm, volume_m3, groundwater_m3,
                      potential_saving_m3, stress_risk, created_at FROM scenarios"""
    params: list = []
    if farm_id is not None:
        query += " WHERE farm_id = ?"
        params.append(farm_id)
    query += " ORDER BY scenario_id DESC LIMIT ?"
    params.append(limit)
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(query, params)]


# -------------------------------------------------------------- reports

def save_report(db_path: str, farm_id: int, title: str, content_md: str) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO reports (farm_id, title, content_md, created_at) VALUES (?, ?, ?, ?)",
            (farm_id, title, content_md, _now()),
        )
        return int(cur.lastrowid)


def fetch_reports(db_path: str, limit: int = 10, farm_id: int | None = None) -> list[dict]:
    query = "SELECT report_id, farm_id, title, content_md, created_at FROM reports"
    params: list = []
    if farm_id is not None:
        query += " WHERE farm_id = ?"
        params.append(farm_id)
    query += " ORDER BY report_id DESC LIMIT ?"
    params.append(limit)
    with get_connection(db_path) as conn:
        return [dict(r) for r in conn.execute(query, params)]
