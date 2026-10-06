import numpy as np
from config import Config
from stream.generator import StreamGenerator
from stream.stream_manager import SEEF
from drift.fingerprint import fingerprint
from memory.episodic_memory import EpisodicMemory
from features.generator import generate,transform
from adaptation.deployment import gate
from adaptation.rollback import VersionRegistry

def test_reproducible_stream():
    a,b=StreamGenerator(Config()),StreamGenerator(Config())
    for _ in range(20):
        x,y=a.next(),b.next();assert np.array_equal(x['x'],y['x']);assert x['y']==y['y']

def test_finite_transforms():
    X=np.array([[0,0,0],[-2,1,3],[1,-.0001,0.]])
    for n in generate({'distribution_shift':{'x1':0},'correlation_shift':{},'drift_type':'concept'},[],Config()):assert np.isfinite(transform(X,n)).all()

def test_fingerprint_normalized_and_memory():
    rng=np.random.default_rng(5);X=rng.normal(size=(100,3));y=(X[:,0]>0).astype(int);p=np.ones(100)*.5
    f=fingerprint((X,y,p),(X+1,y,p),'D1');assert np.isclose(np.linalg.norm(f['fingerprint_vector']),1)
    m=EpisodicMemory();m.add({'fingerprint_vector':f['fingerprint_vector'],'performance_gain':.1,'selected_features':['x1*x2']});assert m.query(f['fingerprint_vector'])[0][1]>.999

def test_gate_rejects_gain_and_latency():
    c=Config();assert not gate(.71,.70,1,4,1,1,1,c)[0];assert not gate(.9,.7,100,4,1,1,1,c)[0];assert gate(.9,.7,1,4,1,1,1,c)[0]

def test_frozen_weights_and_future_shadow():
    e=SEEF(Config(drift_at=320,stage_length=2000,window=80,stable_windows=3));initial=e.model.weights.copy();e.advance(2000)
    assert np.array_equal(e.model.weights,initial)
    for event in e.events:
        if event['event']=='Feature promoted':assert event['adaptation_delay']>=e.c.stable_windows*e.c.window
    assert len(e.history)==25

def test_delayed_labels():
    e=SEEF(Config(label_delay=200));e.advance(320);assert len(e.pending)==200;assert len(e.window)==120;assert len(e.history)==0

def test_rollback_registry():
    r=VersionRegistry();r.deploy('x1*x2',{},100,.9);v=r.rollback();assert v['id']=='SEEF_v1';assert r.versions[-1]['status']=='rolled back'

def test_ablation_changes_generator():
    fp={'distribution_shift':{'x1':0},'correlation_shift':{},'drift_type':'concept'}
    assert len(generate(fp,[],Config()))<len(generate(fp,[],Config(conditioned=False)))


def test_recurrence_recall_reduces_delay_without_model_refit():
    e=SEEF();e.advance(11000)
    events=[x for x in e.events if x['event']=='Feature promoted']
    recalled=[x for x in events if x['reused']]
    assert recalled and recalled[0]['adaptation_delay']<events[0]['adaptation_delay']
    assert np.array_equal(e.model.weights,e.model.initial_weights)

def test_autonomous_rollback_on_degradation():
    e=SEEF(Config(drift_at=320,window=80,stage_length=10000,stable_windows=3))
    for _ in range(30):
        e.advance(80)
        if any(x['event']=='Feature promoted' for x in e.events):break
    assert any(x['event']=='Feature promoted' for x in e.events)
    e.inject('stable');e.advance(240)
    assert any(x['event']=='Autonomous rollback' for x in e.events)
