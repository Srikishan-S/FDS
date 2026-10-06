import numpy as np
from evaluation.metrics import metrics
from model.online_predictor import predict
from .deployment import gate
class ShadowArena:
    def __init__(self,ranked,params,model,config,fp,matches,controller,step):
        self.ranked=ranked;self.params=params;self.model=model;self.c=config;self.fp=fp;self.matches=matches;self.controller=controller;self.start=step;self.windows=0
        self.candidates={r['feature']:{'scores':[],'gains':[],'latencies':[],'streak':0,'status':'Testing','checks':{}} for r in ranked[:config.shortlist]}
    def predictions(self,X,history=None):
        params=dict(self.params,history=history or self.params.get('history',[]))
        return {name:predict(self.model,X,name,params) for name in self.candidates}
    def evaluate(self,rows,current_f1,detector_confidence):
        self.windows+=1;winner=None;best=-1
        y=[r['y'] for r in rows]
        for name,state in self.candidates.items():
            p=[r['shadow'].get(name,(.5,0))[0] for r in rows];lat=float(np.mean([r['shadow'].get(name,(.5,0))[1] for r in rows]))
            f1=metrics(y,p)['f1'];gain=f1-current_f1
            state['scores'].append(f1);state['gains'].append(gain);state['latencies'].append(lat)
            stability=float(max(0,1-np.std(state['scores'])))
            consistency=sum(g>self.c.min_improvement for g in state['gains'])/len(state['gains'])
            sim=max([s for e,s in self.matches if name in e['selected_features']]+[0])
            confidence=float(np.clip(.2*sim+.35*min(1,max(0,gain)*4)+.25*stability+.1*min(1,detector_confidence*2)+.1*consistency,0,1))
            mem=float(sum(np.asarray(v).nbytes for v in self.params.values())/1e6)
            passed,checks=gate(f1,current_f1,lat,4,stability,mem,confidence,self.c)
            state.update(f1=f1,gain=gain,latency=lat,stability=stability,confidence=confidence,checks=checks,memory_mb=mem)
            state['streak']=state['streak']+1 if passed else 0
            required_total=self.c.stable_windows+(0 if sim>=self.c.similarity_threshold else 2)
            if state['streak']>=self.c.stable_windows and self.windows>=required_total and gain>best:winner=name;best=gain
        return winner
