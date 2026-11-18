from lesson import *

lesson(
    id="m8-4", num="8.4", title="Registration decorators",
    intro="Decorators that record a function instead of wrapping it: registries, plugin systems, routers and agent tool "
          "lists. How frameworks such as FastAPI and agent libraries read a function's signature and type hints with "
          "`inspect`, turn them into schemas, and dispatch calls by name or by type with `functools.singledispatch`. "
          "Applied to building tool schemas for an LLM and a small URL router.",
    desc="How `@app.get` and agent tool registries work, `inspect.signature`, schemas and dispatch.",
    keys="registry registration decorator plugin router route dispatch tool calling schema json schema inspect signature parameter kind annotation get_type_hints docstring singledispatch import time fastapi agent",
)

term("Registry", "A dict (or object) that collects functions under names, filled by a decorator at import time and used later to look them up.")
term("Dispatch", "Choosing which function to run for a request: by name (a tool call, a URL) or by type (`functools.singledispatch`).")
term("Signature", "A function's parameters, with their kinds, defaults and annotations, as returned by `inspect.signature(func)`.")
term("Tool schema", "A JSON description of a function (name, description, parameter types) that tells an LLM how to call it.")

section("register", "Decorators that register",
    p("""Not every decorator wraps. A **registration decorator** records the function somewhere and returns it **unchanged**. There is
    no wrapper, no extra cost per call and nothing that can break the function; the only effect is that, from the moment the module
    is imported, the function is listed in a **registry**: usually a dict from a name to the function. Later code looks functions up
    in the registry instead of importing them by name, which is how plugin systems, command-line tools, routers and agent tool lists
    work."""),
    ex("""
    TOOLS = {}

    def tool(func):
        if func.__name__ in TOOLS:
            raise ValueError(f"duplicate tool {func.__name__!r}")
        TOOLS[func.__name__] = func
        return func                        # unchanged: registration only

    @tool
    def search(query):
        return [f"doc about {query}"]

    @tool
    def get_weather(city):
        return f"sunny in {city}"

    print(list(TOOLS))
    print(TOOLS["search"]("refunds"), TOOLS["search"] is search)
    """, "registry.py"),
    p("""Registration happens at **definition time** (8.1): the registry is complete as soon as the module has been imported, before any
    function is called. That has two consequences. A function in a module that is **never imported** is never registered, which is
    why frameworks either import your modules for you (scanning a package) or ask you to import them in one place. And registration
    is a side effect of importing, so a registry should detect duplicates (two tools named `search` would otherwise overwrite each
    other silently) and tests should use a fresh registry rather than a global one."""),
    p("""Often the registered name differs from the function name, or the registration needs metadata (a description, a URL, an HTTP
    method). Then the registration decorator becomes a factory (8.2): `@tool(name="web_search", description="...")`. Frameworks put
    that factory on an object that owns the registry, which is what `app` is in `@app.get("/users/{id}")`: the method `get` is a
    decorator factory, and `app` holds the routing table it fills. (Module 9 shows how such objects are built; a closure over a dict
    does the same job, as below.)"""),
    ex("""
    def make_registry():
        entries = {}

        def register(name=None, **meta):
            def decorator(func):
                key = name or func.__name__
                if key in entries:
                    raise ValueError(f"{key!r} is already registered")
                entries[key] = {"func": func, **meta}
                return func
            return decorator

        return entries, register

    commands, command = make_registry()

    @command(help="Rebuild the vector index")
    def reindex():
        return "reindexed"

    @command(name="eval", help="Run the evaluation suite")
    def run_eval():
        return "evaluated"

    for key, entry in commands.items():
        print(key, "-", entry["help"], "->", entry["func"]())
    """, "registry_factory.py"),
)

section("signature", "Reading a function: `inspect.signature`",
    p("""Once functions are registered, frameworks want to know **how to call them**. `inspect.signature(func)` returns a `Signature`
    object whose `parameters` maps each parameter name to a `Parameter` with a **kind**, a **default** and an **annotation**. The kind
    says how the parameter can be passed: `POSITIONAL_OR_KEYWORD` (an ordinary parameter), `KEYWORD_ONLY` (after `*`),
    `VAR_POSITIONAL` (`*args`), `VAR_KEYWORD` (`**kwargs`) and `POSITIONAL_ONLY` (before `/`). A missing default or annotation is
    `inspect.Parameter.empty`."""),
    ex("""
    import inspect

    def search(query: str, k: int = 5, *, filters: dict | None = None, **extra) -> list:
        \"\"\"Search the knowledge base.\"\"\"
        return []

    sig = inspect.signature(search)
    for name, p in sig.parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            default = "-"
        else:
            default = "required" if p.default is p.empty else repr(p.default)
        annotation = "-" if p.annotation is p.empty else p.annotation
        print(f"{name:8} {p.kind.name:22} {default:9} {annotation}")
    print(sig.return_annotation, "|", inspect.getdoc(search))
    """, "signature.py"),
    p("""Three tools on top of this are worth knowing. `sig.bind(*args, **kwargs)` checks a call against the signature without
    calling the function and maps every value to its parameter (used in 7.3 and 8.2). `inspect.getdoc(func)` returns the docstring
    with indentation cleaned up. And `typing.get_type_hints(func)` returns the annotations as real types: when a module starts with
    `from __future__ import annotations`, or an annotation is written as a string, `p.annotation` is just the **text** `"int"`, and
    `get_type_hints` evaluates it into the type `int` (problem 10)."""),
    ex("""
    import inspect, typing

    def count(text: "str", top: "int" = 3) -> "list[str]":
        return text.split()[:top]

    print([p.annotation for p in inspect.signature(count).parameters.values()])
    hints = typing.get_type_hints(count)
    print(hints, hints["return"] == list[str])
    print(typing.get_origin(list[str]), typing.get_args(list[str]), typing.get_args(int | None))
    """, "type_hints.py"),
    p("""`typing.get_origin` and `typing.get_args` take generic types apart: `list[str]` has origin `list` and argument `str`, and
    `int | None` has the arguments `int` and `NoneType`. Module 11 explains these types in full; for reading signatures, these two
    functions are all you need."""),
)

section("schemas", "From a function to a tool schema",
    p("""LLM tool calling (function calling) works by sending the model a **schema** for each tool: its name, a description, and a JSON
    Schema for its parameters. The model then replies with a tool name and JSON arguments, and your code calls the function. Writing
    those schemas by hand duplicates information the function already contains, so agent libraries generate them from the function:
    the name from `__name__`, the description from the docstring, the parameter types from the type hints, and the `required` list
    from the parameters without defaults. That is what `@tool` in LangChain, `@function_tool` in the OpenAI Agents SDK and similar
    decorators do."""),
    ex("""
    import inspect, typing

    JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}

    def schema_for(func):
        hints = typing.get_type_hints(func)
        props, required = {}, []
        for name, p in inspect.signature(func).parameters.items():
            props[name] = {"type": JSON_TYPES[hints[name]]}
            if p.default is p.empty:
                required.append(name)
        doc = inspect.getdoc(func) or ""
        return {"name": func.__name__, "description": doc.split("\\n")[0],
                "parameters": {"type": "object", "properties": props, "required": required}}

    def get_order(order_id: int, include_items: bool = False) -> dict:
        \"\"\"Look up an order by its id.

        Returns status and, optionally, the items.
        \"\"\"
        return {}

    import json
    print(json.dumps(schema_for(get_order), indent=1))
    """, "tool_schema.py"),
    p("""Two lessons follow from this. The docstring and type hints of a tool are **part of the prompt**: the model only knows what the
    schema says, so a vague first line or a missing type makes it call the tool wrongly. And the schema is generated at import time
    from the code, so it cannot drift away from the function, which is the main argument for generating rather than hand-writing
    it (problem 5). Real implementations also handle `list[...]`, optional types, enums (`Literal`, 11.2) and descriptions per
    parameter, often by building a Pydantic model from the signature (11.4)."""),
)

section("dispatch", "Dispatching calls",
    p("""A registry is useful because of **dispatch**: given a name (from a tool call, a URL, a command line), look up the function and
    call it with the arguments. Dispatch code is a boundary in the sense of 7.3: names and arguments come from outside (a user, a
    model), so unknown names and bad arguments are expected, and should produce clear errors, not tracebacks. A dict lookup also
    replaces long `if`/`elif` chains that compare a command against every known name in turn (problem 8)."""),
    ex("""
    import inspect

    TOOLS = {}

    def tool(func):
        TOOLS[func.__name__] = func
        return func

    @tool
    def add(a: int, b: int) -> int:
        return a + b

    def dispatch(name, args):
        func = TOOLS.get(name)
        if func is None:
            return {"error": f"unknown tool {name!r}; available: {sorted(TOOLS)}"}
        try:
            inspect.signature(func).bind(**args)
        except TypeError as e:
            return {"error": f"bad arguments for {name}: {e}"}
        return {"result": func(**args)}

    print(dispatch("add", {"a": 2, "b": 3}))
    print(dispatch("mul", {"a": 2}))
    print(dispatch("add", {"a": 2, "c": 3}))
    """, "dispatch.py"),
    p("""The standard library has a different kind of dispatch built on registration: **`functools.singledispatch`** picks an
    implementation by the **type of the first argument**. You decorate a default function, then register specialised versions with
    `@func.register`; at call time it finds the most specific registered type in the argument's class hierarchy. It replaces chains of
    `isinstance` checks, and other modules can add support for their own types without editing the original function."""),
    ex("""
    import functools

    @functools.singledispatch
    def to_text(value):
        return str(value)

    @to_text.register
    def _(value: float):
        return f"{value:.2f}"

    @to_text.register
    def _(value: list):
        return ", ".join(to_text(v) for v in value)

    @to_text.register
    def _(value: dict):
        return "; ".join(f"{k}={to_text(v)}" for k, v in value.items())

    print(to_text({"score": 0.91234, "tags": ["eu", 3, 1.5], "ok": True}))
    print(sorted(t.__name__ for t in to_text.registry))
    """, "singledispatch.py"),
    p("""The registered type comes from the annotation of the first parameter (or from `@to_text.register(float)`). Dispatch follows
    inheritance: `bool` is a subclass of `int` (1.2), so with an `int` handler registered and no `bool` handler, `True` would use the
    `int` one (problem 12). The function called `_` is a convention for "the name does not matter", because the implementations are
    reached through the registry, never by name."""),
)

section("pitfalls", "Registration pitfalls",
    p("""Four problems come up with registries in real projects."""),
    p("""- **Nothing registered.** The decorated functions live in a module that nobody imports, so the registry is empty. Import all
      plugin modules from one place (an `__init__.py` or a `load_plugins()` function, 15.1), or use package entry points.
    - **Registering the wrong object.** With stacked decorators, a registration decorator records whatever it receives. Placed
      **below** a wrapping decorator such as `@timed`, it registers the undecorated function, so calls through the registry skip the
      timing. Put registration **outermost** so it records the final, fully decorated function (problem 6).
    - **Silent overwrites.** Two functions registered under one name: the second replaces the first, and calls quietly go to the
      wrong place. Raise on duplicates, or log a warning, deliberately.
    - **Registering at call time.** If the registration line is inside the wrapper instead of the decorator body, nothing is
      registered until the first call, which is too late for a router or a tool list (problem 14)."""),
    ex("""
    import functools

    REGISTRY = {}
    CALLS = []

    def register(func):
        REGISTRY[func.__name__] = func
        return func

    def timed(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            CALLS.append(func.__name__)
            return func(*args, **kwargs)
        return wrapper

    @timed
    @register              # registers the plain function: the registry bypasses @timed
    def wrong():
        return "w"

    @register              # registers the timed wrapper
    @timed
    def right():
        return "r"

    REGISTRY["wrong"](); REGISTRY["right"]()
    print(CALLS, REGISTRY["right"] is right, REGISTRY["wrong"] is wrong)
    """, "register_order.py"),
)

section("warmup", "Warm-up",
    predict("A registry fills at import time", "easy",
        code="""
        HANDLERS = {}

        def handles(event):
            def decorator(func):
                print("registering", func.__name__, "for", event)
                HANDLERS.setdefault(event, []).append(func)
                return func
            return decorator

        @handles("signup")
        def send_welcome(user):
            return f"welcome {user}"

        @handles("signup")
        @handles("login")
        def audit(user):
            return f"audit {user}"

        print({k: [f.__name__ for f in v] for k, v in HANDLERS.items()})
        print([f("ana") for f in HANDLERS["signup"]], audit("bo"))
        """,
        hints=["Each decorator runs once when its `def` executes; stacked ones run bottom-up and both receive the same function."],
        why="""The registrations print while the module is being defined, before any handler runs. `audit` is registered twice: first for
        `"login"` (the lower decorator), then for `"signup"`, and since `handles` returns the function unchanged, both entries hold the
        same object and `audit` is still callable normally. Lists keep registration order, so `send_welcome` comes first for
        `"signup"`."""),
    write("A registry with names and duplicate checks", "easy", tag="GenAI",
        prompt="""Write a decorator factory `register(name=None)` that stores the function in the global dict `PROMPTS` under `name`
        (or the function's own name), raises `ValueError` if that key is already taken, and returns the function unchanged.""",
        code="""
        PROMPTS = {}

        def register(name=None):
            pass
        """,
        tests="""
        @register()
        def summarise(text):
            return f"Summarise: {text}"

        @register(name="qa")
        def question_answer(context, question):
            return f"{context}\\nQ: {question}"

        assert sorted(PROMPTS) == ["qa", "summarise"]
        assert PROMPTS["qa"] is question_answer and summarise("x") == "Summarise: x"
        try:
            @register(name="summarise")
            def other(text):
                return text
            assert False
        except ValueError as e:
            assert "summarise" in str(e)
        assert PROMPTS["summarise"] is summarise
        """,
        hints=["The factory returns a `decorator(func)` that computes `key = name or func.__name__`."],
        solution="""
        PROMPTS = {}

        def register(name=None):
            def decorator(func):
                key = name or func.__name__
                if key in PROMPTS:
                    raise ValueError(f"prompt {key!r} is already registered")
                PROMPTS[key] = func
                return func
            return decorator
        """,
        why="""Returning `func` unchanged means the decorated function behaves exactly as before and is still importable by its own name, while
        the registry offers lookup by a stable key. The duplicate check fails at import time, which is when a copy-pasted
        `@register(name="summarise")` would otherwise silently replace the real one. A prompt registry like this lets an application
        select prompt templates by name from configuration, and makes it easy to list every prompt for review or evaluation."""),
    fix("A registration decorator that loses the function", "easy", tag="Data work",
        prompt="""After decoration, `clean_text` is `None`, although the registry holds it. Fix the decorator.""",
        code="""
        STEPS = []

        def step(func):
            STEPS.append(func)

        @step
        def clean_text(s):
            return " ".join(s.split())

        @step
        def lowercase(s):
            return s.lower()
        """,
        tests="""
        assert clean_text("  Hello   World ") == "Hello World"
        assert [f.__name__ for f in STEPS] == ["clean_text", "lowercase"]
        out = "  Refund   POLICY "
        for f in STEPS:
            out = f(out)
        assert out == "refund policy"
        """,
        hints=["Whatever the decorator returns is bound to the name (8.1)."],
        solution="""
        STEPS = []

        def step(func):
            STEPS.append(func)
            return func

        @step
        def clean_text(s):
            return " ".join(s.split())

        @step
        def lowercase(s):
            return s.lower()
        """,
        why="""Without a `return`, the decorator returns `None`, and `@step` binds the name to that. The registry still worked, which hides the
        problem until someone calls the function directly. A registration decorator must return the function it received. The registry
        here is an ordered pipeline: steps run in the order they were defined in the file, a simple way to build preprocessing chains."""),
    predict("What a signature tells you", "easy",
        code="""
        import inspect

        def embed(texts, /, model="small", *, batch_size: int = 64, normalize=True, **options) -> list:
            return []

        for name, p in inspect.signature(embed).parameters.items():
            print(name, p.kind.name, p.default is p.empty, p.annotation is p.empty)
        print(inspect.signature(embed).bind(["a"], batch_size=8).arguments)
        """,
        hints=["Before `/` is positional-only; after `*`, keyword-only. `bind` maps only the arguments actually given."],
        why="""`texts` is positional-only (before `/`), required and unannotated. `model` is an ordinary parameter with a default. `batch_size` and
        `normalize` are keyword-only (after `*`), with defaults; only `batch_size` has an annotation. `**options` is `VAR_KEYWORD`.
        `bind` returns only the arguments that were passed, mapped to their parameter names; `apply_defaults()` would add the rest."""),
)

section("medium", "Medium",
    write("Generate a tool schema", "medium", tag="GenAI",
        prompt="""Write `tool_schema(func)` returning `{"name": ..., "description": ..., "parameters": {"type": "object",
        "properties": {...}, "required": [...]}}`. The description is the first line of the docstring (empty string if none). Map
        `str`, `int`, `float` and `bool` to `"string"`, `"integer"`, `"number"` and `"boolean"`, and `list[X]` to `{"type": "array",
        "items": {"type": ...}}`. Parameters without a default are required. Raise `TypeError` naming the parameter if one has no
        annotation or an unsupported type. Use `typing.get_type_hints`.""",
        code="""
        import inspect, typing

        def tool_schema(func):
            pass
        """,
        tests="""
        def search_docs(query: str, k: int = 5, tags: list[str] = (), min_score: float = 0.0) -> list:
            \"\"\"Search the help-centre articles.

            Longer explanation that the model does not need.
            \"\"\"
            return []

        s = tool_schema(search_docs)
        assert s == {
            "name": "search_docs",
            "description": "Search the help-centre articles.",
            "parameters": {"type": "object", "required": ["query"], "properties": {
                "query": {"type": "string"}, "k": {"type": "integer"},
                "tags": {"type": "array", "items": {"type": "string"}}, "min_score": {"type": "number"}}},
        }

        def flag(enabled: bool):
            return enabled
        assert tool_schema(flag)["parameters"]["properties"] == {"enabled": {"type": "boolean"}} and tool_schema(flag)["description"] == ""

        def untyped(x, y: int):
            return x
        try:
            tool_schema(untyped)
            assert False
        except TypeError as e:
            assert "'x'" in str(e)
        """,
        hints=["`hints = typing.get_type_hints(func)`; a parameter without an annotation is missing from `hints`.",
               "For lists: `typing.get_origin(t) is list`, then `typing.get_args(t)[0]` is the item type."],
        solution="""
        import inspect, typing

        SIMPLE = {str: "string", int: "integer", float: "number", bool: "boolean"}


        def _json_type(t, name):
            if t in SIMPLE:
                return {"type": SIMPLE[t]}
            if typing.get_origin(t) is list:
                (item,) = typing.get_args(t)
                return {"type": "array", "items": _json_type(item, name)}
            raise TypeError(f"parameter {name!r}: unsupported type {t!r}")


        def tool_schema(func):
            hints = typing.get_type_hints(func)
            properties, required = {}, []
            for name, p in inspect.signature(func).parameters.items():
                if name not in hints:
                    raise TypeError(f"parameter {name!r} of {func.__name__} has no type annotation")
                properties[name] = _json_type(hints[name], name)
                if p.default is p.empty:
                    required.append(name)
            doc = inspect.getdoc(func) or ""
            return {
                "name": func.__name__,
                "description": doc.splitlines()[0] if doc else "",
                "parameters": {"type": "object", "properties": properties, "required": required},
            }
        """,
        why="""Everything the model needs is already in the function: the name, the purpose (first docstring line), the parameters and their
        types, and which ones are required. Generating the schema keeps it in sync with the code forever. Refusing unannotated or
        unsupported parameters is deliberate: a schema that silently omits a parameter or guesses its type makes the model call the tool
        wrongly, which shows up as confusing agent failures. The recursive `_json_type` handles nested lists for free. Note the check
        order matters for `bool`: dict lookup by type is exact, so `bool` maps to `"boolean"` rather than being treated as an `int`. Real
        libraries add per-parameter descriptions (parsed from the docstring or from `Annotated` metadata), enums and optional types."""),
    fix("The registry bypasses the timing", "medium", tag="GenAI",
        prompt="""Agent tools are called through `TOOLS`, and every call must be counted by `@counted`. Calls through the registry are
        not counted. Fix it by changing only the decorator order.""",
        code="""
        import functools

        TOOLS = {}
        COUNTS = {}

        def tool(func):
            TOOLS[func.__name__] = func
            return func

        def counted(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                COUNTS[func.__name__] = COUNTS.get(func.__name__, 0) + 1
                return func(*args, **kwargs)
            return wrapper

        @counted
        @tool
        def search(query):
            return [query]

        @counted
        @tool
        def fetch(doc_id):
            return {"id": doc_id}
        """,
        tests="""
        TOOLS["search"]("refund"); TOOLS["search"]("reset"); TOOLS["fetch"](7)
        assert COUNTS == {"search": 2, "fetch": 1}
        assert TOOLS["search"] is search and search.__name__ == "search"
        """,
        hints=["The bottom decorator runs first. Which object should the registry hold: the plain function or the counted wrapper?"],
        solution="""
        import functools

        TOOLS = {}
        COUNTS = {}

        def tool(func):
            TOOLS[func.__name__] = func
            return func

        def counted(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                COUNTS[func.__name__] = COUNTS.get(func.__name__, 0) + 1
                return func(*args, **kwargs)
            return wrapper

        @tool
        @counted
        def search(query):
            return [query]

        @tool
        @counted
        def fetch(doc_id):
            return {"id": doc_id}
        """,
        why="""Decorators apply bottom-up, so with `@tool` at the bottom it received the plain function and registered that; `@counted` then
        wrapped it for the module-level name only. Calls through `TOOLS` went straight to the unwrapped function. With `@tool` on top, it
        registers the counted wrapper, so every route to the function goes through the counter, and the registry entry and the module
        name are the same object. `wraps` keeps `__name__` as `search`, which is why the registry key is still right. The rule:
        registration goes outermost."""),
    write("Format values by type", "medium", tag="Data work",
        prompt="""Write a `functools.singledispatch` function `render(value)` for building prompt context: the default returns
        `str(value)`; `float` gives 3 decimals; `bool` gives `"yes"`/`"no"`; `None` gives `"n/a"`; `list` and `tuple` give items
        rendered and joined with `", "`; `dict` gives `"key: value"` lines joined with newlines, values rendered recursively.""",
        code="""
        import functools

        @functools.singledispatch
        def render(value):
            pass
        """,
        tests="""
        assert render(0.91234) == "0.912" and render(3) == "3" and render(True) == "yes" and render(None) == "n/a"
        assert render([1, 2.5, False]) == "1, 2.500, no" and render(("a", None)) == "a, n/a"
        assert render({"score": 0.5, "tags": ["eu", "vip"], "active": True}) == "score: 0.500\\ntags: eu, vip\\nactive: yes"
        assert render("text") == "text"
        """,
        hints=["Register implementations with `@render.register` and a type annotation on the first parameter. For `None`, register `type(None)`.",
               "Register `bool` separately: otherwise `True` would match the default (or an `int` handler, if you had one)."],
        solution="""
        import functools

        @functools.singledispatch
        def render(value):
            return str(value)

        @render.register
        def _(value: float):
            return f"{value:.3f}"

        @render.register
        def _(value: bool):
            return "yes" if value else "no"

        @render.register(type(None))
        def _(value):
            return "n/a"

        @render.register(list)
        @render.register(tuple)
        def _(value):
            return ", ".join(render(v) for v in value)

        @render.register
        def _(value: dict):
            return "\\n".join(f"{k}: {render(v)}" for k, v in value.items())
        """,
        why="""Each type gets a small function, and `render` picks one by the type of its argument, so adding a new type later (a `datetime`, a
        NumPy array) is one more registration, possibly in another module, with no change to existing code. `None` has to be registered
        through its type, `type(None)`, since `None` itself is not a type. Stacking two `register` calls attaches one implementation
        to both `list` and `tuple`; `register(cls)` returns the function unchanged, which is what makes stacking possible. Recursion
        through `render` handles nested structures, each item dispatched by its own type."""),
    choose("A command table or an if-chain", "medium",
        prompt="Both route 200,000 commands drawn from 30 names to handlers. Which is faster?",
        setup="""names = [f"cmd{i}" for i in range(30)]
def handler(i):
    return lambda: i
table = {n: handler(i) for i, n in enumerate(names)}
code = "def route(cmd):\\n" + "".join(f"    {'if' if i == 0 else 'elif'} cmd == {n!r}:\\n        return {i}\\n" for i, n in enumerate(names))
ns = {}
exec(code, ns)
route = ns["route"]
commands = [names[i % 30] for i in range(200_000)]""",
        options={
            "a": "out = [route(c) for c in commands]",
            "b": "out = [table[c]() for c in commands]",
        },
        answer="b",
        hints=["How many comparisons does the chain make for `cmd29`? And the dict?"],
        why="""The `if`/`elif` chain compares the command with each name in turn until one matches: on average 15 string comparisons, 30 for the
        last name. The dict computes one hash and usually one comparison, whatever the number of commands (4.5). Beyond speed, the
        table is open for extension: registering a new command does not touch the routing code, and the list of commands is data you
        can print, document or validate."""),
    trace("Registering and dispatching", "medium",
        prompt="Fill in `routes` and `result` after each marked line.",
        code="""
        ROUTES = {}

        def route(path):
            def decorator(func):
                ROUTES[path] = func.__name__
                return func
            return decorator

        routes, result = sorted(ROUTES), None  # row: "before any route"

        @route("/health")
        def health():
            return "ok"

        @route("/docs")
        @route("/documents")
        def docs():
            return ["a", "b"]

        routes, result = sorted(ROUTES), None  # row: "after definitions"
        routes, result = sorted(ROUTES), globals()[ROUTES["/documents"]]()  # row: "dispatch /documents"
        """,
        trace_vars=["routes", "result"],
        hints=["Two stacked route decorators register the same function under two paths."],
        why="""Nothing is registered until the `def` statements run. Afterwards three paths exist, two pointing at `docs`; sorting makes the
        order predictable. Dispatching looks up the function name for the path and calls the function. Real routers store the function
        object itself rather than its name, but the mechanism is the same."""),
    fix("Annotations that are strings", "medium", tag="GenAI",
        prompt="""The tools this registry reads come from modules that use `from __future__ import annotations` (common in modern code),
        so their annotations are stored as **strings**: `p.annotation` is `"int"`, not the type `int`, and `param_types` maps every
        parameter to `"unknown"`. (The tests write the annotations as strings directly, which has the same effect.) Fix it so the real
        types are used.""",
        code="""
        from __future__ import annotations
        import inspect

        NAMES = {str: "string", int: "integer", float: "number", bool: "boolean"}

        def param_types(func):
            return {name: NAMES.get(p.annotation, "unknown") for name, p in inspect.signature(func).parameters.items()}
        """,
        tests="""
        def lookup(order_id: "int", verbose: "bool" = False, note: "str" = "") -> "dict":
            return {}

        assert param_types(lookup) == {"order_id": "integer", "verbose": "boolean", "note": "string"}

        def scale(x: "float", factor: "float"):
            return x * factor
        assert param_types(scale) == {"x": "number", "factor": "number"}
        """,
        hints=["`typing.get_type_hints(func)` evaluates string annotations into real types."],
        solution="""
        from __future__ import annotations
        import inspect, typing

        NAMES = {str: "string", int: "integer", float: "number", bool: "boolean"}

        def param_types(func):
            hints = typing.get_type_hints(func)
            return {name: NAMES.get(hints.get(name), "unknown") for name in inspect.signature(func).parameters}
        """,
        why="""With `from __future__ import annotations`, Python stores annotations as unevaluated strings, which avoids import-time costs and
        allows forward references; Python 3.14 also evaluates annotations lazily by default (PEP 649). Either way, the raw `annotation`
        attribute may not be the type you expect, so code that introspects types should call `typing.get_type_hints`, which evaluates
        them in the function's module and returns real types. This exact issue has broken tool-schema generation in agent frameworks
        and dependency injection in web frameworks, which now all use `get_type_hints`."""),
    refactor("An if-chain into a registry", "medium", tag="GenAI",
        prompt="Replace the `if`/`elif` chain with a registry filled by a `@command(\"name\")` decorator. Same results. Keep the tests green.",
        code="""
        def handle(command, arg):
            if command == "summarise":
                return f"summary of {arg}"
            elif command == "translate":
                return f"{arg} (in French)"
            elif command == "classify":
                return "spam" if "prize" in arg else "ham"
            else:
                return f"unknown command {command!r}"
        """,
        tests="""
        assert handle("summarise", "doc") == "summary of doc"
        assert handle("translate", "hello") == "hello (in French)"
        assert handle("classify", "win a prize") == "spam" and handle("classify", "lunch?") == "ham"
        assert handle("delete", "x") == "unknown command 'delete'"
        """,
        hints=["`COMMANDS = {}`; `def command(name)` returns a decorator that stores the function. `handle` looks up and calls."],
        solution="""
        COMMANDS = {}

        def command(name):
            def decorator(func):
                COMMANDS[name] = func
                return func
            return decorator

        @command("summarise")
        def summarise(arg):
            return f"summary of {arg}"

        @command("translate")
        def translate(arg):
            return f"{arg} (in French)"

        @command("classify")
        def classify(arg):
            return "spam" if "prize" in arg else "ham"

        def handle(command_name, arg):
            func = COMMANDS.get(command_name)
            if func is None:
                return f"unknown command {command_name!r}"
            return func(arg)
        """,
        why="""Each command is now a separate, testable function, the router is three lines that never change, and adding a command means adding
        a decorated function anywhere that is imported. The registry can also be inspected: listing `COMMANDS` gives help text or a tool
        list for free. The `handle` parameter was renamed to `command_name` so it does not shadow the `command` decorator, a small but
        real bug source when names are reused."""),
    predict("Dispatch follows inheritance", "medium",
        code="""
        import functools

        @functools.singledispatch
        def kind(x):
            return "object"

        @kind.register
        def _(x: int):
            return "int"

        @kind.register
        def _(x: list):
            return "list"

        class Scores(list):
            pass

        print(kind(3), kind(True), kind(2.5), kind([1]), kind(Scores()))
        print(kind.dispatch(bool).__name__, kind.dispatch(float) is kind.registry[object])

        @kind.register
        def _(x: bool):
            return "bool"
        print(kind(True), kind(1))
        """,
        hints=["`bool` is a subclass of `int`; a `list` subclass is still a `list`."],
        why="""`singledispatch` looks up the argument's class hierarchy for the most specific registered type. `True` is a `bool`, a subclass of
        `int`, so it uses the `int` handler until a `bool` handler is registered. `2.5` has no handler and falls back to the default for
        `object`. A subclass of `list` uses the `list` handler. `dispatch(cls)` shows which implementation would be chosen without
        calling it; every implementation here is named `_`."""),
)

section("hard", "Hard",
    write("A small URL router", "hard", tag="GenAI",
        prompt="""Write `make_router()` returning `(route, dispatch)`. `route(method, template)` is a decorator factory registering a
        handler for a template such as `"/docs/{doc_id}/chunks/{n}"`. `dispatch(method, path)` finds the template that matches the
        path segment by segment (`{name}` matches any one segment), converts captured values with the handler's type hints (`int`,
        `float`, else `str`), and returns `(200, handler(**params))`. Return `(404, "not found")` if no template matches, `(405,
        "method not allowed")` if one matches but not for this method, and `(422, "invalid <name>")` if a conversion fails.""",
        code="""
        import typing

        def make_router():
            pass
        """,
        tests="""
        route, dispatch = make_router()

        @route("GET", "/docs/{doc_id}")
        def get_doc(doc_id: int):
            return {"id": doc_id}

        @route("GET", "/docs/{doc_id}/chunks/{n}")
        def get_chunk(doc_id: int, n: int):
            return {"doc": doc_id, "chunk": n}

        @route("POST", "/search/{query}")
        def search(query: str):
            return [query]

        @route("GET", "/health")
        def health():
            return "ok"

        assert dispatch("GET", "/docs/7") == (200, {"id": 7})
        assert dispatch("GET", "/docs/7/chunks/3") == (200, {"doc": 7, "chunk": 3})
        assert dispatch("POST", "/search/refund") == (200, ["refund"])
        assert dispatch("GET", "/health") == (200, "ok")
        assert dispatch("GET", "/docs/abc") == (422, "invalid doc_id")
        assert dispatch("DELETE", "/docs/7") == (405, "method not allowed")
        assert dispatch("GET", "/nope") == (404, "not found") and dispatch("GET", "/docs/7/chunks") == (404, "not found")
        assert get_doc(5) == {"id": 5}
        """,
        hints=["Store routes as a list of `(method, segments, handler)`, where `segments = template.strip(\"/\").split(\"/\")`.",
               "A path matches when it has the same number of segments and every non-`{...}` segment is equal. Collect the `{name}` values, then convert with `typing.get_type_hints(handler).get(name, str)`."],
        solution="""
        import typing


        def make_router():
            routes = []

            def route(method, template):
                segments = template.strip("/").split("/")

                def decorator(func):
                    routes.append((method.upper(), segments, func))
                    return func
                return decorator

            def _match(segments, parts):
                if len(segments) != len(parts):
                    return None
                params = {}
                for seg, part in zip(segments, parts):
                    if seg.startswith("{") and seg.endswith("}"):
                        params[seg[1:-1]] = part
                    elif seg != part:
                        return None
                return params

            def dispatch(method, path):
                parts = path.strip("/").split("/")
                path_matched = False
                for route_method, segments, func in routes:
                    params = _match(segments, parts)
                    if params is None:
                        continue
                    path_matched = True
                    if route_method != method.upper():
                        continue
                    hints = typing.get_type_hints(func)
                    converted = {}
                    for name, raw in params.items():
                        kind = hints.get(name, str)
                        try:
                            converted[name] = kind(raw) if kind in (int, float) else raw
                        except ValueError:
                            return 422, f"invalid {name}"
                    return 200, func(**converted)
                if path_matched:
                    return 405, "method not allowed"
                return 404, "not found"

            return route, dispatch
        """,
        why="""This is the core of every web framework's router. Registration splits each template once, at import time, into segments.
        Dispatch compares segments: literals must be equal, placeholders capture the text. The handler's type hints decide conversion,
        which is exactly how FastAPI turns `/docs/7` into `doc_id=7` and answers `/docs/abc` with a 422 validation error instead of
        calling your function with bad data. Distinguishing 404 (no such path) from 405 (path exists, wrong method) is the HTTP
        convention, and it needs the "matched any path" flag. The handlers are returned unchanged, so they can still be called and
        tested directly. Real routers compile templates into regular expressions or a tree for speed and support typed converters in
        the template itself."""),
    fix("Read the code: a plugin registry", "hard", tag="Data work",
        prompt="""This plugin system lets modules register data loaders by file extension. The loaders registered in one test leak into
        others, a second loader for `.csv` silently replaces the first, and `load("x.json")` fails with "no loader" until a JSON file
        has been loaded once. Read it, find the bugs and fix them so that: each `make_plugins()` call has its own registry, duplicates
        raise `ValueError`, and registration happens when the decorator is applied.""",
        code="""
        def make_plugins(registry={}):
            def loader(ext):
                def decorator(func):
                    def wrapper(path):
                        registry[ext] = func
                        return func(path)
                    return wrapper
                return decorator

            def load(path):
                ext = path.rsplit(".", 1)[-1]
                if ext not in registry:
                    raise LookupError(f"no loader for .{ext}")
                return registry[ext](path)

            return loader, load, registry
        """,
        tests="""
        loader, load, registry = make_plugins()

        @loader("csv")
        def read_csv(path):
            return f"csv rows from {path}"

        @loader("json")
        def read_json(path):
            return f"json from {path}"

        assert sorted(registry) == ["csv", "json"]
        assert load("data/x.json") == "json from data/x.json" and load("a.csv") == "csv rows from a.csv"
        try:
            @loader("csv")
            def other_csv(path):
                return "other"
            assert False, "duplicate must raise"
        except ValueError:
            pass
        assert load("a.csv") == "csv rows from a.csv"

        loader2, load2, registry2 = make_plugins()
        assert registry2 == {}
        try:
            load2("a.csv")
            assert False
        except LookupError:
            pass
        assert read_csv("b.csv") == "csv rows from b.csv"
        """,
        hints=["`registry={}` is a mutable default shared by every `make_plugins()` call (2.4).",
               "The registration line is inside `wrapper`, so it runs only when the function is called. Move it into `decorator`, check for duplicates there, and return `func` unchanged."],
        solution="""
        def make_plugins():
            registry = {}

            def loader(ext):
                def decorator(func):
                    if ext in registry:
                        raise ValueError(f"a loader for .{ext} is already registered: {registry[ext].__name__}")
                    registry[ext] = func
                    return func
                return decorator

            def load(path):
                ext = path.rsplit(".", 1)[-1]
                if ext not in registry:
                    raise LookupError(f"no loader for .{ext}")
                return registry[ext](path)

            return loader, load, registry
        """,
        why="""Three bugs. The mutable default `registry={}` was created once, when `def make_plugins` ran, so every "new" plugin system shared
        one dict and registrations leaked between tests (2.4); creating the dict inside the function gives each call its own. The
        registration sat **inside the wrapper**, so a loader was registered only after it had been called once, through the decorated
        name, which made `load` fail for any format nobody had called directly; registration must happen in the decorator level, which
        runs at definition time. And nothing prevented two loaders for one extension, so the later one silently won; the duplicate
        check raises at import with a message naming the existing loader. With no wrapper needed at all, returning `func` unchanged
        also keeps `read_csv` callable and named as before."""),
    write("Call a tool with typed arguments", "hard", tag="GenAI",
        prompt="""A model returns tool calls as a name and a **JSON string** of arguments. Write `call_tool(tools, name, arguments_json)`
        returning `{"result": ...}` or, for problems the model can fix, `{"error": message}`: unknown tool; invalid JSON or not an
        object; missing required or unknown parameters; a value whose type does not match the annotation (`int`, `float`, `str`,
        `bool`; an `int` value is accepted for `float`, a `bool` is not accepted for `int` or `float`). Errors inside the tool itself
        propagate.""",
        code="""
        import inspect, json, typing

        def call_tool(tools, name, arguments_json):
            pass
        """,
        tests="""
        def refund(order_id: int, amount: float, reason: str = "", notify: bool = True):
            if amount > 500:
                raise RuntimeError("limit exceeded in payment system")
            return f"refunded {amount} on {order_id} ({reason or 'no reason'}, notify={notify})"

        tools = {"refund": refund}
        assert call_tool(tools, "refund", '{"order_id": 7, "amount": 20}') == {"result": "refunded 20 on 7 (no reason, notify=True)"}
        assert call_tool(tools, "refund", '{"order_id": 7, "amount": 2.5, "notify": false}')["result"].endswith("notify=False)")
        assert call_tool(tools, "cancel", "{}") == {"error": "unknown tool 'cancel'"}
        assert call_tool(tools, "refund", "{order_id: 7}")["error"].startswith("arguments are not valid JSON")
        assert call_tool(tools, "refund", "[7, 20]") == {"error": "arguments must be a JSON object"}
        assert call_tool(tools, "refund", '{"amount": 1}') == {"error": "missing required argument: order_id"}
        assert call_tool(tools, "refund", '{"order_id": 1, "amount": 1, "currency": "EUR"}') == {"error": "unknown argument: currency"}
        assert call_tool(tools, "refund", '{"order_id": "7", "amount": 1}') == {"error": "order_id must be int, got str"}
        assert call_tool(tools, "refund", '{"order_id": true, "amount": 1}') == {"error": "order_id must be int, got bool"}
        try:
            call_tool(tools, "refund", '{"order_id": 7, "amount": 900}')
            assert False
        except RuntimeError:
            pass
        """,
        hints=["Parse with `json.loads` inside `try`; check `isinstance(args, dict)`.",
               "Compare `set(args)` with the signature's parameters for unknown and missing (required = no default) names.",
               "Type check: reject `bool` unless the annotation is `bool`; accept `int` for `float`; otherwise `isinstance(value, expected)`."],
        solution="""
        import inspect, json, typing


        def _type_error(name, value, expected):
            if isinstance(value, bool) and expected is not bool:
                return f"{name} must be {expected.__name__}, got bool"
            if expected is float and isinstance(value, (int, float)):
                return None
            if not isinstance(value, expected):
                return f"{name} must be {expected.__name__}, got {type(value).__name__}"
            return None


        def call_tool(tools, name, arguments_json):
            func = tools.get(name)
            if func is None:
                return {"error": f"unknown tool {name!r}"}
            try:
                args = json.loads(arguments_json)
            except json.JSONDecodeError as e:
                return {"error": f"arguments are not valid JSON: {e.msg}"}
            if not isinstance(args, dict):
                return {"error": "arguments must be a JSON object"}
            params = inspect.signature(func).parameters
            hints = typing.get_type_hints(func)
            for key in args:
                if key not in params:
                    return {"error": f"unknown argument: {key}"}
            for pname, p in params.items():
                if p.default is p.empty and pname not in args:
                    return {"error": f"missing required argument: {pname}"}
            for key, value in args.items():
                expected = hints.get(key)
                if expected is not None:
                    problem = _type_error(key, value, expected)
                    if problem:
                        return {"error": problem}
            return {"result": func(**args)}
        """,
        why="""Every check before the call targets a mistake the **model** can correct, and returns a short, specific message it can act on:
        "order_id must be int, got str" leads to a corrected call on the next turn, a traceback does not. Booleans need special care
        because `bool` is a subclass of `int` (1.2): without the explicit check, `true` would be accepted as an order id. Accepting an
        integer for a `float` parameter matches JSON, which has a single number type. The final call is deliberately outside any
        handler: the `RuntimeError` comes from the payment system, it is not the model's fault, and it must reach your error handling
        and alerting (7.3). This is the validation that frameworks generate from a Pydantic model of the parameters (11.4)."""),
    predict("Import-time order and stacked registrations", "hard",
        code="""
        import functools

        ORDER = []
        REG = {}

        def reg(name):
            def decorator(func):
                ORDER.append(f"reg {name}")
                REG[name] = func
                return func
            return decorator

        def wrap(func):
            ORDER.append(f"wrap {func.__name__}")
            @functools.wraps(func)
            def wrapper(*args):
                return "wrapped " + func(*args)
            return wrapper

        @reg("b")
        @wrap
        @reg("a")
        def greet(x):
            return f"hi {x}"

        print(ORDER)
        print(REG["a"]("ana"), "|", REG["b"]("bo"), "|", greet("cy"))
        print(REG["b"] is greet, REG["a"] is greet.__wrapped__)
        """,
        hints=["Decorators apply bottom-up: `reg(\"a\")`, then `wrap`, then `reg(\"b\")`. Each registers whatever it receives."],
        why="""The bottom decorator `reg("a")` sees the original function and registers it; `wrap` then creates the wrapper; `reg("b")` registers
        the wrapper, which is also what the name `greet` ends up bound to. So `"a"` dispatches to the undecorated function and `"b"` to the
        wrapped one, and `__wrapped__` confirms which is which. Stacking registrations around a wrapper is legitimate when you want both
        versions available, but usually it is an accident, which is why registration normally goes outermost."""),
)

section("interview", "Interview questions",
    explain("How does FastAPI know which function handles a route and what parameters it expects?", "medium", tag="Interview",
        why="""Through a registration decorator plus introspection. `@app.get("/items/{item_id}")` is a method acting as a decorator factory: when
        the module is imported, it records the path template, the HTTP method and the function in the application's routing table, and
        returns the function unchanged. At that point FastAPI also inspects the function with `inspect.signature` and its type hints:
        parameters named in the path become path parameters, simple types not in the path become query parameters, Pydantic models
        become the JSON body, and `Depends(...)` defaults declare dependencies. It builds validation (with Pydantic) and the OpenAPI
        schema from this information. When a request arrives, the router matches the path, converts and validates the values against the
        annotations (returning 422 on failure), resolves dependencies and calls the function. That is why type hints in FastAPI are not
        documentation but behaviour, and why wrapping route functions in decorators without `functools.wraps` breaks them."""),
    explain("What is `functools.singledispatch`, and when is it better than `isinstance` checks?", "medium", tag="Interview",
        why="""It turns a function into a generic function that chooses an implementation based on the type of its first argument. You decorate a
        default implementation with `@singledispatch`, then register specialised ones with `@func.register` (using the annotation of the
        first parameter or an explicit type); at call time it walks the argument's class hierarchy (its MRO) to find the most specific
        registered type. It is better than an `if isinstance(...)` chain when the set of supported types should be open: other modules can
        register their own types without editing your function, each implementation is a small separate function, and the dispatch is
        cached and fast. It dispatches on one argument only and on types, not values; for methods there is `singledispatchmethod`. A
        chain of `isinstance` checks is fine for two or three fixed cases."""),
    explain("Design the tool-calling layer of an agent framework.", "hard", tag="Interview",
        why="""A registry filled by a decorator (`@tool`, possibly with a name, description and permissions), with duplicate detection and an
        explicit place where tool modules are imported. Schemas generated from each function's signature, type hints and docstring (or a
        Pydantic model of its parameters), so they cannot drift from the code; descriptions written for the model, since they are part of
        the prompt. Dispatch that parses the model's JSON arguments, validates them against the schema, and returns concise, actionable
        errors for unknown tools, bad JSON, missing or mistyped arguments, while letting genuine failures inside a tool reach logging
        and alerting. Around each call: per-tool timeouts, retries only for idempotent tools, rate limits, permission checks per user
        and environment (no file deletion from a public chatbot), confirmation for dangerous actions, and output limits so a huge result
        does not overflow the context. Observability: one trace span per tool call with arguments (redacted), result size, duration and
        errors. Plus testing: tools are plain functions testable without the agent, and the registry is injectable so tests use a fake
        set of tools. Version tool schemas, because changing a tool's parameters changes what deployed prompts and models expect."""),
)

recap(
    "A registration decorator records the function (in a dict or list) and returns it unchanged; it runs at import time, so unimported modules register nothing.",
    "Registries with names and metadata use a factory (`@route(\"GET\", \"/x\")`); check for duplicates and give tests a fresh registry.",
    "`inspect.signature` gives parameters, kinds, defaults and annotations; use `typing.get_type_hints` to get real types, even from string annotations.",
    "Tool schemas, routers and validators are generated from signatures and type hints, so docstrings and hints become behaviour.",
    "Dispatch by name with a dict, by type with `functools.singledispatch`; with stacked decorators, register outermost.",
)
