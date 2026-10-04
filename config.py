from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "aquaguard.db"
DATA_DIR = BASE_DIR / "data"
BG_PATH = BASE_DIR / "assets" / "aquaguard_landscape.svg"

# Drop a picture named assets/background.<ext> to use it behind every page.
APP_BG_PATH = next(
    (p for ext in ("jpg", "jpeg", "png", "webp", "svg")
     if (p := BASE_DIR / "assets" / f"background.{ext}").exists()),
    None,
)

CROPS = ["Wheat", "Maize", "Rice", "Cotton", "Sugarcane"]
SOILS = ["Loam", "Sandy Loam", "Clay Loam", "Clay"]
IRRIGATION_METHODS = ["Flood", "Drip", "Sprinkler"]
WATER_SOURCES = ["Tubewell only", "Canal only", "Canal + Tubewell"]

# Illustrative defaults; all are user-adjustable assumptions, not measurements.
DEFAULT_INPUTS = {
    "eto_mm": 5.2,
    "rain_mm": 4.0,
    "rain_factor": 0.8,
    "period_days": 7,
    "soil_moisture_pct": 30.0,
    "efficiency_override": None,
}
