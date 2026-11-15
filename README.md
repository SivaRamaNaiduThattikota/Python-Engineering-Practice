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

## Running locally

    python -m http.server

then open http://localhost:8000. Code runs in a web worker, so it needs http, not file://.
