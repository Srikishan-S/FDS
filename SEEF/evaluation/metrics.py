import numpy as np
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score

def metrics(y,p):
    y=np.asarray(y);p=np.asarray(p);pred=p>=.5
    return {'accuracy':float(accuracy_score(y,pred)), 'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)), 'f1':float(f1_score(y,pred,zero_division=0)), 'auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None, 'confidence':float(np.mean(np.maximum(p,1-p)))}

def recovery_metrics(events,history,window):
    detected=[e for e in events if e['event']=='Drift detected']
    promoted=[e for e in events if e['event']=='Feature promoted']
    return {'adaptations':len(promoted),'mean_adaptation_delay':float(np.mean([e['adaptation_delay'] for e in promoted])) if promoted else None,'reuse_rate':sum(e.get('reused',False) for e in promoted)/max(1,len(promoted)), 'mean_detection_delay':float(np.mean([e['detection_delay'] for e in detected if e.get('detection_delay') is not None])) if any(e.get('detection_delay') is not None for e in detected) else None}
