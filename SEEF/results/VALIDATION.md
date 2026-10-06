# SEEF — Self-Evolving Feature Engineering Framework

## Validation of the minimal interface update

- All **10 Python engine tests passed** (`python -m pytest -q`).
- Browser numerical integration checks passed: recurring memory recall, frozen classifier weights, delayed labels, and rejection by the latency gate.
- New browser recording checks passed: drift, recall, generation, future-window scores, promotion, stored memory, rejected candidates, immutable historical checkpoints, and trace export.
- Streamlit AppTest passed for initial rendering, start/pause labels, stepping, the full 14,000-sample demo, and reset. Its three tabs are Overview, Process, and Results.
- Headless Chromium UI checks passed for navigation, scenario reset, invalid seed handling, stream start/pause, stepping, the full demo, six-stage visualization, replay, stage evidence, expandable deployment checks, JSON download, method dialog, and reset.
- Desktop and 375px/760px layouts were checked for page overflow. Desktop and mobile screenshots were visually inspected; mobile action buttons were adjusted to fit without clipping.

The browser seed-42 full demo measured four feature promotions, four successful memories, and one recalled repair. Its mean window F1 was approximately 0.7994; these are observed demonstration outputs, not required targets or proof of real-world performance.

The bundled `REPORT.md`, CSVs, comparison HTML, and example JSON are retained historical Python research outputs from the original source package. They are separate from fresh UI run results. No new multi-seed ablation was performed for this UI update.

Process replay is browser-only. Python shows current processing state. The browser retains the most recent 600 process checkpoints; a standard full demo fits within the limit.
