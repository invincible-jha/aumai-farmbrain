# API Reference — aumai-farmbrain

Complete reference for all public classes, functions, and Pydantic models in the
`aumai_farmbrain` package. All classes and functions are typed; the package requires
Python 3.11+ and uses strict mypy mode.

---

## Module: `aumai_farmbrain.models`

Pydantic v2 models used as input and output at all API boundaries.

---

### `AGRICULTURAL_DISCLAIMER`

```python
AGRICULTURAL_DISCLAIMER: str
```

A mandatory disclaimer string included in all `CropAdvisory` outputs and CLI output:

> *"This tool provides AI-assisted agricultural analysis only. Verify all recommendations
> with local agricultural experts and government extension services before application.
> Crop yields and soil recommendations are estimates based on limited data."*

All `CropAdvisory` objects include this in their `disclaimer` field.

---

### `Crop`

```python
class Crop(BaseModel):
    name: str
    season: str
    water_requirement: str
    soil_types: list[str]
    growth_days: int
```

Represents an Indian agricultural crop with cultivation metadata.

**Fields:**

| Field              | Type        | Constraints             | Description |
|--------------------|-------------|-------------------------|-------------|
| `name`             | `str`       | required                | Common name of the crop (e.g., "Rice", "Pearl Millet (Bajra)") |
| `season`           | `str`       | must be `kharif`, `rabi`, or `zaid` | Growing season — normalised to lowercase by validator |
| `water_requirement`| `str`       | required                | Water requirement class: `"low"`, `"medium"`, or `"high"` |
| `soil_types`       | `list[str]` | required, non-empty     | Compatible soil types for this crop |
| `growth_days`      | `int`       | `> 0`                   | Days from sowing to harvest |

**Validator:**

`validate_season` (field validator) normalises the `season` value to lowercase before
storage, ensuring case-insensitive input is accepted.

**Example:**

```python
from aumai_farmbrain.models import Crop

crop = Crop(
    name="Cotton",
    season="kharif",
    water_requirement="medium",
    soil_types=["black", "alluvial", "loam"],
    growth_days=180,
)
print(crop.model_dump())
```

---

### `SoilProfile`

```python
class SoilProfile(BaseModel):
    ph: float
    nitrogen_ppm: float
    phosphorus_ppm: float
    potassium_ppm: float
    organic_carbon_pct: float
    soil_type: str
```

Chemical and physical profile of a soil sample, typically obtained from a Soil Health Card
test.

**Fields:**

| Field                | Type    | Constraints         | Description |
|----------------------|---------|---------------------|-------------|
| `ph`                 | `float` | `0.0 <= ph <= 14.0` | Soil pH value |
| `nitrogen_ppm`       | `float` | `>= 0.0`            | Available nitrogen in ppm (parts per million) |
| `phosphorus_ppm`     | `float` | `>= 0.0`            | Available phosphorus in ppm |
| `potassium_ppm`      | `float` | `>= 0.0`            | Available potassium in ppm |
| `organic_carbon_pct` | `float` | `0.0 <= pct <= 100.0` | Organic carbon as a percentage of soil weight |
| `soil_type`          | `str`   | required            | Soil classification string (e.g., `"alluvial"`, `"black"`, `"red"`, `"loam"`) |

**Raises:** `pydantic.ValidationError` if any field fails its constraint.

**Example:**

```python
from aumai_farmbrain.models import SoilProfile

soil = SoilProfile(
    ph=6.8,
    nitrogen_ppm=150.0,
    phosphorus_ppm=14.0,
    potassium_ppm=130.0,
    organic_carbon_pct=0.55,
    soil_type="alluvial",
)
```

---

### `WeatherData`

```python
class WeatherData(BaseModel):
    location: str
    temperature_c: float
    humidity_pct: float
    rainfall_mm: float
    forecast_days: int = 7
```

Current weather conditions for an agricultural location. Used to enrich crop advisories with
weather-based risk alerts.

**Fields:**

| Field           | Type    | Constraints           | Description |
|-----------------|---------|-----------------------|-------------|
| `location`      | `str`   | required              | Location name or coordinates string |
| `temperature_c` | `float` | required              | Current temperature in Celsius |
| `humidity_pct`  | `float` | `0.0 <= pct <= 100.0` | Relative humidity percentage |
| `rainfall_mm`   | `float` | `>= 0.0`              | Recent rainfall in millimetres |
| `forecast_days` | `int`   | `1 <= days <= 30`, default `7` | Number of forecast days available |

**Example:**

```python
from aumai_farmbrain.models import WeatherData

weather = WeatherData(
    location="Nagpur, Maharashtra",
    temperature_c=42.5,
    humidity_pct=30.0,
    rainfall_mm=0.0,
    forecast_days=7,
)
```

---

### `CropAdvisory`

```python
class CropAdvisory(BaseModel):
    crop: Crop
    soil: SoilProfile
    recommendations: list[str]
    fertilizer_plan: dict[str, str]
    irrigation_schedule: dict[str, str]
    risk_alerts: list[str] = []
    disclaimer: str = AGRICULTURAL_DISCLAIMER
```

Full advisory output for a crop-soil-weather combination. Returned by `CropAdvisor.advise()`.

**Fields:**

| Field                | Type              | Description |
|----------------------|-------------------|-------------|
| `crop`               | `Crop`            | The crop this advisory is for |
| `soil`               | `SoilProfile`     | The soil profile used to generate the advisory |
| `recommendations`    | `list[str]`       | Actionable agronomic recommendations in plain English |
| `fertilizer_plan`    | `dict[str, str]`  | Fertilizer application instructions keyed by growth stage |
| `irrigation_schedule`| `dict[str, str]`  | Irrigation instructions keyed by growth stage |
| `risk_alerts`        | `list[str]`       | Risk warnings for weather or soil issues; may be empty |
| `disclaimer`         | `str`             | Mandatory agricultural advisory disclaimer text |

**Fertilizer plan stages for rice:** `basal`, `tillering`, `panicle initiation`

**Fertilizer plan stages for wheat:** `basal`, `crown root initiation`, `jointing`

**Fertilizer plan stages for cotton:** `basal`, `squaring`, `boll development`

**Fertilizer plan stages (default/all other crops):** `basal`, `vegetative`, `reproductive`

**Irrigation schedule stages (all crops):** `establishment`, `vegetative`, `reproductive`, `maturation`

**Example:**

```python
advisory_dict = advisory.model_dump()
advisory_json = advisory.model_dump_json(indent=2)
restored = CropAdvisory.model_validate(advisory_dict)
```

---

## Module: `aumai_farmbrain.core`

The core engine. Contains three classes: `CropDatabase`, `SoilAnalyzer`, and `CropAdvisor`.

---

### `CropDatabase`

```python
class CropDatabase:
    def __init__(self) -> None: ...
    def all_crops(self) -> list[Crop]: ...
    def by_name(self, name: str) -> Crop | None: ...
    def by_season(self, season: str) -> list[Crop]: ...
    def by_soil_type(self, soil_type: str) -> list[Crop]: ...
```

In-memory catalogue of 50+ Indian crops with lookup utilities. Initialised once and held as
a singleton or recreated per request (it is lightweight).

The catalogue covers:
- **Kharif crops (20):** Rice, Maize, Sorghum, Pearl Millet, Cotton, Sugarcane, Soybean,
  Groundnut, Sesame, Pigeonpea, Blackgram, Greengram, Jute, Turmeric, Ginger, Banana, Okra,
  Bitter Gourd, Cowpea, Castor.
- **Rabi crops (18):** Wheat, Barley, Chickpea, Lentil, Mustard, Rapeseed, Linseed, Sunflower,
  Pea, Potato, Onion, Garlic, Coriander, Fenugreek, Carrot, Cabbage, Cauliflower, Spinach.
- **Zaid crops (13):** Watermelon, Muskmelon, Cucumber, Pumpkin, Summer Squash, Moong, Cowpea,
  Bottle Gourd, Ridge Gourd, Snake Gourd, Bitter Melon, Cluster Beans, Amaranth.

---

#### `CropDatabase.__init__`

```python
def __init__(self) -> None
```

Constructs the crop database from the built-in static catalogue. All 50+ entries are validated
and stored as `Crop` Pydantic models.

**Example:**

```python
from aumai_farmbrain.core import CropDatabase

db = CropDatabase()
```

---

#### `CropDatabase.all_crops`

```python
def all_crops(self) -> list[Crop]
```

Return every crop in the database as a list. Order is insertion order (kharif → rabi → zaid).

**Returns:** `list[Crop]` — all crops (51 in the current release)

**Example:**

```python
all_crops = db.all_crops()
print(f"Total crops: {len(all_crops)}")
```

---

#### `CropDatabase.by_name`

```python
def by_name(self, name: str) -> Crop | None
```

Case-insensitive crop lookup by name.

**Parameters:**

| Parameter | Type  | Description |
|-----------|-------|-------------|
| `name`    | `str` | The crop name to search for. Case-insensitive; full name match required. |

**Returns:** The matching `Crop` object, or `None` if no crop with that name exists.

**Example:**

```python
crop = db.by_name("rice")       # returns Rice crop
crop = db.by_name("WHEAT")      # case-insensitive: returns Wheat crop
crop = db.by_name("mango")      # returns None — not in database
```

---

#### `CropDatabase.by_season`

```python
def by_season(self, season: str) -> list[Crop]
```

Return all crops for a given growing season. The `season` argument is lowercased before
comparison.

**Parameters:**

| Parameter | Type  | Accepted values             | Description |
|-----------|-------|-----------------------------|-------------|
| `season`  | `str` | `"kharif"`, `"rabi"`, `"zaid"` | The season to filter by |

**Returns:** `list[Crop]` — all crops for that season; empty list if none match.

**Example:**

```python
kharif_crops = db.by_season("kharif")
rabi_crops = db.by_season("RABI")  # case-insensitive
```

---

#### `CropDatabase.by_soil_type`

```python
def by_soil_type(self, soil_type: str) -> list[Crop]
```

Return all crops compatible with a specific soil type. Comparison is case-insensitive exact
match against each soil type string in the crop's `soil_types` list.

**Parameters:**

| Parameter   | Type  | Description |
|-------------|-------|-------------|
| `soil_type` | `str` | Soil type string, e.g., `"black"`, `"alluvial"`, `"loam"`, `"red"` |

**Returns:** `list[Crop]` — crops that list this soil type as compatible.

**Example:**

```python
black_crops = db.by_soil_type("black")
alluvial_crops = db.by_soil_type("alluvial")
```

---

### `SoilAnalyzer`

```python
class SoilAnalyzer:
    def __init__(self, crop_db: CropDatabase | None = None) -> None: ...
    def analyze(self, soil: SoilProfile) -> list[str]: ...
    def suitable_crops(self, soil: SoilProfile) -> list[Crop]: ...
```

Analyses soil profiles and recommends suitable crops. Uses ICAR-derived thresholds for five
soil parameters.

**ICAR thresholds used internally:**

| Parameter        | Low (below) | High (above) |
|------------------|-------------|--------------|
| pH               | 6.0         | 7.5          |
| Nitrogen (ppm)   | 140.0       | 280.0        |
| Phosphorus (ppm) | 10.0        | 25.0         |
| Potassium (ppm)  | 108.0       | 280.0        |
| Organic carbon % | 0.50        | —            |

---

#### `SoilAnalyzer.__init__`

```python
def __init__(self, crop_db: CropDatabase | None = None) -> None
```

**Parameters:**

| Parameter  | Type                      | Default  | Description |
|------------|---------------------------|----------|-------------|
| `crop_db`  | `CropDatabase` or `None`  | `None`   | Optional crop database for dependency injection. A new `CropDatabase()` is created if `None`. |

---

#### `SoilAnalyzer.analyze`

```python
def analyze(self, soil: SoilProfile) -> list[str]
```

Evaluate the soil profile against ICAR thresholds and return plain-English recommendations.
The last element of the returned list is always `AGRICULTURAL_DISCLAIMER`.

**Parameters:**

| Parameter | Type          | Description |
|-----------|---------------|-------------|
| `soil`    | `SoilProfile` | The soil profile to analyse |

**Returns:** `list[str]` — one recommendation per soil parameter plus the disclaimer. Typically
6 strings: pH, nitrogen, phosphorus, potassium, organic carbon, disclaimer.

**Example:**

```python
from aumai_farmbrain.core import SoilAnalyzer
from aumai_farmbrain.models import SoilProfile

analyzer = SoilAnalyzer()
soil = SoilProfile(ph=5.2, nitrogen_ppm=90.0, phosphorus_ppm=7.0,
                   potassium_ppm=85.0, organic_carbon_pct=0.3, soil_type="red")

for rec in analyzer.analyze(soil):
    print(rec)
```

---

#### `SoilAnalyzer.suitable_crops`

```python
def suitable_crops(self, soil: SoilProfile) -> list[Crop]
```

Return all crops from the database that are compatible with the given soil profile. A crop is
considered compatible if:

1. Its `soil_types` list contains the `soil.soil_type` (case-insensitive).
2. Its pH tolerance heuristic passes:
   - pH < 5.5: only high-water crops and specific acid-tolerant crops (rice, jute, turmeric, ginger).
   - 5.5 <= pH <= 8.0: all soil-type-matching crops.
   - pH > 8.0: only low-water-requirement crops.

**Parameters:**

| Parameter | Type          | Description |
|-----------|---------------|-------------|
| `soil`    | `SoilProfile` | The soil profile to match against |

**Returns:** `list[Crop]` — compatible crops; may be empty for extreme pH values.

**Example:**

```python
compatible = analyzer.suitable_crops(soil)
print(f"{len(compatible)} compatible crops found")
```

---

### `CropAdvisor`

```python
class CropAdvisor:
    def advise(
        self,
        crop: Crop,
        soil: SoilProfile,
        weather: WeatherData | None = None,
    ) -> CropAdvisory: ...
```

Generates complete crop advisories including fertilizer and irrigation plans. The advisor
uses built-in fertilizer plans for rice, wheat, and cotton; all other crops receive a generic
three-stage fertilizer plan.

---

#### `CropAdvisor.advise`

```python
def advise(
    self,
    crop: Crop,
    soil: SoilProfile,
    weather: WeatherData | None = None,
) -> CropAdvisory
```

Generate a complete `CropAdvisory` for the given inputs.

**Parameters:**

| Parameter | Type                    | Description |
|-----------|-------------------------|-------------|
| `crop`    | `Crop`                  | The crop to generate an advisory for |
| `soil`    | `SoilProfile`           | The soil profile for the field |
| `weather` | `WeatherData` or `None` | Optional current weather data. If provided, weather risk alerts are generated. |

**Returns:** `CropAdvisory` — a fully validated Pydantic model containing:
- `recommendations`: crop metadata + soil analysis recommendations
- `fertilizer_plan`: stage-wise fertilizer instructions
- `irrigation_schedule`: stage-wise irrigation instructions
- `risk_alerts`: weather and soil risk warnings (may be empty)
- `disclaimer`: `AGRICULTURAL_DISCLAIMER`

**Weather risk alert thresholds:**

| Condition                  | Threshold     | Alert generated |
|----------------------------|---------------|-----------------|
| Extreme heat               | > 40°C        | Apply mulching, increase irrigation |
| Cold stress (kharif crops) | < 5°C         | Protect seedlings with polythene |
| Excess rainfall            | > 200 mm      | Clear drainage channels |
| High humidity              | > 85%         | Monitor for fungal disease |
| Strongly acidic soil       | pH < 5.5      | Apply lime before sowing |
| Strongly alkaline soil     | pH > 8.5      | Apply zinc sulphate |

**Example:**

```python
from aumai_farmbrain.core import CropAdvisor, CropDatabase
from aumai_farmbrain.models import SoilProfile, WeatherData

db = CropDatabase()
advisor = CropAdvisor()

crop = db.by_name("cotton")
soil = SoilProfile(ph=7.0, nitrogen_ppm=160.0, phosphorus_ppm=13.0,
                   potassium_ppm=145.0, organic_carbon_pct=0.48, soil_type="black")
weather = WeatherData(location="Akola, Maharashtra", temperature_c=44.0,
                      humidity_pct=82.0, rainfall_mm=5.0, forecast_days=7)

advisory = advisor.advise(crop, soil, weather)

print(f"Risk alerts: {len(advisory.risk_alerts)}")
for alert in advisory.risk_alerts:
    print(f"  {alert}")
```

---

## Module: `aumai_farmbrain.cli`

CLI entry point registered as the `farmbrain` console script.

### `main`

The Click group. Invoke with `farmbrain --help`.

### `advise(crop, soil_file, weather_file)`

Click command. Loads `SoilProfile` and optional `WeatherData` from JSON files, looks up the
crop in `CropDatabase`, calls `CropAdvisor.advise()`, and prints the advisory to stdout.

### `crops(show_list, season)`

Click command. Prints a tabular list of crops, optionally filtered by season.

### `serve(port, host)`

Click command. Starts the FastAPI server via `uvicorn`. Requires `uvicorn` to be installed.

---

## Module: `aumai_farmbrain`

### `__version__`

```python
__version__: str  # "0.1.0"
```

Package version string. Access via `aumai_farmbrain.__version__` or `farmbrain --version`.
