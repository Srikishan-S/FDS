import numpy as np
class DriftInjector:
    """SEEF regimes. The hidden regime is never passed to detection or generation."""
    def __init__(self, config):
        self.c = config
        self.manual = None
    def regime(self, step):
        if self.manual is not None:
            return self.manual, 1.0
        a, length = self.c.drift_at, self.c.stage_length
        if step < a: return 'stable', 0.0
        if self.c.scenario == 'demo':
            phase = (step-a)//length
            return (['interaction','nonlinear','interaction','stable'][phase % 4], 1.0)
        if self.c.scenario == 'gradual':
            return 'interaction', min(1., (step-a)/length)
        return {'sudden':'interaction','concept':'nonlinear','recurring':'interaction' if ((step-a)//length)%2==0 else 'stable','covariate':'covariate'}.get(self.c.scenario,'interaction'), 1.0
    def apply(self, x, step, rng):
        regime, mix = self.regime(step)
        if regime == 'covariate':
            x = x * np.array([2.0,.65,1.4]) + np.array([.9,-.4,.3])
        signal = x[0]
        if regime == 'interaction': signal = (1-mix)*x[0]+mix*x[0]*x[1]
        if regime == 'nonlinear': signal = x[0]**2 - 1.0
        logit = 1.8*signal + .65*x[2] + rng.normal(0,.18)
        return x, int(logit > 0), regime
