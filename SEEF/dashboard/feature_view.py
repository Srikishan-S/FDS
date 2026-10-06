import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import streamlit as st

def render(engine):
    st.subheader('Active feature space');st.code(f"frozen classifier inputs: [{engine.active}, x2, x3]")
    st.caption('A bounded representation adapter replaces the x1 input slot. Classifier weights stay fixed; candidates do not retrain the classifier.')
    st.subheader('Shadow Adaptation Arena')
    rows=[]
    for r in engine.ranked:
        state=engine.arena.candidates.get(r['feature'],{}) if engine.arena else {}
        rows.append({**r,**{k:v for k,v in state.items() if k not in ['scores','gains','latencies','checks']}})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    if engine.arena:
        for n,s in engine.arena.candidates.items():
            if s['checks']:st.write(n,s['checks'])
    st.subheader('Feature genealogy')
    G=engine.genealogy.graph();pos=nx.spring_layout(G,seed=42);edges_x=[];edges_y=[]
    for a,b in G.edges:edges_x += [pos[a][0],pos[b][0],None];edges_y += [pos[a][1],pos[b][1],None]
    fig=go.Figure(go.Scatter(x=edges_x,y=edges_y,mode='lines',line=dict(color='#718096'),hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=[pos[n][0] for n in G],y=[pos[n][1] for n in G],mode='markers+text',text=list(G),textposition='top center',customdata=[str(G.nodes[n]) for n in G],hovertemplate='%{customdata}<extra></extra>',marker=dict(size=14,color=['#18b9a6' if n==engine.active else '#6289d7' for n in G])))
    fig.update_layout(showlegend=False,height=500,xaxis=dict(visible=False),yaxis=dict(visible=False));st.plotly_chart(fig,use_container_width=True)
    st.dataframe(pd.DataFrame(engine.genealogy.nodes.values()),use_container_width=True,hide_index=True)
    st.subheader('Feature-version registry');st.dataframe(pd.DataFrame([{k:v for k,v in r.items() if k!='params'} for r in engine.registry.versions]),hide_index=True)
