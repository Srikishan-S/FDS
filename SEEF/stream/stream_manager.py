from collections import deque
import numpy as np
from sklearn.linear_model import LogisticRegression
from config import Config
from stream.generator import StreamGenerator
from model.baseline_model import FrozenModel
from model.online_predictor import predict
from drift.drift_analyzer import DriftAnalyzer
from memory.episodic_memory import EpisodicMemory
from memory.adaptation_episode import episode
from features.generator import generate,fit_params,CATALOG
from features.ranking import rank
from features.genealogy import Genealogy
from features.pruning import prune
from adaptation.controller import ContextualController
from adaptation.shadow_arena import ShadowArena
from adaptation.rollback import VersionRegistry
from adaptation.reward import reward
from evaluation.metrics import metrics,recovery_metrics

class SEEF:
    def __init__(self,config=None):
        self.c=config or Config();self.stream=StreamGenerator(self.c);self.model=FrozenModel(self.c.seed);self.static_model=FrozenModel(self.c.seed)
        self.analyzer=DriftAnalyzer();self.memory=EpisodicMemory(self.c.memory_path);self.controller=ContextualController(self.c.seed,self.c.epsilon);self.registry=VersionRegistry();self.genealogy=Genealogy()
        self.active='identity';self.params=None;self.arena=None;self.reference=None;self.pending=deque();self.window=[];self.recent=deque(maxlen=20);self.rolling=deque(maxlen=self.c.window);self.history=[];self.events=[];self.fingerprint=None;self.ranked=[];self.cooldown=0;self.bad_windows=0;self.last_injection=None;self.last_regime='stable';self.current_metrics={};self.matches=[];self.pre_drift=None;self.deploy_score=None;self.prune_counter=0;self.drift_streak=0;self.raw_history=[]
    def log(self,event,**kwargs):self.events.append({'step':self.stream.step,'event':event,**kwargs})
    def inject(self,kind):
        self.stream.injector.manual={'sudden':'interaction','concept':'nonlinear','recurring':'interaction','covariate':'covariate','stable':'stable'}[kind];self.last_injection=self.stream.step;self.log('Drift injected',scenario=kind)
    def advance(self,count=None):
        for _ in range(count or self.c.speed):
            sample=self.stream.next();X=sample['x'].reshape(1,-1)
            if sample['regime']!=self.last_regime:
                self.last_injection=sample['step'];self.last_regime=sample['regime'];self.log('Drift injected',scenario=sample['regime'])
            # All predictions are recorded before the label enters the learner.
            active_params=dict(self.params or {},history=self.raw_history);p,lat=predict(self.model,X,self.active,active_params);base,_=predict(self.static_model,X)
            shadow=self.arena.predictions(X,self.raw_history) if self.arena else {}
            self.raw_history=(self.raw_history+[float(X[0,0])])[-20:]
            row={**sample,'p':float(p[0]),'base':float(base[0]),'latency':lat,'shadow':{n:(float(v[0][0]),v[1]) for n,v in shadow.items()}}
            self.pending.append(row)
            if len(self.pending)>self.c.label_delay:
                r=self.pending.popleft();self.window.append(r);self.recent.append(r);self.rolling.append(r);self.analyzer.detector.update((r['p']>=.5)!=r['y'])
                if len(self.window)>=self.c.window:self.finish_window()
        if self.rolling:
            self.current_metrics={**metrics([r['y'] for r in self.rolling],[r['p'] for r in self.rolling]),'latency_ms':float(np.mean([r['latency'] for r in self.rolling]))}
        return self.current_metrics
    def finish_window(self):
        rows=self.window;self.window=[];X=np.array([r['x'] for r in rows]);y=np.array([r['y'] for r in rows]);p=np.array([r['p'] for r in rows]);b=np.array([r['base'] for r in rows]);m=metrics(y,p);bm=metrics(y,b)
        self.current_metrics={**m,'latency_ms':float(np.mean([r['latency'] for r in rows]))};self.history.append({'step':rows[-1]['step'],'SEEF':m['f1'],'Static':bm['f1'],'accuracy':m['accuracy'],'latency_ms':self.current_metrics['latency_ms'],'feature':self.active,'drift_score':0.})
        if self.reference is None:self.reference=(X,y,p);self.pre_drift=m['f1'];return
        fp=self.analyzer.analyze(self.reference,(X,y,p));self.fingerprint=fp;self.history[-1]['drift_score']=fp['combined_score']
        if self.cooldown:self.cooldown-=1
        self.drift_streak=self.drift_streak+1 if fp['combined_score']>=self.c.drift_threshold else 0
        # Roll back only within the probation period; an accepted stable feature
        # is subsequently repaired normally when a new regime arrives.
        active_version=next(v for v in reversed(self.registry.versions) if v['status']=='active')
        if self.deploy_score is not None and self.stream.step-active_version['step']<=self.c.window*8:
            bad=m['f1']<self.deploy_score-.15 or self.current_metrics['latency_ms']>self.c.latency_limit_ms
            self.bad_windows=self.bad_windows+1 if bad else 0
            if self.bad_windows>=2:
                prior=self.registry.rollback();self.active=prior['feature'];self.params=prior['params'];self.log('Autonomous rollback',version=prior['id']);self.deploy_score=None;self.arena=None;self.bad_windows=0;self.cooldown=1
        if self.arena:
            # Ignore a partial transition window; every prediction must belong
            # to the same arena, including when labels are delayed.
            names=set(self.arena.candidates)
            if all(names.issubset(r['shadow']) for r in rows):
                winner=self.arena.evaluate(rows,m['f1'],fp['combined_score'])
                if winner:self.promote(winner,X,y,p)
                elif self.arena.windows>=max(12,self.c.stable_windows*3):
                    for n,s in self.arena.candidates.items():s['status']='Rejected'
                    best=max(self.arena.candidates,key=lambda n:np.mean(self.arena.candidates[n]['gains']))
                    state=self.arena.candidates[best];rwd=reward(float(np.mean(state['gains'])),state['latency']/max(self.c.latency_limit_ms,1e-9),CATALOG[best][1]/10,1-state['stability'],self.c)
                    self.controller.update(self.arena.fp,self.arena.controller['action'],rwd)
                    self.log('Candidates rejected',reason='No candidate passed all consecutive-window gates',best=best);self.arena=None;self.cooldown=3
        elif self.drift_streak>=2 and not self.cooldown and not self.c.static:
            self.analyzer.count+=1;fp['id']=f'D{self.analyzer.count:03d}'
            delay=self.stream.step-1-self.last_injection if self.last_injection is not None else None
            self.log('Drift detected',fingerprint=fp['id'],detection_delay=delay,score=fp['combined_score']);self.log('Fingerprint generated',fingerprint=fp['id'])
            if self.c.retrain:
                fitted=LogisticRegression(C=2,max_iter=300).fit(X,y);self.model.weights=fitted.coef_[0].copy();self.model.bias=float(fitted.intercept_[0]);self.log('Baseline model retrained');self.reference=(X,y,p);self.cooldown=3
            else:
                self.matches=self.memory.query(fp['fingerprint_vector']) if self.c.use_memory else []
                sim=self.matches[0][1] if self.matches else 0;control=self.controller.choose(fp,sim,self.c.similarity_threshold)
                self.log('Memory queried',similarity=sim,mode=control['mode'])
                names=generate(fp,self.matches,self.c);params=fit_params(X);self.ranked=rank(names,X,y,fp,self.matches,params)
                # Contextual action adjusts evaluation priority, never bypasses evidence.
                for r in self.ranked:
                    if CATALOG[r['feature']][0]==control['action']:r['utility']*=1.2
                    if control['action']=='reuse' and any(r['feature'] in e['selected_features'] and s>=self.c.similarity_threshold for e,s in self.matches):r['utility']+=1
                self.ranked.sort(key=lambda r:-r['utility'])
                for n in names:self.genealogy.register(n,fp)
                self.arena=ShadowArena(self.ranked,params,self.model,self.c,fp,self.matches,control,self.stream.step);self.log('Candidate features generated',count=len(names));self.log('Shadow testing',candidates=list(self.arena.candidates))
        elif not self.arena and fp['combined_score']<self.c.drift_threshold*.5:
            self.reference=(X,y,p)
        prune(self.genealogy,self.active)
    def promote(self,name,X,y,p):
        a=self.arena;s=a.candidates[name];old=self.active
        self.active=name;self.params=a.params;v=self.registry.deploy(name,a.params,self.stream.step,s['f1']);self.deploy_score=s['f1'];self.bad_windows=0
        reused=any(name in e['selected_features'] and sim>=self.c.similarity_threshold for e,sim in a.matches)
        gain=float(np.mean(s['gains']));before=float(np.mean([score-g for score,g in zip(s['scores'],s['gains'])]));after=float(np.mean(s['scores']))
        rwd=reward(gain,s['latency']/max(self.c.latency_limit_ms,1e-9),CATALOG[name][1]/10,1-s['stability'],self.c);self.controller.update(a.fp,a.controller['action'],rwd)
        ep=episode(a.fp,list(a.candidates),name,a.controller['action'],before,after,s['latency'],CATALOG[name][1],s['stability'],rwd,self.stream.step,reused)
        if self.c.use_memory:self.memory.add(ep)
        node=self.genealogy.nodes[name];node.update(deployment_status='Active',performance_gain=gain,stability=s['stability'],age=0);node['reuse_frequency']+=int(reused)
        if old in self.genealogy.nodes and old!=name:self.genealogy.nodes[old]['deployment_status']='Dormant'
        sim=max([ss for e,ss in a.matches if name in e['selected_features']]+[0])
        explanation=f"SEEF detected {a.fp['drift_type']} (severity {a.fp['severity']:.1%}). Memory similarity for {name}: {sim:.1%}. Future-window F1 gain: {gain:+.1%}; measured latency {s['latency']:.4f} ms/sample; confidence {s['confidence']:.1%}. {name} passed {self.c.stable_windows} consecutive windows and was promoted as {v['id']}."
        self.log('Feature promoted',feature=name,version=v['id'],gain=gain,reused=reused,confidence=s['confidence'],adaptation_delay=self.stream.step-a.start,recovery_ratio=after/max(self.pre_drift or 1,1e-9),feature_efficiency=gain,explanation=explanation)
        self.log('Memory updated' if self.c.use_memory else 'Memory disabled');self.reference=(X,y,p);self.arena=None;self.cooldown=3
    def summary(self):
        summary=recovery_metrics(self.events,self.history,self.c.window)
        promoted=[e for e in self.events if e['event']=='Feature promoted']
        summary.update(mean_f1=float(np.mean([h['SEEF'] for h in self.history])) if self.history else None,adaptation_gain=float(np.mean([h['SEEF']-h['Static'] for h in self.history])) if self.history else None,recovery_ratio=float(np.mean([e['recovery_ratio'] for e in promoted])) if promoted else None,feature_efficiency=float(np.mean([e['feature_efficiency'] for e in promoted])) if promoted else None)
        return summary
