import numpy as np

def cosine(a,b):
    a,b=np.asarray(a),np.asarray(b)
    return float(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-12))
