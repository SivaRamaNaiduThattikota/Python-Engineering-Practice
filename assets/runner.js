// Code editor, Python runner and problem cards. Loaded after app.js on every page.
(function () {
  const root = document.body.dataset.root || '';
  const PKEY = 'pyp-progress';
  const RUN_LIMIT = 10000;   // ms before a run is stopped (infinite loop guard)
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // ---------- motion: springs for growing, popping, wobbling ----------
  const calm = matchMedia('(prefers-reduced-motion: reduce)');
  const BOUNCE = 'linear(0,.04,.143,.285,.445,.606,.756,.886,.991,1.069,1.122,1.152,1.163,1.158,1.143,1.12,1.095,1.068,1.043,1.022,1.004,.99,.981,.976,.974,.974,.976,.98,.984,.988,.992,.996,.999,1.001,1.003,1.004,1.004,1.003,1.002,1.001,1)';
  const SETTLE = 'linear(0,.048,.166,.32,.483,.637,.772,.882,.965,1.023,1.06,1.078,1.084,1.079,1.07,1.057,1.043,1.03,1.019,1.01,1.003,.998,.995,.993,.993,.993,.994,.995,.996,.997,.998,.999,1)';
  // run a DOM change, then let the box spring from its old height to the new one
  function morph(el, change) {
    if (calm.matches) { change(); return; }
    const h0 = el.hidden ? 0 : el.getBoundingClientRect().height;
    el.getAnimations().forEach(a => a.cancel());
    change();
    const h1 = el.getBoundingClientRect().height;
    if (Math.abs(h1 - h0) < 2) return;
    el.animate({ height: [h0 + 'px', h1 + 'px'] }, { duration: h1 > h0 ? 760 : 520, easing: h1 > h0 ? BOUNCE : SETTLE });
  }
  const pop = (el, k = 1) => { if (el && !calm.matches) el.animate([{ scale: String(1 - .3 * k), opacity: 0 }, { opacity: 1, offset: .3 }, { scale: '1', opacity: 1 }], { duration: 640, easing: BOUNCE }); };
  const shake = el => { if (el && !calm.matches) el.animate([{ translate: '0' }, { translate: '-8px' }, { translate: '7px' }, { translate: '-4px' }, { translate: '2px' }, { translate: '0' }], { duration: 440, easing: 'ease-out' }); };
  const jelly = el => { if (el && !calm.matches) el.animate([{ scale: '1' }, { scale: '1.02 .98' }, { scale: '.992 1.008' }, { scale: '1' }], { duration: 680, easing: SETTLE }); };
  function stagger(els) {
    if (calm.matches) return;
    els.forEach((r, i) => r.animate([{ opacity: 0, translate: '0 8px', scale: '.98' }, { opacity: 1, translate: '0 0', scale: '1' }],
      { duration: 520, delay: Math.min(i, 12) * 45, easing: SETTLE, fill: 'backwards' }));
  }

  // ---------- progress: { pid: { s: 'solved' | 'tried', c: last code, peek: true } } ----------
  const store = {
    all() { try { return JSON.parse(localStorage.getItem(PKEY) || '{}'); } catch (_) { return {}; } },
    get(pid) { return this.all()[pid] || {}; },
    set(pid, patch) {
      const a = this.all(); a[pid] = Object.assign(a[pid] || {}, patch);
      localStorage.setItem(PKEY, JSON.stringify(a));
      dispatchEvent(new Event('pyp-progress'));
    },
  };
  window.PYP = { store };

  // ---------- Python in a worker ----------
  const py = {
    worker: null, ready: false, version: '', seq: 0, jobs: {}, waiters: [],
    start() {
      if (this.worker) return;
      this.ready = false;
      this.worker = new Worker(root + 'assets/py-worker.js', { type: 'module' });
      this.worker.onerror = e => { e.preventDefault(); this.fail('Python could not load. Check your connection and reload the page.'); };
      this.worker.onmessage = e => {
        const m = e.data;
        if (m.type === 'ready') { this.ready = true; this.version = m.version; this.waiters.splice(0).forEach(f => f()); return; }
        if (m.type === 'boot-error') { this.fail('Python could not load: ' + m.error); return; }
        const job = this.jobs[m.id];
        if (!job) return;
        if (m.type === 'out' || m.type === 'err') job.chunk(m.type, m.text);
        else job.finish(m);
      };
    },
    fail(msg) {
      this.failed = msg;
      Object.values(this.jobs).forEach(j => j.finish({ error: msg, tests: [] }));
      if (this.worker) this.worker.terminate();
      this.worker = null; this.ready = false;
    },
    whenReady() { this.start(); return this.ready ? Promise.resolve() : new Promise(r => this.waiters.push(r)); },
    stop() {   // the only reliable way to stop running Python: throw the worker away
      if (!this.worker) return;
      this.worker.terminate(); this.worker = null; this.ready = false;
      Object.values(this.jobs).forEach(j => j.finish({ stopped: true, tests: [] }));
    },
    run(code, tests, onChunk) {
      this.start();
      const id = ++this.seq;
      return new Promise(resolve => {
        let timer;
        const job = this.jobs[id] = {
          chunk: onChunk,
          finish: m => { clearTimeout(timer); delete this.jobs[id]; resolve(m); },
        };
        this.whenReady().then(() => {
          if (!this.jobs[id]) return;
          timer = setTimeout(() => { this.stop(); resolve({ timeout: true, tests: [] }); }, RUN_LIMIT);
          this.worker.postMessage({ id, code, tests });
        });
      });
    },
  };

  // ---------- syntax colouring (same token classes as the lesson code blocks) ----------
  const KW = new Set('False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield match case'.split(' '));
  const BI = new Set('print len range enumerate zip map filter sorted reversed sum min max abs round int float str bool list dict set tuple frozenset type isinstance id hash iter next open repr any all super object property staticmethod classmethod getattr setattr hasattr divmod pow chr ord'.split(' '));
  const TOK = /(#[^\n]*)|([rRbBfFuU]{0,2}(?:"""[\s\S]*?(?:"""|$)|'''[\s\S]*?(?:'''|$)|"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?))|(\b\d[\d_]*(?:\.\d*)?(?:[eE][+-]?\d+)?j?\b)|([A-Za-z_]\w*)/g;
  function colour(src) {
    let out = '', last = 0, prev = '', m;
    TOK.lastIndex = 0;
    while ((m = TOK.exec(src))) {
      out += esc(src.slice(last, m.index));
      const t = esc(m[0]);
      if (m[1]) out += `<span class="tk-c">${t}</span>`;
      else if (m[2]) out += `<span class="tk-s">${t}</span>`;
      else if (m[3]) out += `<span class="tk-n">${t}</span>`;
      else if (KW.has(m[0])) out += `<span class="tk-k">${t}</span>`;
      else if (prev === 'def' || prev === 'class' || BI.has(m[0])) out += `<span class="tk-f">${t}</span>`;
      else out += t;
      if (m[4]) prev = m[0];
      last = TOK.lastIndex;
    }
    return out + esc(src.slice(last));
  }
  window.PYP.colour = colour;

  // ---------- editor: a textarea over a coloured <pre> ----------
  function editor(ta, onRun) {
    const box = document.createElement('div');
    box.className = 'ed';
    const pre = document.createElement('pre');
    pre.setAttribute('aria-hidden', 'true');
    ta.replaceWith(box); box.append(pre, ta);
    ta.spellcheck = false; ta.autocapitalize = 'off'; ta.setAttribute('autocorrect', 'off');
    const paint = () => { pre.innerHTML = colour(ta.value) + '\n '; };
    const insert = text => { ta.focus(); if (!document.execCommand('insertText', false, text)) ta.setRangeText(text, ta.selectionStart, ta.selectionEnd, 'end'); paint(); };
    ta.addEventListener('input', paint);
    ta.addEventListener('keydown', e => {
      const v = ta.value, s = ta.selectionStart, en = ta.selectionEnd;
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); onRun(); return; }
      if (e.key === 'Escape') { ta.blur(); return; }
      if (e.key === 'Tab') {
        e.preventDefault();
        const ls = v.lastIndexOf('\n', s - 1) + 1;
        if (s === en && !e.shiftKey) { insert('    '); return; }
        // indent or dedent every selected line
        const le = en > s && v[en - 1] === '\n' ? en - 1 : en;
        const block = v.slice(ls, le);
        const next = e.shiftKey ? block.replace(/^ {1,4}/gm, '') : block.replace(/^/gm, '    ');
        ta.setSelectionRange(ls, le); insert(next);
        ta.setSelectionRange(ls, ls + next.length);
        return;
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const line = v.slice(v.lastIndexOf('\n', s - 1) + 1, s);
        let ind = line.match(/^ */)[0];
        if (/:\s*(#.*)?$/.test(line)) ind += '    ';
        else if (/^\s*(return|pass|break|continue|raise)\b/.test(line)) ind = ind.slice(4);
        insert('\n' + ind);
        return;
      }
      if (e.key === 'Backspace' && s === en && s > 0) {
        const before = v.slice(v.lastIndexOf('\n', s - 1) + 1, s);
        if (before.length && /^ +$/.test(before) && before.length % 4 === 0) {
          e.preventDefault(); ta.setSelectionRange(s - 4, s); insert('');
        }
      }
    });
    paint();
    return { get: () => ta.value, set: v => { ta.value = v; paint(); }, el: box };
  }

  // ---------- output panel ----------
  function renderResult(out, res, stdout) {
    const parts = [];
    if (stdout.length) parts.push(`<pre class="o-std">${stdout.map(([k, t]) => k === 'err' ? `<span class="o-err">${esc(t)}</span>` : esc(t)).join('\n')}</pre>`);
    if (res.timeout) parts.push(`<pre class="o-err">Stopped after ${RUN_LIMIT / 1000} s. Is there a loop that never ends?</pre>`);
    else if (res.stopped) parts.push('<pre class="o-err">Stopped.</pre>');
    else if (res.error) parts.push(`<pre class="o-err">${esc(res.error)}</pre>`);
    const tests = res.tests || [];
    if (tests.length) {
      const ok = tests.filter(t => t[1]).length;
      parts.push(`<div class="o-tests"><div class="o-sum ${ok === tests.length ? 'all' : ''}">${ok === tests.length ? '✓ All tests passed' : `${ok} of ${tests.length} tests passed`}</div>` +
        tests.map(([src, pass, why]) => `<div class="o-t ${pass ? 'pass' : 'fail'}"><span class="o-i">${pass ? '✓' : '✗'}</span><code>${esc(src)}</code>${why ? `<small>${esc(why)}</small>` : ''}</div>`).join('') + '</div>');
    }
    if (!parts.length) parts.push('<pre class="o-std o-dim">(no output)</pre>');
    out.innerHTML = parts.join('');
  }

  async function runInto(out, btn, code, tests) {
    const stdout = [];
    morph(out, () => { out.hidden = false; out.innerHTML = `<pre class="o-std o-dim">${py.ready ? 'Running…' : 'Starting Python… (about 6 s the first time, then cached)'}</pre>`; });
    btn.classList.add('busy'); btn.dataset.label = btn.dataset.label || btn.textContent; btn.textContent = 'Stop';
    btn.onclick = () => py.stop();
    let first = true;
    const res = await py.run(code, tests, (k, t) => {
      if (first) { out.innerHTML = ''; first = false; }
      stdout.push([k, t]);
      out.innerHTML = `<pre class="o-std">${stdout.map(([kk, tt]) => kk === 'err' ? `<span class="o-err">${esc(tt)}</span>` : esc(tt)).join('\n')}</pre>`;
    });
    btn.classList.remove('busy'); btn.textContent = btn.dataset.label; btn.onclick = null;
    morph(out, () => renderResult(out, res, stdout));
    stagger([...out.querySelectorAll('.o-sum, .o-t')]);
    return res;
  }

  // ---------- problem cards ----------
  const TYPES = { write: 'Write the code', fix: 'Find and fix the bug', refactor: 'Refactor', predict: 'Predict the output',
    trace: 'Trace the variables', choose: 'Pick the faster approach', explain: 'Explain' };
  // a str repr like 'abc' may also be typed with double quotes
  const dq = a => /^'[^'"\\]*'$/.test(a) ? '"' + a.slice(1, -1) + '"' : a;
  const norm = s => s.replace(/\r/g, '').split('\n').map(l => l.trimEnd()).join('\n').trim();

  function setStatus(card, st) {
    card.classList.toggle('solved', st.s === 'solved');
    const pill = card.querySelector('.pstat');
    if (pill) pill.textContent = st.s === 'solved' ? (st.peek ? '✓ Solved, used solution' : '✓ Solved') : st.s === 'tried' ? 'Tried' : '';
  }
  function solved(card, ok) {
    const pid = card.dataset.pid, st = store.get(pid);
    if (ok) store.set(pid, { s: 'solved' });
    else if (st.s !== 'solved') store.set(pid, { s: 'tried' });
    setStatus(card, store.get(pid));
    if (ok) { jelly(card); pop(card.querySelector('.pstat')); }
  }

  function initCard(card) {
    const pid = card.dataset.pid, type = card.dataset.type;
    const head = card.querySelector('.prob-head');
    if (head && !head.querySelector('.ptype')) head.insertAdjacentHTML('afterbegin',
      `<span class="lvl ${card.dataset.level}">${card.dataset.level}</span><span class="ptype">${TYPES[type] || type}</span><span class="pstat"></span>`);
    setStatus(card, store.get(pid));

    // opening the solution before solving is recorded, so the score stays honest
    card.querySelectorAll('details.sol').forEach(d => d.addEventListener('toggle', () => {
      if (d.open && store.get(pid).s !== 'solved') store.set(pid, { peek: true });
      if (d.open && type === 'explain' && !card.querySelector('.self-mark')) {
        d.querySelector('.ans').insertAdjacentHTML('beforeend', '<button class="btn self-mark" type="button">I got this right</button>');
        d.querySelector('.self-mark').onclick = () => solved(card, true);
      }
    }));

    const ta = card.querySelector('textarea.prob-code');
    if (ta) {
      const starter = ta.value;
      const tests = card.querySelector('.prob-tests')?.textContent || '';
      const saved = store.get(pid).c;
      const bar = document.createElement('div');
      bar.className = 'code-bar';
      bar.innerHTML = `<span class="lights"><i></i><i></i><i></i></span><span class="lbl">main.py</span>
        <button class="copy reset" type="button" title="Back to the starting code">Reset</button><button class="copy" type="button">Copy</button>
        <button class="run" type="button" title="Run (Ctrl + Enter)">${tests.trim() ? 'Run tests' : 'Run'}</button>`;
      const wrap = document.createElement('div'); wrap.className = 'code prob-ed';
      ta.before(wrap); wrap.append(bar, ta);
      const ed = editor(ta, () => runBtn.click());
      if (saved != null) ed.set(saved);
      const out = document.createElement('div'); out.className = 'prob-out'; out.hidden = true; wrap.after(out);
      const runBtn = bar.querySelector('.run');
      let saveT;
      ta.addEventListener('input', () => { clearTimeout(saveT); saveT = setTimeout(() => store.set(pid, { c: ed.get() }), 400); });
      ta.addEventListener('focus', () => py.start(), { once: true });
      bar.querySelector('.reset').onclick = () => { if (ed.get() === starter || confirm('Replace your code with the starting code?')) { ed.set(starter); store.set(pid, { c: starter }); } };
      bar.querySelector('.copy:not(.reset)').onclick = e => copy(ed.get(), e.target);
      runBtn.addEventListener('click', async () => {
        if (runBtn.classList.contains('busy')) return;
        store.set(pid, { c: ed.get() });
        const res = await runInto(out, runBtn, ed.get(), tests);
        if (!tests.trim() || res.timeout || res.stopped) return;
        const t = res.tests || [];
        solved(card, !res.error && t.length > 0 && t.every(x => x[1]));
      });
    }

    // predict the output: type what Python prints
    const ans = card.querySelector('textarea.prob-answer, input.prob-answer');
    if (ans && type !== 'trace') {
      const btn = card.querySelector('.check');
      const fb = card.querySelector('.check-fb');
      btn.onclick = () => {
        const ok = norm(ans.value) === norm(card.dataset.answer);
        fb.textContent = ok ? '✓ Correct' : 'Not quite. Run it in your head line by line, or open the hint.';
        fb.className = 'check-fb ' + (ok ? 'ok' : 'no');
        pop(fb, .5); if (!ok) shake(ans);
        solved(card, ok);
      };
    }
    // trace: one box per variable per step
    if (type === 'trace') {
      card.querySelector('.check').onclick = () => {
        let all = true;
        card.querySelectorAll('input.cell').forEach(i => {
          const v = norm(i.value), ok = v === norm(i.dataset.a) || v === dq(norm(i.dataset.a)) || v === norm(i.dataset.s || i.dataset.a);
          i.classList.toggle('ok', ok); i.classList.toggle('no', !ok); all = all && ok;
          ok ? pop(i, .25) : shake(i);
        });
        const fb = card.querySelector('.check-fb');
        fb.textContent = all ? '✓ Every cell is right' : 'Red cells are wrong. Fix them and check again.';
        fb.className = 'check-fb ' + (all ? 'ok' : 'no'); pop(fb, .5);
        solved(card, all);
      };
    }
    // choose: pick an option
    if (type === 'choose') {
      card.querySelectorAll('.opt').forEach(o => o.addEventListener('click', () => {
        card.querySelectorAll('.opt').forEach(x => x.classList.remove('picked', 'ok', 'no'));
        const ok = o.dataset.key === card.dataset.answer;
        o.classList.add('picked', ok ? 'ok' : 'no');
        ok ? jelly(o) : shake(o);
        const fb = card.querySelector('.check-fb');
        fb.textContent = ok ? '✓ Right. Now open the solution and check your reason matches.' : 'Not this one. Think about how many steps each version takes.';
        fb.className = 'check-fb ' + (ok ? 'ok' : 'no'); pop(fb, .5);
        solved(card, ok);
      }));
    }
  }

  async function copy(text, b) {
    try { await navigator.clipboard.writeText(text); } catch (_) {
      const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove();
    }
    b.textContent = 'Copied'; b.classList.add('ok');
    setTimeout(() => { b.textContent = 'Copy'; b.classList.remove('ok'); }, 1400);
  }

  // ---------- free playground ----------
  document.querySelectorAll('.play').forEach(p => {
    const ta = p.querySelector('textarea');
    const KEY = 'pyp-playground';
    const saved = localStorage.getItem(KEY);
    const bar = p.querySelector('.code-bar');
    const ed = editor(ta, () => runBtn.click());
    if (saved) ed.set(saved);
    const out = document.createElement('div'); out.className = 'prob-out'; out.hidden = true; p.after(out);
    const runBtn = bar.querySelector('.run');
    ta.addEventListener('input', () => localStorage.setItem(KEY, ed.get()));
    bar.querySelector('.copy').onclick = e => copy(ed.get(), e.target);
    runBtn.addEventListener('click', () => { if (!runBtn.classList.contains('busy')) runInto(out, runBtn, ed.get(), ''); });
    py.start();
  });

  // static code blocks written by the build
  document.querySelectorAll('pre code.py').forEach(c => { c.innerHTML = colour(c.textContent); });

  const cards = [...document.querySelectorAll('.prob[data-pid]')];
  cards.forEach(initCard);

  // ---------- lesson score + auto "done" ----------
  function score() {
    const el = document.getElementById('lesson-score');
    if (!el || !cards.length) return;
    const n = cards.filter(c => store.get(c.dataset.pid).s === 'solved').length;
    el.textContent = `${n} / ${cards.length} solved`;
    const t = document.getElementById('done-toggle');
    if (t && n === cards.length && !t.checked) { t.checked = true; t.dispatchEvent(new Event('change')); }
  }
  score();
  addEventListener('pyp-progress', score);

  // start Python early on pages with code to run, once the page has settled
  if (cards.some(c => c.querySelector('textarea.prob-code'))) {
    const warm = () => py.start();
    'requestIdleCallback' in window ? requestIdleCallback(warm, { timeout: 2500 }) : setTimeout(warm, 1500);
  }

  // ---------- export / import progress ----------
  const foot = document.getElementById('st-progress');
  if (foot) {
    foot.insertAdjacentHTML('beforeend', `<div class="io-row"><button class="copy" type="button" id="exp">Export progress</button>
      <label class="copy" tabindex="0">Import<input type="file" accept="application/json" id="imp" hidden></label></div>`);
    document.getElementById('exp').onclick = () => {
      const data = {};
      Object.keys(localStorage).filter(k => k.startsWith('pyp-')).forEach(k => data[k] = localStorage.getItem(k));
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }));
      a.download = 'python-practice-progress.json'; a.click();
    };
    document.getElementById('imp').onchange = async e => {
      const f = e.target.files[0]; if (!f) return;
      try {
        const data = JSON.parse(await f.text());
        Object.entries(data).forEach(([k, v]) => { if (k.startsWith('pyp-')) localStorage.setItem(k, v); });
        location.reload();
      } catch (_) { alert('That file is not a progress export.'); }
    };
  }
})();
