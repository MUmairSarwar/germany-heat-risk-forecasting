# Copilot instructions

This repository is a research-style portfolio project for probabilistic heat-risk
forecasting in Darmstadt, Germany.

- Keep time ordering intact. Never randomly shuffle observations or use future data
  in features, model selection, calibration, or evaluation.
- Preserve the train (through 2022), validation (2023-2024), and holdout (2025+)
  boundaries unless a documented experiment explicitly changes them.
- Prefer transparent mathematical methods and state their assumptions.
- Treat DWD values of `-999` as missing and preserve units from the source metadata.
- A DWD hot day means daily maximum air temperature `TXK >= 30.0 °C`.
- Do not describe this research model as an official DWD warning service.
- Add or update tests for every behaviour change.
- Use deterministic random seeds and avoid adding heavy dependencies without need.
- Keep public claims tied to generated metrics in `outputs/metrics.json`.

