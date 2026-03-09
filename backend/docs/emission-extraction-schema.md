# Emission Extraction Schema (LLM Output)

**Version:** 1.0  
**Purpose:** Contract between the AI parser (Noon/Bunker report) and the calculation engine.

## JSON Structure

```json
{
  "vessel_name": "string",
  "imo_number": "string",
  "report_date": "YYYY-MM-DD",
  "fuel_entries": [
    {
      "fuel_type": "VLSFO|LSMGO|MGO|LNG|biofuels|HFO|LFO|MDO|other",
      "consumption_mt": 12.5,
      "operational_status": "at_sea_cruising|at_berth|at_anchor"
    }
  ],
  "distance_nm": 245.0
}
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| vessel_name | string | Yes | Vessel name from report |
| imo_number | string | Yes | IMO number (7 digits) |
| report_date | date | Yes | Report date (YYYY-MM-DD) |
| fuel_entries | array | Yes | Fuel consumption entries |
| distance_nm | float | No | Distance in nautical miles (24h or since last port) |

### Fuel Entry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fuel_type | string | Yes | VLSFO, LSMGO, MGO, LNG, biofuels, HFO, LFO, MDO, other |
| consumption_mt | float | Yes | Fuel consumed in metric tonnes (≥ 0) |
| operational_status | string | Yes | at_sea_cruising, at_berth, at_anchor |

## Pydantic Model

See `app.schemas.emission.EmissionExtractionResult`.
