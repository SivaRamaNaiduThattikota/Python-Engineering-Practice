from lesson import *
from diagrams import *

lesson(
    id="m12-4", num="12.4", title="Configuration and secrets",
    intro="The same code runs on a laptop, in CI and in production with different models, limits and keys, so configuration must "
          "live outside the code, and secrets must never be in it. Environment variables and their parsing, `.env` files, TOML "
          "with `tomllib`, layering defaults, files and environment with clear precedence, keeping secrets out of reprs, logs "
          "and git, and test hygiene. Applied to LLM settings, model registries and secret scanning.",
    desc="Environment variables, `.env` files, `tomllib`, keeping keys out of code.",
    keys="configuration settings environment variables os.environ getenv dotenv .env tomllib toml pyproject layering precedence chainmap deep merge secrets api key secret manager rotate gitignore repr redaction twelve-factor entropy scan monkeypatch",
)

term("Environment variable", "A named string the operating system passes to every process (`PATH`, `HOME`, `OPENAI_API_KEY`). Python reads them through `os.environ`.")
term("Secret", "A value that grants access (API keys, passwords, tokens, private keys). Anyone who sees it can use it, so it must never be in code, logs or git.")
term("TOML", "A configuration file format with typed values (strings, numbers, booleans, dates, arrays and tables), used by `pyproject.toml`. Python reads it with `tomllib`.")

section("why", "Configuration lives outside the code",
    p("""**Configuration** is everything that differs between deployments of the same code: the model name, the temperature, the database URL, timeouts,
    feature flags, log level, and the credentials to reach other services. Hard-coding it means editing and redeploying code to change a timeout, and
    hard-coding a **secret** means everyone with access to the repository, its forks, its CI logs and its history has the key. The widely followed
    "twelve-factor" rule is to keep configuration in the **environment**: the code reads it at start-up, and each environment (developer laptop, CI,
    staging, production) supplies its own values."""),
    p("""In practice, configuration comes in layers, from most general to most specific: **defaults** in the code (safe values that work for development),
    a **configuration file** checked into the repository for non-secret settings (`config.toml`), **environment variables** set by the deployment, and
    sometimes **command-line flags** for one run (15.3). Each layer overrides the ones before it, and secrets come only from the environment or a secret
    manager. The rest of this lesson builds each layer."""),
)

section("env", "Environment variables",
    p("""**`os.environ`** is a mapping of the process's environment variables. `os.environ["KEY"]` raises `KeyError` if the variable is missing,
    `os.environ.get("KEY", default)` (or the identical `os.getenv`) returns a default instead, and assigning `os.environ["KEY"] = "value"` changes it for
    this process and the child processes it starts, never for the parent shell. **Every value is a string**: assigning an int raises `TypeError`, and
    reading `"8"` or `"false"` gives strings that must be parsed. That parsing is where most configuration bugs come from: `bool("false")` is `True`,
    `int("8.0")` fails, and an empty string is not the same as a missing variable."""),
    ex("""
    import os

    os.environ["APP_TOP_K"] = "8"
    os.environ["APP_DEBUG"] = "false"
    os.environ.pop("APP_MISSING", None)
    print(repr(os.environ["APP_TOP_K"]), int(os.environ["APP_TOP_K"]) + 1)
    print(bool(os.environ["APP_DEBUG"]), os.getenv("APP_MISSING"), os.getenv("APP_MISSING", "fallback"))
    print("APP_TOP_K" in os.environ, type(os.environ).__name__, type(os.environ.copy()).__name__)
    try:
        os.environ["APP_TIMEOUT"] = 30
    except TypeError as e:
        print("TypeError:", e)
    try:
        os.environ["APP_MISSING"]
    except KeyError as e:
        print("KeyError:", e)
    """, "environ.py"),
    p("""Two habits follow. **Parse and validate once, at start-up**, into a typed settings object (a frozen dataclass or a Pydantic model, 11.P), so the rest
    of the program never touches `os.environ` and a bad value fails immediately with a clear message instead of an hour later. And **read the environment
    when the settings are created, not at import time**: a module that evaluates `os.getenv` in a global freezes whatever was set when it was first
    imported, which breaks tests and anything that changes configuration (problem 15)."""),
)

section("dotenv", "`.env` files",
    fig(flowchart({
        "line": ("start", 0, 0, "KEY=value in .env"),
        "set": ("ask", 0, 1, "KEY already in the|real environment?"),
        "keep": ("good", 1, 1, "keep the real value"),
        "use": ("step", 0, 2, "use the .env value"),
    }, [("line", "set"), ("set", "keep", "yes"), ("set", "use", "no")], cell=(240, 80), label="how a .env file is applied by default"),
        "By default `.env` only fills gaps, so a value set by the deployment always wins over the developer file."),
    p("""Typing a dozen `export` commands before every run is tedious, so development tools read a **`.env`** file in the project folder: one `KEY=value` per
    line, `#` comments, optional quotes. The `python-dotenv` package loads it into `os.environ`; Docker Compose, VS Code and many frameworks read the same
    format. The file holds **real secrets for your machine**, so it is listed in **`.gitignore`** and never committed; instead the repository contains a
    `.env.example` with every variable name and dummy values, which documents what the application needs. Problem 5 implements the parser, to see exactly
    what the format means: `export` prefixes, quotes, escapes in double quotes, and comments."""),
    p("""By convention, values loaded from `.env` do **not** override variables already set in the real environment, so a deployment can always win over a
    stray file. In production, there is no `.env` file at all: the platform (Kubernetes, a cloud service, CI) injects environment variables, ideally fetched
    from a **secret manager** such as AWS Secrets Manager, Azure Key Vault, GCP Secret Manager or HashiCorp Vault, which stores secrets encrypted, controls
    who can read them, logs every access and supports rotation."""),
)

section("toml", "Configuration files with `tomllib`",
    p("""Non-secret settings with structure (several models, retrieval parameters, prompt names) are clearer in a file than in dozens of variables. **TOML** is the
    Python ecosystem's format: `pyproject.toml` uses it, and since Python 3.11 the standard library reads it with **`tomllib`**. Unlike `.env` and
    environment variables, TOML values are **typed**: `8` is an int, `0.2` a float, `true` a bool, `"text"` a string, `2025-03-01` a date, `[...]` an
    array, and `[section]` headers and `[[array.of.tables]]` create nested dicts and lists of dicts. `tomllib.loads(text)` parses a string and
    `tomllib.load(f)` a file opened in **binary** mode (`"rb"`), returning plain dicts; errors raise `tomllib.TOMLDecodeError`, a subclass of `ValueError`.
    `tomllib` only reads; writing TOML needs a third-party package such as `tomli-w`."""),
    ex("""
    import tomllib

    text = '''
    service = "support-rag"
    debug = false

    [retrieval]
    top_k = 8
    min_score = 0.35
    sources = ["faq", "terms"]

    [[models]]
    name = "small"
    context_window = 8_192

    [[models]]
    name = "large"
    context_window = 128_000
    '''
    cfg = tomllib.loads(text)
    print(cfg["retrieval"], type(cfg["retrieval"]["min_score"]).__name__)
    print([m["name"] for m in cfg["models"]], cfg["models"][1]["context_window"])
    try:
        tomllib.loads("top_k = 8\\ntop_k = 9")
    except tomllib.TOMLDecodeError as e:
        print("TOMLDecodeError:", e)
    """, "toml_config.py"),
)

section("layers", "Layering and precedence",
    fig(chain(["defaults|in the code", "config.toml", "environment|variables", ("command-line|flags", "accent")], note="each layer overrides the ones to its left; secrets come only from the environment"),
        "Configuration layers from most general to most specific; the last one that sets a value wins."),
    p("""Combining the layers is a **merge**, and its rules should be explicit. A shallow merge, `{**defaults, **file_cfg, **env_cfg}` or `defaults | file_cfg`,
    replaces whole nested sections: a file that sets only `model.name` would wipe out the default `model.temperature`. Configuration needs a **deep
    merge**: nested dicts are merged key by key, and other values (including lists) are replaced. `collections.ChainMap(env, file_cfg, defaults)` gives a
    read-only-looking view that searches the maps in order without copying, which suits flat settings; writes go to the first map (problem 9)."""),
    p("""Environment variables are flat strings, so nested keys need a naming convention, usually a prefix and a double underscore for each level:
    `APP_MODEL__TEMPERATURE=0.7` sets `model.temperature`. Their values need types; a neat trick is to parse each one as a TOML value and fall back to the raw
    string, so `0.7` becomes a float, `true` a bool and `["a", "b"]` a list (problem 6). Whatever the scheme, a good settings loader can also report **where
    each value came from** (problem 14), the first thing you want to know when production behaves differently from your laptop."""),
    ex("""
    import copy

    def deep_merge(base, override):
        out = copy.deepcopy(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(out.get(key), dict):
                out[key] = deep_merge(out[key], value)
            else:
                out[key] = copy.deepcopy(value)
        return out

    defaults = {"model": {"name": "small", "temperature": 0.0}, "retrieval": {"top_k": 5, "sources": ["faq"]}}
    file_cfg = {"model": {"name": "large"}, "retrieval": {"sources": ["faq", "terms"]}}
    print({**defaults, **file_cfg}["model"])
    merged = deep_merge(defaults, file_cfg)
    print(merged)
    print(defaults["retrieval"]["sources"])
    """, "layers.py"),
)

section("secrets", "Keeping secrets secret",
    p("""A secret leaks in more ways than being committed. The rules: never write a secret in source code, notebooks, tests or config files that are committed;
    keep `.env` in `.gitignore`; read secrets from the environment or a secret manager at start-up; **never log or print them**, which includes the
    accidental cases: an exception message that contains a URL with a password, a `repr` of a settings object in a log line, a debug dump of request headers,
    or a notebook cell output saved into the repository. Give secrets their own type whose `repr` and `str` are masked (Pydantic has `SecretStr`;
    problem 10 builds one), so printing the settings is safe."""),
    p("""Assume a leak will happen and limit its damage: use **separate keys per environment and per service**, give each key the narrowest permissions and
    spending limits the provider allows, and **rotate** them regularly. Add automated **secret scanning** (GitHub's push protection, `gitleaks`,
    `detect-secrets`, or a pre-commit hook like problem 13) so a key is caught before it is pushed. If a key is committed anyway, **revoke and rotate it
    first**: deleting the commit does not help, because forks, clones, CI caches and bots that scan public repositories for keys within minutes may
    already have it."""),
)

section("warmup", "Warm-up",
    predict("Environment variables are strings", "easy",
        code="""
        import os

        os.environ["P1_LIMIT"] = "10"
        os.environ["P1_FLAG"] = "0"
        os.environ["P1_EMPTY"] = ""
        os.environ.pop("P1_NONE", None)
        print(os.environ["P1_LIMIT"] * 2, int(os.environ["P1_LIMIT"]) * 2)
        print(bool(os.environ["P1_FLAG"]), bool(os.environ["P1_EMPTY"]), os.getenv("P1_NONE", "unset"))
        print(os.environ.get("P1_EMPTY") or "default", os.environ.get("P1_EMPTY", "default") == "")
        print(os.environ.setdefault("P1_NONE", "5"), os.environ.pop("P1_NONE"), "P1_NONE" in os.environ)
        """,
        hints=["Every value is a string; `bool` of any non-empty string is `True`. `get` with a default only helps when the variable is missing, not when it is empty."],
        why="""`"10" * 2` repeats the string; it needs `int` first. `bool("0")` is `True` because the string is not empty, the classic bug when flags are parsed with `bool`.
        An empty variable is **set**, so `get` returns `""` rather than the default, while `or "default"` treats empty as missing; choose deliberately.
        `setdefault` sets and returns the value when missing, and `pop` removes it again."""),
    write("Parse boolean and integer settings", "easy", tag="GenAI",
        prompt="""Write `env_bool(name, default=False, environ=None)` and `env_int(name, default, min_value=None, max_value=None, environ=None)` reading from `environ`
        (default `os.environ`). A missing or empty variable gives the default. `env_bool` accepts `1, true, yes, on` and `0, false, no, off` in any case and with
        surrounding spaces; `env_int` accepts integers only and checks the bounds. Anything else raises `ValueError` whose message names the variable and the
        bad value.""",
        code="""
        import os

        def env_bool(name, default=False, environ=None):
            pass

        def env_int(name, default, min_value=None, max_value=None, environ=None):
            pass
        """,
        tests="""
        env = {"DEBUG": " TRUE ", "STREAM": "off", "EMPTY": "", "FLAG": "maybe", "TOP_K": "8", "BIG": "500", "FLOAT": "8.0"}
        assert [env_bool(k, environ=env) for k in ["DEBUG", "STREAM", "EMPTY", "MISSING"]] == [True, False, False, False]
        assert env_bool("MISSING", default=True, environ=env) is True and env_int("TOP_K", 5, 1, 50, environ=env) == 8 and env_int("NONE", 5, environ=env) == 5
        for call, text in [(lambda: env_bool("FLAG", environ=env), "FLAG"), (lambda: env_int("BIG", 5, max_value=100, environ=env), "BIG"),
                           (lambda: env_int("FLOAT", 5, environ=env), "'8.0'")]:
            try:
                call()
                assert False
            except ValueError as e:
                assert text in str(e)
        """,
        hints=["Use `os.environ if environ is None else environ`, then `.get(name, \"\").strip()`.",
               "Convert with `int(raw)` inside `try` and re-raise a `ValueError` with your own message `from None`."],
        solution="""
        import os

        _TRUE = {"1", "true", "yes", "on"}
        _FALSE = {"0", "false", "no", "off"}


        def _raw(name, environ):
            env = os.environ if environ is None else environ
            return env.get(name, "").strip()


        def env_bool(name, default=False, environ=None):
            raw = _raw(name, environ)
            if not raw:
                return default
            if raw.lower() in _TRUE:
                return True
            if raw.lower() in _FALSE:
                return False
            raise ValueError(f"{name} must be a boolean (true/false, 1/0, yes/no, on/off), got {raw!r}")


        def env_int(name, default, min_value=None, max_value=None, environ=None):
            raw = _raw(name, environ)
            if not raw:
                return default
            try:
                value = int(raw)
            except ValueError:
                raise ValueError(f"{name} must be an integer, got {raw!r}") from None
            if min_value is not None and value < min_value or max_value is not None and value > max_value:
                raise ValueError(f"{name} must be between {min_value} and {max_value}, got {value}")
            return value
        """,
        why="""Parsing settings is validation (7.1): accept an explicit set of spellings, reject everything else with a message that names the variable and shows the bad value,
        so the operator knows exactly what to fix. Treating empty as missing matches how deployment tools often define unset variables (`KEY=`). Passing
        `environ` as a parameter, defaulting to `os.environ`, makes the functions testable with a plain dict and no global state. `int("8.0")` failing is
        deliberate: a fractional value for a count is a configuration mistake, not something to truncate quietly."""),
    fix("An API key in the source code", "easy", tag="GenAI",
        prompt="""`auth_headers` builds the headers for the model API with a key pasted into the code. Make it read the key from the `OPENAI_API_KEY` environment variable
        at call time, and raise `RuntimeError("OPENAI_API_KEY is not set")` if it is missing or empty.""",
        code="""
        import os

        API_KEY = "sk-proj-2pQ8...pasted-from-the-dashboard"

        def auth_headers():
            return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        """,
        tests="""
        import os
        os.environ["OPENAI_API_KEY"] = "sk-test-123"
        assert auth_headers() == {"Authorization": "Bearer sk-test-123", "Content-Type": "application/json"}
        os.environ["OPENAI_API_KEY"] = ""
        try:
            auth_headers()
            assert False
        except RuntimeError as e:
            assert str(e) == "OPENAI_API_KEY is not set"
        os.environ.pop("OPENAI_API_KEY")
        assert "API_KEY" not in globals()
        """,
        hints=["Delete the constant. `key = os.environ.get(\"OPENAI_API_KEY\")`, then check `if not key:`."],
        solution="""
        import os

        def auth_headers():
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set")
            return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        """,
        why="""A key in source code is in every clone, fork, code review, CI log and backup, and in the git history forever, even after the line is deleted; a key pasted
        into code that is pushed to a public repository is typically found by automated scanners within minutes. Reading it from the environment moves the
        secret to the deployment, where each environment can have its own key. Failing with a clear message when it is missing beats sending an
        unauthenticated request and debugging a 401. The official SDKs read `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` from the environment for the same reason."""),
    predict("What TOML gives you", "easy",
        code="""
        import tomllib

        doc = tomllib.loads('''
        title = "RAG service"
        path = 'C:\\\\new\\\\models'
        size = 1_000_000
        ratio = 5e-1
        started = 2025-03-01T09:30:00Z
        day = 2025-03-01
        model.name = "small"
        "quoted.key" = 1
        [server]
        port = 8080
        ''')
        print(sorted(doc), doc["size"], doc["ratio"])
        print(doc["path"], type(doc["started"]).__name__, doc["started"].tzinfo, repr(doc["day"]))
        print(doc["model"], doc["quoted.key"], doc["server"])
        """,
        hints=["Single-quoted TOML strings are literal: backslashes are kept. Dotted keys create nested tables; quoted keys do not."],
        why="""TOML values arrive with their types: an int with digit separators, a float, a timezone-aware `datetime` (the `Z` means UTC) and a `date`. A single-quoted
        string is literal, so the Windows path keeps its backslashes; in a double-quoted string, `\\n` would be a newline. `model.name` creates a nested
        table `model`, while the quoted `"quoted.key"` is a single key containing a dot. The `[server]` header creates another nested dict. The top-level keys
        are sorted here only to print them in a stable order."""),
)

section("medium", "Medium",
    write("Parse a .env file", "medium", tag="Data work",
        prompt="""Write `parse_dotenv(text)` returning a dict. Ignore blank lines and lines starting with `#`, and allow an `export ` prefix. Each other line is `KEY=VALUE`
        with a key matching `[A-Za-z_][A-Za-z0-9_]*` (spaces around `=` allowed). Values: in double quotes, `\\n` becomes a newline and `\\"` a quote; in single
        quotes, the text is literal; after a closing quote, only spaces or a `#` comment may follow. Unquoted values are stripped, and ` #` starts a comment (a
        `#` without a space before it is part of the value). Later keys override earlier ones. An invalid line or an unterminated quote raises
        `ValueError` starting with `f"line {n}: "`.""",
        code="""
        import re

        def parse_dotenv(text):
            pass
        """,
        tests="""
        text = r'''# local settings, never commit
        export OPENAI_API_KEY=sk-test-123
        MODEL = small  # the cheap one
        EMPTY=
        GREETING="Hello\\nWorld"
        QUOTED="say \\"hi\\" # not a comment"   # but this is
        RAW='no $expansion \\n here'
        URL=https://x.io/a#frag
        MODEL=large
        '''
        env = parse_dotenv("\\n".join(line.strip() for line in text.splitlines()))
        assert env == {"OPENAI_API_KEY": "sk-test-123", "MODEL": "large", "EMPTY": "", "GREETING": "Hello\\nWorld",
                       "QUOTED": 'say "hi" # not a comment', "RAW": r"no $expansion \\n here", "URL": "https://x.io/a#frag"}
        assert list(env)[:2] == ["OPENAI_API_KEY", "MODEL"]
        for bad, n in [("A=1\\nthis is not valid", 2), ('X="unterminated', 1), ("1KEY=v", 1), ("Y='a' extra", 1)]:
            try:
                parse_dotenv(bad)
                assert False, bad
            except ValueError as e:
                assert str(e).startswith(f"line {n}: "), str(e)
        """,
        hints=["Match the key part with `re.fullmatch(r\"(?:export\\s+)?([A-Za-z_][A-Za-z0-9_]*)\\s*=(.*)\", line)`.",
               "For a double-quoted value, walk the characters, handling a backslash followed by `n`, `\"` or `\\`; stop at the first unescaped `\"`.",
               "For an unquoted value, `re.split(r\"\\s#\", value, maxsplit=1)[0].strip()`."],
        solution="""
        import re

        _LINE = re.compile(r"(?:export\\s+)?([A-Za-z_][A-Za-z0-9_]*)\\s*=(.*)")
        _ESCAPES = {"n": "\\n", '"': '"', "\\\\": "\\\\"}


        def _rest_ok(rest):
            rest = rest.strip()
            return not rest or rest.startswith("#")


        def _value(raw, n):
            raw = raw.strip()
            if raw.startswith('"'):
                out, i = [], 1
                while i < len(raw):
                    ch = raw[i]
                    if ch == "\\\\" and i + 1 < len(raw) and raw[i + 1] in _ESCAPES:
                        out.append(_ESCAPES[raw[i + 1]])
                        i += 2
                        continue
                    if ch == '"':
                        if not _rest_ok(raw[i + 1:]):
                            raise ValueError(f"line {n}: unexpected text after closing quote")
                        return "".join(out)
                    out.append(ch)
                    i += 1
                raise ValueError(f"line {n}: unterminated double quote")
            if raw.startswith("'"):
                end = raw.find("'", 1)
                if end == -1:
                    raise ValueError(f"line {n}: unterminated single quote")
                if not _rest_ok(raw[end + 1:]):
                    raise ValueError(f"line {n}: unexpected text after closing quote")
                return raw[1:end]
            return re.split(r"\\s#", raw, maxsplit=1)[0].strip()


        def parse_dotenv(text):
            env = {}
            for n, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                m = _LINE.fullmatch(stripped)
                if not m:
                    raise ValueError(f"line {n}: expected KEY=VALUE")
                env[m.group(1)] = _value(m.group(2), n)
            return env
        """,
        why="""Writing the parser shows what the format really promises. Quotes exist so values can hold spaces, `#` and newlines; double quotes interpret a few escapes, single
        quotes nothing, which is why passwords with backslashes belong in single quotes. The comment rule (` #` needs a space before it) is what keeps URLs with
        fragments intact. Strict errors with line numbers turn a typo in a 40-line `.env` into a one-second fix. Dict insertion order keeps the first position of
        a key even when a later line overrides its value. Real loaders such as `python-dotenv` add variable expansion (`${HOME}`) and multi-line values, and,
        by default, do not override variables that are already set in the environment."""),
    write("Layer defaults, a TOML file and the environment", "medium", tag="ML",
        prompt="""Write `load_config(defaults, toml_text, environ, prefix="APP_")`. Start from a deep copy of `defaults`, deep-merge the parsed TOML into it (nested dicts merge
        key by key, other values replace), then apply every environment variable starting with `prefix`: the rest of the name, lower-cased and split on `__`,
        is the nested path (missing dicts are created), and the value is parsed as a TOML value when possible (`0.7`, `true`, `["a"]`), otherwise kept as a
        string. Return the result without changing `defaults`.""",
        code="""
        import copy, tomllib

        def load_config(defaults, toml_text, environ, prefix="APP_"):
            pass
        """,
        tests="""
        defaults = {"model": {"name": "small", "temperature": 0.0}, "retrieval": {"top_k": 5, "sources": ["faq"]}, "debug": False}
        toml_text = 'debug = true\\n[model]\\nname = "medium"\\n[retrieval]\\nsources = ["faq", "terms"]\\n'
        env = {"APP_MODEL__TEMPERATURE": "0.7", "APP_RETRIEVAL__TOP_K": "8", "APP_MODEL__NAME": "large", "APP_TAGS": '["a", "b"]',
               "APP_NOTE": "plain text", "APP_CACHE__REDIS__URL": "redis://cache:6379", "HOME": "/x"}
        cfg = load_config(defaults, toml_text, env)
        assert cfg == {"model": {"name": "large", "temperature": 0.7}, "retrieval": {"top_k": 8, "sources": ["faq", "terms"]}, "debug": True,
                       "tags": ["a", "b"], "note": "plain text", "cache": {"redis": {"url": "redis://cache:6379"}}}
        assert defaults["model"] == {"name": "small", "temperature": 0.0} and defaults["retrieval"]["sources"] == ["faq"]
        assert load_config(defaults, "", {})["retrieval"] is not defaults["retrieval"]
        """,
        hints=["A recursive `_merge(target, src)` that recurses when both sides are dicts and otherwise assigns a deep copy.",
               "Parse a single value with `tomllib.loads(f\"v = {raw}\")[\"v\"]` inside `try`, falling back to `raw` on `TOMLDecodeError`."],
        solution="""
        import copy, tomllib


        def _merge(target, src):
            for key, value in src.items():
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    _merge(target[key], value)
                else:
                    target[key] = copy.deepcopy(value)


        def _parse(raw):
            try:
                return tomllib.loads(f"v = {raw}")["v"]
            except tomllib.TOMLDecodeError:
                return raw


        def load_config(defaults, toml_text, environ, prefix="APP_"):
            cfg = copy.deepcopy(defaults)
            _merge(cfg, tomllib.loads(toml_text))
            for name, raw in environ.items():
                if not name.startswith(prefix):
                    continue
                *parents, last = name[len(prefix):].lower().split("__")
                node = cfg
                for part in parents:
                    node = node.setdefault(part, {})
                node[last] = _parse(raw)
            return cfg
        """,
        why="""Each layer is more specific than the last, so later layers win, but only for the keys they mention: the deep merge keeps the default temperature when the file
        changes only the model name. Lists are replaced, not concatenated, because "the sources are faq and terms" is one setting. The `__` convention maps
        flat variable names onto the nested structure, and parsing values as TOML gives them types for free while plain words stay strings; the trade-off is
        that a value such as `2025-01-01` becomes a date, so a validating model (11.4) should still check the final result. The deep copy keeps the module's
        defaults pristine, which matters when the loader runs more than once, as in tests."""),
    fix("A test helper that leaks environment changes", "medium", tag="Data work",
        prompt="""`temp_env(**changes)` should set environment variables for the duration of a `with` block, where a value of `None` means "unset it", and restore the exact
        previous state afterwards, even if the block raises. It crashes on `None` values, cannot restore variables that did not exist before, and restores
        nothing when the block fails. Fix it.""",
        code="""
        import os
        from contextlib import contextmanager

        @contextmanager
        def temp_env(**changes):
            old = {k: os.environ.get(k) for k in changes}
            for k, v in changes.items():
                os.environ[k] = v
            yield
            for k, v in old.items():
                os.environ[k] = v
        """,
        tests="""
        import os
        os.environ["F7_KEEP"] = "orig"
        os.environ["F7_GONE"] = "here"
        os.environ.pop("F7_NEW", None)
        def run():
            with temp_env(F7_KEEP="tmp", F7_NEW="x", F7_GONE=None):
                inside = (os.environ["F7_KEEP"], os.environ["F7_NEW"], "F7_GONE" in os.environ)
                raise KeyError("test failure inside the block")
        try:
            run()
        except KeyError:
            pass
        assert (os.environ.get("F7_KEEP"), os.environ.get("F7_GONE"), "F7_NEW" in os.environ) == ("orig", "here", False)
        with temp_env(F7_KEEP="tmp", F7_NEW="x", F7_GONE=None):
            assert (os.environ["F7_KEEP"], os.environ["F7_NEW"], "F7_GONE" in os.environ) == ("tmp", "x", False)
        assert os.environ["F7_KEEP"] == "orig" and "F7_NEW" not in os.environ
        """,
        hints=["Put the setting and the `yield` inside `try`, and the restoring loop in `finally`.",
               "Both directions need the same rule: a value of `None` means `os.environ.pop(k, None)`."],
        solution="""
        import os
        from contextlib import contextmanager

        def _apply(values):
            for k, v in values.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        @contextmanager
        def temp_env(**changes):
            old = {k: os.environ.get(k) for k in changes}
            try:
                _apply(changes)
                yield
            finally:
                _apply(old)
        """,
        why="""`os.environ` is process-wide state, so a test that changes it and does not restore it changes every later test, the source of failures that depend on test order.
        Recording the previous value as `None` for missing variables lets one rule handle both directions: `None` means "absent", so it is popped, never
        assigned (assigning `None` raises `TypeError`). The `finally` (10.2) restores the state even when the block fails, which is exactly when a test has
        failed and the next one must not inherit its mess. pytest's `monkeypatch.setenv` and `monkeypatch.delenv` (13.2) do this for you."""),
    choose("Reading a setting in a hot loop", "medium", tag="GenAI",
        prompt="Both need the temperature setting while scoring 20,000 candidates. Which is faster?",
        setup="""import os
os.environ["APP_TEMPERATURE"] = "0.2"
scores = [i / 20_000 for i in range(20_000)]""",
        options={
            "a": "out = [s * float(os.environ.get(\"APP_TEMPERATURE\", \"0\")) for s in scores]",
            "b": "t = float(os.environ.get(\"APP_TEMPERATURE\", \"0\"))\nout = [s * t for s in scores]",
        },
        answer="b",
        hints=["What does each `os.environ.get` and `float` call do, and how many happen in each option?"],
        why="""`os.environ` is not a plain dict: each lookup encodes the key, looks it up in the underlying bytes mapping and decodes the value, and then `float` parses the string,
        20,000 times in option A. Option B reads and parses once. Beyond speed, reading configuration once into a settings object is also the correct design:
        a value that could change halfway through a batch makes results inconsistent, and parsing at start-up surfaces bad values before any work is done."""),
    trace("Layering with ChainMap", "medium",
        prompt="Fill in `a` and `b` after each marked line.",
        code="""
        from collections import ChainMap

        defaults = {"model": "small", "top_k": 5, "debug": False}
        file_cfg = {"top_k": 8}
        env = {"model": "large"}
        cfg = ChainMap({}, env, file_cfg, defaults)

        a, b = cfg["model"], cfg["top_k"]  # row: "lookups"
        cfg["debug"] = True
        a, b = cfg.maps[0], defaults["debug"]  # row: "after a write"
        del env["model"]
        a, b = cfg["model"], len(cfg)  # row: "env changed"
        child = cfg.new_child({"top_k": 1})
        a, b = child["top_k"], cfg["top_k"]  # row: "child scope"
        """,
        trace_vars=["a", "b"],
        hints=["Lookups search the maps in order; writes and deletes only touch the first map. A ChainMap is a view, not a copy."],
        why="""`ChainMap` searches its maps in order, so the environment's model and the file's `top_k` win over the defaults. Writing goes to the first map only, the empty
        dict reserved for run-time overrides, and the defaults are untouched. Because it is a live view, deleting the key from `env` immediately exposes the
        default model; `len` counts distinct keys across all maps. `new_child` adds a map in front, a cheap way to create a temporary scope, without changing
        the parent."""),
    fix("Settings that print the API key", "medium", tag="GenAI",
        prompt="""`Settings` is logged at start-up with `log.info("settings: %s", settings)`, and the log contains the full API key. Add a `Secret` class that stores a string,
        shows `Secret('***')` as its `repr` and `***` as its `str`, and returns the real value from `get()`. `Settings` must still accept a plain string for
        `api_key` and wrap it in `__post_init__`; `headers()` keeps working.""",
        code="""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Settings:
            model: str
            api_key: str

            def headers(self):
                return {"Authorization": f"Bearer {self.api_key}"}
        """,
        tests="""
        key = "sk-live-abc123def456"
        s = Settings("small", key)
        assert key not in repr(s) and key not in str(s) and key not in f"{s} {s.api_key}" and key not in "%s %r" % (s, s)
        assert repr(s.api_key) == "Secret('***')" and str(s.api_key) == "***" and s.api_key.get() == key
        assert s.headers() == {"Authorization": f"Bearer {key}"} and Settings("small", Secret(key)).api_key.get() == key
        """,
        hints=["`Secret` with `__slots__ = (\"_value\",)`, `__repr__`, `__str__` and `get`.",
               "In a frozen dataclass, `__post_init__` must use `object.__setattr__(self, \"api_key\", Secret(self.api_key))`."],
        solution="""
        from dataclasses import dataclass


        class Secret:
            __slots__ = ("_value",)

            def __init__(self, value):
                self._value = value

            def get(self):
                return self._value

            def __repr__(self):
                return "Secret('***')"

            def __str__(self):
                return "***"


        @dataclass(frozen=True)
        class Settings:
            model: str
            api_key: Secret

            def __post_init__(self):
                if not isinstance(self.api_key, Secret):
                    object.__setattr__(self, "api_key", Secret(self.api_key))

            def headers(self):
                return {"Authorization": f"Bearer {self.api_key.get()}"}
        """,
        why="""Logging the settings object at start-up is a good habit, and the dataclass `repr` includes every field, so the key leaked into every log line, log file and
        log platform. A wrapper type makes the safe behaviour the default: `repr` and `str` (and therefore f-strings and `%s`) show a mask, and the real value
        requires an explicit `get()`, which is easy to spot in review. The frozen dataclass needs `object.__setattr__` to replace the field in `__post_init__`
        (11.3). Pydantic's `SecretStr` (`get_secret_value()`) is the same idea. The wrapper does not stop a determined `print(s.api_key.get())`; it stops the
        accidental leaks."""),
    write("A model registry in TOML", "medium", tag="GenAI",
        prompt="""Write `load_models(toml_text)` for a file with an optional `[defaults]` table and a `[[models]]` array. Return a dict from model name to its settings (defaults
        first, then the model's own keys), in file order. Allowed keys are `name`, `provider`, `context_window` and `cost_per_1k`; raise `ValueError` for a
        model without a name (`"model 2: missing name"`, counting from 1), a duplicate name (`"duplicate model 'x'"`), an unknown key
        (`"model 'x': unknown key 'k'"`), or a `context_window` that is not a positive int (`"model 'x': context_window must be a positive int"`). TOML syntax
        errors propagate.""",
        code="""
        import tomllib

        def load_models(toml_text):
            pass
        """,
        tests="""
        import tomllib
        text = '''
        [defaults]
        provider = "local"
        context_window = 8192

        [[models]]
        name = "small"

        [[models]]
        name = "large"
        provider = "cloud"
        context_window = 128_000
        cost_per_1k = 0.01
        '''
        models = load_models(text)
        assert list(models) == ["small", "large"]
        assert models["small"] == {"provider": "local", "context_window": 8192, "name": "small"}
        assert models["large"] == {"provider": "cloud", "context_window": 128000, "name": "large", "cost_per_1k": 0.01}
        cases = [('[[models]]\\nname = "a"\\n[[models]]\\nprovider = "x"', "model 2: missing name"),
                 ('[[models]]\\nname = "a"\\n[[models]]\\nname = "a"', "duplicate model 'a'"),
                 ('[[models]]\\nname = "a"\\ntemprature = 0.2', "model 'a': unknown key 'temprature'"),
                 ('[[models]]\\nname = "a"\\ncontext_window = "8k"', "model 'a': context_window must be a positive int"),
                 ('[[models]]\\nname = "a"\\ncontext_window = true', "model 'a': context_window must be a positive int")]
        for bad, msg in cases:
            try:
                load_models(bad)
                assert False, bad
            except ValueError as e:
                assert str(e) == msg, str(e)
        assert load_models("") == {}
        try:
            load_models("[[models]\\nname = 1")
            assert False
        except tomllib.TOMLDecodeError:
            pass
        """,
        hints=["`data.get(\"defaults\", {})` and `data.get(\"models\", [])`; merge with `{**defaults, **model}`.",
               "`True` is an `int` in Python, so check `isinstance(v, bool)` too."],
        solution="""
        import tomllib

        ALLOWED = {"name", "provider", "context_window", "cost_per_1k"}


        def load_models(toml_text):
            data = tomllib.loads(toml_text)
            defaults = data.get("defaults", {})
            models = {}
            for i, entry in enumerate(data.get("models", []), start=1):
                name = entry.get("name")
                if not name:
                    raise ValueError(f"model {i}: missing name")
                if name in models:
                    raise ValueError(f"duplicate model {name!r}")
                merged = {**defaults, **entry}
                for key in merged:
                    if key not in ALLOWED:
                        raise ValueError(f"model {name!r}: unknown key {key!r}")
                window = merged.get("context_window")
                if window is not None and (not isinstance(window, int) or isinstance(window, bool) or window <= 0):
                    raise ValueError(f"model {name!r}: context_window must be a positive int")
                models[name] = merged
            return models
        """,
        why="""TOML's typed values and `[[array of tables]]` make a registry like this readable and diff-friendly, and the defaults table removes repetition. Parsing is not
        validation, though: TOML happily accepts a misspelt `temprature` or `"8k"` for a size, so the loader checks names, uniqueness, allowed keys and value
        types, with messages that point at the model. Checking the **merged** settings means defaults are validated too. In a larger system this is where a
        Pydantic model (11.4) would take over; the shape of the code stays the same: parse, merge, validate, then hand out trusted objects."""),
    predict("Merging nested settings", "medium",
        code="""
        from collections import ChainMap

        base = {"model": {"name": "small", "temperature": 0.0}, "tags": ["a"]}
        override = {"model": {"name": "large"}}
        print({**base, **override})
        print(base | override == {**base, **override})
        merged = dict(base)
        merged["tags"].append("b")
        print(base["tags"])
        cm = ChainMap(override, base)
        print(cm["model"], cm["tags"])
        child = cm.new_child()
        child["tags"] = []
        print(cm["tags"], child["tags"], len(child.maps))
        """,
        hints=["Unpacking and `|` are shallow merges; `dict(base)` is a shallow copy; ChainMap finds the first map with the key."],
        why="""Shallow merges replace the whole `model` section, so the default temperature silently disappears, the bug deep merges exist to prevent; `|` gives the same
        result as unpacking. `dict(base)` copies the outer dict only, so appending to `merged["tags"]` changes the list shared with `base`. ChainMap does not
        merge either: it returns the first map's `model` as a whole. Writing `tags` in the child goes to the child's own new first map, leaving the parent
        unchanged, and the child has three maps."""),
)

section("hard", "Hard",
    write("Scan text for secrets before committing", "hard", tag="GenAI",
        prompt="""Write `scan_for_secrets(text, min_entropy=4.5)` returning a sorted list of `(line_number, kind)` findings, like a pre-commit hook. Kinds, by regex: `openai_key`
        (`sk-` then at least 20 of `[A-Za-z0-9_-]`), `aws_access_key` (`AKIA` then 16 of `[0-9A-Z]`), `private_key` (`-----BEGIN ... PRIVATE KEY-----`), and
        `password_assignment` (`password`, `passwd`, `secret`, `api_key` or `token`, any case, then `=` or `:`, then a quoted value of at least 6 characters).
        Then, on lines with no regex finding, any token of 24 or more `[A-Za-z0-9+/=_-]` characters whose Shannon entropy (`entropy(s)`, bits per character)
        is at least `min_entropy` is a `high_entropy` finding (once per line). Lines containing `# allow-secret` are skipped.""",
        code="""
        import math, re
        from collections import Counter

        def entropy(s):
            pass

        def scan_for_secrets(text, min_entropy=4.5):
            pass
        """,
        tests="""
        text = '''import os
        OPENAI_KEY = "sk-proj-A1b2C3d4E5f6G7h8I9j0K1l2M3"
        aws = "AKIAIOSFODNN7EXAMPLE"
        db_password = "hunter2-prod"
        config = {"Token": 'abc'}
        TOKEN = os.environ["TOKEN"]
        webhook = "Zx8Qp2Lm9Rt4Vb7Nc1Kd6Hf3Jg5Ws0Ye"
        name = "process_customer_complaints_in_batches"
        digest = "0123456789abcdef0123456789abcdef"
        test_key = "sk-test-FAKEFAKEFAKEFAKEFAKE"  # allow-secret
        -----BEGIN RSA PRIVATE KEY-----
        '''
        assert abs(entropy("aabb") - 1.0) < 1e-9 and entropy("aaaa") == 0 and entropy("") == 0
        assert scan_for_secrets(text) == [(2, "openai_key"), (3, "aws_access_key"), (4, "password_assignment"), (7, "high_entropy"), (11, "private_key")]
        assert (9, "high_entropy") in scan_for_secrets(text, min_entropy=3.9) and scan_for_secrets("") == []
        """,
        hints=["`entropy`: `-sum(p * math.log2(p))` over the character frequencies `p = count / len(s)`.",
               "Keep the patterns in a list of `(kind, compiled_regex)` and use `search` per line; collect findings in a set and return `sorted(...)`."],
        solution="""
        import math, re
        from collections import Counter

        PATTERNS = [
            ("openai_key", re.compile(r"\\bsk-[A-Za-z0-9_-]{20,}")),
            ("aws_access_key", re.compile(r"\\bAKIA[0-9A-Z]{16}\\b")),
            ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
            ("password_assignment", re.compile(r"(?i)(?:password|passwd|secret|api_key|token)\\w*['\\"]?\\s*[:=]\\s*['\\"][^'\\"]{6,}['\\"]")),
        ]
        TOKEN = re.compile(r"[A-Za-z0-9+/=_-]{24,}")


        def entropy(s):
            if not s:
                return 0.0
            n = len(s)
            return -sum(c / n * math.log2(c / n) for c in Counter(s).values())


        def scan_for_secrets(text, min_entropy=4.5):
            findings = set()
            for n, line in enumerate(text.splitlines(), start=1):
                if "# allow-secret" in line:
                    continue
                hits = {kind for kind, pattern in PATTERNS if pattern.search(line)}
                findings.update((n, kind) for kind in hits)
                if not hits and any(entropy(tok) >= min_entropy for tok in TOKEN.findall(line)):
                    findings.add((n, "high_entropy"))
            return sorted(findings)
        """,
        why="""Secret scanners combine two signals. **Patterns** catch secrets with a known shape, such as provider key prefixes and private-key headers, with few false
        alarms, and an assignment pattern catches hard-coded passwords while ignoring `os.environ["TOKEN"]` (no quoted literal) and short dummy values.
        **Entropy** catches unknown formats: random keys use many different characters evenly, so they score near `log2` of their length (5.0 for the 32
        distinct characters here), while identifiers and English score lower (the long function name is about 3.8). The threshold is a trade-off: hex digests
        score about 4.0, so lowering it to 3.9 flags line 9, a false alarm for a checksum but a hit for a hex-encoded key. An explicit allow marker keeps test
        fixtures from blocking every commit. Real tools (`gitleaks`, `detect-secrets`, GitHub push protection) add hundreds of provider patterns and run on
        every commit and push."""),
    write("Explain where each setting came from", "hard", tag="Data work",
        prompt="""Write `resolve(layers)` where `layers` is a list of `(name, dict)` from lowest to highest precedence. Deep-merge them (nested dicts merge; anything else,
        including lists and a dict replacing a scalar or the reverse, replaces) and return `(merged, origin)`, where `origin` maps the dotted path of every leaf
        value in `merged` to the name of the layer that set it, with keys sorted. When a layer replaces a section, origins of the old leaves under it are
        removed. Do not modify the inputs.""",
        code="""
        import copy

        def resolve(layers):
            pass
        """,
        tests="""
        defaults = {"model": {"name": "small", "temperature": 0.0, "limits": {"rpm": 60}}, "retrieval": {"top_k": 5, "sources": ["faq"]}, "debug": False}
        file_cfg = {"model": {"name": "large"}, "retrieval": {"sources": ["faq", "terms"]}}
        env = {"model": {"limits": {"rpm": 600, "tpm": 90000}}, "debug": True}
        cli = {"retrieval": "disabled"}
        merged, origin = resolve([("defaults", defaults), ("config.toml", file_cfg), ("env", env), ("cli", cli)])
        assert merged == {"model": {"name": "large", "temperature": 0.0, "limits": {"rpm": 600, "tpm": 90000}}, "retrieval": "disabled", "debug": True}
        assert origin == {"debug": "env", "model.limits.rpm": "env", "model.limits.tpm": "env", "model.name": "config.toml",
                          "model.temperature": "defaults", "retrieval": "cli"}
        assert list(origin) == sorted(origin) and defaults["retrieval"] == {"top_k": 5, "sources": ["faq"]} and env["model"]["limits"] == {"rpm": 600, "tpm": 90000}
        merged2, origin2 = resolve([("a", {"x": 1}), ("b", {"x": {"y": [1]}})])
        merged2["x"]["y"].append(2)
        assert origin2 == {"x.y": "b"} and resolve([])[0] == {} and resolve([("b", {"x": {"y": [1]}})])[0] == {"x": {"y": [1]}}
        """,
        hints=["A recursive `_merge(target, src, name, origin, prefix)`; when both values are dicts, recurse; otherwise drop origins equal to the path or starting with `path + \".\"`, then assign.",
               "When the new value is a dict replacing a non-dict, assign `{}` and recurse into it so its leaves get origins."],
        solution="""
        import copy


        def _drop(origin, dotted):
            for key in [k for k in origin if k == dotted or k.startswith(dotted + ".")]:
                del origin[key]


        def _merge(target, src, name, origin, prefix):
            for key, value in src.items():
                path = prefix + (key,)
                dotted = ".".join(path)
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    _merge(target[key], value, name, origin, path)
                    continue
                _drop(origin, dotted)
                if isinstance(value, dict):
                    target[key] = {}
                    _merge(target[key], value, name, origin, path)
                else:
                    target[key] = copy.deepcopy(value)
                    origin[dotted] = name


        def resolve(layers):
            merged, origin = {}, {}
            for name, layer in layers:
                _merge(merged, layer, name, origin, ())
            return merged, dict(sorted(origin.items()))
        """,
        why=""""Why is production using 600 requests per minute?" is answered by `origin["model.limits.rpm"]`, the same idea as `git config --show-origin` and the `--show`
        options of many CLI tools. Tracking provenance per **leaf** is what makes it precise: a file that overrides only `model.name` leaves
        `model.temperature` attributed to the defaults. Replacements must clean up: when the command line turns the whole `retrieval` section into a string, the
        old `retrieval.top_k` and `retrieval.sources` entries would otherwise claim values that no longer exist. Building fresh dicts and deep-copying leaves
        means the merged result shares nothing with the layers, so appending to a merged list cannot change the configuration it came from."""),
    fix("Read the code: a settings module", "hard", tag="GenAI",
        prompt="""This settings module reads the environment once at import, so changes made later (in tests, or after loading a `.env` file) are ignored; `APP_DEBUG=false`
        turns debug on; `APP_TIMEOUT=2.5` stays a string; an empty `APP_ORIGINS` gives `[""]`; and callers that modify the returned dict change it for everyone.
        Replace it with `get_settings(environ=None)` that reads `environ` (default `os.environ`) **at call time** and returns a **new** dict each call: `model`
        (default `"small"`), `debug` (strict booleans as in problem 2, default `False`), `timeout` (a float > 0, default 30.0) and `origins` (comma-separated,
        stripped, empty items dropped, default `[]`). Invalid values raise `ValueError`.""",
        code="""
        import os

        SETTINGS = {
            "model": os.getenv("APP_MODEL", "small"),
            "debug": bool(os.getenv("APP_DEBUG", False)),
            "timeout": os.getenv("APP_TIMEOUT", 30),
            "origins": os.getenv("APP_ORIGINS", "").split(","),
        }


        def get_settings():
            return SETTINGS
        """,
        tests="""
        import os
        assert get_settings({}) == {"model": "small", "debug": False, "timeout": 30.0, "origins": []}
        s = get_settings({"APP_DEBUG": "false", "APP_TIMEOUT": "2.5", "APP_ORIGINS": " https://a.io, https://b.io,", "APP_MODEL": "medium"})
        assert s == {"model": "medium", "debug": False, "timeout": 2.5, "origins": ["https://a.io", "https://b.io"]}
        os.environ["APP_MODEL"] = "large"
        assert get_settings()["model"] == "large"
        os.environ.pop("APP_MODEL")
        first = get_settings({})
        first["origins"].append("https://evil.io")
        assert get_settings({})["origins"] == [] and get_settings({"APP_DEBUG": "ON"})["debug"] is True
        for bad in [{"APP_DEBUG": "maybe"}, {"APP_TIMEOUT": "0"}, {"APP_TIMEOUT": "fast"}, {"APP_TIMEOUT": "-1"}]:
            try:
                get_settings(bad)
                assert False, bad
            except ValueError:
                pass
        """,
        hints=["Move all reading into the function; build and return a fresh dict.",
               "Parse the timeout with `float(raw)` in `try`, then check `> 0`; for origins, `[o.strip() for o in raw.split(\",\") if o.strip()]`."],
        solution="""
        import os

        _TRUE = {"1", "true", "yes", "on"}
        _FALSE = {"0", "false", "no", "off"}


        def _bool(raw, name):
            value = raw.strip().lower()
            if value in _TRUE:
                return True
            if value in _FALSE:
                return False
            raise ValueError(f"{name} must be a boolean, got {raw!r}")


        def get_settings(environ=None):
            env = os.environ if environ is None else environ
            debug_raw = env.get("APP_DEBUG", "").strip()
            timeout_raw = env.get("APP_TIMEOUT", "").strip()
            try:
                timeout = float(timeout_raw) if timeout_raw else 30.0
            except ValueError:
                raise ValueError(f"APP_TIMEOUT must be a number, got {timeout_raw!r}") from None
            if timeout <= 0:
                raise ValueError(f"APP_TIMEOUT must be positive, got {timeout}")
            return {
                "model": env.get("APP_MODEL", "small"),
                "debug": _bool(debug_raw, "APP_DEBUG") if debug_raw else False,
                "timeout": timeout,
                "origins": [o.strip() for o in env.get("APP_ORIGINS", "").split(",") if o.strip()],
            }
        """,
        why="""Every bug comes from treating configuration as constants. Module-level reads freeze the environment as it was at the first import, so tests that set variables,
        and a `.env` loaded after the import, have no effect; reading at call time (and, in an application, calling once at start-up and passing the result
        around) fixes that. The parsing bugs are the string traps of this lesson: `bool("false")` is `True`, a timeout that stays `"2.5"` breaks the HTTP client
        later and far away, and `"".split(",")` is `[""]`, which would allow an empty origin in a CORS list. Returning the same global dict let any caller
        change everyone's settings; a fresh dict (or a frozen dataclass or Pydantic model) removes that shared mutable state (9.1)."""),
)

section("interview", "Interview questions",
    explain("How do you manage API keys and other secrets for an LLM application across development, CI and production?", "medium", tag="Interview",
        why="""Secrets never live in code, notebooks or committed files. In **development**, each developer keeps their own keys in a git-ignored `.env` file (with a committed
        `.env.example` listing the names), loaded into the environment by the tooling. In **CI**, keys are stored as the CI system's encrypted secrets, exposed
        only to the jobs that need them and masked in logs; tests mostly use fakes, so few jobs need real keys. In **production**, a secret manager (AWS Secrets
        Manager, Azure Key Vault, GCP Secret Manager, Vault) stores them, and the platform injects them as environment variables or mounted files, or the
        application fetches them at start-up with its own identity, with access logged. Across all three: separate keys per environment and service, least
        privilege and spending limits on each key, regular rotation (two valid keys during a switch), masked types so settings can be logged safely, and secret
        scanning in pre-commit hooks and on push. The application reads everything once into a validated settings object at start-up and fails fast if a
        required secret is missing."""),
    explain("Why is configuration usually passed through environment variables, and what are their downsides?", "medium", tag="Interview",
        why="""Environment variables are supported by every operating system, language, container runtime, CI system and cloud platform, so the same build artefact (a
        Docker image, say) can run anywhere and only its environment changes, which is the "twelve-factor" principle of strict separation of config from code.
        They are easy to override for one run and are not committed by accident the way files are. Their downsides: everything is a flat string, so types and
        nesting need conventions and careful parsing; there is no schema, so typos (`APP_TEMPRATURE`) are silently ignored unless the loader rejects unknown
        prefixed variables; they are inherited by child processes and can show up in crash reports, debug pages and `/proc` listings, so they are not perfect for
        secrets; and long structured settings are unreadable as variables. Hence the usual combination: typed defaults in code, a committed TOML or YAML file
        for structured non-secret settings, environment variables for per-deployment values and secrets, all validated into one settings object."""),
    explain("A teammate just pushed a commit containing a production API key. What do you do?", "hard", tag="Interview",
        why="""Treat the key as compromised the moment it was pushed, because public repositories are scanned by bots within minutes and private ones are copied to clones, forks,
        CI caches and backups. First **revoke or rotate the key** at the provider, deploy the new key from the secret manager, and confirm the old one no longer works;
        this is the only step that actually stops misuse. Then check the provider's usage logs and billing for activity since the push, and follow the incident
        process if anything is suspicious. Next, clean up: remove the key from the code and read it from the environment, and if needed rewrite history (`git
        filter-repo` or BFG) and ask the hosting provider to purge cached views, knowing this only reduces exposure. Finally prevent a repeat: enable push
        protection and secret scanning on the repository, add a pre-commit scanner, move the value into the secret manager, and review why the key was in a file in
        the first place. Blameless and quick beats perfect and slow: rotation first, investigation second."""),
)

recap(
    "Keep configuration outside the code: defaults in code, non-secret structure in TOML, per-deployment values and secrets in the environment.",
    "`os.environ` holds strings only: parse strictly (`bool(\"false\")` is `True`), treat empty versus missing deliberately, and read at start-up, not at import.",
    "`.env` files are for local development and are git-ignored; `tomllib` reads typed TOML (binary mode for files) but does not write it.",
    "Layer with a deep merge (or `ChainMap` for flat settings), map `APP_SECTION__KEY` variables to nested keys, and be able to say where each value came from.",
    "Never put secrets in code, logs or reprs; use masked types, secret managers, scanning, least privilege and rotation, and rotate first when a key leaks.",
)
