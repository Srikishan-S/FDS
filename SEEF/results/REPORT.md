# SEEF — Self-Evolving Feature Engineering Framework

## Historical measured prototype report

Runtime: Python. Seeds: 42, 7, 21. 14,000 samples per independent experiment; 160 samples per window. All values are calculated from predictions and adaptation events.

| Approach | Mean F1 | Mean adaptation delay (samples) | Reuse rate |
|---|---:|---:|---:|
| A Static | 0.6897 | — | 0.0% |
| B Retraining | 0.6754 | — | 0.0% |
| C SEEF without EAM | 0.7842 | 1120 | 0.0% |
| D SEEF with EAM | 0.7955 | 1040 | 25.0% |
| E SEEF unconditioned | 0.7955 | 1040 | 25.0% |

Measured mean F1 benefit with EAM: **1.13 percentage points**.

The unconditioned generation ablation matched full SEEF on these three seeds. This synthetic demonstration therefore does **not** establish that conditioning improves performance. The retraining baseline is only recent-window linear logistic retraining and is weak for interaction concepts.

Memory reduces qualification overhead for previously successful repairs: unfamiliar candidates require two extra qualification windows, recalled candidates retain the same five consecutive safety-window checks. The resulting delay reduction is partly this explicit policy, not proof of an inherently faster search algorithm. Ablate this policy in further work.

The stable-return phase can favor the untouched static baseline. SEEF may select a less accurate repair than the original representation, because ranking and finite-window scores are imperfect. These outputs are retained rather than overwritten to fit a recovery target.

## Seed-42 adaptation evidence

- Step 4480: x1*x2; F1 gain +33.57%; delay 1120 samples; memory reuse False.
- Step 7360: x1²; F1 gain +51.78%; delay 1120 samples; memory reuse False.
- Step 10080: x1*x2; F1 gain +53.97%; delay 800 samples; memory reuse True.
- Step 13440: identity; F1 gain +36.15%; delay 1120 samples; memory reuse False.

## Original-source validation

10 Python tests passed. Browser numerical integration checks passed, including frozen weights, recurrence reuse, delayed labels and latency-gate rejection. Streamlit AppTest rendered the initial, stepped and adapted dashboards without exceptions. A supervised visual browser preview was unavailable for the static-hosted build; responsive styles and JavaScript syntax were checked.

## Research status

The integrated SEEF mechanism is a proposed contribution. No broad performance, statistical significance, or literature novelty claim is established by this prototype.
