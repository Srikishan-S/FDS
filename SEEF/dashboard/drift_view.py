import pandas as pd
import streamlit as st
import plotly.express as px

def render(engine):
    fp=engine.fingerprint
    if not fp:st.info('Collect two labelled windows to generate a fingerprint.');return
    a,b,c=st.columns(3);a.metric('Combined drift score',f"{fp['combined_score']:.3f}");b.metric('Severity',f"{fp['severity']:.1%}");c.metric('Detected type',fp['drift_type'])
    st.write('Affected variables:',', '.join(fp['affected_features']) or 'None identified')
    st.plotly_chart(px.bar(x=list(fp['signals']),y=list(fp['signals'].values()),title='Multi-signal detector outputs'),use_container_width=True)
    st.plotly_chart(px.line_polar(r=list(fp['distribution_shift'].values())+list(fp['correlation_shift'].values()),theta=list(fp['distribution_shift'])+list(fp['correlation_shift']),line_close=True,title='SEEF drift fingerprint'),use_container_width=True)
    st.plotly_chart(px.imshow([list(fp['distribution_shift'].values())],x=list(fp['distribution_shift']),y=['JS divergence'],zmin=0,zmax=1,title='Distribution-shift heatmap'),use_container_width=True)
    st.json(fp)
