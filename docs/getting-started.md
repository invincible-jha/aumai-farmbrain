# Getting Started with aumai-farmbrain

This guide walks you from installation to your first crop advisory in under ten minutes.

---

## Prerequisites

- **Python 3.11 or newer.** Check your version with `python --version`.
- **pip** or **uv** package manager.
- (Optional) A JSON file with your soil test results from a state Soil Health Card test.
- (Optional) `uvicorn` if you want to run the HTTP API server.

No API keys, no database setup, no external services required. FarmBrain runs entirely in-process.

---

## Installation

### With pip

```bash
pip install aumai-farmbrain
```

### With uv (recommended)

```bash
uv add aumai-farmbrain
```

### For development (editable install from source)

```bash
git clone https://github.com/aumai/aumai-farmbrain.git
cd aumai-farmbrain
pip install -e ".[dev]"
```

### Verify the installation

```bash
farmbrain --version
farmbrain --help
```

You should see the version number and the list of subcommands: `advise`, `crops`, `serve`.

---

## Step-by-Step Tutorial

### Step 1 — Explore the crop database

FarmBrain ships with 50+ Indian crops catalogued by season, soil type, water requirement, and
growth duration. Start by browsing what is available:

```bash
# List all crops
farmbrain crops --list

# Filter to kharif crops only
farmbrain crops --season kharif

# Filter to rabi crops only
farmbrain crops --season rabi
```

Or from Python:

```python
from aumai_farmbrain.core import CropDatabase

db = CropDatabase()
print(f"Total crops in database: {len(db.all_crops())}")

# Find a specific crop
rice = db.by_name("rice")
print(f"Rice: {rice.season}, {rice.water_requirement} water, {rice.growth_days} days")

# Crops suited to black cotton soil
black_crops = db.by_soil_type("black")
for crop in black_crops:
    print(f"  {crop.name} ({crop.season})")
```

### Step 2 — Create a soil profile

A `SoilProfile` requires six parameters from a standard soil health test. If you have a Soil
Health Card from your state agriculture department, these values are printed directly on it.

```python
from aumai_farmbrain.models import SoilProfile

soil = SoilProfile(
    ph=6.8,                   # Soil pH (must be between 0 and 14)
    nitrogen_ppm=120.0,       # Available nitrogen in ppm
    phosphorus_ppm=8.0,       # Available phosphorus in ppm
    potassium_ppm=95.0,       # Available potassium in ppm
    organic_carbon_pct=0.42,  # Organic carbon as percentage
    soil_type="alluvial",     # Soil classification
)
```

**Common Indian soil types accepted:** `alluvial`, `black`, `red`, `loam`, `sandy loam`,
`clay loam`, `clay`, `sandy`.

### Step 3 — Analyse the soil alone

Before generating a full crop advisory, you can run just the soil analysis to understand what
corrective actions your soil needs:

```python
from aumai_farmbrain.core import SoilAnalyzer

analyzer = SoilAnalyzer()
recommendations = analyzer.analyze(soil)

for rec in recommendations:
    print(rec)
```

This will evaluate pH, nitrogen, phosphorus, potassium, and organic carbon against ICAR
guidelines and produce plain-language corrective recommendations.

You can also ask which crops are compatible with the soil:

```python
compatible_crops = analyzer.suitable_crops(soil)
print(f"\n{len(compatible_crops)} crops compatible with your soil:")
for crop in compatible_crops:
    print(f"  {crop.name} ({crop.season})")
```

### Step 4 — Generate a full crop advisory

Now combine your crop of interest and your soil profile into a complete advisory:

```python
from aumai_farmbrain.core import CropDatabase, CropAdvisor

db = CropDatabase()
advisor = CropAdvisor()

crop = db.by_name("wheat")  # returns None if not found
if crop is None:
    raise ValueError("Crop not found — check the spelling")

advisory = advisor.advise(crop, soil)

print("RECOMMENDATIONS:")
for rec in advisory.recommendations:
    print(f"  {rec}")

print("\nFERTILIZER PLAN:")
for stage, instruction in advisory.fertilizer_plan.items():
    print(f"  [{stage.upper()}] {instruction}")

print("\nIRRIGATION SCHEDULE:")
for stage, instruction in advisory.irrigation_schedule.items():
    print(f"  [{stage.upper()}] {instruction}")

if advisory.risk_alerts:
    print("\nRISK ALERTS:")
    for alert in advisory.risk_alerts:
        print(f"  WARNING: {alert}")
```

### Step 5 — Add weather context

If you have current weather data (temperature, humidity, recent rainfall), pass it in to
receive weather-specific risk alerts:

```python
from aumai_farmbrain.models import WeatherData

weather = WeatherData(
    location="Kanpur, UP",
    temperature_c=43.0,      # extreme heat — will trigger a heatwave alert
    humidity_pct=55.0,
    rainfall_mm=0.0,
    forecast_days=7,
)

advisory = advisor.advise(crop, soil, weather)

# Risk alerts now include the heatwave warning
for alert in advisory.risk_alerts:
    print(f"ALERT: {alert}")
```

### Step 6 — Use the CLI end-to-end

Save your soil data as JSON:

```bash
cat > my_soil.json << 'EOF'
{
  "ph": 6.8,
  "nitrogen_ppm": 120.0,
  "phosphorus_ppm": 8.0,
  "potassium_ppm": 95.0,
  "organic_carbon_pct": 0.42,
  "soil_type": "alluvial"
}
EOF

cat > my_weather.json << 'EOF'
{
  "location": "Kanpur, UP",
  "temperature_c": 43.0,
  "humidity_pct": 55.0,
  "rainfall_mm": 0.0,
  "forecast_days": 7
}
EOF
```

Run the advisory:

```bash
farmbrain advise --crop wheat --soil my_soil.json --weather my_weather.json
```

---

## Common Patterns and Recipes

### Recipe 1 — Screen all crops for a given soil type and season

```python
from aumai_farmbrain.core import CropDatabase, SoilAnalyzer
from aumai_farmbrain.models import SoilProfile

db = CropDatabase()
soil = SoilProfile(
    ph=7.8,
    nitrogen_ppm=200.0,
    phosphorus_ppm=18.0,
    potassium_ppm=160.0,
    organic_carbon_pct=0.55,
    soil_type="black",
)

# All kharif crops
kharif = db.by_season("kharif")

# Filter to those compatible with this soil
analyzer = SoilAnalyzer()
compatible = analyzer.suitable_crops(soil)
compatible_names = {c.name for c in compatible}

suitable_kharif = [c for c in kharif if c.name in compatible_names]
print(f"Kharif crops suitable for your black soil (pH {soil.ph}):")
for c in suitable_kharif:
    print(f"  {c.name} — {c.growth_days} days, {c.water_requirement} water")
```

### Recipe 2 — Batch advisories for multiple crops

```python
from aumai_farmbrain.core import CropDatabase, CropAdvisor
from aumai_farmbrain.models import SoilProfile

db = CropDatabase()
advisor = CropAdvisor()
soil = SoilProfile(
    ph=6.5,
    nitrogen_ppm=150.0,
    phosphorus_ppm=14.0,
    potassium_ppm=120.0,
    organic_carbon_pct=0.52,
    soil_type="loam",
)

for crop_name in ["rice", "cotton", "soybean"]:
    crop = db.by_name(crop_name)
    if crop:
        advisory = advisor.advise(crop, soil)
        alert_count = len(advisory.risk_alerts)
        print(f"{crop.name}: {len(advisory.recommendations)} recs, {alert_count} alerts")
```

### Recipe 3 — Serialize an advisory for API storage

```python
import json
from aumai_farmbrain.models import CropAdvisory

# advisory is a CropAdvisory instance
advisory_json = advisory.model_dump_json(indent=2)

# Save to file
with open("advisory_output.json", "w") as f:
    f.write(advisory_json)

# Reload and validate
with open("advisory_output.json") as f:
    restored = CropAdvisory.model_validate_json(f.read())
print(f"Restored advisory for: {restored.crop.name}")
```

### Recipe 4 — Inject a ClimateWatch alert as weather context

```python
# Assumes aumai-climatewatch is installed: pip install aumai-climatewatch
from aumai_climatewatch.core import ClimateZoneRegistry, ClimateAnalyzer
from aumai_farmbrain.core import CropAdvisor, CropDatabase
from aumai_farmbrain.models import SoilProfile, WeatherData

# Get climate report from ClimateWatch
registry = ClimateZoneRegistry()
analyzer = ClimateAnalyzer()
zone = registry.get_zone("eastern-india")
obs = {"temperature_c": 39.0, "rainfall_mm": 220.0, "humidity_pct": 88.0,
       "wind_kmh": 20.0, "rainfall_deficit_pct": 0.0}
report = analyzer.generate_report(zone, obs)

# Convert to FarmBrain WeatherData
weather = WeatherData(
    location=report.zone.name,
    temperature_c=float(report.current_conditions["temperature_c"]),
    humidity_pct=float(report.current_conditions["humidity_pct"]),
    rainfall_mm=float(report.current_conditions["rainfall_mm"]),
    forecast_days=7,
)

# Generate advisory with climate-informed weather
db = CropDatabase()
soil = SoilProfile(ph=6.2, nitrogen_ppm=130.0, phosphorus_ppm=12.0,
                   potassium_ppm=150.0, organic_carbon_pct=0.7, soil_type="alluvial")
advisory = CropAdvisor().advise(db.by_name("rice"), soil, weather)
for alert in advisory.risk_alerts:
    print(f"RISK: {alert}")
```

### Recipe 5 — Low-water crops for drought-prone regions

```python
from aumai_farmbrain.core import CropDatabase

db = CropDatabase()
low_water = [c for c in db.all_crops() if c.water_requirement == "low"]
print(f"Drought-tolerant crops ({len(low_water)} total):")
for c in sorted(low_water, key=lambda x: x.growth_days):
    print(f"  {c.name:<30} {c.season:<10} {c.growth_days} days")
```

---

## Troubleshooting FAQ

**Q: `farmbrain advise` exits with "Crop 'X' not found".**

Run `farmbrain crops --list` to see the exact names in the database. The lookup is
case-insensitive but the spelling must match (e.g., "Sorghum (Jowar)" not "jowar").

---

**Q: `SoilProfile` raises a `ValidationError` on construction.**

Check the field constraints:
- `ph` must be between 0.0 and 14.0.
- `nitrogen_ppm`, `phosphorus_ppm`, `potassium_ppm` must be >= 0.0.
- `organic_carbon_pct` must be between 0.0 and 100.0.

All fields are required; there are no defaults.

---

**Q: `farmbrain serve` exits with "uvicorn is required".**

Install uvicorn: `pip install uvicorn`. The `api` module is an optional dependency not
included in the base package.

---

**Q: `db.by_name()` returns `None` even though I can see the crop in `crops --list`.**

The lookup is case-insensitive but checks the full name. Some crops have parenthetical
common names, e.g., `"Pearl Millet (Bajra)"`. You can also search with the simple form
`"pearl millet (bajra)"` since the comparison is lowercased.

---

**Q: The advisory says "nitrogen is LOW" but my soil card says nitrogen is medium.**

FarmBrain uses ICAR-standard thresholds for the Indo-Gangetic plains and similar soils.
These may differ from the thresholds your state uses. Always cross-check recommendations
with your local KVK or block agriculture officer.

---

**Q: How do I use FarmBrain with Hindi input?**

The core Python library and CLI accept English crop names and field names. For a Hindi or
regional-language interface, wrap FarmBrain's API in a translation layer or use
aumai-kisanmitra, which carries a `language` field through all farmer query responses.

---

**Q: Can I add my own crops to the database?**

Yes. Subclass `CropDatabase`, override `__init__`, and append your custom `Crop` objects
to `self._crops`. You can also pass a custom `CropDatabase` instance to `SoilAnalyzer`:

```python
from aumai_farmbrain.core import CropDatabase, SoilAnalyzer
from aumai_farmbrain.models import Crop

class MyCropDatabase(CropDatabase):
    def __init__(self) -> None:
        super().__init__()
        self._crops.append(Crop(
            name="Bamboo",
            season="kharif",
            water_requirement="medium",
            soil_types=["loam", "alluvial"],
            growth_days=365,
        ))

analyzer = SoilAnalyzer(crop_db=MyCropDatabase())
```

---

## Next Steps

- Read the [API Reference](api-reference.md) for complete class and method documentation.
- Explore the [examples/quickstart.py](../examples/quickstart.py) for runnable demo code.
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute crop data or soil analysis improvements.
- For climate integration, install [aumai-climatewatch](https://github.com/aumai/aumai-climatewatch).
- For farmer-facing query handling, see [aumai-kisanmitra](https://github.com/aumai/aumai-kisanmitra).
