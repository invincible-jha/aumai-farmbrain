"""CLI entry point for aumai-farmbrain."""

from __future__ import annotations

import json
import sys

import click

from .core import CropAdvisor, CropDatabase, SoilAnalyzer
from .models import AGRICULTURAL_DISCLAIMER, SoilProfile, WeatherData


@click.group()
@click.version_option()
def main() -> None:
    """AumAI FarmBrain — Crop advisory and soil analysis for Indian agriculture."""


@main.command("advise")
@click.option("--crop", required=True, help="Crop name (e.g. rice, wheat)")
@click.option(
    "--soil",
    "soil_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to JSON file with SoilProfile data",
)
@click.option("--weather", "weather_file", type=click.Path(exists=True), default=None, help="Optional path to JSON file with WeatherData")
def advise(crop: str, soil_file: str, weather_file: str | None) -> None:
    """Generate a crop advisory for a given crop and soil profile."""
    db = CropDatabase()
    advisor = CropAdvisor()

    crop_obj = db.by_name(crop)
    if crop_obj is None:
        click.echo(f"Error: Crop '{crop}' not found. Use 'crops --list' to see available crops.", err=True)
        sys.exit(1)

    with open(soil_file) as fh:
        soil = SoilProfile.model_validate(json.load(fh))

    weather: WeatherData | None = None
    if weather_file:
        with open(weather_file) as fh:
            weather = WeatherData.model_validate(json.load(fh))

    advisory = advisor.advise(crop_obj, soil, weather)

    click.echo(f"\n{'='*60}")
    click.echo(f"CROP ADVISORY: {advisory.crop.name.upper()}")
    click.echo(f"{'='*60}")
    click.echo("\nRECOMMENDATIONS:")
    for rec in advisory.recommendations:
        click.echo(f"  - {rec}")

    click.echo("\nFERTILIZER PLAN:")
    for stage, instruction in advisory.fertilizer_plan.items():
        click.echo(f"  [{stage.upper()}] {instruction}")

    click.echo("\nIRRIGATION SCHEDULE:")
    for stage, instruction in advisory.irrigation_schedule.items():
        click.echo(f"  [{stage.upper()}] {instruction}")

    if advisory.risk_alerts:
        click.echo("\nRISK ALERTS:")
        for alert in advisory.risk_alerts:
            click.echo(f"  WARNING: {alert}")

    click.echo(f"\nDISCLAIMER: {AGRICULTURAL_DISCLAIMER}\n")


@main.command("crops")
@click.option("--list", "show_list", is_flag=True, default=False, help="List all available crops")
@click.option("--season", default=None, help="Filter by season: kharif, rabi, zaid")
def crops(show_list: bool, season: str | None) -> None:
    """List available crops in the database."""
    db = CropDatabase()
    if season:
        crop_list = db.by_season(season)
    else:
        crop_list = db.all_crops()

    click.echo(f"\nAVAILABLE CROPS ({len(crop_list)} total):")
    click.echo(f"{'Name':<30} {'Season':<10} {'Water':<10} {'Days':>6}")
    click.echo("-" * 60)
    for c in crop_list:
        click.echo(f"{c.name:<30} {c.season:<10} {c.water_requirement:<10} {c.growth_days:>6}")
    click.echo(f"\n{AGRICULTURAL_DISCLAIMER}\n")


@main.command("serve")
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def serve(port: int, host: str) -> None:
    """Start the FarmBrain API server."""
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn is required to run the server. Install with: pip install uvicorn", err=True)
        sys.exit(1)
    uvicorn.run("aumai_farmbrain.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
