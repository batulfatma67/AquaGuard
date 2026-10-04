import unittest
from datetime import date, timedelta

from engine.reference_data import crop_kc, growth_stage
from engine.scenario_engine import compare_scenarios, recommend
from engine.water_engine import calculate_water_account


def account(**overrides):
    args = dict(
        eto_mm=5.0, kc=1.0, effective_rain_mm=0.0, soil_water_contribution_mm=0.0,
        application_efficiency=0.5, area_ha=2.0, surface_water_m3=0.0, period_days=1.0,
    )
    args.update(overrides)
    return calculate_water_account(**args)


class WaterEngineTests(unittest.TestCase):
    def test_hand_calculated_example(self):
        r = account()
        self.assertAlmostEqual(r["etc_mm"], 5.0)
        self.assertAlmostEqual(r["gross_irrigation_mm"], 10.0)
        self.assertAlmostEqual(r["gross_volume_m3"], 200.0)  # 10 mm x 2 ha x 10
        self.assertAlmostEqual(r["groundwater_dependency_pct"], 100.0)

    def test_period_scales_demand(self):
        self.assertAlmostEqual(account(period_days=7)["etc_mm"], 35.0)

    def test_rain_and_soil_reduce_need_but_not_below_zero(self):
        self.assertAlmostEqual(account(effective_rain_mm=2, soil_water_contribution_mm=1)["net_irrigation_mm"], 2.0)
        r = account(effective_rain_mm=50)
        self.assertEqual(r["gross_volume_m3"], 0.0)
        self.assertEqual(r["groundwater_dependency_pct"], 0.0)

    def test_surface_water_is_capped_at_gross_volume(self):
        r = account(surface_water_m3=500.0)
        self.assertAlmostEqual(r["surface_water_m3"], 200.0)
        self.assertEqual(r["groundwater_m3"], 0.0)

    def test_invalid_inputs(self):
        for bad in ({"application_efficiency": 0}, {"application_efficiency": 1.2},
                    {"area_ha": 0}, {"eto_mm": -1}, {"surface_water_m3": -1}, {"period_days": 0}):
            with self.assertRaises(ValueError):
                account(**bad)


class ScenarioEngineTests(unittest.TestCase):
    def test_difference_and_stress(self):
        acc = account(surface_water_m3=40.0)  # need: 10 mm gross
        rows = compare_scenarios([("Plan", 20.0), ("Exact", 10.0), ("Short", 5.0)], acc, 2.0)
        self.assertAlmostEqual(rows[0]["groundwater_m3"], 400.0 - 40.0)
        self.assertAlmostEqual(rows[1]["difference_vs_baseline_m3"], 200.0)
        self.assertFalse(rows[1]["stress_risk"])
        self.assertTrue(rows[2]["stress_risk"])
        self.assertEqual(recommend(rows)["name"], "Exact")


class ReferenceDataTests(unittest.TestCase):
    def test_stage_and_kc(self):
        sown = date.today() - timedelta(days=85)
        stage, days = growth_stage("Wheat", sown)
        self.assertEqual((stage, days), ("Mid-season", 85))
        self.assertAlmostEqual(crop_kc("Wheat", stage), 1.05)

    def test_missing_csv_stage_falls_back(self):
        self.assertGreater(crop_kc("Rice", "Development"), 0)


if __name__ == "__main__":
    unittest.main()
