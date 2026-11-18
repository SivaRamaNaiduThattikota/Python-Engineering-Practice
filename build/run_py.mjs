// Runs every snippet of a lesson in the same Pyodide the site uses.
// usage: node run_py.mjs jobs.json results.json
import fs from 'node:fs';
import { loadPyodide } from 'pyodide';
import { HELPER } from '../assets/py-helper.js';

const [, , jobsPath, outPath] = process.argv;
const jobs = JSON.parse(fs.readFileSync(jobsPath, 'utf8'));
const py = await loadPyodide();
py.runPython(HELPER);
const version = py.runPython('import sys; sys.version.split()[0]');
const results = {};

for (const j of jobs) {
  const lines = [];
  py.setStdout({ batched: s => lines.push(s) });
  py.setStderr({ batched: s => lines.push(s) });
  const src = (j.code || j.setup || '') + '\n' + (j.tests || '');
  await py.loadPackagesFromImports(src, { messageCallback: () => {} });
  if (src.includes('lessontools')) await py.loadPackage('pytest', { messageCallback: () => {} });
  if (j.kind === 'time') {
    const r = py.globals.get('_time')(j.setup, py.toPy(j.stmts), j.number || 0);
    results[j.id] = { times: r.toJs() };
    r.destroy();
    continue;
  }
  const r = py.globals.get('_run')(j.code, j.tests || '');
  const o = r.toJs({ dict_converter: Object.fromEntries });
  r.destroy();
  results[j.id] = { stdout: lines.join('\n'), error: o.error ?? null, tests: o.tests || [] };
}
fs.writeFileSync(outPath, JSON.stringify({ version, results }));
