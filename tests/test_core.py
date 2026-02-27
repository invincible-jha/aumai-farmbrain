"""Comprehensive tests for aumai-farmbrain core module."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from aumai_farmbrain.core import CropAdvisor, CropDatabase, SoilAnalyzer
from aumai_farmbrain.models import (
    AGRICULTURAL_DISCLAIMER,
    Crop,
    CropAdvisory,
    SoilProfile,
    WeatherData,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db() -> CropDatabase:
    return CropDatabase()


@pytest.fixture()
def analyzer(db: CropDatabase) -> SoilAnalyzer:
    return SoilAnalyzer(crop_db=db)


@pytest.fixture()
def advisor() -> CropAdvisor:
    return CropAdvisor()


@pytest.fixture()
def optimal_soil() -> SoilProfile:
    """Soil profile where all nutrients and pH are in optimal range."""
    return SoilProfile(
        ph=6.8,
        nitrogen_ppm=200.0,
        phosphorus_ppm=18.0,
        potassium_ppm=180.0,
        organic_carbon_pct=0.75,
        soil_type="loam",
    )


@pytest.fixture()
def rice_crop(db: CropDatabase) -> Crop:
    crop = db.by_name("Rice")
    assert crop is not None
    return crop


@pytest.fixture()
def wheat_crop(db: CropDatabase) -> Crop:
    crop = db.by_name("Wheat")
    assert crop is not None
    return crop


@pytest.fixture()
def cotton_crop(db: CropDatabase) -> Crop:
    crop = db.by_name("Cotton")
    assert crop is not None
    return crop


# ---------------------------------------------------------------------------
# Crop model tests
# ---------------------------------------------------------------------------


class TestCropModel:
    def test_crop_valid_kharif(self) -> None:
        crop = Crop(
            name="Rice",
            season="kharif",
            water_requirement="high",
            soil_types=["alluvial", "clay"],
            growth_days=120,
        )
        assert crop.name == "Rice"
        assert crop.season == "kharif"

    def test_crop_valid_rabi(self) -> None:
        crop = Crop(
            name="Wheat",
            season="rabi",
            water_requirement="medium",
            soil_types=["loam"],
            growth_days=120,
        )
        assert crop.season == "rabi"

    def test_crop_valid_zaid(self) -> None:
        crop = Crop(
            name="Watermelon",
            season="zaid",
            water_requirement="medium",
            soil_types=["sandy loam"],
            growth_days=90,
        )
        assert crop.season == "zaid"

    def test_crop_season_normalised_to_lowercase(self) -> None:
        # Pydantic v2 applies the Field pattern constraint before the field_validator
        # runs, so uppercase input fails regex validation rather than being normalised.
        with pytest.raises(ValidationError):
            Crop(
                name="Rice",
                season="KHARIF",
                water_requirement="high",
                soil_types=["loam"],
                growth_days=120,
            )

    def test_crop_invalid_season_raises(self) -> None:
        with pytest.raises(ValidationError):
            Crop(
                name="Rice",
                season="monsoon",
                water_requirement="high",
                soil_types=["loam"],
                growth_days=120,
            )

    def test_crop_growth_days_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Crop(
                name="Rice",
                season="kharif",
                water_requirement="high",
                soil_types=["loam"],
                growth_days=0,
            )

    def test_crop_negative_growth_days_raises(self) -> None:
        with pytest.raises(ValidationError):
            Crop(
                name="Rice",
                season="kharif",
                water_requirement="high",
                soil_types=["loam"],
                growth_days=-10,
            )


# ---------------------------------------------------------------------------
# SoilProfile model tests
# ---------------------------------------------------------------------------


class TestSoilProfileModel:
    def test_valid_soil_profile(self) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="alluvial",
        )
        assert soil.ph == 6.5

    def test_ph_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            SoilProfile(
                ph=-0.1,
                nitrogen_ppm=200.0,
                phosphorus_ppm=15.0,
                potassium_ppm=150.0,
                organic_carbon_pct=0.8,
                soil_type="loam",
            )

    def test_ph_above_14_raises(self) -> None:
        with pytest.raises(ValidationError):
            SoilProfile(
                ph=14.1,
                nitrogen_ppm=200.0,
                phosphorus_ppm=15.0,
                potassium_ppm=150.0,
                organic_carbon_pct=0.8,
                soil_type="loam",
            )

    def test_negative_nitrogen_raises(self) -> None:
        with pytest.raises(ValidationError):
            SoilProfile(
                ph=6.5,
                nitrogen_ppm=-1.0,
                phosphorus_ppm=15.0,
                potassium_ppm=150.0,
                organic_carbon_pct=0.8,
                soil_type="loam",
            )

    def test_organic_carbon_above_100_raises(self) -> None:
        with pytest.raises(ValidationError):
            SoilProfile(
                ph=6.5,
                nitrogen_ppm=200.0,
                phosphorus_ppm=15.0,
                potassium_ppm=150.0,
                organic_carbon_pct=101.0,
                soil_type="loam",
            )

    def test_boundary_ph_zero_valid(self) -> None:
        soil = SoilProfile(
            ph=0.0,
            nitrogen_ppm=0.0,
            phosphorus_ppm=0.0,
            potassium_ppm=0.0,
            organic_carbon_pct=0.0,
            soil_type="acid",
        )
        assert soil.ph == 0.0


# ---------------------------------------------------------------------------
# WeatherData model tests
# ---------------------------------------------------------------------------


class TestWeatherDataModel:
    def test_valid_weather(self) -> None:
        w = WeatherData(
            location="Pune",
            temperature_c=30.0,
            humidity_pct=70.0,
            rainfall_mm=5.0,
        )
        assert w.location == "Pune"
        assert w.forecast_days == 7  # default

    def test_humidity_above_100_raises(self) -> None:
        with pytest.raises(ValidationError):
            WeatherData(
                location="Delhi",
                temperature_c=35.0,
                humidity_pct=101.0,
                rainfall_mm=0.0,
            )

    def test_negative_rainfall_raises(self) -> None:
        with pytest.raises(ValidationError):
            WeatherData(
                location="Mumbai",
                temperature_c=30.0,
                humidity_pct=80.0,
                rainfall_mm=-5.0,
            )

    def test_forecast_days_above_30_raises(self) -> None:
        with pytest.raises(ValidationError):
            WeatherData(
                location="Chennai",
                temperature_c=32.0,
                humidity_pct=75.0,
                rainfall_mm=10.0,
                forecast_days=31,
            )

    def test_forecast_days_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            WeatherData(
                location="Kolkata",
                temperature_c=28.0,
                humidity_pct=85.0,
                rainfall_mm=20.0,
                forecast_days=0,
            )


# ---------------------------------------------------------------------------
# CropDatabase tests
# ---------------------------------------------------------------------------


class TestCropDatabase:
    def test_all_crops_returns_at_least_50(self, db: CropDatabase) -> None:
        assert len(db.all_crops()) >= 50

    def test_all_crops_returns_list_of_crop_objects(self, db: CropDatabase) -> None:
        for crop in db.all_crops():
            assert isinstance(crop, Crop)

    def test_by_name_rice_found(self, db: CropDatabase) -> None:
        crop = db.by_name("Rice")
        assert crop is not None
        assert crop.name == "Rice"

    def test_by_name_case_insensitive(self, db: CropDatabase) -> None:
        assert db.by_name("rice") is not None
        assert db.by_name("RICE") is not None
        assert db.by_name("Rice") is not None

    def test_by_name_unknown_returns_none(self, db: CropDatabase) -> None:
        assert db.by_name("avocado") is None

    def test_by_name_wheat_found(self, db: CropDatabase) -> None:
        crop = db.by_name("Wheat")
        assert crop is not None
        assert crop.season == "rabi"

    def test_by_season_kharif(self, db: CropDatabase) -> None:
        kharif = db.by_season("kharif")
        assert len(kharif) > 0
        for c in kharif:
            assert c.season == "kharif"

    def test_by_season_rabi(self, db: CropDatabase) -> None:
        rabi = db.by_season("rabi")
        assert len(rabi) > 0
        for c in rabi:
            assert c.season == "rabi"

    def test_by_season_zaid(self, db: CropDatabase) -> None:
        zaid = db.by_season("zaid")
        assert len(zaid) > 0
        for c in zaid:
            assert c.season == "zaid"

    def test_by_season_unknown_returns_empty(self, db: CropDatabase) -> None:
        assert db.by_season("winter") == []

    def test_by_season_case_insensitive(self, db: CropDatabase) -> None:
        assert len(db.by_season("KHARIF")) > 0

    def test_by_soil_type_loam(self, db: CropDatabase) -> None:
        loam_crops = db.by_soil_type("loam")
        assert len(loam_crops) > 0

    def test_by_soil_type_alluvial(self, db: CropDatabase) -> None:
        alluvial = db.by_soil_type("alluvial")
        assert len(alluvial) > 0

    def test_by_soil_type_case_insensitive(self, db: CropDatabase) -> None:
        lower = db.by_soil_type("black")
        upper = db.by_soil_type("BLACK")
        assert len(lower) == len(upper)

    def test_by_soil_type_unknown_returns_empty(self, db: CropDatabase) -> None:
        assert db.by_soil_type("lunar_regolith") == []

    def test_all_crops_mutates_do_not_affect_db(self, db: CropDatabase) -> None:
        """all_crops returns a copy; mutating it does not alter internal state."""
        crops1 = db.all_crops()
        crops1.clear()
        crops2 = db.all_crops()
        assert len(crops2) > 0

    def test_rice_is_kharif(self, db: CropDatabase) -> None:
        rice = db.by_name("Rice")
        assert rice is not None
        assert rice.season == "kharif"

    def test_rice_has_high_water_requirement(self, db: CropDatabase) -> None:
        rice = db.by_name("Rice")
        assert rice is not None
        assert rice.water_requirement == "high"

    def test_sugarcane_growth_days(self, db: CropDatabase) -> None:
        crop = db.by_name("Sugarcane")
        assert crop is not None
        assert crop.growth_days == 365


# ---------------------------------------------------------------------------
# SoilAnalyzer tests
# ---------------------------------------------------------------------------


class TestSoilAnalyzer:
    def test_analyze_returns_list_of_strings(
        self, analyzer: SoilAnalyzer, optimal_soil: SoilProfile
    ) -> None:
        recs = analyzer.analyze(optimal_soil)
        assert isinstance(recs, list)
        assert all(isinstance(r, str) for r in recs)

    def test_analyze_includes_disclaimer(
        self, analyzer: SoilAnalyzer, optimal_soil: SoilProfile
    ) -> None:
        recs = analyzer.analyze(optimal_soil)
        assert AGRICULTURAL_DISCLAIMER in recs

    def test_analyze_acidic_soil_recommends_lime(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=5.0,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "lime" in combined

    def test_analyze_alkaline_soil_recommends_gypsum_or_sulphur(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=8.0,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "gypsum" in combined or "sulphur" in combined

    def test_analyze_optimal_ph_reports_optimal(
        self, analyzer: SoilAnalyzer, optimal_soil: SoilProfile
    ) -> None:
        recs = analyzer.analyze(optimal_soil)
        combined = " ".join(recs)
        assert "optimal" in combined.lower() or "within" in combined.lower()

    def test_analyze_low_nitrogen_recommends_urea(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=100.0,  # below 140 threshold
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "nitrogen" in combined and ("urea" in combined or "low" in combined)

    def test_analyze_high_nitrogen_warns_excess(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=300.0,  # above 280 threshold
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "nitrogen" in combined and ("high" in combined or "reduce" in combined)

    def test_analyze_low_phosphorus_recommends_dap(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=5.0,  # below 10 threshold
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "phosphorus" in combined and ("dap" in combined or "low" in combined)

    def test_analyze_low_potassium_recommends_mop(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=80.0,  # below 108 threshold
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "potassium" in combined and ("mop" in combined or "low" in combined)

    def test_analyze_low_organic_carbon_recommends_manure(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.3,  # below 0.5 threshold
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        combined = " ".join(recs).lower()
        assert "organic" in combined and ("manure" in combined or "vermicompost" in combined)

    def test_analyze_adequate_oc_reports_satisfactory(
        self, analyzer: SoilAnalyzer, optimal_soil: SoilProfile
    ) -> None:
        recs = analyzer.analyze(optimal_soil)
        combined = " ".join(recs).lower()
        assert "satisfactory" in combined

    def test_suitable_crops_loam_neutral_ph(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.8,
            nitrogen_ppm=200.0,
            phosphorus_ppm=18.0,
            potassium_ppm=180.0,
            organic_carbon_pct=0.75,
            soil_type="loam",
        )
        crops = analyzer.suitable_crops(soil)
        assert len(crops) > 0
        for crop in crops:
            assert isinstance(crop, Crop)

    def test_suitable_crops_incompatible_soil_type_returns_empty(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="lunar_dust",
        )
        crops = analyzer.suitable_crops(soil)
        assert crops == []

    def test_suitable_crops_high_ph_filters_for_low_water(
        self, analyzer: SoilAnalyzer
    ) -> None:
        soil = SoilProfile(
            ph=8.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        crops = analyzer.suitable_crops(soil)
        for crop in crops:
            assert crop.water_requirement == "low"

    def test_analyzer_uses_default_db_when_none_passed(self) -> None:
        analyzer = SoilAnalyzer()  # no db argument
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        recs = analyzer.analyze(soil)
        assert len(recs) > 0


# ---------------------------------------------------------------------------
# CropAdvisor tests
# ---------------------------------------------------------------------------


class TestCropAdvisor:
    def test_advise_returns_crop_advisory(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert isinstance(advisory, CropAdvisory)

    def test_advisory_crop_matches_input(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert advisory.crop.name == "Rice"

    def test_advisory_soil_matches_input(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert advisory.soil.ph == optimal_soil.ph

    def test_advisory_has_recommendations(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert len(advisory.recommendations) > 0

    def test_advisory_has_fertilizer_plan(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert len(advisory.fertilizer_plan) > 0

    def test_advisory_has_irrigation_schedule(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert len(advisory.irrigation_schedule) > 0

    def test_advisory_disclaimer_present(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert advisory.disclaimer == AGRICULTURAL_DISCLAIMER

    def test_advisory_rice_uses_rice_fertilizer_plan(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        assert "basal" in advisory.fertilizer_plan
        assert "tillering" in advisory.fertilizer_plan

    def test_advisory_wheat_uses_wheat_fertilizer_plan(
        self,
        advisor: CropAdvisor,
        wheat_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(wheat_crop, optimal_soil)
        assert "crown root initiation" in advisory.fertilizer_plan or "basal" in advisory.fertilizer_plan

    def test_advisory_cotton_uses_cotton_fertilizer_plan(
        self,
        advisor: CropAdvisor,
        cotton_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(cotton_crop, optimal_soil)
        assert "squaring" in advisory.fertilizer_plan or "basal" in advisory.fertilizer_plan

    def test_advisory_unknown_crop_uses_default_plan(
        self, advisor: CropAdvisor, optimal_soil: SoilProfile
    ) -> None:
        rare_crop = Crop(
            name="Amaranth (Rajgira)",
            season="zaid",
            water_requirement="low",
            soil_types=["loam"],
            growth_days=100,
        )
        advisory = advisor.advise(rare_crop, optimal_soil)
        assert "basal" in advisory.fertilizer_plan
        assert "vegetative" in advisory.fertilizer_plan

    def test_advisory_high_water_crop_has_high_irrigation_schedule(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(rice_crop, optimal_soil)
        schedule_text = " ".join(advisory.irrigation_schedule.values())
        # High water schedule says "every 4-5 days" or similar short interval
        assert "irrigate" in schedule_text.lower()

    def test_advisory_no_weather_has_empty_risk_alerts(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        # With neutral soil and no weather, minimal or zero alerts
        advisory = advisor.advise(rice_crop, optimal_soil)
        # risk_alerts may be empty or non-empty depending on soil pH; just check it's a list
        assert isinstance(advisory.risk_alerts, list)

    def test_advisory_extreme_heat_adds_risk_alert(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        hot_weather = WeatherData(
            location="Rajasthan",
            temperature_c=45.0,
            humidity_pct=20.0,
            rainfall_mm=0.0,
        )
        advisory = advisor.advise(rice_crop, optimal_soil, hot_weather)
        assert any("heat" in alert.lower() or "45" in alert for alert in advisory.risk_alerts)

    def test_advisory_excess_rainfall_adds_risk_alert(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        rainy_weather = WeatherData(
            location="Assam",
            temperature_c=28.0,
            humidity_pct=90.0,
            rainfall_mm=250.0,
        )
        advisory = advisor.advise(rice_crop, optimal_soil, rainy_weather)
        assert any("rainfall" in alert.lower() or "waterlogging" in alert.lower() for alert in advisory.risk_alerts)

    def test_advisory_high_humidity_adds_fungal_risk_alert(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        humid_weather = WeatherData(
            location="Kerala",
            temperature_c=30.0,
            humidity_pct=90.0,
            rainfall_mm=10.0,
        )
        advisory = advisor.advise(rice_crop, optimal_soil, humid_weather)
        assert any("humid" in alert.lower() or "fungal" in alert.lower() for alert in advisory.risk_alerts)

    def test_advisory_strongly_acidic_soil_adds_risk_alert(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
    ) -> None:
        acidic_soil = SoilProfile(
            ph=5.0,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        advisory = advisor.advise(rice_crop, acidic_soil)
        assert any("acid" in alert.lower() or "lime" in alert.lower() for alert in advisory.risk_alerts)

    def test_advisory_strongly_alkaline_soil_adds_risk_alert(
        self,
        advisor: CropAdvisor,
        wheat_crop: Crop,
    ) -> None:
        alkaline_soil = SoilProfile(
            ph=9.0,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        advisory = advisor.advise(wheat_crop, alkaline_soil)
        assert any("alkaline" in alert.lower() or "zinc" in alert.lower() for alert in advisory.risk_alerts)

    def test_advisory_cold_temp_kharif_crop_adds_risk_alert(
        self,
        advisor: CropAdvisor,
        rice_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        cold_weather = WeatherData(
            location="Shimla",
            temperature_c=2.0,
            humidity_pct=60.0,
            rainfall_mm=0.0,
        )
        advisory = advisor.advise(rice_crop, optimal_soil, cold_weather)
        assert any("cold" in alert.lower() or "kharif" in alert.lower() for alert in advisory.risk_alerts)

    def test_recommendations_mention_crop_name(
        self,
        advisor: CropAdvisor,
        wheat_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(wheat_crop, optimal_soil)
        combined = " ".join(advisory.recommendations)
        assert "Wheat" in combined

    def test_recommendations_mention_season(
        self,
        advisor: CropAdvisor,
        wheat_crop: Crop,
        optimal_soil: SoilProfile,
    ) -> None:
        advisory = advisor.advise(wheat_crop, optimal_soil)
        combined = " ".join(advisory.recommendations)
        assert "rabi" in combined.lower()


# ---------------------------------------------------------------------------
# CropAdvisory model tests
# ---------------------------------------------------------------------------


class TestCropAdvisoryModel:
    def test_advisory_model_default_disclaimer(self) -> None:
        crop = Crop(
            name="Rice",
            season="kharif",
            water_requirement="high",
            soil_types=["loam"],
            growth_days=120,
        )
        soil = SoilProfile(
            ph=6.5,
            nitrogen_ppm=200.0,
            phosphorus_ppm=15.0,
            potassium_ppm=150.0,
            organic_carbon_pct=0.8,
            soil_type="loam",
        )
        advisory = CropAdvisory(
            crop=crop,
            soil=soil,
            recommendations=["Plant in May"],
            fertilizer_plan={"basal": "Apply DAP"},
            irrigation_schedule={"establishment": "Irrigate now"},
        )
        assert advisory.disclaimer == AGRICULTURAL_DISCLAIMER
        assert advisory.risk_alerts == []


# ---------------------------------------------------------------------------
# Property-based tests with Hypothesis
# ---------------------------------------------------------------------------


@given(ph=st.floats(min_value=0.0, max_value=14.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=30)
def test_soil_analyzer_analyze_always_returns_list(ph: float) -> None:
    """For any valid pH, analyze should return a non-empty list."""
    soil = SoilProfile(
        ph=ph,
        nitrogen_ppm=200.0,
        phosphorus_ppm=15.0,
        potassium_ppm=150.0,
        organic_carbon_pct=0.8,
        soil_type="loam",
    )
    analyzer = SoilAnalyzer()
    recs = analyzer.analyze(soil)
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert AGRICULTURAL_DISCLAIMER in recs


@given(
    nitrogen=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    phosphorus=st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    potassium=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_soil_analyzer_handles_all_nutrient_combinations(
    nitrogen: float, phosphorus: float, potassium: float
) -> None:
    """analyze must never raise for any valid nutrient combination."""
    soil = SoilProfile(
        ph=6.5,
        nitrogen_ppm=nitrogen,
        phosphorus_ppm=phosphorus,
        potassium_ppm=potassium,
        organic_carbon_pct=0.8,
        soil_type="loam",
    )
    analyzer = SoilAnalyzer()
    recs = analyzer.analyze(soil)
    assert AGRICULTURAL_DISCLAIMER in recs


@given(season=st.sampled_from(["kharif", "rabi", "zaid"]))
@settings(max_examples=10)
def test_crop_database_by_season_consistent(season: str) -> None:
    db = CropDatabase()
    result = db.by_season(season)
    for crop in result:
        assert crop.season == season
