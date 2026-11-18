# Python Engineering Practice

A problems-first Python workbook. Each lesson has a short recap, then graded problems
(predict the output, fix the bug, write the function, refactor, trace, pick the faster one)
that run and check themselves in the browser with Pyodide.

The full theory is in [python-core-foundations](https://github.com/SivaRamaNaiduThattikota/python-core-foundations).

## Building a lesson

Lessons are written as Python files in `src/` and turned into pages by the build:

    cd build && npm install && cd ..
    python build/build.py m1_1

The build runs every snippet in the same Pyodide the site uses, so every output on a page
is real. It stops if a solution fails its tests, a starter already passes, or the "faster"
option is not actually faster.

The build needs a few package wheels next to the local Pyodide:

    python build/fetch_wheels.py numpy pandas pydantic pytest packaging

## How some modules are graded

`assets/py-helper.js` is shared by the build and the browser, so both grade the same way.

- Module 13 (testing): learners write test files. `lessontools.run_pytest` runs real pytest on
  them, and `swap_impl` replaces the code under test (between `# --- code under test` and
  `# --- tests`) with buggy versions that the tests must catch.
- Module 14 (concurrency): the browser cannot start threads or processes, so executors and
  `Thread.start` run tasks inline (the process pool still checks picklability), and
  `asyncio.run` uses an event loop on simulated time, so timings are exact.
- Module 15 (imports): `lessontools.make_tree` writes small packages to disk and puts them on
  `sys.path`; `forget` clears them from the import cache.

## Running locally

    python -m http.server

then open http://localhost:8000. Code runs in a web worker, so it needs http, not file://.

## Theory pages

`theory/` holds the full theory notes, converted from the notebooks in
[python-core-foundations](https://github.com/SivaRamaNaiduThattikota/python-core-foundations):

    python build/theory.py "../Python Core Foundations"

Re-run it after editing a notebook. The outputs shown are the ones saved in the notebooks.
