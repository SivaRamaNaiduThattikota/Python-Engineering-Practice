from lesson import *

lesson(
    id="m15-p", num="15.P", title="Module 15 practice set and mini project",
    intro="Mixed problems from all of Module 15: how imports and `python -m` work, versions and requirements, and command-line "
          "tools. Then a mini project that needs all of it: an evaluation command-line tool with subcommands, a scorer plugin loaded "
          "by name, an environment check against a requirements list, configuration from the environment and flags, and clean "
          "streams and exit codes.",
    desc="Mixed problems from the whole module, then one small program that uses all of it.",
    keys="practice mixed review project cli subcommands plugin import_module runpy python -m __main__ version bump requirements diff entry points environment check exit codes stdin stdout stderr",
)

section("how", "How to use this page",
    p("""When a tool misbehaves, ask three questions in order. **Which code is running?** Check `sys.path`, `module.__file__`, `__name__` and import-time side effects (15.1).
    **Which versions are installed, and which were declared?** Parse versions and requirements with `packaging`, never as strings, and compare the environment with the
    lock (15.2). **How is it invoked?** Through `main(argv) -> int`, with results on standard output, diagnostics on standard error and meaningful exit codes (15.3)."""),
    p("""The problems mix the lessons on purpose, and the mini project combines all three in a tool you could ship with an LLM project."""),
)

section("set", "Practice set",
    predict("What python -m does", "easy",
        code="""
        import contextlib, io, runpy
        from lessontools import make_tree, forget

        forget("reporter_p1")
        make_tree({
            "reporter_p1/__init__.py": 'print("package init, __name__ =", __name__)',
            "reporter_p1/__main__.py": '''
            from .core import summary
            print("main, __name__ =", __name__, "__package__ =", __package__)
            print(summary([3, 4, 5]))
            ''',
            "reporter_p1/core.py": '''
            def summary(values):
                return f"n={len(values)} mean={sum(values) / len(values):.1f}"
            ''',
        })
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            runpy.run_module("reporter_p1", run_name="__main__")
        print(out.getvalue(), end="")
        import reporter_p1.core
        print(reporter_p1.core.summary([1]))
        """,
        hints=["`python -m pkg` is `runpy.run_module(\"pkg\", run_name=\"__main__\")`: it imports the package, then runs `pkg/__main__.py` as `__main__` with `__package__` set."],
        why="""Running a package with `python -m` first imports the package (its `__init__` runs, with its normal name), then executes `__main__.py` under the name `"__main__"` but with
        `__package__` set to the package, which is exactly why relative imports such as `from .core import summary` work there and fail when the file is run directly as a
        script. The package stays imported, so a later `import reporter_p1.core` is served from `sys.modules` without running `__init__` again."""),
    write("Bump a version", "easy", tag="Data work",
        prompt="""Write `bump(version, part)` returning the next version string for `part` in `"major"`, `"minor"`, `"patch"`: `1.4.2` becomes `2.0.0`, `1.5.0` or `1.4.3`. Drop any
        pre-release, post-release, dev or local part before bumping (`2.0.0rc1` bumped as a patch gives `2.0.1`), and count missing segments as 0 (`1.4` bumped as a patch gives
        `1.4.1`). An unknown part raises `ValueError`.""",
        code="""
        from packaging.version import Version

        def bump(version, part):
            pass
        """,
        tests="""
        assert [bump("1.4.2", p) for p in ("major", "minor", "patch")] == ["2.0.0", "1.5.0", "1.4.3"]
        assert bump("1.4", "patch") == "1.4.1" and bump("2.0.0rc1", "patch") == "2.0.1" and bump("0.9.9.post2", "minor") == "0.10.0"
        assert bump("v3.1.0+cu121", "major") == "4.0.0"
        try:
            bump("1.0.0", "build")
            assert False
        except ValueError:
            pass
        """,
        hints=["`Version(version).release` gives the integer segments; pad to three with zeros.", "Return `f\"{major}.{minor}.{patch}\"` after incrementing one and resetting the lower ones."],
        solution="""
        from packaging.version import Version


        def bump(version, part):
            major, minor, patch = (list(Version(version).release) + [0, 0, 0])[:3]
            if part == "major":
                return f"{major + 1}.0.0"
            if part == "minor":
                return f"{major}.{minor + 1}.0"
            if part == "patch":
                return f"{major}.{minor}.{patch + 1}"
            raise ValueError(f"unknown part: {part!r}")
        """,
        why="""Parsing with `Version` normalises everything a version string may carry (a leading `v`, pre-release, post-release and local labels) and exposes the numeric release
        segments, so the bump logic is three lines of integer arithmetic. Resetting the lower segments is the semantic-versioning rule: a new minor release starts at patch
        0. Release tooling (`uv version --bump`, `bump-my-version`, `hatch version`) implements this together with updating `pyproject.toml` and tagging the commit."""),
    fix("A plugin loader that hides real import errors", "easy", tag="GenAI",
        prompt="""`load_scorer(name)` imports `scorers_f3.<name>` and returns its `score` function, reporting `LookupError(f"no scorer named {name}")` when the plugin does not exist. But
        it catches every `ImportError`, so a plugin that **exists** but fails to import one of **its own** dependencies is also reported as "no scorer named ...", which sends
        people looking in the wrong place. Only translate the error when the missing module is the plugin itself (`e.name`).""",
        code="""
        import importlib

        def load_scorer(name):
            try:
                module = importlib.import_module(f"scorers_f3.{name}")
            except ImportError:
                raise LookupError(f"no scorer named {name}") from None
            return module.score
        """,
        tests="""
        from lessontools import make_tree, forget
        forget("scorers_f3")
        make_tree({
            "scorers_f3/__init__.py": "",
            "scorers_f3/exact.py": "def score(answer, expected):\\n    return float(answer == expected)",
            "scorers_f3/semantic.py": "import sentence_transformers_not_installed\\ndef score(a, b):\\n    return 1.0",
        })
        assert load_scorer("exact")("a", "a") == 1.0
        assert load_scorer("exact")("a", "b") == 0.0
        try:
            load_scorer("bleu")
            assert False
        except LookupError as e:
            assert str(e) == "no scorer named bleu"
        try:
            load_scorer("semantic")
            assert False
        except ModuleNotFoundError as e:
            assert e.name == "sentence_transformers_not_installed"
        """,
        hints=["`except ModuleNotFoundError as e:` and check `e.name == f\"scorers_f3.{name}\"`; otherwise re-raise with a bare `raise`."],
        solution="""
        import importlib

        def load_scorer(name):
            target = f"scorers_f3.{name}"
            try:
                module = importlib.import_module(target)
            except ModuleNotFoundError as e:
                if e.name == target:
                    raise LookupError(f"no scorer named {name}") from None
                raise
            return module.score
        """,
        why="""`ModuleNotFoundError` carries the name of the module that could not be found. When it is the plugin itself, "no such scorer" is the right message; when it is something the
        plugin imports, the real problem is a missing dependency (an extra that was not installed, 15.2), and re-raising preserves the original error and traceback that say so.
        Catching broad exceptions and replacing them with a friendly message is only friendly when the message is true; otherwise it turns a one-minute fix into an hour of
        searching."""),
    predict("parse_args and sys.argv", "medium",
        code="""
        import argparse, sys

        def build():
            p = argparse.ArgumentParser(prog="sync-index")
            p.add_argument("--full", action="store_true")
            p.add_argument("source", nargs="?", default="docs/")
            return p

        saved = sys.argv
        try:
            sys.argv = ["sync-index", "--full", "kb/"]
            a = build().parse_args()
            b = build().parse_args([])
            c = build().parse_args(None)
        finally:
            sys.argv = saved
        print((a.full, a.source), (b.full, b.source), (c.full, c.source), build().prog)
        """,
        hints=["`parse_args()` and `parse_args(None)` read `sys.argv[1:]`; an explicit empty list means no arguments at all."],
        why="""With no argument (or `None`), `parse_args` reads `sys.argv[1:]`, so `a` and `c` both see `--full kb/`. Passing `[]` explicitly parses an empty command line, so `b` gets the
        defaults; `nargs="?"` makes the positional optional with its default. This is why `main(argv=None)` works both as an entry point (called with nothing, it reads the real
        command line) and in tests (called with an explicit list, it ignores the real one)."""),
    write("Review a dependency change", "medium", tag="Data work",
        prompt="""Write `requirements_diff(old, new)` comparing two lists of requirement strings by canonical name and returning `{"added": [...], "removed": [...], "changed": [...]}`,
        each sorted, where `changed` holds strings `f"{name}: {old_spec} -> {new_spec}"` for projects whose specifier, extras or marker changed (show the specifier, or `"(any)"`
        when empty, followed by `[extras]` when present).""",
        code="""
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        def requirements_diff(old, new):
            pass
        """,
        tests="""
        old = ["httpx>=0.27,<1", "pydantic~=2.7", "numpy", "openai>=1.30", "rich"]
        new = ["HTTPX>=0.27,<1", "pydantic>=2.9,<3", "numpy>=2", "openai[datalib]>=1.30", "tiktoken==0.7.*"]
        assert requirements_diff(old, new) == {
            "added": ["tiktoken"],
            "removed": ["rich"],
            "changed": ["numpy: (any) -> >=2", "openai: >=1.30 -> >=1.30[datalib]", "pydantic: ~=2.7 -> <3,>=2.9"],
        }
        assert requirements_diff(old, old) == {"added": [], "removed": [], "changed": []}
        """,
        hints=["Parse both lists into dicts `canonical name -> Requirement`; compare `(str(r.specifier), sorted(r.extras), str(r.marker))`.",
               "A small helper `describe(req)` builds `\"<spec or (any)>[extras]\"`."],
        solution="""
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name


        def _parse(lines):
            return {canonicalize_name(r.name): r for r in map(Requirement, lines)}


        def _key(req):
            return (str(req.specifier), sorted(req.extras), str(req.marker) if req.marker else "")


        def _describe(req):
            spec = str(req.specifier) or "(any)"
            extras = f"[{','.join(sorted(req.extras))}]" if req.extras else ""
            return spec + extras


        def requirements_diff(old, new):
            a, b = _parse(old), _parse(new)
            changed = [f"{n}: {_describe(a[n])} -> {_describe(b[n])}" for n in sorted(a.keys() & b.keys()) if _key(a[n]) != _key(b[n])]
            return {"added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys()), "changed": changed}
        """,
        why="""Dependency changes deserve review like code changes, and a semantic diff is far easier to read than a text diff: renaming `httpx` to `HTTPX` is not a change at all, while
        widening `pydantic` from `~=2.7` to `<3,>=2.9` or adding an extra to `openai` pulls in different code. Comparing parsed specifiers, extras and markers catches exactly
        those, and canonical names prevent false "removed and added" pairs. A CI job can post this summary on every pull request that touches `pyproject.toml`."""),
    write("Validate the scripts table", "medium", tag="Data work",
        prompt="""Write `validate_scripts(pyproject_text)` returning a sorted list of problems in `[project.scripts]`: `"NAME: target must look like module:function"` when there is no single
        `:` with text on both sides, `"NAME: module MODULE not found"` when `importlib.util.find_spec` finds nothing (without importing it), and nothing otherwise. An absent
        table means no problems.""",
        code="""
        import importlib.util, tomllib

        def validate_scripts(pyproject_text):
            pass
        """,
        tests="""
        from lessontools import make_tree
        make_tree({"evaltool_w6/__init__.py": "", "evaltool_w6/cli.py": "def main(argv=None):\\n    return 0"})
        text = '''
        [project]
        name = "evaltool"
        version = "0.1.0"
        [project.scripts]
        evaltool = "evaltool_w6.cli:main"
        broken = "evaltool_w6.cli.main"
        typo = "evaltool_w6.clii:main"
        empty = "evaltool_w6.cli:"
        '''
        assert validate_scripts(text) == ["broken: target must look like module:function", "empty: target must look like module:function",
                                          "typo: module evaltool_w6.clii not found"]
        assert validate_scripts("[project]\\nname = 'x'\\nversion = '1'") == []
        """,
        hints=["`module, sep, func = target.partition(\":\")`; reject when `not sep or not module or not func or \":\" in func`.",
               "`importlib.util.find_spec(module)` returns `None` for a missing module; it raises `ModuleNotFoundError` when a parent package is missing, so catch that too."],
        solution="""
        import importlib.util, tomllib


        def validate_scripts(pyproject_text):
            scripts = tomllib.loads(pyproject_text).get("project", {}).get("scripts", {})
            problems = []
            for name, target in scripts.items():
                module, sep, func = target.partition(":")
                if not sep or not module or not func or ":" in func:
                    problems.append(f"{name}: target must look like module:function")
                    continue
                try:
                    found = importlib.util.find_spec(module) is not None
                except ModuleNotFoundError:
                    found = False
                if not found:
                    problems.append(f"{name}: module {module} not found")
            return sorted(problems)
        """,
        why="""A wrong entry point is only discovered when someone installs the package and types the command, typically in production; validating `[project.scripts]` in CI catches it at
        the pull request. The format check rejects the classic dotted-path mistake (`cli.main` instead of `cli:main`), and `find_spec` confirms the module exists **without importing
        it**, so the check has no side effects (15.1). A fuller check would import the module in a clean environment and confirm the function exists and is callable."""),
    fix("Read the code: a release helper", "hard", tag="ML",
        prompt="""`release_check` gates a model-serving release: the requested `version` must be newer than every published version, and each required package must be installed at
        a satisfying version. It compares versions as strings, considers `2.0.0rc1` newer than `2.0.0`, matches package names exactly, and returns `True`/`False` without saying
        why. Rewrite it to return a sorted list of problems (empty means go): `"version V is not newer than LATEST"`, `"missing: NAME"`, `"NAME VERSION does not satisfy SPEC"`.""",
        code="""
        def release_check(version, published, required, installed):
            if version <= max(published):
                return False
            for line in required:
                name, _, spec = line.partition(">=")
                if name not in installed or installed[name] < spec:
                    return False
            return True
        """,
        tests="""
        published = ["1.9.0", "1.10.0", "2.0.0rc1"]
        required = ["torch>=2.3", "transformers[torch]>=4.40", "fastapi>=0.110"]
        installed = {"Torch": "2.10.0", "transformers": "4.9.0"}
        problems = release_check("1.10.1", published, required, installed)
        assert problems == ["missing: fastapi", "transformers 4.9.0 does not satisfy >=4.40", "version 1.10.1 is not newer than 2.0.0rc1"]
        assert release_check("2.0.0", published, required, {**installed, "transformers": "4.44.0", "fastapi": "0.115.0"}) == []
        """,
        hints=["Compare with `packaging.version.Version`: `max(published, key=Version)`; `Version(\"2.0.0\") > Version(\"2.0.0rc1\")`.",
               "Canonicalise installed names; parse each requirement with `Requirement` and test `req.specifier.contains(Version(v), prereleases=True)`."],
        solution="""
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version


        def release_check(version, published, required, installed):
            problems = []
            latest = max(published, key=Version) if published else None
            if latest is not None and Version(version) <= Version(latest):
                problems.append(f"version {version} is not newer than {latest}")
            have = {canonicalize_name(k): v for k, v in installed.items()}
            for line in required:
                req = Requirement(line)
                name = canonicalize_name(req.name)
                if name not in have:
                    problems.append(f"missing: {name}")
                elif not req.specifier.contains(Version(have[name]), prereleases=True):
                    problems.append(f"{name} {have[name]} does not satisfy {req.specifier}")
            return sorted(problems)
        """,
        why="""String comparison got every version question wrong: `"1.10.0"` sorts below `"1.9.0"`, `"2.10.0"` below `"2.3"`, and `"2.0.0rc1"` above `"2.0.0"`, so the gate could approve a
        version that goes backwards and reject a valid environment. `Version` compares by PEP 440, where a release candidate precedes its final release, so `2.0.0` is a valid
        release after `2.0.0rc1`. Package names need canonicalising (`Torch` is `torch`), requirements need the real parser (extras broke `partition`), and a gate should say
        **why** it fails, listing every problem at once, so the release engineer can fix them in one pass."""),
    explain("You install your package and `mytool` runs an old version of your code. What could be going on?", "medium", tag="Interview",
        why="""Usually more than one copy of the code or the interpreter is in play. The `mytool` on `PATH` may belong to another environment (a global install, a previous virtual
        environment, `pipx`); check `which mytool` (or `where` on Windows) and the shebang inside it. The package may be installed **non-editable** in the environment, so a
        wheel copy in `site-packages` is used instead of your working tree (`pip install -e .` or `uv sync` fixes it); `python -c "import mytool; print(mytool.__file__)"` shows
        which copy is imported. Stale build artefacts (`build/`, an old wheel, `.egg-info`) or a cached `__pycache__` from a moved file can confuse things, and a local folder
        or file with the same name can shadow the installed package. Finally, the entry point may point at an old module path. Printing `sys.executable`, `sys.path` and
        `module.__file__` settles it quickly."""),
    explain("How would you structure a Python project that ships both a library and a command-line tool?", "hard", tag="Interview",
        why="""Use a `src/` layout with one importable package (`src/mytool/`): pure, well-tested library modules for the domain logic, and a thin `cli.py` that only parses arguments
        (argparse, Click or Typer), reads configuration with clear precedence, calls library functions, writes results to standard output and diagnostics to standard error,
        and returns exit codes from `main(argv) -> int`. Declare everything in `pyproject.toml`: metadata, `requires-python`, runtime dependencies with ranges (it is a library),
        heavy optional features as extras (`mytool[pdf]`), development tools in dependency groups, and `[project.scripts] mytool = "mytool.cli:main"`; add `__main__.py` so
        `python -m mytool` works too. Keep import-time side effects out of the package. Test the library directly, the CLI through `main([...])` with captured streams, and the
        installed entry point with a few subprocess tests; lock development environments with `uv.lock`, test against the minimum and latest supported dependency versions in CI,
        and publish wheels from CI with versions bumped deliberately."""),
)

section("project", "Mini project: an evaluation command-line tool",
    p("""Teams evaluate prompts and models from the command line and from CI. Build `evalctl`, a small tool with three subcommands: `run` scores model answers read as JSON Lines,
    using a scorer plugin chosen by name; `summary` aggregates result lines; `check-env` checks installed package versions against requirements. It must behave well in pipes
    and schedulers: data on standard output, diagnostics on standard error, and meaningful exit codes."""),
    write("Build the evalctl command", "hard", key="evalctl", tag="Project",
        prompt="""Implement `main(argv=None, *, stdin=None, stdout=None, stderr=None, env=None, installed=None)`.

        - **`run [--scorer MODULE:FUNC] [--threshold T]`**: read JSONL lines `{"id", "answer", "expected"}` from stdin; load the scorer with `importlib` (15.1), default
          `"evalctl_scorers.exact:score"`; write one JSONL line per case to stdout, `{"id", "score", "passed"}` with `passed = score >= threshold`. The threshold comes from
          `--threshold`, else the `EVAL_THRESHOLD` environment variable in `env`, else 0.5 (15.3 precedence). Invalid JSON lines are reported on stderr as `f"line {n}: invalid
          JSON"`; exit code 1 if any line was invalid, else 0. A scorer target that cannot be loaded prints `f"error: cannot load scorer {target}"` to stderr and returns 2.
        - **`summary`**: read result lines from stdin and print `f"cases={n} passed={p} rate={p / n:.2f}"` (rate 0.00 when empty); exit 0.
        - **`check-env REQUIREMENT...`**: compare with `installed` (a dict of names to versions; canonicalise names, 15.2); print one line per problem to stderr, sorted (`f"missing:
          {name}"` or `f"{name} {version} does not satisfy {spec}"`), print `"ok"` to stdout when there is none; exit 0 if fine, else 1.

        Streams default to the `sys` ones and `env` to `os.environ`.""",
        code="""
        import argparse, importlib, json, os, sys
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version


        def main(argv=None, *, stdin=None, stdout=None, stderr=None, env=None, installed=None):
            pass
        """,
        tests="""
        import io, json
        from lessontools import make_tree, forget
        forget("evalctl_scorers")
        make_tree({
            "evalctl_scorers/__init__.py": "",
            "evalctl_scorers/exact.py": '''
            def score(answer, expected):
                return float(answer.strip().lower() == expected.strip().lower())
            ''',
            "evalctl_scorers/overlap.py": '''
            def score(answer, expected):
                words = expected.lower().split()
                have = set(answer.lower().split())
                return round(sum(w in have for w in words) / len(words), 3) if words else 0.0
            ''',
        })
        def call(argv, data="", env=None, installed=None):
            out, err = io.StringIO(), io.StringIO()
            code = main(argv, stdin=io.StringIO(data), stdout=out, stderr=err, env=env or {}, installed=installed or {})
            return code, out.getvalue(), err.getvalue()

        cases = '{"id": 1, "answer": "Five days", "expected": "five days"}\\nnot json\\n{"id": 2, "answer": "Refunds take five business days", "expected": "five days to refund"}\\n'
        code, out, err = call(["run"], cases)
        assert code == 1 and err == "line 2: invalid JSON\\n"
        assert [json.loads(l) for l in out.splitlines()] == [{"id": 1, "score": 1.0, "passed": True}, {"id": 2, "score": 0.0, "passed": False}]
        code, out, err = call(["run", "--scorer", "evalctl_scorers.overlap:score"], cases, env={"EVAL_THRESHOLD": "0.5"})
        assert [json.loads(l)["passed"] for l in out.splitlines()] == [True, True] and json.loads(out.splitlines()[1])["score"] == 0.5
        code, out, err = call(["run", "--scorer", "evalctl_scorers.overlap:score", "--threshold", "0.9"], cases, env={"EVAL_THRESHOLD": "0.1"})
        assert [json.loads(l)["passed"] for l in out.splitlines()] == [True, False]
        assert call(["run", "--scorer", "evalctl_scorers.bleu:score"], cases) == (2, "", "error: cannot load scorer evalctl_scorers.bleu:score\\n")

        results = '{"id": 1, "score": 1.0, "passed": true}\\n{"id": 2, "score": 0.0, "passed": false}\\n{"id": 3, "score": 0.8, "passed": true}\\n'
        assert call(["summary"], results) == (0, "cases=3 passed=2 rate=0.67\\n", "")
        assert call(["summary"], "") == (0, "cases=0 passed=0 rate=0.00\\n", "")

        installed = {"Pydantic": "2.9.2", "numpy": "1.9.0"}
        assert call(["check-env", "pydantic~=2.7", "numpy>=1.26", "httpx"], installed=installed) == (1, "", "missing: httpx\\nnumpy 1.9.0 does not satisfy >=1.26\\n")
        assert call(["check-env", "pydantic>=2"], installed=installed) == (0, "ok\\n", "")
        """,
        hints=["Subparsers with `set_defaults(func=...)`; each handler takes `(args, io)` where `io` holds the streams, the env and `installed`, and returns an exit code.",
               "Threshold precedence: `args.threshold if args.threshold is not None else float(env.get(\"EVAL_THRESHOLD\", 0.5))`.",
               "Load the scorer like 15.1's `load_tool`; catch `ImportError`, `AttributeError` and `ValueError` and return 2 with the error message."],
        solution="""
        import argparse, importlib, json, os, sys
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version

        DEFAULT_SCORER = "evalctl_scorers.exact:score"


        def _load(target):
            module_name, sep, attr = target.partition(":")
            if not sep:
                raise ValueError(target)
            fn = getattr(importlib.import_module(module_name), attr)
            if not callable(fn):
                raise ValueError(target)
            return fn


        def _run(args, io):
            try:
                scorer = _load(args.scorer)
            except (ImportError, AttributeError, ValueError):
                print(f"error: cannot load scorer {args.scorer}", file=io["stderr"])
                return 2
            threshold = args.threshold if args.threshold is not None else float(io["env"].get("EVAL_THRESHOLD", 0.5))
            bad = False
            for n, line in enumerate(io["stdin"], start=1):
                if not line.strip():
                    continue
                try:
                    case = json.loads(line)
                except json.JSONDecodeError:
                    print(f"line {n}: invalid JSON", file=io["stderr"])
                    bad = True
                    continue
                score = scorer(case["answer"], case["expected"])
                io["stdout"].write(json.dumps({"id": case["id"], "score": score, "passed": score >= threshold}) + "\\n")
            return 1 if bad else 0


        def _summary(args, io):
            n = passed = 0
            for line in io["stdin"]:
                if line.strip():
                    n += 1
                    passed += bool(json.loads(line)["passed"])
            rate = passed / n if n else 0.0
            print(f"cases={n} passed={passed} rate={rate:.2f}", file=io["stdout"])
            return 0


        def _check_env(args, io):
            have = {canonicalize_name(k): v for k, v in io["installed"].items()}
            problems = []
            for line in args.requirements:
                req = Requirement(line)
                name = canonicalize_name(req.name)
                if name not in have:
                    problems.append(f"missing: {name}")
                elif not req.specifier.contains(Version(have[name]), prereleases=True):
                    problems.append(f"{name} {have[name]} does not satisfy {req.specifier}")
            for p in sorted(problems):
                print(p, file=io["stderr"])
            if not problems:
                print("ok", file=io["stdout"])
            return 1 if problems else 0


        def main(argv=None, *, stdin=None, stdout=None, stderr=None, env=None, installed=None):
            io = {"stdin": stdin or sys.stdin, "stdout": stdout or sys.stdout, "stderr": stderr or sys.stderr,
                  "env": os.environ if env is None else env, "installed": installed or {}}
            parser = argparse.ArgumentParser(prog="evalctl")
            sub = parser.add_subparsers(dest="command", required=True)
            run = sub.add_parser("run", help="score answers read from stdin")
            run.add_argument("--scorer", default=DEFAULT_SCORER)
            run.add_argument("--threshold", type=float, default=None)
            run.set_defaults(func=_run)
            summary = sub.add_parser("summary", help="aggregate result lines")
            summary.set_defaults(func=_summary)
            check = sub.add_parser("check-env", help="check installed versions")
            check.add_argument("requirements", nargs="+")
            check.set_defaults(func=_check_env)
            args = parser.parse_args(argv)
            return args.func(args, io)
        """,
        why="""Every lesson of the module has a job here:

        - **Imports (15.1):** the scorer is a plugin named by a `module:function` string and loaded with `importlib.import_module`, so new scorers are added by writing a module,
          not by editing the tool; a target that cannot be loaded is a usage problem, exit code 2.
        - **Dependencies (15.2):** `check-env` uses `packaging`'s `Requirement`, `canonicalize_name` and `Version`, so names like `Pydantic` and versions like `1.9.0` versus
          `>=1.26` are judged correctly.
        - **The CLI (15.3):** subcommands dispatch through `set_defaults(func=...)`, the threshold follows the precedence default < environment < flag, results go to standard
          output as JSON Lines so `evalctl run < cases.jsonl | evalctl summary` works, problems go to standard error, and the exit code tells CI whether to fail the build.

        Injecting the streams, the environment and the installed-package map makes the whole tool testable without subprocesses; in a real package, `installed` would come from
        `importlib.metadata`, `main` would be registered as `[project.scripts] evalctl = "evalctl.cli:main"`, and `python -m evalctl` would call it from `__main__.py`."""),
)

recap(
    "`python -m pkg` imports the package and runs `pkg/__main__.py` as `__main__` with `__package__` set, so relative imports work.",
    "Load plugins with `importlib.import_module`, and translate `ModuleNotFoundError` only when the missing module is the plugin itself.",
    "Treat versions and requirements as data: `Version`, `Requirement`, `canonicalize_name`; diff and validate them in CI.",
    "`parse_args(None)` reads `sys.argv`; `main(argv=None) -> int` serves both entry points and tests.",
    "A good tool keeps data on stdout, diagnostics on stderr, and tells schedulers the truth with its exit code.",
)
