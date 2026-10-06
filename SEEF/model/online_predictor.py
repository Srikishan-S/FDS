from time import perf_counter
from features.generator import transform

def predict(model, X, feature='identity', params=None):
    start=perf_counter(); Z=transform(X,feature,params)
    probability=model.predict(Z)
    return probability, (perf_counter()-start)*1000/max(1,len(X))
