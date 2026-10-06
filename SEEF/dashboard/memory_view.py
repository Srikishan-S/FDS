import pandas as pd
import streamlit as st

def render(engine):
    st.caption('EAM stores only adaptations that passed the safe deployment gate. Similarity is calculated, not assigned from a regime label.')
    episodes=engine.memory.all();similarities={e['id']:s for e,s in engine.matches}
    st.dataframe(pd.DataFrame([{'Episode':e['id'],'Drift':e['fingerprint']['drift_type'],'Similarity':similarities.get(e['id']),'Feature repair':', '.join(e['selected_features']),'F1 gain':e['performance_gain'],'Reward':e['reward'],'Reused':e['reused']} for e in episodes]),use_container_width=True,hide_index=True)
    st.download_button('Export EAM JSON',__import__('json').dumps(episodes,indent=2),'SEEF_memory.json','application/json')
