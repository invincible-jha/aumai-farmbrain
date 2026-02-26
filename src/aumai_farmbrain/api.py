"""FastAPI application for aumai-farmbrain crop advisory service."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core import CropAdvisor, CropDatabase, SoilAnalyzer
from .models import AGRICULTURAL_DISCLAIMER, CropAdvisory, SoilProfile, WeatherData

app = FastAPI(
    title="AumAI FarmBrain API",
    description="Crop advisory and soil analysis AI for Indian agriculture.",
    version="0.1.0",
)

_crop_db = CropDatabase()
_soil_analyzer = SoilAnalyzer(_crop_db)
_crop_advisor = CropAdvisor()


class SoilAnalysisRequest(BaseModel):
    """Request body for soil analysis endpoint."""

    soil: SoilProfile


class SoilAnalysisResponse(BaseModel):
    """Response body for soil analysis endpoint."""

    recommendations: list[str]
    suitable_crop_names: list[str]
    disclaimer: str = AGRICULTURAL_DISCLAIMER


class CropAdvisoryRequest(BaseModel):
    """Request body for crop advisory endpoint."""

    crop_name: str
    soil: SoilProfile
    weather: WeatherData | None = None


@app.post("/api/soil-analysis", response_model=SoilAnalysisResponse)
def soil_analysis(request: SoilAnalysisRequest) -> SoilAnalysisResponse:
    """Analyse a soil profile and return suitability recommendations."""
    recs = _soil_analyzer.analyze(request.soil)
    suitable = _soil_analyzer.suitable_crops(request.soil)
    return SoilAnalysisResponse(
        recommendations=recs,
        suitable_crop_names=[c.name for c in suitable],
    )


@app.post("/api/crop-advisory", response_model=CropAdvisory)
def crop_advisory(request: CropAdvisoryRequest) -> CropAdvisory:
    """Generate a full crop advisory for the specified crop and soil."""
    crop = _crop_db.by_name(request.crop_name)
    if crop is None:
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{request.crop_name}' not found in database.",
        )
    return _crop_advisor.advise(crop, request.soil, request.weather)


@app.get("/api/crops")
def list_crops(season: str | None = None) -> dict[str, object]:
    """List all crops in the database, optionally filtered by season."""
    if season:
        crops = _crop_db.by_season(season)
    else:
        crops = _crop_db.all_crops()
    return {
        "crops": [c.model_dump() for c in crops],
        "total": len(crops),
        "disclaimer": AGRICULTURAL_DISCLAIMER,
    }
