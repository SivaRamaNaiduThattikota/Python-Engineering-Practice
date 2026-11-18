from lesson import *
from diagrams import *

lesson(
    id="m15-1", num="15.1", title="Imports and modules",
    intro="Every Python project is a tree of modules, and many confusing errors (ModuleNotFoundError, circular imports, a patch that "
          "does nothing, a local file shadowing a library) come from not knowing what `import` actually does. Module objects and "
          "`sys.modules`, the search path, packages and relative imports, `__name__` and `python -m`, circular imports and how to "
          "break them, import-time side effects, `__all__`, and dynamic imports for plugins. Problems build real package folders "
          "with `lessontools.make_tree`, which writes files and puts their folder on `sys.path`.",
    desc="The import system, `__name__`, packages, circular imports.",
    keys="import module sys.modules sys.path package __init__.py namespace package relative import absolute import __name__ __main__ python -m circular import partially initialized side effects __all__ importlib import_module reload pkgutil iter_modules plugin lazy import shadowing",
)

term("Module", "A Python file (or other importable unit) loaded as an object whose attributes are the names defined at its top level.")
term("Package", "A folder of modules that can be imported as one name, usually marked by an `__init__.py` file; subpackages nest further.")
term("Import system", "The machinery behind `import`: it finds a module on the search path, runs its code once, and caches the module object in `sys.modules`.")

section("what", "What `import` does",
    fig(stage_map(15, "an evaluation command-line tool"), "Module 15 at a glance: imports, environments and packaging, and command-line tools, building up to evalctl."),
    fig(flowchart({
        "imp": ("start", 0, 0, "import shop"),
        "cached": ("ask", 0, 1, "'shop' in sys.modules?"),
        "bind": ("good", 1, 1, "bind the name|(no code runs)"),
        "find": ("ask", 0, 2, "found in a folder|on sys.path?"),
        "err": ("bad", 1, 2, "ModuleNotFoundError"),
        "store": ("step", 0, 3, "create the module,|store it in sys.modules"),
        "run": ("accent", 0, 4, "run its code top to|bottom, bind the name"),
    }, [("imp", "cached"), ("cached", "bind", "yes"), ("cached", "find", "no"), ("find", "err", "no"), ("find", "store", "yes"), ("store", "run")],
        cell=(250, 80), label="what import does"),
        "A module's code runs once per process; every later import just finds it in `sys.modules`."),
    p("""`import shop` does three things. It looks in **`sys.modules`**, a dict of every module already imported, and if `shop` is there, simply binds the name. Otherwise it
    **finds** the module by searching the folders in **`sys.path`** in order (the folder of the script you ran, or the current folder for `python -m` and the REPL, then
    the `PYTHONPATH` entries, then the standard library and `site-packages`). Then it **executes** the module's code from top to bottom in a fresh namespace, stores the
    module object in `sys.modules` **before** running it, and binds the name. So a module's top-level code runs **once per process**, however many files import
    it, and every importer shares the same module object."""),
    p("""`from shop import price` imports `shop` the same way and then binds the name `price` in the importing module to the object `shop.price` refers to **at that moment**.
    If `shop` later rebinds `price`, the importer still holds the old object, which is why patching must happen where a name is looked up (13.3), and why `import shop`
    then `shop.price(...)` sees updates. `import shop.cart as cart` binds a short name; `from shop import *` imports the names listed in `shop.__all__`, or all public
    names if it is not defined."""),
    ex("""
    import sys
    from lessontools import make_tree, forget

    make_tree({"pricing_demo.py": '''
    print("  running pricing_demo top-level code")
    TAX = 0.2

    def price(net):
        return round(net * (1 + TAX), 2)
    '''})
    print("before:", "pricing_demo" in sys.modules)
    import pricing_demo
    import pricing_demo as again
    from pricing_demo import price, TAX
    print(again is pricing_demo is sys.modules["pricing_demo"], price(10))
    pricing_demo.TAX = 0.1
    print(pricing_demo.price(10), TAX)
    forget("pricing_demo")
    import pricing_demo
    print(pricing_demo.TAX, pricing_demo is again)
    """, "import_once.py"),
    p("""The top-level code ran once for three import statements; all names refer to the same module object. Changing `TAX` on the module changed `price`'s result, because
    `price` reads the module global at call time, while the copied name `TAX` kept the old value. Removing the entry from `sys.modules` (what `forget` does) makes the
    next import run the file again and create a **new** module object; `importlib.reload(module)` re-runs the code into the existing object instead."""),
)

section("packages", "Packages and relative imports",
    p("""A **package** is a folder of modules. With an `__init__.py` file it is a regular package: importing `shop` runs `shop/__init__.py`, and `import shop.cart` imports `shop`
    first and then `shop/cart.py` as `shop.cart`. `__init__.py` is often empty, or re-exports the package's public API (`from .cart import Cart`) so users can write
    `from shop import Cart`. Folders **without** `__init__.py` can still be imported as **namespace packages**, which exist so that several distributions can share one
    package name; for your own code, add `__init__.py` to avoid surprises."""),
    p("""Inside a package, modules refer to each other with **absolute** imports (`from shop.cart import Cart`) or **relative** ones (`from .cart import Cart`, `from ..utils import
    slugify`), where dots count package levels from the current module. Relative imports only work in modules that are part of a package, so running a package
    module as a script (`python shop/cart.py`) breaks them: the file runs as `__main__` with no parent package. Run it as **`python -m shop.cart`** instead, which
    imports the package properly and runs the module as `__main__`. A project's code usually lives in a `src/` folder with the package inside (`src/shop/...`), and
    is installed in development mode (15.2) so `import shop` works from anywhere, including tests."""),
    ex("""
    from lessontools import make_tree

    make_tree({
        "shopkit/__init__.py": '''
            from .cart import Cart
            __all__ = ["Cart"]
            print("  shopkit/__init__ ran, __name__ =", __name__)
        ''',
        "shopkit/cart.py": '''
            from .pricing import total
            class Cart:
                def __init__(self):
                    self.items = []
                def add(self, net):
                    self.items.append(net)
                def total(self):
                    return total(self.items)
        ''',
        "shopkit/pricing.py": '''
            def total(nets, tax=0.2):
                return round(sum(nets) * (1 + tax), 2)
        ''',
    })
    from shopkit import Cart
    import shopkit.pricing
    c = Cart()
    c.add(10)
    c.add(5)
    print(c.total(), shopkit.pricing.__name__, shopkit.cart.__package__, sorted(m for m in __import__("sys").modules if m.startswith("shopkit")))
    """, "packages.py"),
)

section("main", "`__name__` and running modules",
    fig(table(["", "python cart.py", "import shopkit.cart"], [
        ["__name__", "'__main__'", "'shopkit.cart'"],
        ["if __name__ == '__main__': block", "runs", "skipped"],
    ], hl={(1, 1)}, label="the same file, run or imported"),
        "`__name__` tells a module whether it is the program or a library being imported."),
    p("""Every module has `__name__`: its import name (`"shopkit.cart"`), except the module Python was asked to run, which is called **`"__main__"`**. The idiom `if __name__ ==
    "__main__":` therefore separates code to run when the file is executed (a command-line entry point, a quick demo) from definitions that importers need, and it is
    essential for multiprocessing (14.3). Two related attributes: `__file__` is the path the module was loaded from, and `__package__` is the package used to resolve
    relative imports. A file run directly and the same file imported are **two different module objects** (`__main__` and `shopkit.cart`), each with its own globals,
    a classic source of "my singleton exists twice" bugs."""),
)

section("circular", "Circular imports",
    fig(chain(["import a starts|running a", "a reaches import b,|b starts running", "b does from a|import helper", ("a is only half run:|ImportError", "bad")]),
        "In a circular import, the second module sees the first one only partly initialised."),
    p("""If `a` imports `b` and `b` imports `a`, importing `a` starts running `a`, which reaches `import b`, which starts running `b`, which reaches `import a`. Because `a` is already
    in `sys.modules` (it is put there before its code runs), Python hands `b` the **partially initialised** `a`, whose code stopped at the `import b` line. `import a`
    succeeds, but `from a import helper` fails with `ImportError: cannot import name 'helper' from partially initialized module 'a' (most likely due to a circular
    import)` if `helper` is defined below that line, and `a.helper` raises `AttributeError` if used at `b`'s top level."""),
    p("""The fixes, from best to most tactical: **restructure** so the dependency goes one way (move the shared code both modules need into a third module that imports neither);
    depend on the **module** rather than the name (`import a` and use `a.helper` inside functions, which runs after both modules finished loading); move the import
    **inside the function** that needs it; or, for imports needed only by type hints, guard them with `if typing.TYPE_CHECKING:` (11.1). A circular import is usually a
    design smell: two modules that need each other's internals are really one module, or both need a third (problem 6)."""),
)

section("side", "Import-time side effects and dynamic imports",
    p("""Because importing runs a module's top-level code, anything slow or stateful there runs whenever anyone imports the module, including tests, linters, documentation
    tools and multiprocessing workers: connecting to a database, loading a 2 GB model, reading environment variables (12.4), configuring logging (12.3), or printing.
    Keep the top level to definitions and cheap constants; put setup in functions (`get_client()`, `load_model()`), called once, often cached with `functools.cache`
    (problem 12)."""),
    p("""Imports can also be computed at run time: **`importlib.import_module("plugins.csv_loader")`** imports a module by its name string, which is how plugin systems, framework
    settings (`"myapp.handlers.classify"`) and optional backends work. `pkgutil.iter_modules(package.__path__)` lists the modules in a package, so a registry can discover
    every plugin in a folder (problem 5). Importing a heavy optional dependency **inside** the function that uses it keeps start-up fast and lets the rest of the
    library work without it; catching `ImportError` there can give a helpful message such as "install the `pdf` extra" (problem 9). Packaging tools can also declare
    plugins as **entry points** (15.2), found with `importlib.metadata.entry_points(group=...)`."""),
)

section("warmup", "Warm-up",
    predict("Imports run once and share one object", "easy",
        code="""
        import sys
        from lessontools import make_tree

        make_tree({
            "counter_p1.py": '''
            print("loading counter_p1")
            count = 0
            def bump():
                global count
                count += 1
                return count
            ''',
            "user_a_p1.py": '''
            import counter_p1
            counter_p1.bump()
            ''',
            "user_b_p1.py": '''
            from counter_p1 import bump, count
            bump()
            snapshot = count
            ''',
        })
        import user_a_p1
        import user_b_p1
        import counter_p1
        print(counter_p1.count, user_b_p1.snapshot, user_b_p1.count)
        print("user_a_p1" in sys.modules, user_a_p1.counter_p1 is counter_p1)
        """,
        hints=["The module code runs on the first import only. `from m import count` copies the current value of `count` into the importer."],
        why="""`counter_p1` is loaded once, by the first importer, and both users share that one module object, so the two `bump()` calls increment the same counter to 2. But
        `user_b_p1` copied `count` when it imported it, while it was still 1 (after `user_a_p1`'s bump and before its own), and that copied name never changes, since
        `bump` rebinds the module's global, not the importer's. Module attributes are live; names imported with `from` are snapshots of references."""),
    write("Load a plugin by name", "easy", tag="GenAI",
        prompt="""Write `load_tool(dotted)` for an agent's tool registry: given `"package.module:function"`, import the module with `importlib.import_module`, get the function, and
        return it. Raise `ValueError` if the string has no `:`, `ModuleNotFoundError` (let it propagate) if the module does not exist, and `LookupError(f"{module} has no
        {name}")` if the attribute is missing or not callable.""",
        code="""
        import importlib

        def load_tool(dotted):
            pass
        """,
        tests="""
        from lessontools import make_tree
        make_tree({
            "tools_w2/__init__.py": "",
            "tools_w2/math_tools.py": '''
            def add(a, b):
                return a + b
            PI = 3.14159
            ''',
        })
        add = load_tool("tools_w2.math_tools:add")
        assert add(2, 3) == 5 and add.__module__ == "tools_w2.math_tools"
        assert load_tool("tools_w2.math_tools:add") is add
        for bad, err in [("tools_w2.math_tools", ValueError), ("tools_w2.math_tools:PI", LookupError), ("tools_w2.math_tools:sub", LookupError)]:
            try:
                load_tool(bad)
                assert False, bad
            except err:
                pass
        try:
            load_tool("tools_w2.nope:add")
            assert False
        except ModuleNotFoundError:
            pass
        """,
        hints=["`module_name, sep, attr = dotted.partition(\":\")`; if `sep` is empty, raise `ValueError`.",
               "`getattr(module, attr, None)` and `callable(...)`."],
        solution="""
        import importlib


        def load_tool(dotted):
            module_name, sep, attr = dotted.partition(":")
            if not sep or not module_name or not attr:
                raise ValueError(f"expected 'module:function', got {dotted!r}")
            module = importlib.import_module(module_name)
            fn = getattr(module, attr, None)
            if fn is None or not callable(fn):
                raise LookupError(f"{module_name} has no {attr}")
            return fn
        """,
        why="""`"module:attribute"` strings are how configuration files refer to code: entry points in `pyproject.toml` (15.2), ASGI servers (`uvicorn app.main:app`), task queues and
        agent tool registries all use them. `import_module` performs a normal import from a string, so the module is cached in `sys.modules` and its own imports work as
        usual. Separate errors for "malformed string", "no such module" and "no such function" tell whoever wrote the configuration exactly what to fix."""),
    fix("A package module with an implicit relative import", "easy", tag="Data work",
        prompt="""The package below fails with `ModuleNotFoundError: No module named 'pricing'` when `shop_f3.cart` is imported, because `cart.py` uses a Python 2 style import of its
        sibling. Fix the file contents in `FILES` so the package imports correctly, using a relative import (the grader builds the folder from `FILES`).""",
        code="""
        FILES = {
            "shop_f3/__init__.py": "",
            "shop_f3/pricing.py": '''
        def with_tax(net, rate=0.2):
            return round(net * (1 + rate), 2)
        ''',
            "shop_f3/cart.py": '''
        import pricing

        def total(nets):
            return pricing.with_tax(sum(nets))
        ''',
        }
        """,
        tests="""
        from lessontools import make_tree, forget
        forget("shop_f3")
        make_tree(FILES)
        import shop_f3.cart
        assert shop_f3.cart.total([10, 5]) == 18.0
        assert "pricing" not in __import__("sys").modules or not hasattr(__import__("sys").modules.get("pricing"), "with_tax")
        """,
        hints=["Inside a package, refer to a sibling module with `from . import pricing` (or `from shop_f3 import pricing`)."],
        solution="""
        FILES = {
            "shop_f3/__init__.py": "",
            "shop_f3/pricing.py": '''
        def with_tax(net, rate=0.2):
            return round(net * (1 + rate), 2)
        ''',
            "shop_f3/cart.py": '''
        from . import pricing

        def total(nets):
            return pricing.with_tax(sum(nets))
        ''',
        }
        """,
        why="""Python 3 imports are absolute by default: `import pricing` searches `sys.path` for a top-level module called `pricing`, and the package folder itself is not on the
        path, so it fails (or, worse, silently imports some other `pricing.py` that happens to be on the path). `from . import pricing` means "the module `pricing` in my own
        package", resolved through `__package__`, so it works wherever the package is installed. The absolute form `from shop_f3 import pricing` is equally correct and some
        style guides prefer it for clarity."""),
    predict("Names that describe a module", "easy",
        code="""
        from lessontools import make_tree

        root = make_tree({
            "app_p4/__init__.py": "",
            "app_p4/core/__init__.py": "",
            "app_p4/core/models.py": '''
            INFO = (__name__, __package__)
            ''',
        })
        import app_p4.core.models as m
        import app_p4
        print(__name__, m.INFO, app_p4.__package__)
        print(m.__file__.endswith("app_p4/core/models.py"), m.__spec__.name, m.__spec__.parent)
        print(app_p4.core.models is m, hasattr(app_p4, "core"))
        """,
        hints=["A submodule's `__name__` is its full dotted name; `__package__` is the package containing it, used for relative imports."],
        why="""The code you run is `__main__`. A module's `__name__` is its full dotted import name, and `__package__` (also `__spec__.parent`) is the package it belongs to, which is how
        `from . import x` knows where to look; a package's own `__package__` is its own name. Importing a submodule also sets it as an attribute of its parent package, so
        `app_p4.core.models` is the same object."""),
)

section("medium", "Medium",
    write("Discover tools in a plugin package", "medium", tag="GenAI",
        prompt="""Write `discover_tools(package_name)` that imports the package, lists its modules with `pkgutil.iter_modules(package.__path__)`, imports each (skipping names that start
        with `_`), and collects every **class** defined in those modules that has a string attribute `tool_name`. Return a dict from `tool_name` to class, sorted by name.
        Two classes with the same `tool_name` raise `ValueError` naming both modules.""",
        code="""
        import importlib, inspect, pkgutil

        def discover_tools(package_name):
            pass
        """,
        tests="""
        from lessontools import make_tree, forget
        forget("agent_tools_w5")
        make_tree({
            "agent_tools_w5/__init__.py": "",
            "agent_tools_w5/search.py": '''
            class WebSearch:
                tool_name = "web_search"
            class NotATool:
                pass
            ''',
            "agent_tools_w5/calc.py": '''
            class Calculator:
                tool_name = "calculator"
            from agent_tools_w5.search import WebSearch
            ''',
            "agent_tools_w5/_internal.py": '''
            class Hidden:
                tool_name = "hidden"
            ''',
        })
        tools = discover_tools("agent_tools_w5")
        assert list(tools) == ["calculator", "web_search"] and tools["web_search"].__name__ == "WebSearch"
        assert "hidden" not in tools
        import importlib, os, sys
        pkg = sys.modules["agent_tools_w5"]
        target = os.path.join(pkg.__path__[0], "dup.py")
        with open(target, "w", encoding="utf-8") as f:
            f.write('class AlsoCalc:\\n    tool_name = "calculator"\\n')
        importlib.invalidate_caches()
        try:
            discover_tools("agent_tools_w5")
            assert False
        except ValueError as e:
            assert "agent_tools_w5.calc" in str(e) and "agent_tools_w5.dup" in str(e)
        """,
        hints=["For each `info` from `iter_modules`, import `f\"{package_name}.{info.name}\"`.",
               "`inspect.getmembers(module, inspect.isclass)` lists classes; keep those whose `__module__` equals the module's name, so re-exported classes are not counted twice."],
        solution="""
        import importlib, inspect, pkgutil


        def discover_tools(package_name):
            package = importlib.import_module(package_name)
            found = {}
            for info in pkgutil.iter_modules(package.__path__):
                if info.name.startswith("_"):
                    continue
                module = importlib.import_module(f"{package_name}.{info.name}")
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if cls.__module__ != module.__name__ or not isinstance(getattr(cls, "tool_name", None), str):
                        continue
                    if cls.tool_name in found:
                        other = found[cls.tool_name].__module__
                        raise ValueError(f"tool {cls.tool_name!r} defined in {other} and {module.__name__}")
                    found[cls.tool_name] = cls
            return dict(sorted(found.items()))
        """,
        why="""Plugin discovery turns "add a file to this folder" into "add a tool to the agent", without editing a central list. `pkgutil.iter_modules` lists the modules inside the
        package's folder, `import_module` loads each, and `inspect.getmembers` finds the classes. Checking `cls.__module__` matters: `calc.py` imports `WebSearch`, so it is
        visible there too, and without the check it would look like a duplicate. Private modules are skipped by convention, and a real duplicate is an error that names
        both places, because silently letting one plugin shadow another is a hard bug to find."""),
    fix("Break a circular import", "medium", tag="Data work",
        prompt="""`models.py` imports `validate` from `validation.py`, and `validation.py` imports `Ticket` from `models.py` to check types, so `import helpdesk_f6.models` fails with
        "cannot import name ... from partially initialized module". Fix the structure in `FILES`: keep `Ticket` in `models.py` and `validate` in `validation.py`, but make
        each file depend on the other **module** (not on names from it) and look names up inside functions, so the cycle is harmless whichever module is imported
        first.""",
        code="""
        FILES = {
            "helpdesk_f6/__init__.py": "",
            "helpdesk_f6/models.py": '''
        from helpdesk_f6.validation import validate

        class Ticket:
            def __init__(self, title):
                self.title = validate(title)
        ''',
            "helpdesk_f6/validation.py": '''
        from helpdesk_f6.models import Ticket

        def validate(title):
            if isinstance(title, Ticket):
                raise TypeError("a Ticket is not a title")
            if not title.strip():
                raise ValueError("empty title")
            return title.strip()
        ''',
        }
        """,
        tests="""
        from lessontools import make_tree, forget
        forget("helpdesk_f6")
        make_tree(FILES)
        import helpdesk_f6.models as models
        t = models.Ticket("  Refund missing ")
        assert t.title == "Refund missing"
        import helpdesk_f6.validation as validation
        for bad, err in [(t, TypeError), ("  ", ValueError)]:
            try:
                validation.validate(bad)
                assert False
            except err:
                pass
        forget("helpdesk_f6")
        import helpdesk_f6.validation
        assert helpdesk_f6.validation.validate(" ok ") == "ok"
        """,
        hints=["In `validation.py`, use `from helpdesk_f6 import models` and write `models.Ticket` inside `validate`; in `models.py`, use `from helpdesk_f6 import validation` and call `validation.validate(...)`.",
               "The grader imports the package both ways round, starting from `models` and from `validation`; fixing only one side fails the second import."],
        solution="""
        FILES = {
            "helpdesk_f6/__init__.py": "",
            "helpdesk_f6/models.py": '''
        from helpdesk_f6 import validation

        class Ticket:
            def __init__(self, title):
                self.title = validation.validate(title)
        ''',
            "helpdesk_f6/validation.py": '''
        from helpdesk_f6 import models

        def validate(title):
            if isinstance(title, models.Ticket):
                raise TypeError("a Ticket is not a title")
            if not title.strip():
                raise ValueError("empty title")
            return title.strip()
        ''',
        }
        """,
        why="""Importing `models` first runs `models.py` until its first line, which imports `validation`, which asked for the name `Ticket` from `models`, a module that existed in
        `sys.modules` but had not reached the `class Ticket` line yet. Importing the **module** instead of the name only needs the module object to exist, which it does, and
        `models.Ticket` and `validation.validate` are looked up when the functions are **called**, by which time both files have finished loading. Both sides need the
        change: with only `validation.py` fixed, importing `validation` first runs `models.py`, which still asks for the name `validate` from a half-loaded module. The cleaner long-term fix is often to remove the cycle
        (here, validation could check `type(title).__name__` or accept only strings), but depending on modules rather than names inside a cycle is the standard tactical
        fix, and it works whichever module is imported first."""),
    trace("sys.modules, reload and forget", "medium",
        prompt="Fill in `state` after each marked line.",
        code="""
        import importlib, sys
        from lessontools import make_tree, forget

        make_tree({"config_t7.py": '''
        import itertools
        LOADS = globals().get("LOADS", 0) + 1
        VALUE = "first"
        '''})

        import config_t7
        state = (config_t7.LOADS, config_t7.VALUE)  # row: "first import"
        import config_t7
        config_t7.VALUE = "patched"
        state = (config_t7.LOADS, config_t7.VALUE)  # row: "second import"
        old = config_t7
        importlib.reload(config_t7)
        state = (config_t7.LOADS, config_t7.VALUE, config_t7 is old)  # row: "after reload"
        forget("config_t7")
        import config_t7
        state = (config_t7.LOADS, config_t7.VALUE, config_t7 is old)  # row: "after forget"
        """,
        trace_vars=["state"],
        hints=["`reload` re-runs the file in the **same** module object, so `globals()` still has the old names. After removing it from `sys.modules`, the next import creates a new object."],
        why="""The second `import` finds the module in `sys.modules` and runs nothing, so only the manual patch changes `VALUE`. `importlib.reload` re-executes the file inside the existing
        module object: old globals are still there when the code runs, so `LOADS` counts to 2, and `VALUE` is reset by the re-executed assignment. Forgetting the module
        and importing again builds a brand-new module object with fresh globals, so `LOADS` is 1 again and the object differs from the old one, which anyone holding the
        old module (or names imported from it) would still be using."""),
    predict("Live module attributes versus copied names", "medium",
        code="""
        from lessontools import make_tree

        make_tree({"settings_p8.py": '''
        MODEL = "small"
        LIMITS = {"rpm": 60}

        def use_large():
            global MODEL
            MODEL = "large"
            LIMITS["rpm"] = 600
        '''})
        import settings_p8
        from settings_p8 import MODEL, LIMITS, use_large

        use_large()
        print(MODEL, settings_p8.MODEL)
        print(LIMITS, settings_p8.LIMITS is LIMITS)
        settings_p8.LIMITS = {"rpm": 1}
        print(LIMITS, settings_p8.LIMITS)
        """,
        hints=["`from m import NAME` binds the object NAME referred to at import time. Rebinding the module global does not change it; mutating the shared object does."],
        why="""`use_large` **rebinds** the module global `MODEL`, so the module sees `"large"` but the importer's `MODEL` still refers to the string `"small"`. For `LIMITS`, the function
        **mutates** the dict, which both names share, so the change is visible through both. Replacing `settings_p8.LIMITS` with a new dict rebinds the module's name only, and
        the importer keeps the old dict. This is the same rule as variables and objects (2.4) applied to modules, and the reason configuration should be read through the
        module (`settings.MODEL`) or a function, not copied out at import time."""),
    write("An optional dependency with a helpful error", "medium", tag="Data work",
        prompt="""Libraries import heavy optional dependencies lazily. Write `optional_import(name, extra)` that returns the imported module if available, and otherwise a placeholder
        object whose **attribute access** raises `ImportError(f"{name} is required for this feature: pip install 'mylib[{extra}]'")`, so the error appears only when the feature
        is used. Also write `has_module(name)` using `importlib.util.find_spec` without importing.""",
        code="""
        import importlib, importlib.util

        def optional_import(name, extra):
            pass

        def has_module(name):
            pass
        """,
        tests="""
        json_mod = optional_import("json", "json")
        assert json_mod.dumps([1]) == "[1]"
        pdf = optional_import("pdf_parser_that_does_not_exist", "pdf")
        try:
            pdf.parse("x.pdf")
            assert False
        except ImportError as e:
            assert str(e) == "pdf_parser_that_does_not_exist is required for this feature: pip install 'mylib[pdf]'"
        assert has_module("json") and not has_module("pdf_parser_that_does_not_exist") and has_module("collections.abc")
        assert repr(pdf).startswith("<missing optional module")
        """,
        hints=["Try `importlib.import_module(name)` and catch `ImportError`; return an instance of a small class whose `__getattr__` raises.",
               "`importlib.util.find_spec(name) is not None` checks availability without running the module."],
        solution="""
        import importlib, importlib.util


        class _Missing:
            def __init__(self, name, extra):
                self._name, self._extra = name, extra

            def __getattr__(self, attr):
                raise ImportError(f"{self._name} is required for this feature: pip install 'mylib[{self._extra}]'")

            def __repr__(self):
                return f"<missing optional module {self._name}>"


        def optional_import(name, extra):
            try:
                return importlib.import_module(name)
            except ImportError:
                return _Missing(name, extra)


        def has_module(name):
            try:
                return importlib.util.find_spec(name) is not None
            except ModuleNotFoundError:
                return False
        """,
        why="""Optional features (PDF parsing, GPU backends, a specific vector store) should not force every user to install their dependencies, nor fail with a bare
        `ModuleNotFoundError` deep inside the code. The placeholder delays the failure until the feature is actually used and turns it into instructions, naming the
        **extra** that installs it (15.2). `__getattr__` is only called for attributes that are not found normally (9.3), so `_name` and `_extra` still work. `find_spec`
        answers "is it installed?" without running the module's import-time code; it raises `ModuleNotFoundError` when a parent package is missing, hence the `try`."""),
    fix("Star imports that export too much", "medium", tag="Data work",
        prompt="""`from textkit_f10 import *` is used in notebooks, but it also exports `re`, `json` and the internal helper `normalise`, shadowing users' own names. Define the public
        API explicitly with `__all__` in `FILES` so a star import gives exactly `clean` and `tokenize`.""",
        code="""
        FILES = {
            "textkit_f10.py": '''
        import json, re

        def normalise(text):
            return re.sub(r"[ ]+", " ", text).strip()

        def clean(text):
            return normalise(text).lower()

        def tokenize(text):
            return clean(text).split(" ")
        ''',
        }
        """,
        tests="""
        from lessontools import make_tree, forget
        forget("textkit_f10")
        make_tree(FILES)
        ns = {}
        exec("from textkit_f10 import *", ns)
        assert sorted(k for k in ns if not k.startswith("__")) == ["clean", "tokenize"]
        import textkit_f10
        assert textkit_f10.tokenize("  Refund   Policy ") == ["refund", "policy"] and textkit_f10.normalise(" a  b ") == "a b"
        """,
        hints=["Add `__all__ = [\"clean\", \"tokenize\"]` to the module; names not listed stay importable explicitly."],
        solution="""
        FILES = {
            "textkit_f10.py": '''
        import json, re

        __all__ = ["clean", "tokenize"]

        def normalise(text):
            return re.sub(r"[ ]+", " ", text).strip()

        def clean(text):
            return normalise(text).lower()

        def tokenize(text):
            return clean(text).split(" ")
        ''',
        }
        """,
        why="""Without `__all__`, `import *` copies every top-level name that does not start with an underscore, including modules the file imported and internal helpers, so a user's
        own `json` or `normalise` can be silently replaced. `__all__` declares the public API: star imports take exactly those names, documentation tools and type checkers
        use it, and everything else remains reachable by explicit import (`from textkit_f10 import normalise`) for those who really need it. Renaming the helper to
        `_normalise` would also hide it from star imports and signal that it is private."""),
)

section("hard", "Hard",
    write("Find import cycles in a project", "hard", tag="Data work",
        prompt="""Write `import_graph(root, package)` that reads every `.py` file under `root/package` with `ast` (without importing), and returns a dict from each module's dotted name to
        the sorted list of modules **inside the package** it imports (via `import x` or `from x import y`, resolving relative imports; `from . import name` refers to the
        submodule `name` if such a file exists). Then write `find_cycles(graph)` returning the sorted list of cycles, each as a list of module names starting from the
        alphabetically smallest member, in import order.""",
        code="""
        import ast
        from pathlib import Path

        def import_graph(root, package):
            pass

        def find_cycles(graph):
            pass
        """,
        tests="""
        from lessontools import make_tree
        root = make_tree({
            "billing/__init__.py": "from .api import charge",
            "billing/api.py": "from .models import Invoice\\nfrom . import tax\\nimport json",
            "billing/models.py": "from billing.api import charge\\nimport billing.util",
            "billing/tax.py": "from .rates import RATE",
            "billing/rates.py": "from . import tax\\nRATE = 0.2",
            "billing/util.py": "import os",
        }, on_path=False)
        g = import_graph(root, "billing")
        assert g == {"billing": ["billing.api"], "billing.api": ["billing.models", "billing.tax"], "billing.models": ["billing.api", "billing.util"],
                     "billing.rates": ["billing.tax"], "billing.tax": ["billing.rates"], "billing.util": []}
        assert find_cycles(g) == [["billing.api", "billing.models"], ["billing.rates", "billing.tax"]]
        assert find_cycles({"a": ["b"], "b": ["c"], "c": []}) == []
        assert find_cycles({"a": ["b"], "b": ["c"], "c": ["a"]}) == [["a", "b", "c"]]
        """,
        hints=["Module names: `billing/api.py` is `billing.api` and `billing/__init__.py` is `billing`. The package of a module is its own name for `__init__`, otherwise its parent.",
               "For `ast.ImportFrom`, `node.level` counts leading dots; drop `level - 1` parts from the package name, then append `node.module` if any.",
               "Cycles: run a DFS from each node keeping the current path; when you reach a node already on the path, the slice from it is a cycle; rotate it to start at its smallest name and store it in a set of tuples."],
        solution="""
        import ast
        from pathlib import Path


        def _module_name(path, root):
            parts = list(path.relative_to(root).with_suffix("").parts)
            if parts[-1] == "__init__":
                parts.pop()
            return ".".join(parts)


        def import_graph(root, package):
            root = Path(root)
            files = {_module_name(p, root): p for p in (root / package).rglob("*.py")}
            graph = {}
            for name, path in files.items():
                pkg = name if path.name == "__init__.py" else name.rpartition(".")[0]
                deps = set()
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    if isinstance(node, ast.Import):
                        targets = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        if node.level:
                            parts = pkg.split(".")
                            base = parts[: len(parts) - (node.level - 1)]
                            mod = ".".join(base + ([node.module] if node.module else []))
                        else:
                            mod = node.module
                        targets = []
                        for alias in node.names:
                            full = f"{mod}.{alias.name}"
                            targets.append(full if full in files else mod)
                    else:
                        continue
                    for t in targets:
                        if t in files and t != name:
                            deps.add(t)
                graph[name] = sorted(deps)
            return dict(sorted(graph.items()))


        def find_cycles(graph):
            cycles = set()

            def dfs(node, path, on_path):
                for nxt in graph.get(node, []):
                    if nxt in on_path:
                        cycle = path[path.index(nxt):]
                        i = cycle.index(min(cycle))
                        cycles.add(tuple(cycle[i:] + cycle[:i]))
                    elif len(path) < len(graph) + 1:
                        on_path.add(nxt)
                        path.append(nxt)
                        dfs(nxt, path, on_path)
                        path.pop()
                        on_path.discard(nxt)

            for start in graph:
                dfs(start, [start], {start})
            return [list(c) for c in sorted(cycles)]
        """,
        why="""Reading imports with `ast` shows a project's structure **without running it**, which is safe on code with import-time side effects and is how tools such as `pydeps`,
        `import-linter` and Ruff's import rules work. Relative imports are resolved with the module's package and the number of leading dots, and `from . import tax` counts
        as a dependency on the submodule `tax` (not on the package) because that file exists, while `from .api import charge` depends on `billing.api`. The cycle search is a depth-first search that notices when it reaches a module already on the
        current path (16.4); rotating each cycle to start at its smallest name makes the same cycle found from different starting points identical. Running this in CI
        and failing on new cycles keeps a growing codebase layered."""),
    fix("Read the code: import-time side effects", "hard", tag="GenAI",
        prompt="""`assistant_f12/client.py` connects to the model service, reads the API key and prints a banner **at import time**, so merely importing the package (in tests, in a
        notebook, in a worker process) opens a connection and crashes when the key is missing. Move all of it into a function `get_client()` that creates the client on the
        first call and returns the same one afterwards (`functools.cache`), reading the key from the environment then; importing must have no side effects.""",
        code="""
        FILES = {
            "assistant_f12/__init__.py": "",
            "assistant_f12/connection.py": '''
        CONNECTIONS = []

        class Client:
            def __init__(self, api_key):
                if not api_key:
                    raise RuntimeError("ASSISTANT_KEY is not set")
                self.api_key = api_key
                CONNECTIONS.append(self)

            def ask(self, q):
                return f"answer to {q}"
        ''',
            "assistant_f12/client.py": '''
        import os
        from assistant_f12.connection import Client

        print("assistant client ready")
        CLIENT = Client(os.environ.get("ASSISTANT_KEY", ""))

        def ask(question):
            return CLIENT.ask(question)
        ''',
        }
        """,
        tests="""
        import io, os, contextlib
        from lessontools import make_tree, forget
        forget("assistant_f12")
        make_tree(FILES)
        os.environ.pop("ASSISTANT_KEY", None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            import assistant_f12.client as client
        import assistant_f12.connection as connection
        assert buf.getvalue() == "" and connection.CONNECTIONS == []
        os.environ["ASSISTANT_KEY"] = "sk-test"
        assert client.ask("refund?") == "answer to refund?" and client.get_client() is client.get_client()
        assert len(connection.CONNECTIONS) == 1
        os.environ.pop("ASSISTANT_KEY")
        """,
        hints=["In `client.py`: `@functools.cache def get_client(): return Client(os.environ.get(\"ASSISTANT_KEY\", \"\"))`, and `ask` calls `get_client().ask(question)`.",
               "Delete the `print` and the module-level `CLIENT`."],
        solution="""
        FILES = {
            "assistant_f12/__init__.py": "",
            "assistant_f12/connection.py": '''
        CONNECTIONS = []

        class Client:
            def __init__(self, api_key):
                if not api_key:
                    raise RuntimeError("ASSISTANT_KEY is not set")
                self.api_key = api_key
                CONNECTIONS.append(self)

            def ask(self, q):
                return f"answer to {q}"
        ''',
            "assistant_f12/client.py": '''
        import functools, os
        from assistant_f12.connection import Client


        @functools.cache
        def get_client():
            return Client(os.environ.get("ASSISTANT_KEY", ""))


        def ask(question):
            return get_client().ask(question)
        ''',
        }
        """,
        why="""Module top-level code runs on import, for every importer, so expensive or stateful setup there leaks into tests (which may not have the key), tools that only want the
        module's names, and every multiprocessing worker (14.3). Moving setup into `get_client()` makes importing free and deterministic, reads the environment when the client
        is actually needed (12.4), and `functools.cache` makes it a lazily created singleton, created once on first use; tests can call `get_client.cache_clear()` or patch
        `get_client` (13.3) to swap in a fake. The banner belonged in logging at start-up, not in a library's import."""),
    predict("Shadowing and namespace packages", "hard",
        code="""
        import sys
        from lessontools import make_tree, forget

        make_tree({"statistics.py": '''
        def mean(values):
            return "my mean"
        '''})
        forget("statistics")
        import statistics
        print(statistics.mean([1, 2, 3]), statistics.__file__.endswith("statistics.py") and "site" not in statistics.__file__)
        sys.path.pop(0)
        forget("statistics")
        import statistics
        print(statistics.mean([1, 2, 3]))
        make_tree({"plugins_p13/alpha.py": "NAME = 'alpha'"})
        import plugins_p13.alpha
        import plugins_p13
        print(plugins_p13.alpha.NAME, getattr(plugins_p13, "__file__", None), type(plugins_p13.__path__).__name__)
        """,
        hints=["The first folder on `sys.path` that contains a matching name wins, even over the standard library for most modules.",
               "A folder without `__init__.py` imports as a namespace package: it has a `__path__` but no `__file__`."],
        why="""Because `make_tree` put the new folder first on `sys.path`, a local file named `statistics.py` **shadows** the standard library module, so `statistics.mean` is the local
        one. Removing that folder from the path and the cached module restores the real `statistics`. This is the classic "my script is called `random.py` (or `json.py`,
        `email.py`, `test.py`) and imports break" bug: never name your files after standard library or installed modules. The `plugins_p13` folder has no `__init__.py`, so
        it is a **namespace package**: importable, with a `__path__` for finding submodules but no `__file__`, which is why regular packages should always have
        `__init__.py`."""),
)

section("interview", "Interview questions",
    explain("What happens when Python executes `import x`?", "medium", tag="Interview",
        why="""Python first checks `sys.modules`; if `x` is already imported, it binds the name to that module object and does nothing else. Otherwise it **finds** the module: for a
        dotted name it imports the parent packages first, then asks the finders in `sys.meta_path` (which search `sys.path` entries: the script's folder, `PYTHONPATH`, the
        standard library, `site-packages`, and handle built-in, frozen, extension and zip modules) for a **spec** describing how to load it. It **creates** a module object,
        inserts it into `sys.modules` **before** executing (which is what makes circular imports partially work), and **executes** the module's code in the module's
        namespace, compiling it to bytecode and caching that in `__pycache__`. Finally it binds the name in the importer's namespace. Consequences: module code runs once per
        process, all importers share the module object, `from x import y` copies a reference at import time, and import-time side effects run wherever the module is imported."""),
    explain("How do you fix a circular import?", "medium", tag="Interview",
        why="""First understand it: module A imports B at the top, B imports A, so B receives a partially initialised A and fails when it asks for a name A has not defined yet. The best
        fix is structural: find what both modules need from each other and move it into a third module that both import (shared types, constants, interfaces), or merge two
        modules that are really one; this restores a one-way dependency graph. Tactical fixes: import the module rather than names (`import a` and use `a.helper` inside
        functions), move the import into the function that needs it, or, when the dependency exists only for type annotations, import under `if TYPE_CHECKING:` and use
        string or lazy annotations. Dependency injection (passing the object in instead of importing it) also breaks cycles. Tools such as `import-linter` or a CI check of
        the import graph prevent new cycles."""),
    explain("Your package imports fine in tests but fails with ModuleNotFoundError in production (or the reverse). What do you check?", "hard", tag="Interview",
        why="""Check **how the code is found**. Tests often pass because pytest inserts the project root (or test folders) into `sys.path`, or because the current working directory is the
        repository root, while production runs an **installed** package from another directory. Use a `src/` layout and install the project (`pip install -e .` or `uv sync`)
        so tests import the installed package exactly as production does. Check **packaging**: is the module included in the built wheel (package discovery settings in
        `pyproject.toml`, missing `__init__.py`, data files), and are optional dependencies installed in that environment? Check for **shadowing**: a local file or folder named
        like a dependency (`requests.py`, `config/` without `__init__.py`), or two installed distributions providing the same package. Check **which interpreter and environment**
        run the code (`sys.executable`, `sys.path`, `pip list` in that environment), and relative imports in modules run as scripts instead of with `python -m`. Printing
        `module.__file__` and `sys.path` at the failure point usually settles it in minutes."""),
)

recap(
    "`import` checks `sys.modules`, searches `sys.path`, runs the module once, and caches it; every importer shares the one module object.",
    "`from m import name` copies a reference at import time; read changing values through the module (`m.name`).",
    "Packages are folders with `__init__.py`; use relative (`from . import x`) or absolute imports inside them, and `python -m pkg.module` to run their modules.",
    "Circular imports hand a partially initialised module to the other side: restructure, import modules instead of names, or import inside functions.",
    "Keep import time free of side effects (lazy `get_client()`), use `__all__` for public APIs, `importlib.import_module` for plugins, and never name files after libraries.",
)
