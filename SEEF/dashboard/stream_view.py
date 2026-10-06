import pandas as pd
import streamlit as st
import plotly.express as px

def render(engine):
    m=engine.current_metrics
    cols=st.columns(6)
    for col,key,label in zip(cols,['accuracy','precision','recall','f1','auc','latency_ms'],['Accuracy','Precision','Recall','F1','ROC-AUC','Latency / sample']):
        value=m.get(key);col.metric(label,'—' if value is None else f'{value:.3f} ms' if key=='latency_ms' else f'{value:.1%}')
    if engine.history:
        st.plotly_chart(px.line(pd.DataFrame(engine.history),x='step',y=['SEEF','Static'],title='Measured rolling F1'),use_container_width=True)
    st.dataframe(pd.DataFrame([{'Step':r['step'],'x1':r['x'][0],'x2':r['x'][1],'x3':r['x'][2],'Prediction':int(r['p']>=.5),'Label':r['y'],'Confidence':max(r['p'],1-r['p'])} for r in reversed(engine.recent)]),use_container_width=True,hide_index=True)
