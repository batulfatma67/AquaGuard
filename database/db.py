import sqlite3

from pathlib import Path
from datetime import datetime


# ============================================================
# CONNECTION
# ============================================================

def get_connection(
    db_path: str
):

    Path(db_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        db_path
    )

    conn.row_factory = (
        sqlite3.Row
    )

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db(
    db_path: str
):

    conn = get_connection(
        db_path
    )

    cur = conn.cursor()


    cur.executescript(
        """

        CREATE TABLE IF NOT EXISTS farms (

            farm_id
                INTEGER PRIMARY KEY AUTOINCREMENT,

            district
                TEXT NOT NULL,

            tehsil
                TEXT,

            area_ha
                REAL NOT NULL,

            crop
                TEXT NOT NULL,

            sowing_date
                TEXT,

            soil_type
                TEXT,

            irrigation_method
                TEXT,

            water_source
                TEXT,

            canal_water_m3
                REAL DEFAULT 0,

            created_at
                TEXT NOT NULL
        );


        CREATE TABLE IF NOT EXISTS water_accounts (

            account_id
                INTEGER PRIMARY KEY AUTOINCREMENT,

            farm_id
                INTEGER,

            eto_mm
                REAL,

            kc
                REAL,

            etc_mm
                REAL,

            effective_rain_mm
                REAL,

            soil_water_contribution_mm
                REAL,

            net_irrigation_mm
                REAL,

            application_efficiency
                REAL,

            gross_irrigation_mm
                REAL,

            gross_volume_m3
                REAL,

            surface_water_m3
                REAL,

            groundwater_m3
                REAL,

            groundwater_dependency_pct
                REAL,

            created_at
                TEXT NOT NULL,

            FOREIGN KEY(farm_id)
                REFERENCES farms(farm_id)
        );


        CREATE TABLE IF NOT EXISTS scenarios (

            scenario_id
                INTEGER PRIMARY KEY AUTOINCREMENT,

            farm_id
                INTEGER,

            scenario_name
                TEXT,

            irrigation_mm
                REAL,

            groundwater_m3
                REAL,

            potential_saving_m3
                REAL,

            created_at
                TEXT NOT NULL,

            FOREIGN KEY(farm_id)
                REFERENCES farms(farm_id)
        );

        """
    )


    conn.commit()

    conn.close()


# ============================================================
# SAVE FARM
# ============================================================

def save_farm(
    db_path: str,
    farm: dict
) -> int:

    conn = get_connection(
        db_path
    )

    cur = conn.cursor()


    cur.execute(

        """

        INSERT INTO farms
        (
            district,
            tehsil,
            area_ha,
            crop,
            sowing_date,
            soil_type,
            irrigation_method,
            water_source,
            canal_water_m3,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )

        """,

        (

            farm["district"],

            farm["tehsil"],

            farm["area_ha"],

            farm["crop"],

            str(
                farm["sowing_date"]
            ),

            farm["soil"],

            farm["irrigation_method"],

            farm["water_source"],

            farm["canal_water_m3"],

            datetime.now().isoformat(
                timespec="seconds"
            ),
        )
    )


    farm_id = cur.lastrowid


    conn.commit()

    conn.close()


    return farm_id


# ============================================================
# SAVE WATER ACCOUNT
# ============================================================

def save_water_account(
    db_path: str,
    farm: dict,
    result: dict
):

    conn = get_connection(
        db_path
    )

    cur = conn.cursor()


    cur.execute(

        """

        SELECT farm_id

        FROM farms

        ORDER BY farm_id DESC

        LIMIT 1

        """
    )


    row = cur.fetchone()


    farm_id = (
        row["farm_id"]
        if row
        else None
    )


    cur.execute(

        """

        INSERT INTO water_accounts
        (
            farm_id,
            eto_mm,
            kc,
            etc_mm,
            effective_rain_mm,
            soil_water_contribution_mm,
            net_irrigation_mm,
            application_efficiency,
            gross_irrigation_mm,
            gross_volume_m3,
            surface_water_m3,
            groundwater_m3,
            groundwater_dependency_pct,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )

        """,

        (

            farm_id,

            result["eto_mm"],

            result["kc"],

            result["etc_mm"],

            result[
                "effective_rain_mm"
            ],

            result[
                "soil_water_contribution_mm"
            ],

            result[
                "net_irrigation_mm"
            ],

            result[
                "application_efficiency"
            ],

            result[
                "gross_irrigation_mm"
            ],

            result[
                "gross_volume_m3"
            ],

            result[
                "surface_water_m3"
            ],

            result[
                "groundwater_m3"
            ],

            result[
                "groundwater_dependency_pct"
            ],

            datetime.now().isoformat(
                timespec="seconds"
            ),
        )
    )


    conn.commit()

    conn.close()


# ============================================================
# FETCH RECENT WATER ACCOUNTS
# ============================================================

def fetch_recent_accounts(
    db_path: str,
    limit: int = 10
):

    conn = get_connection(
        db_path
    )

    cur = conn.cursor()


    cur.execute(

        """

        SELECT

            account_id,

            eto_mm,

            etc_mm,

            gross_volume_m3,

            groundwater_m3,

            groundwater_dependency_pct,

            created_at

        FROM water_accounts

        ORDER BY account_id DESC

        LIMIT ?

        """,

        (limit,)
    )


    rows = [

        dict(row)

        for row
        in cur.fetchall()
    ]


    conn.close()


    return rows
