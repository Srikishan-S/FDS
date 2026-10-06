import numpy as np
from sklearn.linear_model import LogisticRegression
class FrozenModel:
    def __init__(self, seed):
        rng=np.random.default_rng(seed+1000)
        X=rng.normal(size=(2500,3)); y=(1.8*X[:,0]+.65*X[:,2]+rng.normal(0,.18,2500)>0).astype(int)
        fitted=LogisticRegression(C=2,max_iter=300).fit(X,y)
        self.weights=fitted.coef_[0].copy();self.bias=float(fitted.intercept_[0]); self.initial_weights=self.weights.copy()
    def predict(self, Z):
        z=np.clip(np.asarray(Z)@self.weights+self.bias,-35,35)
        return 1/(1+np.exp(-z))
