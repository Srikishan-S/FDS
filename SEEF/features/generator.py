import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
CATALOG = {
 'identity':('hybrid',1,['x1']), 'x1*x2':('interaction',2,['x1','x2']),
 'x1*x3':('interaction',2,['x1','x3']), 'x1/x2':('interaction',3,['x1','x2']),
 'x1-x2':('interaction',1,['x1','x2']), 'x1+x2':('interaction',1,['x1','x2']),
 'x1²':('nonlinear',2,['x1']), 'x1³':('nonlinear',3,['x1']),
 'log|x1|':('nonlinear',2,['x1']), 'sqrt|x1|':('nonlinear',2,['x1']),
 'robust(x1)':('robust',2,['x1']), 'clip(x1)':('robust',1,['x1']),
 'rank(x1)':('robust',3,['x1']), 'zscore(x1)':('robust',2,['x1']),
 'rolling mean':('temporal',3,['x1']), 'rolling std':('temporal',3,['x1']),
 'EWMA':('temporal',2,['x1']), 'lag(x1)':('temporal',1,['x1']),
 'trend(x1)':('temporal',2,['x1']), 'PCA1':('structural',4,['x1','x2','x3']),
 'centroid distance':('structural',5,['x1','x2','x3']),
 'anomaly score':('structural',5,['x1','x2','x3']),
 'density':('structural',5,['x1','x2','x3'])}

def fit_params(X):
    X=np.asarray(X); centers=KMeans(n_clusters=3,n_init=3,random_state=0).fit(X).cluster_centers_
    pca=PCA(n_components=1).fit(X).components_[0]
    return {'median':np.median(X,axis=0).tolist(),'scale':np.maximum(np.percentile(X,75,axis=0)-np.percentile(X,25,axis=0),.1).tolist(),'mean':X.mean(0).tolist(),'std':np.maximum(X.std(0),.1).tolist(),'reference':np.sort(X[:,0]).tolist(),'centers':centers.tolist(),'pca':pca.tolist(),'history':X[-20:,0].tolist()}

def transform(X,name='identity',params=None):
    X=np.asarray(X,dtype=float); Z=X.copy();a,b,c=X.T;p=params or {}
    if name=='identity': return Z
    if name=='x1*x2':v=a*b
    elif name=='x1*x3':v=a*c
    elif name=='x1/x2':v=a/np.where(abs(b)<.2,np.where(b<0,-.2,.2),b)
    elif name=='x1-x2':v=a-b
    elif name=='x1+x2':v=a+b
    elif name=='x1²':v=a*a-1
    elif name=='x1³':v=a**3
    elif name=='log|x1|':v=np.sign(a)*np.log1p(abs(a))
    elif name=='sqrt|x1|':v=np.sign(a)*np.sqrt(abs(a))
    elif name=='robust(x1)':v=(a-p.get('median',[0])[0])/p.get('scale',[1])[0]
    elif name=='zscore(x1)':v=(a-p.get('mean',[0])[0])/p.get('std',[1])[0]
    elif name=='clip(x1)':v=np.clip(a,-2,2)
    elif name=='rank(x1)':v=2*np.searchsorted(p.get('reference',[-2,-1,0,1,2]),a)/max(1,len(p.get('reference',[])))-1
    elif name in ['rolling mean','rolling std','EWMA','lag(x1)','trend(x1)']:
        # Causal: only previous values and the current unlabeled observation.
        hist=list(p.get('history',[]));vals=[];ema=hist[-1] if hist else 0
        for value in a:
            previous=hist[-1] if hist else 0;hist.append(float(value));hist=hist[-20:];ema=.2*value+.8*ema
            vals.append({'rolling mean':np.mean(hist),'rolling std':np.std(hist),'EWMA':ema,'lag(x1)':previous,'trend(x1)':value-hist[0]}[name])
        v=np.array(vals)
    elif name=='PCA1':v=X@np.array(p.get('pca',[1,0,0]))
    elif name in ['centroid distance','anomaly score','density']:
        d=np.linalg.norm(X[:,None,:]-np.array(p.get('centers',[[0,0,0]]))[None,:,:],axis=2).min(1)
        v=d if name=='centroid distance' else d*d if name=='anomaly score' else 1/(1+d)
    else:raise ValueError(name)
    Z[:,0]=np.clip(np.nan_to_num(v),-20,20)
    return Z

def generate(fingerprint,episodes,config):
    shifts=fingerprint['distribution_shift'];corr=fingerprint['correlation_shift']
    groups=['interaction','nonlinear','hybrid']
    if max(shifts.values())>.2: groups=['robust','structural']+groups
    if fingerprint['drift_type'].startswith('gradual'):groups=['temporal']+groups
    names=[]
    for ep,sim in episodes:
        if ep['performance_gain']>0: names.extend(ep['selected_features'])
    ranked=list(CATALOG) if not config.conditioned else sorted([n for n in CATALOG if CATALOG[n][0] in groups],key=lambda n:(groups.index(CATALOG[n][0]) if CATALOG[n][0] in groups else 10, -max([corr.get(k,0) for k in corr],default=0) if CATALOG[n][0]=='interaction' else 0))
    affected=set(fingerprint.get('affected_features',[]))
    if config.conditioned and affected:
        ranked=sorted(ranked,key=lambda n:-len(affected.intersection(CATALOG[n][2])))
    return list(dict.fromkeys(names+ranked))[:config.max_candidates]
