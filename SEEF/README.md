# SEEF — Self-Evolving Feature Engineering Framework

SEEF adapts the feature representation of a changing data stream while keeping its classifier weights fixed. This project contains a Python research engine and an independent, dependency-free browser simulation.

The interface keeps the core workflow in **three views**:

| View | Purpose |
|---|---|
| **Overview** | Rolling F1, baseline gain, drift evidence, current representation, recent activity |
| **Process** | Monitor → Detect & fingerprint → Recall → Evolve → Validate → Deploy & remember |
| **Results** | Measured performance, deployed repairs, successful memories, JSON export |

The browser Process view includes an interactive visualizer and recorded checkpoint replay. Select a stage to inspect its evidence, drag the replay slider to an earlier checkpoint, or choose **Follow live**. The visualizer reads actual engine snapshots; it does not animate a predetermined success story. Candidate rejection and automatic rollback are displayed when they occur.

## Open the webpage

On Windows, double-click **Start_SEEF.bat** (Python must be installed), or run `python launch_browser.py` to start the local server and open the webpage.

Alternatively, from the extracted `SEEF` directory:

```bash
python -m http.server 8000 --directory browser
```

Open **http://localhost:8000**. No npm installation, API key, internet connection, or external font/CDN is required. ES modules must be served over HTTP; do not open `index.html` directly by double-clicking it.

1. Choose **Full evolution demo**, **Sudden drift**, or **Recurring drift**.
2. Choose a seed (42 by default).
3. Use **Start stream**, **Step +160**, or **Run full demo**.
4. Inspect **Process** and **Results**.
5. Use **Export run** in Results to save measurements, events, memory, versions, and recorded checkpoints.

Scenario changes restart the browser stream. Seed edits apply when using **Reset** or **Run full demo**. The full demo always runs the complete predefined schedule to 14,000 samples. Reset starts a fresh run and clears its memories and replay history. Replay inspects recorded state without changing the model. The most recent 600 process checkpoints are retained; the normal full demo fits within this limit.

## Run the Python dashboard

Python 3.11 or later:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The Python dashboard has the same three core views and a live process visualizer. Recorded checkpoint replay is available in the browser implementation. Python scenario and seed edits apply with Reset; Run full demo selects the predefined schedule. The UI exposes only these core settings. Research parameters remain available in `config.py`; they are not separate dashboard features.

## The core method

1. **Monitor.** Train one logistic classifier on an independent seeded stable dataset, then freeze its weights. Predict each sample before processing its label. Compare SEEF with the untouched static baseline.
2. **Detect & fingerprint.** Combine error, input-distribution shift, target-correlation change, confidence, residual, and detector-vote signals. Confirm drift using two consecutive above-threshold windows. Form a scaled, normalized fingerprint from observed evidence.
3. **Recall.** Retrieve up to three previously successful repairs using cosine similarity. A sufficiently similar repair receives priority; it does not bypass validation.
4. **Evolve.** Generate bounded, context-relevant transformations and rank them using the past labelled window. Transform parameters use only past inputs. A shortlisted adapter replaces the `x1` input slot; `x2`, `x3`, weights, and classifier dimensionality stay fixed.
5. **Validate.** Record each candidate's predictions on the same future samples as the production representation. Check paired F1 gain, latency, feature count, stability, adapter resources, and confidence. Require five consecutive passing windows by default. Unfamiliar repairs require two extra qualification windows.
6. **Deploy & remember.** Promote a passing representation, save its successful repair, and monitor the new version. During an eight-window probation period, two degraded windows or excessive latency restore the previous stable representation. Rejected candidates retain the current representation.

Default evaluation window: 160 samples. Drift threshold: 0.28. Required paired F1 improvement: **more than 3 percentage points**. Memory similarity threshold: 0.85. No recovery score, similarity, or deployment success is assigned in advance.

The predefined demo is stable for the first 3,000 samples, then visits interaction, nonlinear, recurring interaction, and stable regimes at 3,000-sample intervals. The stream generator's ground-truth regime is evaluation context; it is never an input to fingerprint inference, memory retrieval, or feature selection.

## Runtime differences and scope

**Python** uses River ADWIN, Page-Hinkley, and DDM; scikit-learn mutual information; and a contextual ridge bandit. **Browser** uses bounded detector approximations, binned information gain, and cosine-kernel contextual action estimates. Both run the complete adaptation workflow. They are separate implementations, not a webpage connected to the Python server. Their seeded numerical results can differ. Latency depends on the device.

This is a synthetic binary classification prototype with three variables and a single replaceable feature slot. It does not ingest arbitrary CSV files, support regression, or establish general real-world superiority. Fingerprint types and adaptation confidence are heuristic. Improvements and memory reuse can be zero or negative. The memory qualification policy itself contributes to faster recall and should be ablated in further research.

The proposed integrated mechanism is drift-fingerprint-conditioned feature evolution with episodic adaptation memory. The product name is always **SEEF — Self-Evolving Feature Engineering Framework**. Existing component algorithms are not claimed as individually novel.

## Validate and run optional research experiments

```bash
node tests/browser.test.mjs
python -m pytest -q
python -m evaluation.experiments --steps 14000 --seeds 42 7 21 --output results
```

The optional command-line experiments compare static prediction, recent-window retraining, SEEF without memory, SEEF with memory, and unconditioned feature generation. They are not exposed as extra UI pages. `results/REPORT.md` and its experiment files are retained historical Python outputs from the original source package; the UI computes fresh values. Do not treat historical results as outputs of the current browser run.

See [architecture](docs/ARCHITECTURE.md), [algorithm](docs/ALGORITHM.md), [modules](docs/MODULES.md), and [validation](results/VALIDATION.md).
