import pandas as pd
import plotly.express as px
import streamlit as st
from evaluation.experiments import run_experiments

def render(engine):
    st.write('A: static · B: retraining · C: SEEF without EAM · D: SEEF with EAM · E: unconditioned generation')
    steps=st.number_input('Experiment steps',min_value=1600,max_value=40000,value=14000,step=1600)
    if st.button('Run all five ablations'):
        with st.spinner('Running identical seeded streams with independent adaptation states…'):
            st.session_state['experiments']=run_experiments(engine.c,int(steps),(engine.c.seed,))
    if 'experiments' in st.session_state:
        h,s=st.session_state['experiments'];st.plotly_chart(px.line(h,x='step',y='f1',color='approach'),use_container_width=True);st.dataframe(s,hide_index=True)
        means=s.set_index('approach')['mean_f1'];st.metric('Measured EAM benefit (mean F1)',f"{means['D SEEF with EAM']-means['C SEEF without EAM']:+.2%}")
        st.download_button('Download measured comparison CSV',h.to_csv(index=False),'SEEF_comparison.csv','text/csv')
    st.json(engine.summary())
