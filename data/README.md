# Data

The pipeline downloads daily climate observations for DWD station **00917
Darmstadt** from the [DWD Climate Data Center](https://opendata.dwd.de/).

Raw archives are cached locally under `.cache/dwd/` and are not committed. The
generated `outputs/darmstadt_daily.csv` file is also excluded from source control;
run `heat-risk download` to recreate it.

Source attribution: **Deutscher Wetterdienst (DWD), Climate Data Center (CDC)**.
See [`docs/data_card.md`](../docs/data_card.md) for variables, quality checks, and
known limitations.

