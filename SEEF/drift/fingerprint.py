import numpy as np
from scipy.spatial.distance import jensenshannon

def correlations(X,y):
    vals=[]
    for v in [X[:,0],X[:,1],X[:,2],X[:,0]*X[:,1],X[:,0]**2]:
        vals.append(float(np.nan_to_num(np.corrcoef(v,y)[0,1])))
    return np.array(vals)

def fingerprint(reference,current,fp_id):
    A,ya,pa=reference;B,yb,pb=current
    shifts={}
    for i in range(3):
        bins=np.r_[-np.inf,np.linspace(-4,4,15),np.inf]
        ha=np.histogram(A[:,i],bins)[0]+.1;hb=np.histogram(B[:,i],bins)[0]+.1
        shifts['x'+str(i+1)]=float(jensenshannon(ha/ha.sum(),hb/hb.sum())**2)
    ca,cb=correlations(A,ya),correlations(B,yb);d=abs(cb-ca)
    err=float(np.mean((pb>=.5)!=yb)-np.mean((pa>=.5)!=ya))
    conf=float(np.mean(np.maximum(pa,1-pa))-np.mean(np.maximum(pb,1-pb)))
    residual=float(abs(np.mean(yb-pb)-np.mean(ya-pa)))
    severity=float(np.clip(max(max(shifts.values())*3,d.max(),err*2),0,1))
    kind='covariate_drift' if max(shifts.values())>.20 and d.mean()<.25 else 'concept_drift'
    half=max(1,len(yb)//2); e1=np.mean((pb[:half]>=.5)!=yb[:half]);e2=np.mean((pb[half:]>=.5)!=yb[half:])
    if e2-e1>.12:kind='gradual_'+kind
    # Fixed coordinate scales, then L2 normalization; absolute relationship signature
    # helps recurring-regime matching even when the departure regime differs.
    vector=np.r_[severity*.3,np.array(list(shifts.values()))*.5,d*.3,err*.3,conf*.3,residual*.3,cb*3,B.mean(0)*.2,B.std(0)*.2]
    vector=vector/max(np.linalg.norm(vector),1e-12)
    return {'id':fp_id,'drift_type':kind,'severity':severity,'affected_features':['x'+str(i+1) for i in range(3) if d[i]>.2 or shifts['x'+str(i+1)]>.1], 'distribution_shift':shifts,'correlation_shift':dict(zip(['x1_y','x2_y','x3_y','x1_x2_y','x1_squared_y'],map(float,d))), 'prediction_error_delta':err,'confidence_delta':conf,'residual_shift':residual,'window_statistics':{'mean':B.mean(0).tolist(),'std':B.std(0).tolist(),'target_correlations':cb.tolist(),'samples':len(B)},'fingerprint_vector':vector.tolist()}
