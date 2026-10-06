import numpy as np
from sklearn.feature_selection import mutual_info_classif
from .generator import CATALOG,transform

def rank(names,X,y,fingerprint,episodes,params):
    scores=[]
    for name in names:
        v=transform(X,name,params)[:,0]
        mi=float(mutual_info_classif(v.reshape(-1,1),y,random_state=0)[0])
        historical=max([ep['performance_gain']*sim for ep,sim in episodes if name in ep['selected_features']]+[0])
        group,cost,_=CATALOG[name]
        relevance=1+fingerprint['severity']*(1 if group in ['interaction','nonlinear'] else .5)
        redundancy=abs(float(np.corrcoef(v,X[:,2])[0,1])) if np.std(v)>1e-8 else 1
        utility=relevance*(mi+.03)*(1+3*historical)/(1+.12*cost+.3*redundancy)
        scores.append({'feature':name,'utility':utility,'information_gain':mi,'complexity':cost,'historical_success':historical,'status':'pre-ranked'})
    return sorted(scores,key=lambda s:-s['utility'])
