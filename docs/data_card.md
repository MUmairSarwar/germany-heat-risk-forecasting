# Data card

## Source

- Provider: Deutscher Wetterdienst (DWD), Climate Data Center (CDC)
- Station: 00917 Darmstadt, Hessen (49.8809 N, 8.6779 E; 162 m)
- Resolution: daily
- Access: DWD Open Data server
- Historical coverage used by the current run: recorded in `outputs/metrics.json`

## Variables

| Code | Meaning | Unit |
|---|---|---|
| TXK | Daily maximum air temperature | °C |
| TNK | Daily minimum air temperature | °C |
| TMK | Daily mean air temperature | °C |
| UPM | Daily mean relative humidity | % |
| RSK | Daily precipitation height | mm |
| SDK | Daily sunshine duration | hours |
| VPM | Daily mean vapour pressure | hPa |

The pipeline converts DWD's `-999` sentinel to missing values, sorts dates, and
keeps the most recent record when historical and recent archives overlap.
Annual trend calculations retain only years with at least 350 valid daily maximum
temperature observations, excluding partial first/current years.

## Scope and limitations

One station cannot represent every neighbourhood or the urban heat-island effect.
Observations can be missing, corrected, or revised by DWD. The project predicts a
station-level meteorological indicator; it does not contain medical outcomes and
cannot estimate individual health risk.
