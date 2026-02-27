"""
aumai-farmbrain quickstart examples.

Run this file directly to verify your installation and explore the API:

    python examples/quickstart.py

Each demo function is self-contained and prints clearly labelled output.
"""

from __future__ import annotations

from aumai_farmbrain.core import CropAdvisor, CropDatabase, SoilAnalyzer
from aumai_farmbrain.models import SoilProfile, WeatherData


# ---------------------------------------------------------------------------
# Demo 1: Browse the crop database
# ---------------------------------------------------------------------------


def demo_crop_database() -> None:
    """Explore the 50+ Indian crop catalogue by season and soil type."""
    print("\n" + "=" * 60)
    print("DEMO 1: Crop Database")
    print("=" * 60)

    db = CropDatabase()
    all_crops = db.all_crops()
    print(f"Total crops in database: {len(all_crops)}")

    # Seasonal breakdown
    for season in ("kharif", "rabi", "zaid"):
        seasonal = db.by_season(season)
        names = ", ".join(c.name for c in seasonal[:5])
        print(f"\n{season.capitalize()} crops ({len(seasonal)}): {names}...")

    # Lookup a specific crop
    wheat = db.by_name("wheat")
    if wheat:
        print(f"\nWheat detail:")
        print(f"  Season: {wheat.season}")
        print(f"  Water requirement: {wheat.water_requirement}")
        print(f"  Growth duration: {wheat.growth_days} days")
        print(f"  Compatible soils: {', '.join(wheat.soil_types)}")

    # Crops for black soil
    black_soil_crops = db.by_soil_type("black")
    print(f"\nCrops compatible with black soil: {len(black_soil_crops)}")
    low_water = [c for c in black_soil_crops if c.water_requirement == "low"]
    print(f"  Of which low-water-requirement: {len(low_water)}")
    for crop in low_water:
        print(f"    {crop.name} ({crop.season})")


# ---------------------------------------------------------------------------
# Demo 2: Soil analysis
# ---------------------------------------------------------------------------


def demo_soil_analysis() -> None:
    """Analyse a typical Vidarbha black soil with low organic carbon."""
    print("\n" + "=" * 60)
    print("DEMO 2: Soil Analysis — Vidarbha Black Cotton Soil")
    print("=" * 60)

    # This soil profile is representative of nutrient-depleted black cotton soil
    # in Vidarbha: acidic, low nitrogen, very low organic carbon.
    soil = SoilProfile(
        ph=5.8,
        nitrogen_ppm=115.0,
        phosphorus_ppm=7.5,
        potassium_ppm=90.0,
        organic_carbon_pct=0.35,
        soil_type="black",
    )

    analyzer = SoilAnalyzer()
    recommendations = analyzer.analyze(soil)

    print(f"\nSoil profile: pH={soil.ph}, N={soil.nitrogen_ppm} ppm, "
          f"P={soil.phosphorus_ppm} ppm, K={soil.potassium_ppm} ppm, "
          f"OC={soil.organic_carbon_pct}%")
    print("\nSoil analysis recommendations:")
    # Skip the last element (disclaimer) for cleaner demo output
    for rec in recommendations[:-1]:
        print(f"  - {rec}")

    # Find compatible crops for this soil
    compatible = analyzer.suitable_crops(soil)
    print(f"\n{len(compatible)} crops compatible with this acidic black soil:")
    kharif_compat = [c for c in compatible if c.season == "kharif"]
    for crop in kharif_compat[:8]:
        print(f"  {crop.name:<30} water={crop.water_requirement}")


# ---------------------------------------------------------------------------
# Demo 3: Full crop advisory — wheat on alluvial soil
# ---------------------------------------------------------------------------


def demo_crop_advisory_wheat() -> None:
    """Generate a complete wheat advisory for alluvial soil in the Indo-Gangetic plain."""
    print("\n" + "=" * 60)
    print("DEMO 3: Wheat Advisory — Alluvial Soil, UP")
    print("=" * 60)

    db = CropDatabase()
    advisor = CropAdvisor()

    crop = db.by_name("wheat")
    if crop is None:
        print("ERROR: wheat not found in database")
        return

    # Typical alluvial soil in western UP — moderate nutrient levels
    soil = SoilProfile(
        ph=7.2,
        nitrogen_ppm=135.0,
        phosphorus_ppm=9.5,
        potassium_ppm=105.0,
        organic_carbon_pct=0.47,
        soil_type="alluvial",
    )

    advisory = advisor.advise(crop, soil)

    print(f"\nAdvisory for: {advisory.crop.name}")
    print(f"Season: {advisory.crop.season}, Growth: {advisory.crop.growth_days} days\n")

    print("Recommendations:")
    for rec in advisory.recommendations:
        print(f"  {rec}")

    print("\nFertilizer Plan:")
    for stage, instruction in advisory.fertilizer_plan.items():
        print(f"  [{stage.upper()}]")
        print(f"    {instruction}")

    print("\nIrrigation Schedule:")
    for stage, instruction in advisory.irrigation_schedule.items():
        print(f"  [{stage.upper()}]")
        print(f"    {instruction}")

    if advisory.risk_alerts:
        print("\nRisk Alerts:")
        for alert in advisory.risk_alerts:
            print(f"  WARNING: {alert}")
    else:
        print("\nNo risk alerts for current conditions.")


# ---------------------------------------------------------------------------
# Demo 4: Advisory with weather — rice during extreme monsoon
# ---------------------------------------------------------------------------


def demo_advisory_with_weather() -> None:
    """Generate a rice advisory for Bihar during heavy monsoon rainfall."""
    print("\n" + "=" * 60)
    print("DEMO 4: Rice Advisory with Weather — Bihar, Peak Monsoon")
    print("=" * 60)

    db = CropDatabase()
    advisor = CropAdvisor()

    crop = db.by_name("rice")
    if crop is None:
        print("ERROR: rice not found in database")
        return

    # Alluvial clay loam in North Bihar — typical flood-affected district
    soil = SoilProfile(
        ph=6.3,
        nitrogen_ppm=125.0,
        phosphorus_ppm=11.0,
        potassium_ppm=148.0,
        organic_carbon_pct=0.72,
        soil_type="alluvial",
    )

    # Peak monsoon weather — heavy rainfall + high humidity
    weather = WeatherData(
        location="Darbhanga, Bihar",
        temperature_c=34.0,
        humidity_pct=92.0,      # triggers fungal disease alert
        rainfall_mm=240.0,      # triggers excess rainfall alert
        forecast_days=7,
    )

    advisory = advisor.advise(crop, soil, weather)

    print(f"\nLocation: {weather.location}")
    print(f"Temperature: {weather.temperature_c}°C, Humidity: {weather.humidity_pct}%, "
          f"Rainfall: {weather.rainfall_mm} mm")

    print(f"\nRisk Alerts ({len(advisory.risk_alerts)} active):")
    for alert in advisory.risk_alerts:
        print(f"  [ALERT] {alert}")

    print("\nFertilizer Plan (Rice-specific, stage-wise):")
    for stage, instruction in advisory.fertilizer_plan.items():
        print(f"  [{stage.upper()}] {instruction}")

    print("\nIrrigation Schedule (High water crop):")
    for stage, instruction in advisory.irrigation_schedule.items():
        print(f"  [{stage.upper()}] {instruction}")


# ---------------------------------------------------------------------------
# Demo 5: Drought-tolerant crop screening
# ---------------------------------------------------------------------------


def demo_drought_tolerant_crops() -> None:
    """Screen all low-water-requirement crops for a drought-prone sandy loam region."""
    print("\n" + "=" * 60)
    print("DEMO 5: Drought-Tolerant Crop Screening — Rajasthan Sandy Loam")
    print("=" * 60)

    db = CropDatabase()
    analyzer = SoilAnalyzer()

    # Sandy loam in eastern Rajasthan — alkaline, low organic carbon, low moisture
    soil = SoilProfile(
        ph=8.1,
        nitrogen_ppm=95.0,
        phosphorus_ppm=6.0,
        potassium_ppm=180.0,
        organic_carbon_pct=0.28,
        soil_type="sandy loam",
    )

    # Find crops compatible with this alkaline sandy loam
    compatible = analyzer.suitable_crops(soil)

    # Filter to low water requirement only (drought tolerant)
    drought_tolerant = [c for c in compatible if c.water_requirement == "low"]

    print(f"\nSoil: {soil.soil_type}, pH {soil.ph} (alkaline)")
    print(f"Total compatible crops: {len(compatible)}")
    print(f"Drought-tolerant (low water) crops: {len(drought_tolerant)}")

    print(f"\n{'Crop':<32} {'Season':<10} {'Days':>6}")
    print("-" * 52)
    for crop in sorted(drought_tolerant, key=lambda c: c.growth_days):
        print(f"{crop.name:<32} {crop.season:<10} {crop.growth_days:>6}")

    # Quick advisory for the fastest-maturing drought-tolerant crop
    if drought_tolerant:
        fastest = min(drought_tolerant, key=lambda c: c.growth_days)
        print(f"\nRecommended quick-maturing option: {fastest.name} "
              f"({fastest.growth_days} days, {fastest.season})")
        advisor = CropAdvisor()
        advisory = advisor.advise(fastest, soil)
        print(f"Fertilizer (basal): {advisory.fertilizer_plan.get('basal', 'see plan')}")
        print(f"Irrigation (vegetative): "
              f"{advisory.irrigation_schedule.get('vegetative', 'see schedule')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all quickstart demos in sequence."""
    print("aumai-farmbrain — Quickstart Demo")
    print("Crop advisory and soil analysis for Indian agriculture")

    demo_crop_database()
    demo_soil_analysis()
    demo_crop_advisory_wheat()
    demo_advisory_with_weather()
    demo_drought_tolerant_crops()

    print("\n" + "=" * 60)
    print("All demos complete.")
    print("\nDISCLAIMER: This tool provides AI-assisted agricultural analysis only.")
    print("Verify all recommendations with local agricultural experts and government")
    print("extension services before application.")
    print("=" * 60)


if __name__ == "__main__":
    main()
