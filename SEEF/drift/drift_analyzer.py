from .fingerprint import fingerprint
from .detectors import MultiSignalDetector
class DriftAnalyzer:
    def __init__(self):self.detector=MultiSignalDetector();self.count=0
    def analyze(self,reference,current):
        fp=fingerprint(reference,current,f'D{self.count+1:03d}');score,signals=self.detector.combine(fp)
        fp['combined_score']=score;fp['signals']=signals
        return fp
