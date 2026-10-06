import numpy as np
from river.drift import ADWIN,PageHinkley
from river.drift.binary import DDM
class MultiSignalDetector:
    def __init__(self):
        self.adwin=ADWIN(delta=.01);self.ph=PageHinkley(min_instances=60,threshold=15);self.ddm=DDM(warm_start=60)
        self.flags={'ADWIN':False,'Page-Hinkley':False,'DDM':False}
    def update(self,error):
        for label,detector in [('ADWIN',self.adwin),('Page-Hinkley',self.ph),('DDM',self.ddm)]:
            detector.update(int(error));self.flags[label] |= bool(detector.drift_detected)
    def combine(self,fingerprint):
        f=fingerprint
        error=min(1,max(0,f['prediction_error_delta'])*3)
        distribution=min(1,np.mean(list(f['distribution_shift'].values()))*3)
        correlation=min(1,np.mean(list(f['correlation_shift'].values()))*2)
        confidence=min(1,abs(f['confidence_delta'])*3)
        residual=min(1,f['residual_shift']*2)
        detector_vote=sum(self.flags.values())/3
        signals={'error':error,'distribution':distribution,'correlation':correlation,'confidence':confidence,'residual':residual,'detector_vote':detector_vote,**{k:float(v) for k,v in self.flags.items()}}
        score=.32*error+.18*distribution+.20*correlation+.10*confidence+.08*residual+.12*detector_vote
        self.flags={k:False for k in self.flags}
        return float(score),signals
