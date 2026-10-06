"""SEEF — Self-Evolving Feature Engineering Framework: minimal Python dashboard."""
import json
import streamlit as st
from config import Config
from stream.stream_manager import SEEF
from dashboard import core_view

NAME = 'SEEF — Self-Evolving Feature Engineering Framework'
st.set_page_config(page_title=NAME, layout='wide', page_icon='◈')
st.markdown('''<style>
.stApp {background:#f6f7fb;color:#25263c}
.block-container {max-width:1320px;padding-top:2rem}
[data-testid="stMetric"] {background:white;border:1px solid #e7e9f1;border-radius:12px;padding:18px}
[data-testid="stMetricLabel"] {color:#7a8093}
.stTabs [data-baseweb="tab-list"] {gap:22px;border-bottom:1px solid #e7e9f1}
.stTabs [aria-selected="true"] {color:#6c53df}
.seef-stage {background:white;border:1px solid #e7e9f1;border-radius:12px;padding:22px;margin:8px 0;min-height:130px}
.seef-stage small {display:block;color:#9a9eb0;margin-bottom:15px}
.seef-stage strong {font-size:16px}
.seef-stage p {font-size:12px;color:#7f8499;margin:8px 0 0}
.seef-stage.active {border-color:#c5b5ee;background:#f0ebfb}
.seef-stage.complete {border-color:#d1e6db;background:#f0f8f4}
.seef-stage.rejected,.seef-stage.rollback {border-color:#ebcaa7;background:#fff5ea}
.seef-heading {font-size:11px;letter-spacing:1px;color:#6c53df;font-weight:700;margin-bottom:8px}
</style>''', unsafe_allow_html=True)
st.markdown(f'<div class="seef-heading">{NAME}</div>', unsafe_allow_html=True)
st.title('Understand every adaptation.')
st.caption('Python engine · A changing stream. Evolving features. One frozen classifier.')

if 'engine' not in st.session_state:
    st.session_state.engine = SEEF()
    st.session_state.engine.advance(320)
    st.session_state.running = False

setup = st.columns([3, 1, 1.4, 1.4, 1.4, 1.4], vertical_alignment='bottom')
with setup[0]:
    scenario = st.selectbox('Scenario', ['demo', 'sudden', 'recurring'], format_func=lambda s: {'demo':'Full evolution demo', 'sudden':'Sudden drift', 'recurring':'Recurring drift'}[s])
with setup[1]:
    seed = st.number_input('Seed', min_value=0, max_value=4294967295, value=42, step=1)
with setup[2]:
    reset = st.button('Reset', use_container_width=True)
with setup[3]:
    step = st.button('Step +160', use_container_width=True)
with setup[4]:
    demo = st.button('Run full demo', use_container_width=True)
with setup[5]:
    toggle = st.button('Pause stream' if st.session_state.running else 'Start stream', type='primary', use_container_width=True)

if reset or demo:
    st.session_state.engine.memory.close()
    st.session_state.engine = SEEF(Config(seed=int(seed), scenario='demo' if demo else scenario, speed=160))
    st.session_state.engine.advance(320)
    st.session_state.running = False
engine = st.session_state.engine
if toggle:
    st.session_state.running = not st.session_state.running
    st.rerun()
if step:
    engine.advance(160)
if demo:
    with st.spinner('Computing predictions and future-window adaptations…'):
        engine.advance(max(0, 14000 - engine.stream.step))
if reset or demo:
    st.rerun()
if scenario != engine.c.scenario or int(seed) != engine.c.seed:
    st.caption('Scenario and seed changes apply on Reset. Run full demo always uses the full evolution scenario.')

@st.fragment(run_every=1)
def live():
    if st.session_state.running:
        engine.advance(160)
    st.caption(f"{'Streaming' if st.session_state.running else 'Paused'} · {engine.stream.step:,} samples · seed {engine.c.seed}")
    overview, process, results = st.tabs(['Overview', 'Process', 'Results'])
    with overview:
        core_view.overview(engine)
    with process:
        core_view.process(engine)
    with results:
        core_view.results(engine)
        st.download_button('Export run', json.dumps({'framework':NAME, 'runtime':'Python', 'config':vars(engine.c), 'history':engine.history, 'events':engine.events, 'memory':engine.memory.all(), 'summary':engine.summary()}, indent=2), 'SEEF_run.json', 'application/json')
    with st.expander('How SEEF works'):
        st.write(NAME)
        st.write('Monitor → Detect & fingerprint → Recall → Evolve → Validate → Deploy & remember')
        st.write('SEEF replaces one feature input slot while keeping classifier weights fixed. Candidates are ranked using past data and tested on future samples. Memory recalls successful repairs; repeated deployment checks still apply. The default threshold is 0.28, minimum paired F1 gain is 3 percentage points, and five consecutive passing windows are required.')
        st.caption('Synthetic binary classification with three variables. Python uses River detectors and scikit-learn. The independent browser engine uses approximations and provides recorded process replay. Results can differ between runtimes and gains are not guaranteed. Advanced research parameters remain in config.py; ablations run from the command line.')
live()
