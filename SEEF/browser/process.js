// SEEF — Self-Evolving Feature Engineering Framework.
// Process snapshots contain observed engine state, never scheduled outcomes.
export const STAGES = [
  {id: 'stream', title: 'Monitor stream', short: 'Monitor', note: 'Predict before observing labels.'},
  {id: 'detect', title: 'Detect & fingerprint', short: 'Detect', note: 'Confirm drift using two labelled windows.'},
  {id: 'recall', title: 'Recall a repair', short: 'Recall', note: 'Match fingerprints to successful episodes.'},
  {id: 'evolve', title: 'Evolve features', short: 'Evolve', note: 'Rank transformations using past data.'},
  {id: 'validate', title: 'Validate candidates', short: 'Validate', note: 'Test on future windows before deployment.'},
  {id: 'deploy', title: 'Deploy & remember', short: 'Deploy', note: 'Save a passing repair and monitor its version.'},
];
export function captureProcess(engine, event, details = {}) {
  if (event === 'Drift detected') {
    engine.processCycle++;
    engine.cycleFingerprint = structuredClone(engine.fp);
  }
  const stage = {
    'Drift injected': engine.arena ? engine.processStage : 'stream', 'Drift detected': 'detect', 'Fingerprint generated': 'detect',
    'Memory queried': 'recall', 'Candidate features generated': 'evolve',
    'Shadow testing': 'validate', 'Feature promoted': 'deploy', 'Memory updated': 'deploy',
    'Memory disabled': 'deploy', 'Candidates rejected': 'validate', 'Autonomous rollback': 'deploy',
  }[event];
  if (stage) engine.processStage = stage;
  if (event === 'Window evaluated' && engine.arena) engine.processStage = 'validate';
  const candidates = engine.arena ? Object.entries(engine.arena.candidates).map(([name, s]) => ({name, ...s})) : engine.lastArena;
  const stageIndex = STAGES.findIndex(s => s.id === engine.processStage);
  const snapshot = {
    id: engine.traceSequence++, step: engine.step, cycle: engine.processCycle,
    stage: engine.processStage, event, details: structuredClone(details),
    active: engine.active, version: engine.versions.find(v => v.status === 'active')?.id,
    memoryCount: engine.memory.length, windows: engine.arena?.windows ?? Math.max(0, ...candidates.map(s => s.scores?.length ?? 0)),
    metric: {...engine.metric}, score: engine.fp?.score ?? null,
    fingerprint: stageIndex >= 1 ? structuredClone(engine.arena?.fp ?? engine.cycleFingerprint ?? null) : null,
    matches: (stageIndex >= 2 ? engine.matches : []).map(m => ({id: m.episode.id, similarity: m.similarity, selected: [...m.episode.selected]})),
    candidates: (stageIndex >= 3 ? candidates : []).map(s => ({name: s.name, f1: s.f1 ?? null, gain: s.gain ?? null,
      streak: s.streak, status: event === 'Feature promoted' || event === 'Memory updated' ? (s.name === engine.active ? 'Selected' : 'Rejected') : s.status,
      checks: {...s.checks}, latency: s.latency ?? null})),
    generated: stageIndex >= 3 ? engine.ranked.length : 0, testing: Boolean(engine.arena), outcome: engine.processOutcome,
    regime: engine.lastRegime,
  };
  engine.processTrace.push(snapshot);
  if (engine.processTrace.length > 600) engine.processTrace.shift();
  return snapshot;
}
export function stageState(snapshot, id) {
  const index = STAGES.findIndex(s => s.id === id);
  const current = STAGES.findIndex(s => s.id === snapshot.stage);
  if (snapshot.outcome === 'rejected' && id === 'validate') return 'rejected';
  if (snapshot.outcome === 'rollback' && id === 'deploy') return 'rollback';
  if (snapshot.outcome === 'promoted' && current === 5) return 'complete';
  if (index < current) return 'complete';
  return index === current ? 'active' : 'pending';
}
