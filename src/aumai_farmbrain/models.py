"""Pydantic v2 models for aumai-farmbrain crop advisory and soil analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

AGRICULTURAL_DISCLAIMER = (
    "Verify recommendations with local agricultural experts before application."
)

__all__ = [
    "Crop",
    "SoilProfile",
    "WeatherData",
    "CropAdvisory",
    "AGRICULTURAL_DISCLAIMER",
]


class Crop(BaseModel):
    """Represents an Indian agricultural crop with cultivation metadata."""

    name: str = Field(..., description="Common name of the crop")
    season: str = Field(
        ...,
        description="Growing season: kharif, rabi, or zaid",
        pattern="^(kharif|rabi|zaid)$",
    )
    water_requirement: str = Field(
        ..., description="Water requirement descriptor (low/medium/high)"
    )
    soil_types: list[str] = Field(
        ..., description="Compatible soil types for this crop"
    )
    growth_days: int = Field(
        ..., gt=0, description="Number of days from sowing to harvest"
    )

    @field_validator("season")
    @classmethod
    def validate_season(cls, value: str) -> str:
        """Normalise season to lowercase."""
        return value.lower()


class SoilProfile(BaseModel):
    """Chemical and physical profile of a soil sample."""

    ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH (0-14)")
    nitrogen_ppm: float = Field(
        ..., ge=0.0, description="Available nitrogen in ppm"
    )
    phosphorus_ppm: float = Field(
        ..., ge=0.0, description="Available phosphorus in ppm"
    )
    potassium_ppm: float = Field(
        ..., ge=0.0, description="Available potassium in ppm"
    )
    organic_carbon_pct: float = Field(
        ..., ge=0.0, le=100.0, description="Organic carbon as percentage"
    )
    soil_type: str = Field(
        ..., description="Soil classification (e.g., alluvial, black, red)"
    )


class WeatherData(BaseModel):
    """Current weather conditions for an agricultural location."""

    location: str = Field(..., description="Location name or coordinates string")
    temperature_c: float = Field(..., description="Current temperature in Celsius")
    humidity_pct: float = Field(
        ..., ge=0.0, le=100.0, description="Relative humidity percentage"
    )
    rainfall_mm: float = Field(
        ..., ge=0.0, description="Recent rainfall in millimetres"
    )
    forecast_days: int = Field(
        default=7, gt=0, le=30, description="Number of forecast days available"
    )


class CropAdvisory(BaseModel):
    """Full advisory output for a crop-soil-weather combination."""

    crop: Crop
    soil: SoilProfile
    recommendations: list[str] = Field(
        ..., description="Actionable agronomic recommendations"
    )
    fertilizer_plan: dict[str, str] = Field(
        ..., description="Fertilizer application schedule keyed by stage"
    )
    irrigation_schedule: dict[str, str] = Field(
        ..., description="Irrigation schedule keyed by growth stage"
    )
    risk_alerts: list[str] = Field(
        default_factory=list,
        description="Risk warnings for pests, weather, or soil issues",
    )
    disclaimer: str = Field(
        default=AGRICULTURAL_DISCLAIMER,
        description="Mandatory agricultural advisory disclaimer",
    )
