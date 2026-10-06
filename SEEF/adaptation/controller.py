import numpy as np
ACTIONS=['interaction','nonlinear','temporal','robust','structural','reuse','hybrid']
class ContextualController:
    """SEEF contextual epsilon-greedy linear bandit with ridge sufficient statistics."""
    def __init__(self,seed,epsilon):self.rng=np.random.default_rng(seed+77);self.epsilon=epsilon;self.states={}
    def choose(self,fp,similarity,threshold):
        x=np.r_[1,fp['fingerprint_vector']]
        if not self.states:self.states={a:[np.eye(len(x)),np.zeros(len(x)),0] for a in ACTIONS}
        estimates={a:float(x@np.linalg.solve(A,b)) for a,(A,b,n) in self.states.items()}
        if similarity>=threshold: action='reuse';mode='exploitation'
        elif self.rng.random()<self.epsilon:action=self.rng.choice(ACTIONS[:-2]);mode='exploration'
        else:action=max(estimates,key=estimates.get);mode='contextual exploitation'
        self.last={'action':str(action),'mode':mode,'estimates':estimates,'probability':1-self.epsilon+self.epsilon/len(ACTIONS) if mode!='exploration' else self.epsilon/len(ACTIONS),'reward':None}
        return self.last
    def update(self,fp,action,reward):
        x=np.r_[1,fp['fingerprint_vector']];A,b,n=self.states[action];self.states[action]=[A+np.outer(x,x),b+reward*x,n+1];self.last['reward']=reward
