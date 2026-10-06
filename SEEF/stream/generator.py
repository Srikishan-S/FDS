import numpy as np
from .drift_injector import DriftInjector
class StreamGenerator:
    def __init__(self, config):
        self.config=config; self.rng=np.random.default_rng(config.seed)
        self.injector=DriftInjector(config); self.step=0
    def next(self):
        x,y,regime=self.injector.apply(self.rng.normal(size=3),self.step,self.rng)
        result={'step':self.step,'x':x,'y':y,'regime':regime}
        self.step+=1
        return result
