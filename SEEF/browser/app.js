import {SEEF, DEFAULTS} from './engine.js';
import {STAGES, stageState} from './process.js';

const $ = selector => document.querySelector(selector);
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = value => Number(value).toLocaleString();
const percent = value => value == null ? '—' : `${(value * 100).toFixed(1)}%`;
const points = value => value == null ? '—' : `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)} pp`;
const feature = name => name === 'identity' ? 'x1' : name;
const pages = {
  overview: ['Understand every adaptation.', 'A changing stream. Evolving features. One frozen classifier.'],
  process: ['See the evolution happen.', 'Inspect the actual pipeline, or replay a recorded processing checkpoint.'],
  results: ['Evidence, at a glance.', 'Measured performance, deployed repairs, and what SEEF remembers.'],
};
let config = {...DEFAULTS, speed: 160};
let engine = new SEEF(config);
let page = pages[location.hash.slice(1)] ? location.hash.slice(1) : 'overview';
let playing = false, busy = false, timer = null, noticeTimer = null, replayTimer = null;
let replayIndex = null, selectedStage = 'validate';
engine.advance(320);

function badge(text, style = '') { return `<span class="badge ${style}">${escape(text)}</span>`; }
function panel(title, subtitle, body, action = '', cls = '') {
  return `<article class="panel ${cls}"><header class="panel-head"><div><h2>${title}</h2><p>${subtitle}</p></div>${action}</header>${body}</article>`;
}
function table(headers, rows, empty) {
  if (!rows.length) return `<div class="empty"><span class="empty-symbol" aria-hidden="true">◇</span><b>${empty}</b><p>Run the full demo to follow a complete adaptation.</p></div>`;
  return `<div class="table-wrap"><table><thead><tr>${headers.map(h => `<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function stats() {
  const latest = engine.history.at(-1);
  const items = [
    ['Rolling F1', percent(engine.metric.f1), `${config.window} labelled samples`, 'purple'],
    ['Gain vs. baseline', points(latest ? latest.f1 - latest.baseline : null), 'Latest completed window', 'green'],
    ['Drifts detected', number(engine.driftCount), `${engine.summary().adaptations} features promoted`, 'orange'],
    ['Successful memories', number(engine.memory.length), `${engine.events.filter(e => e.event === 'Feature promoted' && e.reused).length} recalled repairs`, 'blue'],
  ];
  return `<div class="metric-grid">${items.map(([label, value, note, color]) => `<article class="metric ${color}"><span class="metric-label">${label}<i aria-hidden="true"></i></span><strong>${value}</strong><small>${note}</small></article>`).join('')}</div>`;
}
function chart(title = 'Performance through change') {
  return panel(title, 'F1 score on consecutive labelled windows', `<div class="chart-wrap"><canvas id="performance-chart" role="img" aria-label="SEEF and static baseline F1 over processed samples"></canvas></div><div class="chart-foot"><span>Sample step</span><span>Drift markers = detected events</span></div>`, `<div class="legend"><span><i class="seef-line"></i>SEEF</span><span><i class="baseline-line"></i>Static baseline</span></div>`);
}
function latestActivity(limit = 5) {
  const events = engine.events.filter(e => !['Fingerprint generated', 'Memory updated'].includes(e.event)).slice(-limit).reverse();
  if (!events.length) return `<div class="activity-empty"><i></i><div><b>Monitoring the initial stream</b><p>First scheduled change at sample ${number(engine.c.driftAt)}.</p></div></div>`;
  return `<ol class="activity">${events.map(e => `<li><span class="event-mark ${e.event === 'Feature promoted' ? 'green' : ''}" aria-hidden="true">${e.event === 'Feature promoted' ? '✓' : e.event === 'Candidates rejected' ? '×' : '•'}</span><div><b>${escape(e.event)}</b><small>${escape(e.feature || e.reason || e.scenario || e.mode || (e.candidates ? `${e.candidates.length} candidates` : e.fingerprint) || 'Recorded engine event')}</small></div><span class="event-step">${number(e.step)}</span></li>`).join('')}</ol>`;
}
function loopMini() {
  const snapshot = engine.processTrace.at(-1);
  return panel('The evolution loop', 'Every step follows the engine', `<div class="mini-loop">${STAGES.map((s, i) => `<div class="mini-stage ${stageState(snapshot, s.id)}"><span>${String(i + 1).padStart(2, '0')}</span><b>${s.short}</b><small>${stageState(snapshot, s.id) === 'complete' ? 'Completed' : stageState(snapshot, s.id) === 'active' ? 'Current stage' : stageState(snapshot, s.id) === 'rejected' ? 'Rejected' : stageState(snapshot, s.id) === 'rollback' ? 'Rolled back' : 'Waiting'}</small></div>`).join('')}</div><button class="open-process" data-page="process">Open process visualizer <span>↗</span></button>`, badge(engine.arena ? 'Testing' : 'Monitoring', engine.arena ? 'amber' : 'neutral'));
}
function representation() {
  return `<div class="representation"><div><span class="eyebrow">ACTIVE REPRESENTATION</span><div class="feature-chips"><span class="feature-chip evolved">${escape(feature(engine.active))}</span><span class="feature-chip">x2</span><span class="feature-chip">x3</span><span class="feature-arrow" aria-hidden="true">→</span><span class="model-chip">Frozen classifier</span></div></div><div class="version"><b>${escape(engine.versions.find(v => v.status === 'active')?.id)}</b><small>Classifier weights unchanged</small></div></div>`;
}
function overview() {
  return `${stats()}<div class="overview-grid">${chart()}${loopMini()}</div>${representation()}<div class="bottom-grid">${panel('Recent activity', 'Decisions recorded by SEEF', latestActivity())}${panel('What is changing?', 'Observed drift evidence', `<div class="evidence"><div><span>Drift score</span><b>${engine.fp ? engine.fp.score.toFixed(3) : '—'}</b></div><div class="score-track"><i style="width:${Math.min(100, (engine.fp?.score || 0) * 100)}%"></i><span style="left:${engine.c.threshold * 100}%" title="Detection threshold"></span></div><p>Threshold ${engine.c.threshold.toFixed(2)} · Two windows required</p><div class="evidence-row"><span>Input scenario</span><b>${escape(engine.lastRegime)}</b></div><div class="evidence-row"><span>Inferred drift</span><b>${escape(engine.fp?.type || 'Collecting evidence')}</b></div><div class="evidence-row"><span>Changed variables</span><b>${escape(engine.fp?.affected.join(', ') || 'None identified')}</b></div></div>`)}</div>`;
}
function checkpoint() {
  return engine.processTrace[replayIndex === null ? engine.processTrace.length - 1 : Math.min(replayIndex, engine.processTrace.length - 1)];
}
function graph(snapshot) {
  const descriptions = {
    stream: `${number(snapshot.step)} samples processed`,
    detect: snapshot.fingerprint ? `${snapshot.fingerprint.id} · ${snapshot.fingerprint.type}` : 'Waiting for confirmed drift',
    recall: snapshot.matches.length ? `${percent(snapshot.matches[0].similarity)} best match` : 'No successful match yet',
    evolve: snapshot.generated ? `${snapshot.generated} ranked transformations` : 'Waiting for drift context',
    validate: snapshot.candidates.length ? `${snapshot.candidates.length} candidates · ${snapshot.windows} windows` : 'No candidates under test',
    deploy: snapshot.outcome === 'promoted' ? `${feature(snapshot.active)} · repair stored` : snapshot.outcome === 'rollback' ? 'Previous version restored' : 'Waiting for a passing feature',
  };
  return `<div class="process-canvas"><svg class="flow-links" viewBox="0 0 900 350" preserveAspectRatio="none" aria-hidden="true"><path d="M150 86H750V263H150"/><path class="flow-return" d="M150 263C25 263 25 86 150 86"/></svg><div class="process-nodes">${STAGES.map((s, i) => `<button id="stage-${s.id}" class="process-node ${stageState(snapshot, s.id)} ${selectedStage === s.id ? 'selected' : ''}" data-stage="${s.id}" aria-pressed="${selectedStage === s.id}" style="--node-order:${[1,2,3,6,5,4][i]}"><span class="node-top"><span class="node-number">${String(i + 1).padStart(2, '0')}</span><span class="node-state">${({complete:'✓ Complete', active:'● Current', pending:'Waiting', rejected:'× Rejected', rollback:'↶ Rolled back'})[stageState(snapshot, s.id)]}</span></span><strong>${s.title}</strong><small>${escape(descriptions[s.id])}</small></button>`).join('')}</div><div class="canvas-caption"><span>SELECT A STAGE TO INSPECT ITS EVIDENCE</span><span>Successful repairs feed the next cycle ↻</span></div></div>`;
}
function stageDetail(snapshot) {
  const stage = STAGES.find(s => s.id === selectedStage);
  const state = stageState(snapshot, selectedStage);
  const f = snapshot.fingerprint;
  let body;
  if (state === 'pending') body = `<p class="detail-text">${stage.note} This stage has not run at the selected checkpoint.</p>`;
  else if (selectedStage === 'stream') body = `<div class="detail-values"><div><small>Samples processed</small><b>${number(snapshot.step)}</b></div><div><small>Checkpoint F1</small><b>${percent(snapshot.metric.f1)}</b></div><div><small>Ground-truth scenario</small><b>${escape(snapshot.regime)}</b></div></div><p class="detail-text">Predictions are recorded before labels are processed. Scenario labels are evaluation context and are never passed into feature selection.</p>`;
  else if (selectedStage === 'detect') body = `<div class="detail-values"><div><small>Fingerprint</small><b>${escape(f?.id || 'Collecting')}</b></div><div><small>Severity</small><b>${percent(f?.severity)}</b></div><div><small>Affected variables</small><b>${escape(f?.affected.join(', ') || 'None identified')}</b></div></div><p class="detail-text">Two consecutive above-threshold windows confirm drift. The fingerprint combines distribution, target relationships, error, confidence, and residual changes.</p>`;
  else if (selectedStage === 'recall') body = snapshot.matches.length ? `<div class="recall-list">${snapshot.matches.map(m => `<div><b>${escape(m.id)} · ${escape(m.selected.join(', '))}</b><span>${percent(m.similarity)} similarity</span>${badge(m.similarity >= engine.c.similarity ? 'Qualified match' : 'Below threshold', m.similarity >= engine.c.similarity ? 'green' : 'neutral')}</div>`).join('')}</div><p class="detail-text">A match needs ${percent(engine.c.similarity)} similarity. Recalled repairs still pass future-window deployment checks.</p>` : `<p class="detail-text">No successful episodes were available. SEEF explores new repairs; the first successful one becomes a memory.</p>`;
  else if (selectedStage === 'evolve') body = `<p class="detail-text">${snapshot.generated} transformations ranked from the past labelled window; ${snapshot.candidates.length} shortlisted for future testing. Only the x1 input slot evolves.</p><div class="candidate-chips">${snapshot.candidates.map(s => `<span class="feature-chip">${escape(feature(s.name))}</span>`).join('')}</div>`;
  else if (selectedStage === 'validate') body = candidateTable(snapshot) + `<p class="detail-text">Required gain: &gt; ${points(engine.c.minGain)}. All checks must pass for ${engine.c.stableWindows} consecutive windows. Unfamiliar repairs require two additional qualification windows.</p>`;
  else body = `<div class="detail-values"><div><small>Active feature</small><b>${escape(feature(snapshot.active))}</b></div><div><small>Version</small><b>${escape(snapshot.version)}</b></div><div><small>Stored repairs</small><b>${snapshot.memoryCount}</b></div></div><p class="detail-text">${snapshot.outcome === 'rollback' ? 'The representation degraded during probation. SEEF restored the previous stable version.' : snapshot.outcome === 'promoted' ? 'A feature passed prospective testing and was promoted. Its repair is stored for future recall. The new version remains under probation for eight windows.' : 'A feature is deployed only after passing the repeated safety checks. Failed candidates keep the existing representation in place.'}</p>`;
  return panel(stage.title, stage.note, `<div class="stage-detail">${body}</div>`, badge(state === 'active' ? 'Current stage' : state, state === 'complete' ? 'green' : 'neutral'));
}
function candidateTable(snapshot) {
  return table(['Candidate', 'Future F1', 'Paired gain', 'Pass streak', 'Checks'], snapshot.candidates.map(s => {
    const checks = Object.entries(s.checks);
    return [`<span class="mono">${escape(feature(s.name))}</span>`, percent(s.f1), `<span class="${s.gain > 0 ? 'positive' : ''}">${points(s.gain)}</span>`, `${s.streak} / ${engine.c.stableWindows}`, checks.length ? `<details class="gate-details" data-candidate="${escape(s.name)}"><summary class="check-count">${checks.filter(([,v]) => v).length} / ${checks.length} passed</summary><div>${checks.map(([k,v]) => `<span class="${v ? 'gate-pass' : 'gate-fail'}">${v ? '✓' : '×'} ${escape(k)}</span>`).join('')}</div></details>` : 'Waiting for a future window'];
  }), 'No candidates at this checkpoint');
}
function process() {
  const snapshot = checkpoint();
  const position = replayIndex === null ? engine.processTrace.length - 1 : replayIndex;
  return `<article class="panel visualizer"><header class="panel-head"><div><h2>Live process visualizer</h2><p>${escape(snapshot.event)} · Sample ${number(snapshot.step)} · Cycle ${snapshot.cycle}</p></div>${badge(replayIndex === null ? 'Live engine state' : 'Recorded checkpoint', replayIndex === null ? 'green' : 'purple')}</header>${graph(snapshot)}<div class="replay-bar"><div><button id="replay-prev" class="button secondary compact" aria-label="Previous checkpoint" ${position <= 0 ? 'disabled' : ''}>←</button><button id="replay-toggle" class="button secondary compact" ${engine.processTrace.length < 2 ? 'disabled' : ''}>${replayTimer ? 'Pause replay' : 'Replay'}</button><button id="replay-next" class="button secondary compact" aria-label="Next checkpoint" ${position >= engine.processTrace.length - 1 ? 'disabled' : ''}>→</button></div><label for="replay-range" class="sr-only">Recorded processing checkpoint</label><input id="replay-range" type="range" min="0" max="${engine.processTrace.length - 1}" value="${position}"><span class="checkpoint-count">${position + 1} / ${engine.processTrace.length}</span><button id="follow-live" class="button ${replayIndex === null ? 'primary' : 'secondary'} compact">Follow live</button></div></article>${stageDetail(snapshot)}<div class="visualizer-note">The graph and replay show recorded engine states. Candidate rejection and rollback appear when they actually occur. Replay does not rerun the model.</div>`;
}
function results() {
  const summary = engine.summary();
  const promotions = engine.events.filter(e => e.event === 'Feature promoted');
  return `${stats()}${chart('SEEF against its static baseline')}<div class="result-summary"><div><span>Mean window F1</span><b>${percent(summary.meanF1)}</b></div><div><span>Mean baseline gain</span><b>${points(summary.adaptationGain)}</b></div><div><span>Mean adaptation delay</span><b>${summary.adaptationDelay == null ? '—' : `${number(summary.adaptationDelay)} samples`}</b></div><button id="export-run" class="button primary">↓ Export run</button></div>${panel('Deployed feature repairs', 'Each repair passed repeated future-window checks', table(['Sample', 'Feature', 'Mean paired F1 gain', 'Delay (samples)', 'Memory reuse', 'Version'], promotions.map(e => [number(e.step), `<span class="mono">${escape(feature(e.feature))}</span>`, `<span class="positive">${points(e.gain)}</span>`, number(e.adaptationDelay), badge(e.reused ? 'Recalled' : 'New repair', e.reused ? 'purple' : 'neutral'), escape(e.version)]), 'No feature has been promoted yet'))}${panel('Episodic adaptation memory', 'Successful repairs available to later drift cycles', table(['Episode', 'Inferred drift', 'Saved feature', 'Paired F1 gain', 'Sample'], engine.memory.map(e => [escape(e.id), escape(e.fingerprint.type), `<span class="mono">${escape(e.selected.map(feature).join(', '))}</span>`, points(e.gain), number(e.step)]), 'Memory fills after a successful repair'))}<p class="results-note">F1 is measured from actual predictions. Gains use percentage points (pp). Synthetic results vary with seed and runtime; successful adaptation is not guaranteed.</p>`;
}
function drawChart() {
  const canvas = $('#performance-chart');
  if (!canvas) return;
  const box = canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  if (!box.width || !box.height) return;
  canvas.width = box.width * dpr; canvas.height = box.height * dpr;
  const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
  const left = 42, top = 22, w = box.width - 58, h = box.height - 56;
  const max = Math.max(1600, engine.step);
  ctx.font = '11px system-ui'; ctx.lineWidth = 1;
  for (let v = 0; v <= 1.001; v += .25) {
    const y = top + (1 - v) * h;
    ctx.strokeStyle = '#ebedf5'; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(left + w, y); ctx.stroke();
    ctx.fillStyle = '#7d8495'; ctx.textAlign = 'right'; ctx.fillText(`${Math.round(v * 100)}%`, left - 10, y + 4);
  }
  for (let i = 0; i <= 4; i++) {
    ctx.textAlign = i === 0 ? 'left' : i === 4 ? 'right' : 'center'; ctx.fillStyle = '#7d8495';
    ctx.fillText(number(Math.round(max * i / 4)), left + w * i / 4, top + h + 23);
  }
  for (const event of engine.events.filter(e => e.event === 'Drift detected')) {
    const x = left + event.step / max * w;
    ctx.strokeStyle = '#e6bd86'; ctx.setLineDash([3, 5]); ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, top + h); ctx.stroke(); ctx.setLineDash([]);
  }
  const plot = (key, color, dashed = false, fill = false) => {
    const data = engine.history;
    if (!data.length) return;
    ctx.beginPath(); data.forEach((r, i) => {const x = left + r.step / max * w, y = top + (1 - Math.max(0, Math.min(1, r[key]))) * h; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);});
    if (fill) {
      ctx.lineTo(left + data.at(-1).step / max * w, top + h); ctx.lineTo(left + data[0].step / max * w, top + h); ctx.closePath();
      const gradient = ctx.createLinearGradient(0, top, 0, top + h); gradient.addColorStop(0, '#7962ec25'); gradient.addColorStop(1, '#7962ec00'); ctx.fillStyle = gradient; ctx.fill();
      ctx.beginPath(); data.forEach((r, i) => {const x = left + r.step / max * w, y = top + (1 - r[key]) * h; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);});
    }
    ctx.strokeStyle = color; ctx.lineWidth = dashed ? 1.7 : 2.5; ctx.lineJoin = 'round'; if (dashed) ctx.setLineDash([5, 5]); ctx.stroke(); ctx.setLineDash([]);
    if (!dashed) {const r = data.at(-1);ctx.beginPath();ctx.arc(left + r.step / max * w, top + (1 - r[key]) * h, 3.5, 0, Math.PI * 2);ctx.fillStyle = color;ctx.fill();}
  };
  plot('baseline', '#a7acbc', true); plot('f1', '#7057e5', false, true);
}
function render() {
  const focused = document.activeElement?.id;
  const expanded = new Set([...document.querySelectorAll('.gate-details[open]')].map(el => el.dataset.candidate));
  if (replayIndex !== null) replayIndex = Math.min(replayIndex, engine.processTrace.length - 1);
  $('#page-title').textContent = pages[page][0]; $('#page-desc').textContent = pages[page][1];
  $('#run-status').textContent = busy ? 'Computing' : playing ? 'Streaming' : engine.step <= 320 ? 'Ready' : 'Paused';
  $('#status-dot').classList.toggle('live', playing || busy); $('#sample-status').textContent = `${number(engine.step)} samples`;
  $('#play').innerHTML = playing ? '<span aria-hidden="true">Ⅱ</span> Pause stream' : '<span aria-hidden="true">▶</span> Start stream';
  for (const id of ['play', 'tick', 'reset', 'demo', 'scenario', 'seed']) $(`#${id}`).disabled = busy;
  document.querySelectorAll('nav [data-page]').forEach(b => {b.classList.toggle('active', b.dataset.page === page);b.setAttribute('aria-current', b.dataset.page === page ? 'page' : 'false');});
  $('#view').innerHTML = ({overview, process, results})[page]();
  document.querySelectorAll('[data-page]').forEach(b => b.onclick = () => navigate(b.dataset.page));
  document.querySelectorAll('[data-stage]').forEach(b => b.onclick = () => {selectedStage = b.dataset.stage; render();});
  if ($('#export-run')) $('#export-run').onclick = exportRun;
  if ($('#replay-range')) {
    $('#replay-range').onchange = e => {stopReplay();replayIndex = Number(e.target.value);render();};
    $('#replay-prev').onclick = () => {stopReplay();replayIndex = Math.max(0, (replayIndex ?? engine.processTrace.length - 1) - 1);render();};
    $('#replay-next').onclick = () => {stopReplay();replayIndex = Math.min(engine.processTrace.length - 1, (replayIndex ?? engine.processTrace.length - 1) + 1);render();};
    $('#follow-live').onclick = () => {stopReplay();replayIndex = null;render();};
    $('#replay-toggle').onclick = () => {
      if (replayTimer) {stopReplay();render();return;}
      if (replayIndex === null || replayIndex >= engine.processTrace.length - 1) replayIndex = 0;
      replayTimer = setInterval(() => {if (replayIndex >= engine.processTrace.length - 1) stopReplay();else replayIndex++;render();}, 650);render();
    };
  }
  document.querySelectorAll('.gate-details').forEach(el => {el.open = expanded.has(el.dataset.candidate);});
  if (focused && $(`#${focused}`)) $(`#${focused}`).focus({preventScroll: true});
  drawChart();
}
function navigate(next) {page = next;location.hash = next;render();}
function notify(message) {clearTimeout(noticeTimer);$('#notice').hidden = false;$('#notice').textContent = message;noticeTimer = setTimeout(() => {$('#notice').hidden = true;}, 6000);}
function stopReplay() {clearInterval(replayTimer);replayTimer = null;}
function stop() {clearInterval(timer);timer = null;playing = false;}
function readSetup() {
  const seed = Number($('#seed').value);
  if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295 || $('#seed').value === '') {notify('Enter a whole-number seed from 0 to 4,294,967,295.');$('#seed').focus();return false;}
  config = {...config, seed, scenario: $('#scenario').value};return true;
}
function resetEngine() {stop();stopReplay();replayIndex = null;engine = new SEEF(config);engine.advance(320);render();}
async function fullDemo() {
  if (!readSetup()) return;
  config.scenario = 'demo'; $('#scenario').value = 'demo'; resetEngine(); busy = true;
  $('#progress-wrap').hidden = false; render();
  try {
    while (engine.step < 14000) {
      engine.advance(Math.min(160, 14000 - engine.step));
      const progress = Math.round(engine.step / 14000 * 100);
      $('#progress-bar').value = progress; $('#progress-percent').textContent = `${progress}%`;
      $('#progress-label').textContent = `Running SEEF · ${number(engine.step)} / 14,000 samples`;
      render(); await new Promise(resolve => setTimeout(resolve, 0));
    }
    notify('Demo complete. Open Process to replay the recorded evolution, or Results to inspect the repairs.');
  } catch (error) {console.error(error);notify(`The demo stopped: ${error.message}`);}
  finally {busy = false;$('#progress-wrap').hidden = true;render();}
}
function exportRun() {
  const blob = new Blob([JSON.stringify(engine.export(), null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = 'SEEF_run.json'; link.click();setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('#play').onclick = () => {
  if (playing) stop();
  else {playing = true;timer = setInterval(() => {try {engine.advance(config.speed);render();} catch (error) {stop();notify(`The stream stopped: ${error.message}`);render();}}, 850);}
  render();
};
$('#tick').onclick = () => {engine.advance(config.speed);render();};
$('#demo').onclick = fullDemo;
$('#reset').onclick = () => {if (readSetup()) {resetEngine();notify(`New run ready with seed ${config.seed}.`);}};
$('#scenario').onchange = () => {if (readSetup()) resetEngine();};
$('#seed').onchange = () => {notify('Seed changes apply on Reset or Run full demo.');};
$('#method-open').onclick = () => $('#method-dialog').showModal();
$('#method-close').onclick = () => $('#method-dialog').close();
window.addEventListener('resize', drawChart);
window.addEventListener('hashchange', () => {const next = location.hash.slice(1);if (pages[next]) {page = next;render();}});
window.addEventListener('pagehide', () => {stop();stopReplay();});
render();
