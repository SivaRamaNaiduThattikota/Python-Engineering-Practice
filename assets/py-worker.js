// Runs Python (Pyodide) off the main thread so a long loop never freezes the page.
// The page can always stop a run by terminating this worker and starting a new one.
// Loaded as a module worker: the classic importScripts route fails for this Pyodide build.
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';
import { HELPER } from './py-helper.js';



let py;
const ready = (async () => {
  py = await loadPyodide({ indexURL: PYODIDE });
  py.runPython(HELPER);
  postMessage({ type: 'ready', version: py.runPython('import sys; sys.version.split()[0]') });
})().catch(e => postMessage({ type: 'boot-error', error: String(e) }));

onmessage = async e => {
  await ready;
  const { id, code, tests } = e.data;
  try {
    // numpy, pandas and friends are fetched the first time a snippet imports them
    await py.loadPackagesFromImports(code + '\n' + (tests || ''), { messageCallback: () => {} });
    if ((code + (tests || '')).includes('lessontools')) await py.loadPackage('pytest', { messageCallback: () => {} });
    py.setStdout({ batched: s => postMessage({ id, type: 'out', text: s }) });
    py.setStderr({ batched: s => postMessage({ id, type: 'err', text: s }) });
    const res = py.globals.get('_run')(code, tests || '');
    const out = res.toJs({ dict_converter: Object.fromEntries });
    res.destroy();
    postMessage({ id, type: 'done', error: out.error, tests: out.tests });
  } catch (err) {
    postMessage({ id, type: 'done', error: String(err.message || err), tests: [] });
  }
};
