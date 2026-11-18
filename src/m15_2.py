from lesson import *

lesson(
    id="m15-2", num="15.2", title="Environments and dependencies",
    intro="\"It works on my machine\" is usually a dependency problem. Virtual environments, pip and uv, how versions and specifiers "
          "work (PEP 440), requirement strings with extras and markers, `pyproject.toml`, lock files and why applications pin "
          "while libraries declare ranges, and the extra care ML stacks need. The browser cannot create environments or install "
          "packages, so problems work with the same building blocks the tools use: the `packaging` library that pip and uv rely on.",
    desc="venv, pip and uv, lock files, `pyproject.toml`.",
    keys="virtual environment venv pip uv requirements lock file uv.lock pyproject.toml dependencies optional-dependencies extras dependency-groups version pep 440 specifier compatible release prerelease marker packaging canonicalize_name resolver editable install src layout wheel reproducible",
)

term("Virtual environment", "A folder with its own Python interpreter link and its own `site-packages`, so each project has its own installed packages.")
term("Specifier", "A version constraint such as `>=2.0,<3` or `~=1.4.2`, used in requirements to say which versions of a package are acceptable.")
term("Lock file", "A file recording the exact version (and usually the hash) of every package installed, direct and transitive, so an environment can be recreated identically.")

section("venv", "Virtual environments",
    p("""Installing packages into the system Python mixes every project's dependencies in one `site-packages` folder, where project A needs `pydantic 1` and project B needs
    `pydantic 2`, and upgrading one breaks the other (or the operating system's own tools). A **virtual environment** gives each project its own folder of installed
    packages: `python -m venv .venv` creates it, activating it (`source .venv/bin/activate` on Linux and macOS, `.venv\\Scripts\\activate` on Windows) puts its `python` and
    `pip` first on `PATH`, and inside it `sys.prefix` points at `.venv` while `sys.base_prefix` still points at the base installation. Use one environment per project,
    keep it out of git (`.venv/` in `.gitignore`), and treat it as disposable: it is rebuilt from the dependency files, never edited by hand."""),
    p("""Always invoke pip as **`python -m pip`**, which guarantees it installs into the interpreter you are running; a bare `pip` may belong to another Python. Never use `sudo
    pip`. When something "is installed but cannot be imported", compare `sys.executable` and `python -m pip --version`: they usually belong to different environments."""),
)

section("tools", "pip and uv",
    p("""**pip** installs packages from PyPI (`python -m pip install "httpx>=0.27"`), from requirement files (`-r requirements.txt`), and from a local project in **editable**
    mode (`pip install -e .`), which links the source folder so code changes apply without reinstalling. `pip freeze` lists exactly what is installed. pip resolves
    dependencies but does not maintain a lock file on its own; `pip-tools` (`pip-compile`) adds one."""),
    p("""**uv** is a much faster, all-in-one replacement written in Rust and now widely used: `uv venv` creates an environment, `uv add httpx` adds a dependency to
    `pyproject.toml` and installs it, `uv lock` writes a cross-platform **`uv.lock`** with exact versions and hashes, `uv sync` makes the environment match the lock exactly
    (adding and removing packages), `uv run pytest` runs a command inside the project environment, and `uv python install 3.13` installs interpreters. Poetry and PDM offer
    similar project workflows. Whatever the tool, the model is the same: **declare** what you need in `pyproject.toml`, **lock** what was resolved, **sync** environments
    from the lock."""),
)

section("versions", "Versions and specifiers",
    p("""Python versions follow **PEP 440**: a release such as `2.7.1`, optionally with a pre-release (`2.8.0a1`, `b2`, `rc1`), a post-release (`2.7.1.post1`), a development release
    (`2.8.0.dev3`), or a local label (`2.1.0+cu121`, used by PyTorch for CUDA builds). They compare numerically segment by segment, so `1.10` is newer than `1.9`, and
    pre-releases come before their final release. Most libraries use **semantic versioning** loosely: a major bump (2.x to 3.0) may break your code, a minor bump adds
    features, a patch fixes bugs; ML libraries break more often than that promise suggests, so pin tightly in applications."""),
    p("""A **specifier** constrains versions: `==2.7.1` exact, `==2.7.*` any 2.7 release, `!=2.7.0` excludes one, `>=2.5,<3` a range, and the **compatible release** operator
    **`~=2.5.1`**, meaning `>=2.5.1,<2.6` (and `~=2.5` meaning `>=2.5,<3`). Pre-releases need care: installers (pip, uv) do not pick a pre-release when a final release
    satisfies the requirement, unless you opt in (`--pre`) or the specifier itself names a pre-release, and `SpecifierSet.filter()` follows that rule; but in `packaging` 26,
    `contains()` asked about one version accepts a pre-release that lies inside the range unless you pass `prereleases=False`, so be explicit when it matters (problem 2). A **requirement** string
    combines a name, optional **extras** in brackets that pull in optional dependencies (`fastapi[standard]`, `torch[cuda]`), a specifier, and an optional **environment
    marker** after `;` that limits when it applies (`tomli>=2; python_version < "3.11"`). The `packaging` library implements all of this, and it is what pip and uv use."""),
    ex("""
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet
    from packaging.requirements import Requirement

    versions = ["1.9.0", "1.10.0", "2.0.0rc1", "2.0.0", "2.0.0.post1", "1.10.0.dev2"]
    print(sorted(versions), sorted(versions, key=Version))
    spec = SpecifierSet("~=1.9")
    print([v for v in versions if Version(v) in spec], spec.contains("2.0.0rc1", prereleases=True))
    req = Requirement('openai[datalib]>=1.40,<2; python_version >= "3.9"')
    print(req.name, sorted(req.extras), str(req.specifier), str(req.marker), req.marker.evaluate({"python_version": "3.8"}))
    """, "versions.py"),
    p("""String sorting puts `1.10` before `1.9` and the development release last; `Version` sorts them correctly, with the `.dev` and `rc` releases before their finals.
    `~=1.9` accepts anything from 1.9 up to, but not including, 2.0, and `contains` (used through `in`) let the
    `1.10.0.dev2` development release through, the behaviour described above. The requirement parses into its parts, and its marker says it does not apply on Python 3.8."""),
)

section("pyproject", "pyproject.toml",
    p("""Modern projects describe themselves in **`pyproject.toml`** (11.4's TOML). `[project]` holds the metadata: `name`, `version`, `requires-python = ">=3.11"`, `dependencies` (the
    requirement strings the package needs at run time), and `[project.optional-dependencies]` for **extras** (`pdf = ["pypdf>=4"]`, installed with `pip install
    "mytool[pdf]"`). `[dependency-groups]` (PEP 735) holds development-only groups such as `dev = ["pytest", "ruff", "mypy"]`, which are not published with the package.
    `[project.scripts]` declares command-line entry points (15.3). `[build-system]` names the build backend (hatchling, setuptools, flit, uv's own) that turns the project
    into a **wheel**, the installable archive. With a `src/` layout (`src/mytool/__init__.py`), tests import the installed package, not files that happen to be in the current
    folder (15.1)."""),
)

section("locks", "Lock files and reproducibility",
    p("""Your direct dependencies have dependencies of their own (**transitive** dependencies), often dozens. If you declare only ranges, two installs a month apart can resolve
    to different versions, and a new release of a package you never heard of breaks your build. A **lock file** records the exact resolved version of every package, and
    usually its hash, so `uv sync` (or `pip install -r requirements.lock --require-hashes`) recreates the same environment on every machine and in CI and production. The
    rule of thumb: **applications lock** (services, pipelines, notebooks you need to rerun), **libraries declare ranges** (so they can be installed alongside other
    libraries) and test against the lowest and highest versions they claim to support. Update locks deliberately (`uv lock --upgrade`, Dependabot or Renovate pull requests),
    run the tests, and scan for known vulnerabilities (`pip-audit`)."""),
    p("""ML environments add pitfalls: GPU builds of PyTorch and friends come from special package indexes and carry local version labels (`+cu124`), CUDA and driver versions must
    match, some packages ship platform-specific wheels only, and model behaviour can change between library versions. Pin the Python version (`.python-version`,
    `requires-python`), lock everything including the index URLs, record library versions next to saved models and evaluation results, and build production images from
    the lock file."""),
)

section("warmup", "Warm-up",
    predict("PEP 440 ordering", "easy",
        code="""
        from packaging.version import Version

        print(Version("1.10") > Version("1.9"), "1.10" > "1.9")
        print(Version("2.0rc1") < Version("2.0"), Version("2.0.post1") > Version("2.0"), Version("1.0.dev1") < Version("1.0a1"))
        print(Version("1.0") == Version("1.0.0"), Version("2.0.0rc2").is_prerelease, Version("2.1.0+cu121").public)
        print(sorted(["3.0.0", "3.0.0b1", "2.9.9", "3.0.0.post2", "3.0.0a3"], key=Version))
        print(Version("v1.2").base_version, Version("1.2.3").release, Version("1.4.2").major)
        """,
        hints=["Versions compare by numeric release segments; `dev` < `a` < `b` < `rc` < final < `post` for the same release; trailing zeros do not matter."],
        why="""`Version` compares release numbers as integers, so 1.10 is newer than 1.9, while plain strings compare character by character. For the same release, development
        releases sort first, then alphas, betas and release candidates, then the final, then post-releases. `1.0` equals `1.0.0` because trailing zeros are ignored.
        The local label `+cu121` is not part of the public version. A leading `v` is accepted and normalised away, and `release` gives the integer segments."""),
    write("Pick the newest compatible release", "easy", tag="ML",
        prompt="""Write `latest_compatible(available, spec, allow_prereleases=False)` returning the newest version string from `available` that satisfies the specifier string `spec`,
        or `None`. Ignore pre-releases unless `allow_prereleases` is true, and skip strings that are not valid versions.""",
        code="""
        from packaging.specifiers import SpecifierSet
        from packaging.version import InvalidVersion, Version

        def latest_compatible(available, spec, allow_prereleases=False):
            pass
        """,
        tests="""
        available = ["2.1.0", "2.3.1", "2.10.0", "3.0.0rc1", "3.0.0", "not-a-version", "2.4.0.dev1"]
        assert latest_compatible(available, ">=2.1,<3") == "2.10.0"
        assert latest_compatible(available, "~=2.3.0") == "2.3.1"
        assert latest_compatible(available, ">=3.0.0rc1") == "3.0.0" and latest_compatible(["3.0.0rc1"], ">=3") is None
        assert latest_compatible(["3.0.0rc1"], ">=3.0.0a1", allow_prereleases=True) == "3.0.0rc1"
        assert latest_compatible(available, ">=4") is None and latest_compatible(available, "==2.4.*", allow_prereleases=True) == "2.4.0.dev1"
        """,
        hints=["`SpecifierSet(spec).filter(versions, prereleases=...)` returns the matching ones; parse each with `Version` inside `try`.",
               "Return the `max` by `Version`, keeping the original string."],
        solution="""
        from packaging.specifiers import SpecifierSet
        from packaging.version import InvalidVersion, Version


        def latest_compatible(available, spec, allow_prereleases=False):
            parsed = {}
            for v in available:
                try:
                    parsed[v] = Version(v)
                except InvalidVersion:
                    continue
            specifier = SpecifierSet(spec)
            ok = [v for v, ver in parsed.items() if specifier.contains(ver, prereleases=allow_prereleases or None) and (allow_prereleases or not ver.is_prerelease)]
            return max(ok, key=lambda v: parsed[v]) if ok else None
        """,
        why="""This is the first step of every resolver: from the versions an index offers, keep those the specifier allows and pick the newest. Comparing parsed `Version` objects is
        essential (2.10 is newer than 2.3, not older). Pre-releases are excluded by default, as pip and uv do, so `>=3` does not silently pick up `3.0.0rc1`; a specifier that
        itself mentions a pre-release, or an explicit flag, opts in. Invalid strings are skipped, because real indexes contain legacy version numbers that newer tools reject."""),
    fix("Versions sorted as strings", "easy", tag="Data work",
        prompt="""`newest_model(names)` picks the newest model artefact from names like `"classifier-1.9.0.pkl"`. It sorts the version strings alphabetically, so `1.10.0` loses to
        `1.9.0`, and a release candidate beats its final release. Fix it with `packaging.version.Version`.""",
        code="""
        def newest_model(names):
            versions = [n.removeprefix("classifier-").removesuffix(".pkl") for n in names]
            return "classifier-" + max(versions) + ".pkl"
        """,
        tests="""
        assert newest_model(["classifier-1.9.0.pkl", "classifier-1.10.0.pkl", "classifier-1.2.0.pkl"]) == "classifier-1.10.0.pkl"
        assert newest_model(["classifier-2.0.0rc1.pkl", "classifier-2.0.0.pkl"]) == "classifier-2.0.0.pkl"
        """,
        hints=["`max(versions, key=Version)`."],
        solution="""
        from packaging.version import Version

        def newest_model(names):
            versions = [n.removeprefix("classifier-").removesuffix(".pkl") for n in names]
            return "classifier-" + max(versions, key=Version) + ".pkl"
        """,
        why="""Strings compare character by character, so `"1.10.0"` sorts before `"1.9.0"` because `"1"` comes before `"9"`, and `"2.0.0rc1"` sorts after `"2.0.0"` because it is longer.
        `Version` parses the numbers and the pre-release marker and compares them as PEP 440 defines. The same bug appears in checkpoint names (12.1), dataset folders and
        Docker tags; parse versions before comparing them."""),
    predict("Specifiers in practice", "easy",
        code="""
        from packaging.specifiers import SpecifierSet

        def ok(spec, version, pre=None):
            return SpecifierSet(spec).contains(version, prereleases=pre)

        print(ok("~=1.4.2", "1.4.9"), ok("~=1.4.2", "1.5.0"), ok("~=1.4", "1.9"), ok("~=1.4", "2.0"))
        print(ok("==1.4.*", "1.4.10"), ok("==1.4.*", "1.40"), ok("!=2.1.0,>=2", "2.1.0"), ok(">=2,<3", "3.0"))
        print(ok(">=2,<3", "3.0rc1"), ok(">=2,<3", "2.5rc1"), ok(">=2,<3", "2.5rc1", pre=True), ok(">=2.5rc1", "2.5rc1"))
        print(str(SpecifierSet("<3,>=2")), len(SpecifierSet(">=2,<3,!=2.4")))
        """,
        hints=["`~=X.Y.Z` means `>=X.Y.Z, ==X.Y.*`; `~=X.Y` means `>=X.Y, ==X.*`.",
               "`contains` accepts a pre-release inside the range by default, but `<3` never accepts pre-releases of 3 itself."],
        why="""The compatible-release operator keeps every segment but the last: `~=1.4.2` allows 1.4.x from 1.4.2 on but not 1.5, and `~=1.4` allows any 1.x from 1.4 on but not 2.0.
        `==1.4.*` matches the 1.4 series only, so 1.40 is not included. Ranges exclude their upper bound, and `<3` also excludes the pre-releases of 3 (`3.0rc1` would otherwise
        sneak in, since it sorts below 3.0). A pre-release inside the range, `2.5rc1`, is accepted by `contains` whether or not `prereleases=True` is passed, and a
        specifier that names a pre-release obviously accepts it; installers still prefer final releases when choosing. A `SpecifierSet` normalises its string (sorted)
        and counts its clauses."""),
)

section("medium", "Medium",
    write("Parse a requirements file", "medium", tag="GenAI",
        prompt="""Write `parse_requirements(text)` for a `requirements.txt`-style string: ignore blank lines and comments (whole-line `#` and trailing ` #`), parse each line with
        `packaging.requirements.Requirement`, and return a dict from the **canonical** project name (`packaging.utils.canonicalize_name`) to `{"specifier": str,
        "extras": sorted list, "marker": str or None}`, sorted by name. A duplicate project (after canonicalisation) raises `ValueError(f"duplicate requirement: {name}")`;
        an unparsable line raises `ValueError(f"line {n}: ...")`.""",
        code="""
        from packaging.requirements import InvalidRequirement, Requirement
        from packaging.utils import canonicalize_name

        def parse_requirements(text):
            pass
        """,
        tests="""
        text = '''
        # LLM service
        openai[datalib]>=1.40,<2   # client
        Pydantic~=2.7
        tiktoken==0.7.*
        tomli>=2; python_version < "3.11"

        scikit_learn>=1.4
        '''
        reqs = parse_requirements(text)
        assert list(reqs) == ["openai", "pydantic", "scikit-learn", "tiktoken", "tomli"]
        assert reqs["openai"] == {"specifier": "<2,>=1.40", "extras": ["datalib"], "marker": None}
        assert reqs["tomli"]["marker"] == 'python_version < "3.11"' and reqs["pydantic"]["specifier"] == "~=2.7"
        for bad, msg in [("httpx\\nHTTPX>=0.27", "duplicate requirement: httpx"), ("numpy\\nnot valid ===", "line 2: ")]:
            try:
                parse_requirements(bad)
                assert False, bad
            except ValueError as e:
                assert str(e).startswith(msg), str(e)
        """,
        hints=["Strip each line, drop text after `\" #\"`, skip empty lines, and wrap `Requirement(line)` in `try` to re-raise `InvalidRequirement` as `ValueError` with the line number.",
               "`canonicalize_name(\"scikit_learn\")` gives `\"scikit-learn\"`; `str(req.specifier)` and `str(req.marker)` give normalised strings."],
        solution="""
        from packaging.requirements import InvalidRequirement, Requirement
        from packaging.utils import canonicalize_name


        def parse_requirements(text):
            out = {}
            for n, raw in enumerate(text.splitlines(), start=1):
                line = raw.split(" #", 1)[0].strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    req = Requirement(line)
                except InvalidRequirement as e:
                    raise ValueError(f"line {n}: {e}") from None
                name = canonicalize_name(req.name)
                if name in out:
                    raise ValueError(f"duplicate requirement: {name}")
                out[name] = {"specifier": str(req.specifier), "extras": sorted(req.extras),
                             "marker": str(req.marker) if req.marker else None}
            return dict(sorted(out.items()))
        """,
        why="""Requirement strings have a precise grammar (PEP 508), and using the same parser as pip avoids subtle disagreements about extras, markers and specifiers. Project names
        are case-insensitive and treat `-`, `_` and `.` as equivalent, so `scikit_learn`, `Scikit-Learn` and `scikit.learn` are one project; canonicalising before comparing is
        what catches the `httpx`/`HTTPX` duplicate, which pip would otherwise resolve unpredictably. Line numbers in errors make a 200-line requirements file fixable. A
        parser like this is the basis of dependency audits, licence checks and "what does this service depend on" dashboards."""),
    write("Is the lock file in sync?", "medium", tag="Data work",
        prompt="""Write `check_lock(pyproject_text, lock)` where `lock` maps canonical package names to exact version strings. Read `[project].dependencies` from the TOML and return a
        sorted list of problems: `"missing from lock: NAME"` for a dependency not in the lock, and `"NAME VERSION does not satisfy SPEC"` when the locked version is outside the
        specifier. Dependencies whose marker does not apply to `environment` (default `{"python_version": "3.12"}`) are skipped.""",
        code="""
        import tomllib
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version

        def check_lock(pyproject_text, lock, environment=None):
            pass
        """,
        tests="""
        pyproject = '''
        [project]
        name = "support-rag"
        version = "0.3.0"
        requires-python = ">=3.11"
        dependencies = [
            "httpx>=0.27,<1",
            "Pydantic~=2.7",
            "numpy>=1.26",
            "tomli>=2; python_version < '3.11'",
            "rich",
        ]
        '''
        lock = {"httpx": "0.28.1", "pydantic": "3.0.0", "numpy": "1.26.4", "anyio": "4.4.0"}
        assert check_lock(pyproject, lock) == ["missing from lock: rich", "pydantic 3.0.0 does not satisfy ~=2.7"]
        assert check_lock(pyproject, {**lock, "pydantic": "2.9.2", "rich": "13.7.1"}) == []
        assert check_lock(pyproject, lock, {"python_version": "3.10"}) == ["missing from lock: rich", "missing from lock: tomli", "pydantic 3.0.0 does not satisfy ~=2.7"]
        """,
        hints=["`tomllib.loads(text)[\"project\"].get(\"dependencies\", [])`; for each, `Requirement(...)`, then `req.marker.evaluate(env)` when there is a marker.",
               "Check `Version(locked) in req.specifier`, with `prereleases=True` so a locked pre-release is judged by the range."],
        solution="""
        import tomllib
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version


        def check_lock(pyproject_text, lock, environment=None):
            env = environment or {"python_version": "3.12"}
            deps = tomllib.loads(pyproject_text)["project"].get("dependencies", [])
            problems = []
            for line in deps:
                req = Requirement(line)
                if req.marker and not req.marker.evaluate(env):
                    continue
                name = canonicalize_name(req.name)
                if name not in lock:
                    problems.append(f"missing from lock: {name}")
                elif not req.specifier.contains(Version(lock[name]), prereleases=True):
                    problems.append(f"{name} {lock[name]} does not satisfy {req.specifier}")
            return sorted(problems)
        """,
        why="""A lock that does not satisfy the project's own declared ranges means someone edited one file without regenerating the other, so CI tests one set of versions and
        `pyproject.toml` promises another; `uv lock --check` and `poetry check --lock` exist for exactly this. Markers decide whether a dependency applies at all (`tomli` is only
        needed before Python 3.11, when `tomllib` joined the standard library), so the same project can be in sync for one environment and not another. Extra entries in the
        lock are normal: they are transitive dependencies such as `anyio`, pulled in by `httpx`."""),
    fix("Pinning that drops extras and markers", "medium", tag="ML",
        prompt="""`pin(requirements, resolved)` should turn each requirement string into a pinned one with `==` the resolved version, for a reproducible deploy, **keeping** its extras and
        environment marker. It currently writes `>=` instead of `==`, drops extras (so `torch[cuda]` loses its CUDA dependencies) and drops markers (so a Linux-only package is
        installed on macOS). Fix it.""",
        code="""
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        def pin(requirements, resolved):
            out = []
            for line in requirements:
                req = Requirement(line)
                out.append(f"{req.name}>={resolved[canonicalize_name(req.name)]}")
            return out
        """,
        tests="""
        reqs = ["transformers[torch]>=4.40", "uvloop>=0.19; sys_platform == 'linux'", "Rich"]
        resolved = {"transformers": "4.44.2", "uvloop": "0.20.0", "rich": "13.7.1"}
        assert pin(reqs, resolved) == ['transformers[torch]==4.44.2', 'uvloop==0.20.0; sys_platform == "linux"', "Rich==13.7.1"]
        assert pin([], {}) == []
        """,
        hints=["Build `extras = f\"[{','.join(sorted(req.extras))}]\" if req.extras else \"\"` and `marker = f\"; {req.marker}\" if req.marker else \"\"`."],
        solution="""
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        def pin(requirements, resolved):
            out = []
            for line in requirements:
                req = Requirement(line)
                extras = f"[{','.join(sorted(req.extras))}]" if req.extras else ""
                marker = f"; {req.marker}" if req.marker else ""
                out.append(f"{req.name}{extras}=={resolved[canonicalize_name(req.name)]}{marker}")
            return out
        """,
        why="""A pin must be an exact `==`, or the deploy is not reproducible: `>=` lets tomorrow's release in. Extras are part of what gets installed (`transformers[torch]` also installs
        PyTorch), and markers are part of where it gets installed, so dropping either changes the environment silently. Rebuilding the string from the parsed parts keeps
        them, and `packaging` normalises the marker's quotes. Real lock tools also record hashes and the index URL; this is the core of `pip-compile`'s output."""),
    trace("Evaluating markers", "medium",
        prompt="Fill in `applies` after each marked line.",
        code="""
        from packaging.markers import Marker

        linux_new = {"python_version": "3.12", "sys_platform": "linux", "platform_machine": "x86_64"}
        mac_old = {"python_version": "3.10", "sys_platform": "darwin", "platform_machine": "arm64"}
        m1 = Marker('python_version < "3.11"')
        m2 = Marker('sys_platform == "linux" and platform_machine == "x86_64"')
        m3 = Marker('sys_platform != "win32" or python_version >= "3.13"')

        applies = (m1.evaluate(linux_new), m1.evaluate(mac_old))  # row: "tomli backport"
        applies = (m2.evaluate(linux_new), m2.evaluate(mac_old))  # row: "CUDA wheels"
        applies = (m3.evaluate(mac_old), m3.evaluate({**mac_old, "sys_platform": "win32"}))  # row: "or"
        applies = str(Marker("python_version>='3.9'"))  # row: "normalised"
        """,
        trace_vars=["applies"],
        hints=["`evaluate(env)` overrides the given variables and uses the running interpreter's values for the rest. Version comparisons in markers are numeric."],
        why="""Markers are small boolean expressions over the target environment. The `tomli` backport is needed only before 3.11, so only the old Mac needs it. CUDA-specific
        packages target Linux on x86_64, so the ARM Mac skips them. The `or` marker is true unless both sides are false: Windows on 3.10 fails both. `packaging` normalises
        spacing and quotes, so a marker printed back looks the same however it was written. Resolvers such as uv evaluate markers for every target platform to produce one
        cross-platform lock."""),
    write("Find undeclared and unused dependencies", "medium", tag="Data work",
        prompt="""Write `dependency_report(sources, declared, import_to_dist, local=())`: `sources` maps file names to Python source, `declared` is a list of requirement strings, and
        `import_to_dist` maps top-level import names to distribution names where they differ (`"sklearn": "scikit-learn"`). Collect top-level imported names with `ast`
        (absolute imports only), ignore the standard library (`sys.stdlib_module_names`) and `local` packages, and return `{"missing": [...], "unused": [...]}` with
        canonical names, sorted: imported but not declared, and declared but never imported.""",
        code="""
        import ast, sys
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        def dependency_report(sources, declared, import_to_dist, local=()):
            pass
        """,
        tests="""
        sources = {
            "app/main.py": "import os, json\\nimport httpx\\nfrom pydantic import BaseModel\\nfrom app.retrieval import search\\nimport yaml",
            "app/retrieval.py": "import numpy as np\\nfrom sklearn.metrics import f1_score\\nfrom . import utils\\nimport collections.abc",
            "app/utils.py": "def f():\\n    import tiktoken\\n    return tiktoken",
        }
        declared = ["httpx>=0.27", "pydantic~=2.7", "numpy", "requests", "Scikit_Learn>=1.4"]
        mapping = {"sklearn": "scikit-learn", "yaml": "PyYAML"}
        assert dependency_report(sources, declared, mapping, local=("app",)) == {"missing": ["pyyaml", "tiktoken"], "unused": ["requests"]}
        assert dependency_report({}, [], {}) == {"missing": [], "unused": []}
        """,
        hints=["Walk every `ast.Import` (`alias.name.split(\".\")[0]`) and `ast.ImportFrom` with `level == 0` (`node.module.split(\".\")[0]`).",
               "Map each import name to a distribution with `import_to_dist.get(name, name)`, then canonicalise both sides before comparing sets."],
        solution="""
        import ast, sys
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name


        def dependency_report(sources, declared, import_to_dist, local=()):
            imported = set()
            for src in sources.values():
                for node in ast.walk(ast.parse(src)):
                    if isinstance(node, ast.Import):
                        imported.update(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        imported.add(node.module.split(".")[0])
            third_party = {n for n in imported if n not in sys.stdlib_module_names and n not in local}
            needed = {canonicalize_name(import_to_dist.get(n, n)) for n in third_party}
            have = {canonicalize_name(Requirement(r).name) for r in declared}
            return {"missing": sorted(needed - have), "unused": sorted(have - needed)}
        """,
        why="""Two common failures in real projects: code imports a package that is only installed by accident (a transitive dependency, or something in the developer's environment), so
        a clean install in CI or production breaks; and `pyproject.toml` keeps dependencies nobody uses, slowing installs and widening the security surface. Static analysis
        with `ast` finds both without running the code, including imports inside functions such as `tiktoken`. The mapping is necessary because import names and
        distribution names often differ (`sklearn` is `scikit-learn`, `yaml` is `PyYAML`, `cv2` is `opencv-python`). Tools such as `deptry` run this check in CI."""),
    predict("Reading pyproject.toml", "medium",
        code="""
        import tomllib
        from packaging.specifiers import SpecifierSet

        doc = tomllib.loads('''
        [project]
        name = "support-rag"
        version = "0.3.0"
        requires-python = ">=3.11"
        dependencies = ["httpx>=0.27,<1", "pydantic~=2.7"]

        [project.optional-dependencies]
        pdf = ["pypdf>=4"]
        eval = ["ragas>=0.1", "pandas>=2"]

        [project.scripts]
        rag-ingest = "support_rag.cli:main"

        [dependency-groups]
        dev = ["pytest>=8", "ruff", "mypy"]

        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"
        ''')
        project = doc["project"]
        print(project["name"], sorted(project["optional-dependencies"]), project["scripts"]["rag-ingest"])
        py = SpecifierSet(project["requires-python"])
        print([v for v in ["3.10", "3.11", "3.14"] if v in py], doc["dependency-groups"]["dev"][0], doc["build-system"]["build-backend"])
        print(len(project["dependencies"]) + sum(len(v) for v in project["optional-dependencies"].values()))
        """,
        hints=["`[project.optional-dependencies]` defines extras; `[dependency-groups]` defines development groups that are not published; `requires-python` is a specifier."],
        why="""The project's name, its two extras (`pip install "support-rag[pdf]"` or `[eval]`) and its command-line entry point all come from `[project]`. `requires-python` is an
        ordinary specifier, so tools check the running interpreter against it before installing. The `dev` group (pytest, ruff, mypy) is for contributors and is not
        part of the published package's metadata. The build backend turns the project into a wheel. Counting runtime and optional requirements gives 5."""),
)

section("hard", "Hard",
    write("A tiny dependency resolver", "hard", tag="Data work",
        prompt="""Write `resolve(index, requirements)` where `index` maps package names to `{version: [requirement strings of that version's dependencies]}` and `requirements` is a list of
        requirement strings. Choose one version per package such that every requirement (from the root and from every chosen version) is satisfied, preferring the **newest**
        versions, with **backtracking** when a choice leads to a conflict. Return a dict name -> version sorted by name, or raise `ValueError("no solution")`. Ignore pre-releases
        and markers.""",
        code="""
        from packaging.requirements import Requirement
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version

        def resolve(index, requirements):
            pass
        """,
        tests="""
        index = {
            "app-sdk": {"2.0.0": ["httpx>=0.27", "pydantic>=2"], "1.5.0": ["httpx>=0.25", "pydantic<2"]},
            "httpx": {"0.28.0": ["anyio>=4"], "0.27.0": ["anyio>=3"], "0.25.0": ["anyio<4"]},
            "anyio": {"4.4.0": [], "3.7.1": []},
            "pydantic": {"2.9.0": ["typing-extensions>=4.6"], "1.10.0": []},
            "typing-extensions": {"4.12.0": [], "4.5.0": []},
            "legacy-tool": {"1.0.0": ["pydantic<2"]},
        }
        assert resolve(index, ["app-sdk"]) == {"anyio": "4.4.0", "app-sdk": "2.0.0", "httpx": "0.28.0", "pydantic": "2.9.0", "typing-extensions": "4.12.0"}
        assert resolve(index, ["app-sdk", "legacy-tool"]) == {"anyio": "4.4.0", "app-sdk": "1.5.0", "httpx": "0.28.0", "legacy-tool": "1.0.0", "pydantic": "1.10.0"}
        assert resolve(index, ["app-sdk", "anyio<4"])["httpx"] == "0.27.0"
        try:
            resolve(index, ["app-sdk>=2", "legacy-tool"])
            assert False
        except ValueError as e:
            assert str(e) == "no solution"
        """,
        hints=["Recursive search over a list of pending requirements and a dict of choices: pop a requirement; if its package is chosen, check the version satisfies it; otherwise try the index's versions newest first that satisfy **all** constraints collected so far for that package.",
               "Keep constraints per package (a dict name -> list of specifiers) so a later requirement can reject an earlier choice; on failure, undo and try the next version."],
        solution="""
        from packaging.requirements import Requirement
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version


        def resolve(index, requirements):
            def ok(name, version, constraints):
                return all(Version(version) in spec for spec in constraints.get(name, []))

            def search(pending, chosen, constraints):
                if not pending:
                    return dict(chosen)
                req, rest = pending[0], pending[1:]
                name = req.name
                new_constraints = {k: list(v) for k, v in constraints.items()}
                new_constraints.setdefault(name, []).append(req.specifier)
                if name in chosen:
                    if not ok(name, chosen[name], new_constraints):
                        return None
                    return search(rest, chosen, new_constraints)
                candidates = sorted(index.get(name, {}), key=Version, reverse=True)
                for version in candidates:
                    if Version(version).is_prerelease or not ok(name, version, new_constraints):
                        continue
                    deps = [Requirement(d) for d in index[name][version]]
                    result = search(rest + deps, {**chosen, name: version}, new_constraints)
                    if result is not None:
                        return result
                return None

            result = search([Requirement(r) for r in requirements], {}, {})
            if result is None:
                raise ValueError("no solution")
            return dict(sorted(result.items()))
        """,
        why="""Dependency resolution is a search problem: each package needs one version, every chosen version adds constraints, and a choice that looks fine early can conflict with a
        requirement found later. Here the newest `app-sdk` needs `pydantic>=2`, so adding `legacy-tool` (which needs `pydantic<2`) forces the resolver to **backtrack** to
        `app-sdk 1.5.0`, whose constraints are compatible; with `app-sdk>=2` pinned there is no solution at all, the "dependency hell" every developer meets. Trying newest
        versions first matches what pip and uv do. Real resolvers use smarter algorithms (pip's backtracking, uv's PubGrub, which also explains conflicts in plain language),
        but the core is this depth-first search with undo (16.5)."""),
    fix("Read the code: an environment checker", "hard", tag="ML",
        prompt="""`check_environment(required, installed)` should report which required packages are missing or outside their specifier in an environment (`installed` maps
        distribution names, as the environment reports them, to versions). It compares versions as strings, compares names case-sensitively and without normalising `_` and
        `-`, treats a pre-release as satisfying a range, and crashes on requirements with extras. Rewrite it to return sorted `"missing: NAME"` and `"NAME VERSION not in SPEC"`
        problems using `packaging`.""",
        code="""
        def check_environment(required, installed):
            problems = []
            for line in required:
                name, _, minimum = line.partition(">=")
                if name not in installed:
                    problems.append(f"missing: {name}")
                elif installed[name] < minimum:
                    problems.append(f"{name} {installed[name]} not in >={minimum}")
            return sorted(problems)
        """,
        tests="""
        required = ["scikit-learn>=1.4", "torch[cuda]>=2.3,<2.6", "numpy>=1.26", "tiktoken>=0.7", "Pillow>=10"]
        installed = {"scikit_learn": "1.10.0", "torch": "2.6.0rc1", "numpy": "1.9.0", "pillow": "10.4.0"}
        assert check_environment(required, installed) == ["missing: tiktoken", "numpy 1.9.0 not in >=1.26", "torch 2.6.0rc1 not in <2.6,>=2.3"]
        assert check_environment(["numpy>=1.26"], {"NumPy": "2.1.0"}) == []
        """,
        hints=["Canonicalise both the requirement name and every installed name: `{canonicalize_name(k): v for k, v in installed.items()}`.",
               "`Requirement(line)` handles extras; test with `req.specifier.contains(Version(v), prereleases=True)` so a pre-release is checked against the range."],
        solution="""
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version


        def check_environment(required, installed):
            have = {canonicalize_name(k): v for k, v in installed.items()}
            problems = []
            for line in required:
                req = Requirement(line)
                name = canonicalize_name(req.name)
                if name not in have:
                    problems.append(f"missing: {name}")
                elif not req.specifier.contains(Version(have[name]), prereleases=True):
                    problems.append(f"{name} {have[name]} not in {req.specifier}")
            return sorted(problems)
        """,
        why="""Each bug is a rule from this lesson. String comparison declared `1.9.0` newer than `1.26` and `1.10.0` older than `1.4`. Distribution names are case-insensitive and
        `scikit_learn` is the same project as `scikit-learn`, so names must be canonicalised on both sides. `partition(">=")` broke on extras and on any other operator; the
        real `Requirement` parser handles the whole grammar. And `2.6.0rc1` is a pre-release of 2.6, which sorts **below** 2.6 but is still outside `<2.6` in spirit: with
        `prereleases=True` it is judged against the range and `packaging` excludes it, because `<2.6` rejects pre-releases of 2.6 itself. Checks like this run at service
        start-up or in a notebook's first cell to fail fast on a wrong environment."""),
    predict("Names and version normalisation", "hard",
        code="""
        from packaging.utils import canonicalize_name
        from packaging.version import Version

        names = ["Pillow", "scikit_learn", "Scikit.Learn", "typing-extensions", "Typing__Extensions"]
        print([canonicalize_name(n) for n in names], len({canonicalize_name(n) for n in names}))
        for raw in ["1.0-alpha.1", "v2.0", "2.0.0-rc.2", "1.0.post", "2.1.0+cu121", "1.0.0.0"]:
            v = Version(raw)
            print(raw, "->", str(v), v.local, v.is_prerelease)
        print(Version("2.1.0+cu121") > Version("2.1.0"), Version("2.1.0+cu121") == Version("2.1.0"))
        """,
        hints=["Canonical names are lower-case with runs of `-`, `_` and `.` replaced by a single `-`. `Version` normalises spellings such as `alpha` and `-rc.2`."],
        why="""Canonical names collapse case and separators, so the five spellings name only three projects; this is why `pip install Scikit_Learn` works. `Version` accepts many
        historical spellings and prints the normalised form: `1.0a1`, `2.0`, `2.0.0rc2`, `1.0.post0`. A local label such as `+cu121` is kept but not part of the public version,
        and a version with a local label sorts **after** the same version without one, which is how `torch 2.1.0+cu121` is distinguished from the CPU build in a resolver."""),
)

section("interview", "Interview questions",
    explain("Why do you use virtual environments, and how do you set up a new project today?", "medium", tag="Interview",
        why="""A virtual environment isolates a project's installed packages from the system and from other projects, so incompatible versions can coexist, the system Python's tools are
        not broken, and the environment can be deleted and rebuilt at will. For a new project I would pin the Python version (`.python-version`, `requires-python`), create the
        project with `uv init` (or a `pyproject.toml` by hand) in a `src/` layout, add runtime dependencies with `uv add` and development tools with `uv add --dev` (pytest, ruff,
        mypy) into a dependency group, commit `pyproject.toml` and the lock file but not `.venv`, and use `uv sync` / `uv run` locally and in CI so everyone runs the locked
        versions. With plain pip, the equivalent is `python -m venv .venv`, `python -m pip install -e ".[dev]"` and a compiled requirements lock. The point is that the environment
        is reproducible from files in the repository."""),
    explain("Should a library pin exact dependency versions? Should an application?", "medium", tag="Interview",
        why="""A **library** should declare the broadest ranges it actually supports (`httpx>=0.25,<1`), not exact pins: it will be installed alongside other libraries, and exact pins
        make conflicts likely (two libraries pinning different exact versions of a shared dependency cannot be installed together). It should test against its minimum and
        latest supported versions, and set upper bounds only for known incompatibilities. An **application** (a service, a pipeline, a training job) should **lock** every direct
        and transitive dependency to exact versions with hashes, so every install is identical and builds are reproducible, while still declaring ranges in `pyproject.toml`
        so the lock can be regenerated. Locks are upgraded deliberately and regularly (automated update pull requests plus the test suite) to pick up security fixes without
        surprises."""),
    explain("How do you make an ML project's environment reproducible six months from now?", "hard", tag="Interview",
        why="""Pin the interpreter (`requires-python` and a `.python-version`, ideally a specific minor version), declare dependencies in `pyproject.toml`, and commit a lock file with exact
        versions and hashes for every package, including the package index URLs used for GPU builds (PyTorch's CUDA wheels with local labels such as `+cu124`). Record the
        system-level pieces the lock cannot capture: CUDA and cuDNN versions, driver requirements, and the operating system, ideally by building a container image from the lock
        file with a pinned base image digest, and keep the built image in a registry, since base images and indexes change. Store the environment's identity (lock hash,
        image digest, `pip freeze` output) next to every trained model, dataset version and evaluation result, so results can be traced to the exact stack. Seed randomness and
        enable deterministic algorithms where needed. Finally, test the rebuild: CI should create the environment from scratch from the lock, so drift is noticed early."""),
)

recap(
    "One virtual environment per project; run tools as `python -m pip` or through uv, and rebuild environments from files rather than editing them.",
    "PEP 440 versions compare numerically with pre-, post-, dev- and local parts; never compare version strings directly.",
    "Specifiers (`>=`, `<`, `~=`, `==X.*`) constrain versions, extras add optional dependencies, markers limit where a requirement applies; `packaging` parses them all.",
    "`pyproject.toml` declares the project: dependencies, extras, dependency groups, scripts and build backend.",
    "Applications lock exact versions with hashes; libraries declare ranges; ML stacks also pin Python, CUDA builds and images.",
)
