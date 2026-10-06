"""Core views for SEEF — Self-Evolving Feature Engineering Framework."""
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

STAGES = ['Monitor stream', 'Detect & fingerprint', 'Recall a repair', 'Evolve features', 'Validate candidates', 'Deploy & remember']


def pct(value):
    return '—' if value is None else f'{value:.1%}'


def pp(value):
    return '—' if value is None else f'{value * 100:+.1f} pp'


def active_feature(engine):
    return 'x1' if engine.active == 'identity' else engine.active


def metrics(engine):
    latest = engine.history[-1] if engine.history else None
    promotions = [e for e in engine.events if e['event'] == 'Feature promoted']
    values = [
        ('Rolling F1', pct(engine.current_metrics.get('f1'))),
        ('Gain vs. baseline', pp(latest['SEEF'] - latest['Static']) if latest else '—'),
        ('Drifts detected', str(sum(e['event'] == 'Drift detected' for e in engine.events))),
        ('Successful memories', str(len(engine.memory.all()))),
    ]
    for col, (label, value) in zip(st.columns(4), values):
        col.metric(label, value)
    st.caption(f'{len(promotions)} features promoted · {sum(bool(e.get("reused")) for e in promotions)} recalled repairs')


def chart(engine, key='overview-performance'):
    if not engine.history:
        st.info('Advance the stream to collect an evaluation window.')
        return
    fig = go.Figure()
    steps = [r['step'] for r in engine.history]
    fig.add_trace(go.Scatter(x=steps, y=[r['Static'] for r in engine.history], name='Static baseline', line=dict(color='#adb3c2', dash='dash', width=2)))
    fig.add_trace(go.Scatter(x=steps, y=[r['SEEF'] for r in engine.history], name='SEEF', line=dict(color='#7057e5', width=3)))
    for e in engine.events:
        if e['event'] == 'Drift detected':
            fig.add_vline(x=e['step'], line_dash='dot', line_color='#d7b587', line_width=1)
    fig.update_layout(title='Performance through change', height=350, paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=30,r=20,t=55,b=35), legend=dict(orientation='h', y=1.15, x=1, xanchor='right'), xaxis_title='Sample step', yaxis=dict(title='F1', range=[0,1], tickformat='.0%', gridcolor='#edf0f6'), font=dict(color='#767d90'))
    st.plotly_chart(fig, key=key, use_container_width=True)


def overview(engine):
    metrics(engine)
    chart(engine)
    st.subheader('Active representation')
    st.code(f'[{active_feature(engine)}, x2, x3] → frozen classifier → prediction', language=None)
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader('Recent activity')
        events = engine.events[-6:]
        if events:
            st.dataframe(pd.DataFrame([{'Sample':e['step'],'Event':e['event'],'Detail':e.get('feature',e.get('reason',e.get('scenario',e.get('fingerprint',''))))} for e in reversed(events)]), hide_index=True, use_container_width=True)
        else:
            st.info(f'Monitoring the initial stream. First scheduled drift at sample {engine.c.drift_at:,}.')
    with right:
        st.subheader('Drift evidence')
        fp = engine.fingerprint or {}
        st.metric('Drift score', f"{fp['combined_score']:.3f}" if fp else '—')
        st.caption(f'Threshold {engine.c.drift_threshold:.2f} · Two windows required')
        st.write('Inferred drift:', fp.get('drift_type', 'Collecting evidence'))
        st.caption('Ground-truth scenario: ' + engine.last_regime)


def process(engine):
    stages = {'Drift injected':0,'Drift detected':1,'Fingerprint generated':1,'Memory queried':2,'Candidate features generated':3,'Shadow testing':4,'Candidates rejected':4,'Feature promoted':5,'Memory updated':5,'Memory disabled':5,'Autonomous rollback':5}
    last = next((e for e in reversed(engine.events) if e['event'] in stages), None)
    current = 4 if engine.arena else stages.get(last['event'], 0) if last else 0
    outcome = last['event'] if last else ''
    st.subheader('Live process visualizer')
    st.caption('Observed Python engine state. Open browser/ for checkpoint replay.')
    for row in range(2):
        cols = st.columns(3)
        for index, col in enumerate(cols, start=row * 3):
            state = 'complete' if index < current or outcome == 'Memory updated' else 'active' if index == current else 'pending'
            if index == current and outcome == 'Candidates rejected':
                state = 'rejected'
            if index == current and outcome == 'Autonomous rollback':
                state = 'rollback'
            with col:
                st.markdown(f'<div class="seef-stage {state}"><small>{index+1:02d} · {escape(state.capitalize())}</small><strong>{STAGES[index]}</strong><p>{escape([f"{engine.stream.step:,} samples processed", "Two-window drift confirmation", f"{len(engine.memory.all())} saved repairs", "Past-window candidate ranking", f"{engine.arena.windows if engine.arena else 0} active shadow windows", f"Active feature: {active_feature(engine)}"][index])}</p></div>', unsafe_allow_html=True)
    if engine.arena:
        st.subheader('Future-window validation')
        rows = []
        for name, s in engine.arena.candidates.items():
            checks = s.get('checks', {})
            rows.append({'Candidate':name, 'Future F1':pct(s.get('f1')), 'Paired gain':pp(s.get('gain')), 'Pass streak':f"{s['streak']} / {engine.c.stable_windows}", 'Checks':f'{sum(checks.values())} / {len(checks)}' if checks else 'Waiting'})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.caption('Checks cover improvement, latency, feature count, stability, resources, and confidence. Unfamiliar repairs require two additional qualification windows.')
    else:
        explanation = next((e['explanation'] for e in reversed(engine.events) if 'explanation' in e), None)
        if explanation:
            st.info(explanation)
        else:
            st.info('Run the full demo or start the stream to observe detection, candidate testing, and deployment.')
    st.subheader('Adaptation events')
    if engine.events:
        st.dataframe(pd.DataFrame([{'Sample':e['step'],'Event':e['event'],'Feature':e.get('feature',''),'Reason':e.get('reason','')} for e in engine.events[-30:]]), hide_index=True, use_container_width=True)


def results(engine):
    metrics(engine)
    chart(engine, key='results-performance')
    st.subheader('Deployed feature repairs')
    promotions = [e for e in engine.events if e['event'] == 'Feature promoted']
    if promotions:
        st.dataframe(pd.DataFrame([{'Sample':e['step'],'Feature':e['feature'],'Mean paired F1 gain':pp(e['gain']),'Delay (samples)':e['adaptation_delay'],'Memory reuse':bool(e['reused']),'Version':e['version']} for e in promotions]), hide_index=True, use_container_width=True)
    else:
        st.info('No feature has been promoted yet.')
    st.subheader('Episodic adaptation memory')
    episodes = engine.memory.all()
    if episodes:
        st.dataframe(pd.DataFrame([{'Episode':e['id'],'Inferred drift':e['fingerprint']['drift_type'],'Saved feature':', '.join(e['selected_features']),'Paired F1 gain':pp(e['performance_gain']),'Sample':e['step']} for e in episodes]), hide_index=True, use_container_width=True)
    else:
        st.info('Memory fills after a successful repair.')
    st.caption('Measured synthetic results vary with seed and runtime. Gains use percentage points (pp).')
