"""Core logic for aumai-farmbrain: soil analysis and crop advisory engine."""

from __future__ import annotations

from .models import (
    AGRICULTURAL_DISCLAIMER,
    Crop,
    CropAdvisory,
    SoilProfile,
    WeatherData,
)

__all__ = ["CropDatabase", "SoilAnalyzer", "CropAdvisor"]

# ---------------------------------------------------------------------------
# Static crop catalogue — 50+ Indian crops
# ---------------------------------------------------------------------------

_RAW_CROPS: list[dict[str, object]] = [
    # Kharif crops
    {"name": "Rice", "season": "kharif", "water_requirement": "high", "soil_types": ["alluvial", "clay", "loam"], "growth_days": 120},
    {"name": "Maize", "season": "kharif", "water_requirement": "medium", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 90},
    {"name": "Sorghum (Jowar)", "season": "kharif", "water_requirement": "low", "soil_types": ["black", "loam", "red"], "growth_days": 100},
    {"name": "Pearl Millet (Bajra)", "season": "kharif", "water_requirement": "low", "soil_types": ["sandy", "sandy loam", "loam"], "growth_days": 75},
    {"name": "Cotton", "season": "kharif", "water_requirement": "medium", "soil_types": ["black", "alluvial", "loam"], "growth_days": 180},
    {"name": "Sugarcane", "season": "kharif", "water_requirement": "high", "soil_types": ["alluvial", "loam", "clay loam"], "growth_days": 365},
    {"name": "Soybean", "season": "kharif", "water_requirement": "medium", "soil_types": ["black", "loam", "clay loam"], "growth_days": 100},
    {"name": "Groundnut", "season": "kharif", "water_requirement": "medium", "soil_types": ["sandy loam", "loam", "red"], "growth_days": 120},
    {"name": "Sesame (Til)", "season": "kharif", "water_requirement": "low", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 80},
    {"name": "Pigeonpea (Arhar/Tur)", "season": "kharif", "water_requirement": "low", "soil_types": ["black", "red", "loam"], "growth_days": 160},
    {"name": "Blackgram (Urad)", "season": "kharif", "water_requirement": "low", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 70},
    {"name": "Greengram (Moong)", "season": "kharif", "water_requirement": "low", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 65},
    {"name": "Jute", "season": "kharif", "water_requirement": "high", "soil_types": ["alluvial", "loam", "clay"], "growth_days": 120},
    {"name": "Turmeric", "season": "kharif", "water_requirement": "medium", "soil_types": ["loam", "clay loam", "red"], "growth_days": 270},
    {"name": "Ginger", "season": "kharif", "water_requirement": "medium", "soil_types": ["loam", "sandy loam", "red"], "growth_days": 210},
    {"name": "Banana", "season": "kharif", "water_requirement": "high", "soil_types": ["alluvial", "loam", "clay loam"], "growth_days": 365},
    {"name": "Okra (Bhindi)", "season": "kharif", "water_requirement": "medium", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 60},
    {"name": "Bitter Gourd", "season": "kharif", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 70},
    {"name": "Cowpea (Lobia)", "season": "kharif", "water_requirement": "low", "soil_types": ["sandy loam", "loam", "red"], "growth_days": 75},
    {"name": "Castor", "season": "kharif", "water_requirement": "low", "soil_types": ["black", "red", "alluvial"], "growth_days": 200},
    # Rabi crops
    {"name": "Wheat", "season": "rabi", "water_requirement": "medium", "soil_types": ["alluvial", "loam", "clay loam"], "growth_days": 120},
    {"name": "Barley", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 100},
    {"name": "Chickpea (Chana)", "season": "rabi", "water_requirement": "low", "soil_types": ["black", "loam", "red"], "growth_days": 100},
    {"name": "Lentil (Masoor)", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "clay loam", "alluvial"], "growth_days": 100},
    {"name": "Mustard (Sarson)", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "alluvial", "sandy loam"], "growth_days": 110},
    {"name": "Rapeseed", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "alluvial", "clay loam"], "growth_days": 115},
    {"name": "Linseed", "season": "rabi", "water_requirement": "low", "soil_types": ["black", "loam", "alluvial"], "growth_days": 120},
    {"name": "Sunflower", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "clay loam", "alluvial"], "growth_days": 100},
    {"name": "Pea (Matar)", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 90},
    {"name": "Potato", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 90},
    {"name": "Onion", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "alluvial", "black"], "growth_days": 130},
    {"name": "Garlic", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "clay loam", "alluvial"], "growth_days": 150},
    {"name": "Coriander", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "sandy loam"], "growth_days": 60},
    {"name": "Fenugreek (Methi)", "season": "rabi", "water_requirement": "low", "soil_types": ["loam", "clay loam", "alluvial"], "growth_days": 60},
    {"name": "Carrot", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "sandy loam", "alluvial"], "growth_days": 70},
    {"name": "Cabbage", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "clay loam", "alluvial"], "growth_days": 80},
    {"name": "Cauliflower", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "clay loam", "alluvial"], "growth_days": 75},
    {"name": "Spinach (Palak)", "season": "rabi", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 40},
    # Zaid crops
    {"name": "Watermelon", "season": "zaid", "water_requirement": "medium", "soil_types": ["sandy loam", "loam"], "growth_days": 90},
    {"name": "Muskmelon", "season": "zaid", "water_requirement": "medium", "soil_types": ["sandy loam", "loam"], "growth_days": 75},
    {"name": "Cucumber", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 55},
    {"name": "Pumpkin", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "clay loam"], "growth_days": 80},
    {"name": "Summer Squash", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 50},
    {"name": "Moong (Zaid)", "season": "zaid", "water_requirement": "low", "soil_types": ["loam", "sandy loam"], "growth_days": 65},
    {"name": "Cowpea (Zaid)", "season": "zaid", "water_requirement": "low", "soil_types": ["sandy loam", "loam"], "growth_days": 70},
    {"name": "Bottle Gourd", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "clay loam"], "growth_days": 65},
    {"name": "Ridge Gourd", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 60},
    {"name": "Snake Gourd", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 65},
    {"name": "Bitter Melon (Zaid)", "season": "zaid", "water_requirement": "medium", "soil_types": ["loam", "sandy loam"], "growth_days": 70},
    {"name": "Cluster Beans (Guar)", "season": "zaid", "water_requirement": "low", "soil_types": ["sandy loam", "loam"], "growth_days": 90},
    {"name": "Amaranth (Rajgira)", "season": "zaid", "water_requirement": "low", "soil_types": ["loam", "sandy loam", "red"], "growth_days": 100},
]


class CropDatabase:
    """In-memory catalogue of 50+ Indian crops with lookup utilities."""

    def __init__(self) -> None:
        self._crops: list[Crop] = [Crop(**entry) for entry in _RAW_CROPS]  # type: ignore[arg-type]

    def all_crops(self) -> list[Crop]:
        """Return every crop in the database."""
        return list(self._crops)

    def by_name(self, name: str) -> Crop | None:
        """Case-insensitive crop lookup by name."""
        name_lower = name.lower()
        for crop in self._crops:
            if crop.name.lower() == name_lower:
                return crop
        return None

    def by_season(self, season: str) -> list[Crop]:
        """Return crops for a given season (kharif/rabi/zaid)."""
        return [c for c in self._crops if c.season == season.lower()]

    def by_soil_type(self, soil_type: str) -> list[Crop]:
        """Return crops compatible with a specific soil type."""
        soil_lower = soil_type.lower()
        return [c for c in self._crops if any(s.lower() == soil_lower for s in c.soil_types)]


# ---------------------------------------------------------------------------
# Soil analysis thresholds (ICAR guidelines)
# ---------------------------------------------------------------------------

_PH_LOW = 6.0
_PH_HIGH = 7.5
_N_LOW = 140.0   # kg/ha equivalent in ppm for low
_N_HIGH = 280.0
_P_LOW = 10.0
_P_HIGH = 25.0
_K_LOW = 108.0
_K_HIGH = 280.0
_OC_LOW = 0.5


class SoilAnalyzer:
    """Analyses soil profiles and recommends suitable crops."""

    def __init__(self, crop_db: CropDatabase | None = None) -> None:
        self._db = crop_db or CropDatabase()

    def analyze(self, soil: SoilProfile) -> list[str]:
        """Return agronomic recommendations for the given soil profile."""
        recs: list[str] = []

        # pH
        if soil.ph < _PH_LOW:
            recs.append(
                f"Soil pH {soil.ph:.1f} is acidic. Apply agricultural lime at"
                " 2-4 tonnes/hectare to raise pH to 6.0-7.5 range."
            )
        elif soil.ph > _PH_HIGH:
            recs.append(
                f"Soil pH {soil.ph:.1f} is alkaline. Apply gypsum or sulphur"
                " to lower pH towards 6.0-7.5 range."
            )
        else:
            recs.append(f"Soil pH {soil.ph:.1f} is within the optimal range (6.0-7.5).")

        # Nitrogen
        if soil.nitrogen_ppm < _N_LOW:
            recs.append(
                "Nitrogen is LOW. Apply urea (46% N) at 120-150 kg/ha or"
                " incorporate green manure crops like dhaincha."
            )
        elif soil.nitrogen_ppm > _N_HIGH:
            recs.append(
                "Nitrogen is HIGH. Reduce nitrogenous fertilizer applications"
                " and monitor for vegetative imbalance."
            )
        else:
            recs.append("Nitrogen level is adequate.")

        # Phosphorus
        if soil.phosphorus_ppm < _P_LOW:
            recs.append(
                "Phosphorus is LOW. Apply DAP (18-46-0) at 100-125 kg/ha"
                " or single super phosphate (SSP)."
            )
        elif soil.phosphorus_ppm > _P_HIGH:
            recs.append("Phosphorus is HIGH. Skip phosphatic fertilizers this season.")
        else:
            recs.append("Phosphorus level is adequate.")

        # Potassium
        if soil.potassium_ppm < _K_LOW:
            recs.append(
                "Potassium is LOW. Apply muriate of potash (MOP) at 60-80 kg/ha"
                " or use potassium sulphate for chloride-sensitive crops."
            )
        elif soil.potassium_ppm > _K_HIGH:
            recs.append("Potassium is HIGH. No additional potassic fertilizer required.")
        else:
            recs.append("Potassium level is adequate.")

        # Organic carbon
        if soil.organic_carbon_pct < _OC_LOW:
            recs.append(
                f"Organic carbon {soil.organic_carbon_pct:.2f}% is below 0.50%."
                " Incorporate farmyard manure (10-15 tonnes/ha) or vermicompost"
                " to improve soil health."
            )
        else:
            recs.append(
                f"Organic carbon {soil.organic_carbon_pct:.2f}% is satisfactory."
            )

        recs.append(AGRICULTURAL_DISCLAIMER)
        return recs

    def suitable_crops(self, soil: SoilProfile) -> list[Crop]:
        """Return crops compatible with the given soil profile based on type and pH."""
        compatible: list[Crop] = []
        for crop in self._db.all_crops():
            soil_match = any(
                s.lower() == soil.soil_type.lower() for s in crop.soil_types
            )
            if not soil_match:
                continue
            # pH suitability heuristic
            if soil.ph < 5.5 and crop.water_requirement == "high":
                # Rice tolerates acidic; keep it
                compatible.append(crop)
            elif soil.ph < 5.5 and crop.name in ("Rice", "Jute", "Turmeric", "Ginger"):
                compatible.append(crop)
            elif 5.5 <= soil.ph <= 8.0:
                compatible.append(crop)
            elif soil.ph > 8.0 and crop.water_requirement == "low":
                compatible.append(crop)
        return compatible


# ---------------------------------------------------------------------------
# Crop advisor
# ---------------------------------------------------------------------------

class CropAdvisor:
    """Generates complete crop advisories including fertilizer and irrigation plans."""

    _FERTILIZER_PLANS: dict[str, dict[str, str]] = {
        "rice": {
            "basal": "Apply DAP 50 kg/ha + MOP 25 kg/ha at transplanting.",
            "tillering": "Top-dress urea 30 kg/ha at 21 DAT.",
            "panicle initiation": "Apply urea 30 kg/ha + potassium sulphate 20 kg/ha.",
        },
        "wheat": {
            "basal": "Apply DAP 50 kg/ha + MOP 20 kg/ha at sowing.",
            "crown root initiation": "Top-dress urea 60 kg/ha at CRI stage (20-25 DAS).",
            "jointing": "Apply urea 30 kg/ha at jointing stage.",
        },
        "cotton": {
            "basal": "Apply SSP 150 kg/ha + MOP 25 kg/ha at sowing.",
            "squaring": "Apply urea 40 kg/ha + boron 1 kg/ha at squaring.",
            "boll development": "Top-dress NPK 12:32:16 at 50 kg/ha.",
        },
        "default": {
            "basal": "Apply recommended NPK complex fertilizer at sowing/planting.",
            "vegetative": "Top-dress nitrogen source at active vegetative growth.",
            "reproductive": "Apply potassium-rich fertilizer at flowering/fruiting.",
        },
    }

    _IRRIGATION_SCHEDULES: dict[str, dict[str, str]] = {
        "high": {
            "establishment": "Irrigate immediately after sowing/transplanting.",
            "vegetative": "Maintain field capacity; irrigate every 5-7 days.",
            "reproductive": "Critical stage — do not stress; irrigate every 4-5 days.",
            "maturation": "Reduce irrigation; withhold 10-15 days before harvest.",
        },
        "medium": {
            "establishment": "Apply light irrigation at sowing.",
            "vegetative": "Irrigate every 10-12 days or at 50% soil moisture depletion.",
            "reproductive": "Irrigate every 7-10 days at flowering/grain fill.",
            "maturation": "Reduce irrigation 2-3 weeks before harvest.",
        },
        "low": {
            "establishment": "One irrigation at sowing if soil is dry.",
            "vegetative": "Irrigate every 15-20 days or rely on rainfall.",
            "reproductive": "One critical irrigation at flowering if rainfall is inadequate.",
            "maturation": "Withhold irrigation 3 weeks before harvest.",
        },
    }

    def advise(
        self,
        crop: Crop,
        soil: SoilProfile,
        weather: WeatherData | None = None,
    ) -> CropAdvisory:
        """Generate a complete CropAdvisory for the given inputs."""
        recommendations: list[str] = []
        risk_alerts: list[str] = []

        recommendations.append(
            f"{crop.name} is a {crop.season} crop requiring"
            f" {crop.water_requirement} water and {crop.growth_days} days to mature."
        )
        recommendations.append(
            f"Compatible soil types: {', '.join(crop.soil_types)}."
            f" Current soil type is {soil.soil_type}."
        )

        soil_analyzer = SoilAnalyzer()
        recommendations.extend(soil_analyzer.analyze(soil)[:-1])  # strip trailing disclaimer

        # Weather-based recommendations
        if weather is not None:
            if weather.temperature_c > 40:
                risk_alerts.append(
                    f"Extreme heat ({weather.temperature_c}°C) at {weather.location}."
                    " Apply mulching and increase irrigation frequency."
                )
            if weather.temperature_c < 5 and crop.season == "kharif":
                risk_alerts.append(
                    "Unexpectedly cold conditions for a kharif crop."
                    " Protect seedlings with polythene covers."
                )
            if weather.rainfall_mm > 200:
                risk_alerts.append(
                    f"Excess rainfall ({weather.rainfall_mm} mm) detected."
                    " Ensure drainage channels are clear to prevent waterlogging."
                )
            if weather.humidity_pct > 85:
                risk_alerts.append(
                    f"High humidity ({weather.humidity_pct}%)."
                    " Monitor for fungal diseases; apply preventive fungicide."
                )

        # Soil pH risk
        if soil.ph < 5.5:
            risk_alerts.append(
                "Strongly acidic soil may cause aluminium toxicity."
                " Apply lime before sowing."
            )
        if soil.ph > 8.5:
            risk_alerts.append(
                "Strongly alkaline soil may cause micronutrient deficiencies."
                " Apply zinc sulphate 25 kg/ha."
            )

        # Fertilizer plan
        crop_key = crop.name.lower().split("(")[0].strip()
        fertilizer_plan = self._FERTILIZER_PLANS.get(
            crop_key, self._FERTILIZER_PLANS["default"]
        )

        # Irrigation schedule
        irrigation_schedule = self._IRRIGATION_SCHEDULES[crop.water_requirement]

        return CropAdvisory(
            crop=crop,
            soil=soil,
            recommendations=recommendations,
            fertilizer_plan=dict(fertilizer_plan),
            irrigation_schedule=dict(irrigation_schedule),
            risk_alerts=risk_alerts,
            disclaimer=AGRICULTURAL_DISCLAIMER,
        )
