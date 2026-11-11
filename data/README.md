# Data

The pipeline downloads daily climate observations for DWD station **00917
Darmstadt** from the [DWD Climate Data Center](https://opendata.dwd.de/).

The historical archive is cached under its DWD filename in `.cache/dwd/`. The
rolling recent archive is fetched on every download. Source control excludes
the cache and the generated `outputs/darmstadt_daily.csv`. Run `heat-risk download`
to recreate the CSV using the current sources.

Source attribution: **Deutscher Wetterdienst (DWD), Climate Data Center (CDC)**.
See [`docs/data_card.md`](../docs/data_card.md) for variables, quality checks, and
known limitations.

