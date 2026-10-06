# SEEF — Self-Evolving Feature Engineering Framework

## Interface

| Module | Responsibility |
|---|---|
| `browser/index.html` | Accessible page shell, three-view navigation, scenario/seed controls, method dialog |
| `browser/style.css` | Responsive modern interface, process states, focus visibility, reduced-motion support |
| `browser/app.js` | Overview, interactive Process visualizer/replay, Results, stream controls, JSON export |
| `browser/process.js` | Immutable summaries of observed processing events and windows; stage-state derivation |
| `app.py` | Minimal three-view Streamlit entry point with scenario/seed and stream controls |
| `dashboard/core_view.py` | Python metrics, baseline chart, live process view, repairs, memory |

## Core engine

| Module | Responsibility |
|---|---|
| `browser/engine.js` | Independent browser numerical engine, adaptation loop, event-backed trace |
| `config.py` | Python research defaults and advanced parameters |
| `stream/` | Seeded observations, controlled drift scenarios, pipeline orchestration |
| `model/` | Independently trained frozen classifier and measured predictions |
| `drift/` | Detector signals, fingerprints, drift confirmation |
| `memory/` | Successful repair episodes, SQLite storage, cosine recall |
| `features/` | Bounded transformations, past-window ranking, internal metadata lifecycle |
| `adaptation/` | Contextual strategy, prospective candidate checks, rewards, deployment, rollback |
| `evaluation/` | Prediction metrics and optional command-line experiments |
| `tests/` | Numerical invariants and process recording checks |

The original specialist dashboard helpers remain as unused research utilities; they are not connected to the minimal UI. The core engines retain advanced configuration for reproducible research without additional UI pages.

Python and browser detector/controller implementations differ. See README for scope and runtime details. Neither implementation assigns successful outcomes in advance.
