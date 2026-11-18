from lesson import *
from diagrams import *

lesson(
    id="m9-1", num="9.1", title="Classes and instances",
    intro="A class bundles data with the functions that work on it. What happens step by step when you create an object "
          "and call a method, what `self` really is, where attributes live and how Python finds them, class attributes "
          "and the shared-mutable trap, bound methods, and when a class is the right tool. Applied to conversations, "
          "running statistics, token budgets and a small search index.",
    desc="Attributes, methods, `self`, and the class attribute trap.",
    keys="class instance object self __init__ constructor attribute method bound method class attribute instance attribute __dict__ lookup order mutable class attribute state encapsulation type isinstance",
)

term("Class", "A blueprint for objects: it defines the methods and default attributes that every object of that type shares.")
term("Instance", "One object made from a class, with its own attribute values. `Conversation()` creates a new instance of `Conversation`.")
term("self", "The first parameter of a method: the instance the method was called on. `obj.method(x)` runs `Class.method(obj, x)`.")
term("Attribute", "A name stored on an object (`obj.name`) or on its class. Instance attributes live in `obj.__dict__`.")

section("why", "Why classes",
    fig(stage_map(9, "a provider layer for LLMs"), "Module 9 at a glance: classes, special methods, properties, inheritance and composition, building up to a provider layer."),
    p("""You have used objects from the first lesson: a list holds items **and** has methods such as `append` and `sort` that work on those
    items; a string has `split` and `upper`. A **class** lets you define your own kind of object in the same way: some **data**
    (attributes) and the **functions that work on that data** (methods), kept together. The class is the blueprint; each object made
    from it is an **instance**, with its own data but the same methods."""),
    p("""Without classes, the same program is a dict plus loose functions that all take the dict as their first argument:
    `add_message(conv, role, text)`, `last_messages(conv, n)`. That works, and for small scripts it is fine. Classes become worth it
    when the data has **rules** that must always hold (a role must be valid, a budget must not go negative), when several functions
    share and change the same state, and when you want many independent objects of the same kind. The class puts the rules in one
    place, and code that uses it can only change the data through its methods."""),
    ex("""
    class Conversation:
        def __init__(self, system_prompt):
            self.messages = [{"role": "system", "content": system_prompt}]

        def add(self, role, content):
            if role not in ("user", "assistant"):
                raise ValueError(f"bad role {role!r}")
            self.messages.append({"role": role, "content": content})

        def last(self, n):
            return self.messages[-n:]

    chat = Conversation("Be brief.")
    chat.add("user", "Refund?")
    chat.add("assistant", "5 days.")
    print(len(chat.messages), chat.last(1))
    other = Conversation("Be formal.")
    print(len(other.messages), type(chat).__name__, isinstance(chat, Conversation))
    """, "first_class.py"),
    callout("sql", "SQL / Power BI", """A class is like a table definition and its instances are rows: the definition says which columns
    exist (attributes) and the rules they follow (constraints), and every row has its own values. Methods are like stored procedures
    bound to the table: the only sanctioned way to change the data, so the rules are always applied."""),
)

section("steps", "What happens when you create an object and call a method",
    fig(chain(["Ticket('Refund')", "__new__ makes an|empty object", "__init__(self, ...)|fills its attributes", ("the object is bound|to the name", "good")]),
        "Calling a class creates the object and then runs `__init__` on it; `self` is simply that new object."),
    p("""The `class` statement runs once, like `def`: it executes the class body and creates a **class object** (here `Conversation`)
    that holds the functions defined inside it. Calling the class, `Conversation("Be brief.")`, then does three things in order.
    First Python creates a new, **empty** instance. Then it calls `__init__` with that instance as the first argument, followed by
    the arguments you passed: `Conversation.__init__(new_object, "Be brief.")`. `__init__` sets up the instance's attributes and must
    return `None`. Finally the call returns the new instance. `__init__` is often called the constructor; strictly it is the
    **initialiser**, since the object already exists when it runs."""),
    p("""**`self`** is simply the name, by convention, of that first parameter: the instance the method is working on. When you call a
    method on an instance, `chat.add("user", "Hi")`, Python looks up `add` on the class and calls it with the instance inserted as
    the first argument: `Conversation.add(chat, "user", "Hi")`. That is the whole mechanism. Inside the method, `self.messages` means
    "the `messages` attribute of whichever instance this call is for", which is how one method serves every instance."""),
    ex("""
    class Counter:
        def __init__(self, start=0):
            print("  __init__ with", start)
            self.value = start

        def bump(self, by=1):
            self.value += by
            return self.value

    c = Counter(10)
    print(c.bump(), Counter.bump(c, 5), c.value)     # the two calls are the same thing
    d = Counter()
    print(d.bump(), c.value)                          # separate instances, separate state
    try:
        Counter.bump()
    except TypeError as e:
        print("TypeError:", e)
    """, "self.py"),
    p("""The `TypeError` at the end is what happens when the instance is missing: calling the function through the class without one
    leaves `self` unfilled. You will also see the reverse mistake, a method defined without `self`, which fails with "takes 0
    positional arguments but 1 was given" because Python always passes the instance (problem 3)."""),
)

section("attributes", "Where attributes live, and how Python finds them",
    fig(flowchart({
        "start": ("start", 0, 0, "obj.name"),
        "inst": ("ask", 0, 1, "in the instance's|__dict__?"),
        "use": ("good", 1, 1, "use it"),
        "cls": ("ask", 0, 2, "in the class or a base|(following the MRO)?"),
        "meth": ("good", 1, 2, "use it (a function|becomes a bound method)"),
        "err": ("bad", 0, 3, "AttributeError"),
    }, [("start", "inst"), ("inst", "use", "yes"), ("inst", "cls", "no"), ("cls", "meth", "yes"), ("cls", "err", "no")], cell=(250, 80),
        label="attribute lookup on an instance"),
        "Attribute lookup checks the instance first, then the class and its bases, which is why a class attribute is shared until an instance shadows it."),
    p("""Instance attributes are stored in a dict on each instance, `obj.__dict__` (also available as `vars(obj)`). Assigning
    `self.messages = [...]` in `__init__` adds the key `"messages"` to that dict. Methods are **not** stored on the instance; they live in
    the class's own namespace, `Conversation.__dict__`, shared by every instance. So each instance carries only its own data."""),
    p("""Reading `obj.name` follows a fixed **lookup order**: first the instance's `__dict__`, then the class (and then the class's base
    classes, 9.4). The first place that has the name wins; if none has it, Python raises `AttributeError`. **Assigning**
    `obj.name = value` is different: it always writes to the **instance's** dict, never to the class. That asymmetry explains most of
    the surprises with class attributes, below."""),
    ex("""
    class Model:
        provider = "acme"                     # a class attribute: stored on the class

        def __init__(self, name):
            self.name = name                  # an instance attribute: stored on the instance

    m = Model("small")
    print(vars(m), "provider" in vars(m), m.provider)
    print(sorted(k for k in vars(Model) if not k.startswith("__")))
    m.provider = "other"                      # writes to the instance, shadowing the class attribute
    print(m.provider, Model.provider, Model("large").provider)
    del m.provider                            # remove the instance's copy: the class value shows again
    print(m.provider)
    try:
        m.temperature
    except AttributeError as e:
        print("AttributeError:", e)
    """, "lookup.py"),
    p("""Python also lets you add attributes to an instance anywhere, `m.anything = 1`, even outside the class. That flexibility is useful
    occasionally, but it also means a typo such as `self.mesages = []` silently creates a new attribute instead of raising an error.
    A good habit is to create **every** instance attribute in `__init__`, even if only as `None`, so a reader can see the complete
    state of the object in one place. (`__slots__`, 9.3, can enforce it.)"""),
)

section("classattrs", "Class attributes and the shared-mutable trap",
    p("""A name assigned in the class body, outside any method, is a **class attribute**: one value stored on the class and shared by all
    instances. Class attributes are right for **constants** that belong to the type (`VALID_ROLES`, `DEFAULT_MODEL`) and for data that
    is genuinely shared (a count of instances created). Reading them through `self` works because of the lookup order; changing a
    shared value deliberately is done through the class, `Counter.created += 1`."""),
    p("""The trap is a **mutable** class attribute used as if it were per instance. `history = []` in the class body creates **one** list,
    and `self.history.append(x)` does not assign anything, it **reads** `self.history`, which finds the class's list, and changes it in
    place. Every instance appends to the same list (2.2). Assignment would have created an instance attribute; mutation does not. The
    fix is to create mutable state in `__init__`, so each instance gets its own (problem 6)."""),
    ex("""
    class Bad:
        history = []                          # ONE list, shared by every instance
        def record(self, x):
            self.history.append(x)            # reads the class list and mutates it

    class Good:
        MAX = 3                               # an immutable class constant: fine to share
        def __init__(self):
            self.history = []                 # a new list per instance
        def record(self, x):
            self.history.append(x)
            del self.history[:-self.MAX]      # keep the last MAX items

    a, b = Bad(), Bad()
    a.record("a1"); b.record("b1")
    print(a.history, b.history, a.history is Bad.history)

    g, h = Good(), Good()
    for i in range(5):
        g.record(i)
    h.record("only")
    print(g.history, h.history)
    """, "shared_mutable.py"),
    p("""`del self.history[:-self.MAX]` deletes everything except the last `MAX` items, in place, keeping the same list. Notice
    `self.MAX` reads the class constant through the instance; a subclass could override `MAX` (9.4) and the method would follow. The
    same trap exists for default argument values (2.4): `def __init__(self, tags=[])` shares one list between all instances created
    without `tags` (problem 9)."""),
)

section("methods", "Methods are functions, bound to an instance",
    p("""A method is an ordinary function stored on the class. Accessing it through an instance, `chat.add`, produces a **bound method**:
    a small object that remembers both the function (`__func__`) and the instance (`__self__`), so calling it later inserts the
    instance automatically. You can store a bound method in a variable, pass it as a callback, or put it in a list, and it keeps
    working on its instance. That is why `sorted(items, key=obj.score)` or `button.on_click(handler.save)` style code works."""),
    ex("""
    class Scorer:
        def __init__(self, keywords):
            self.keywords = set(keywords)

        def score(self, text):
            return len(self.keywords & set(text.lower().split()))

    refunds = Scorer(["refund", "money", "return"])
    s = refunds.score                          # a bound method: remembers refunds
    docs = ["How to reset a password", "Refund your money", "Return and refund policy"]
    print(sorted(docs, key=s, reverse=True))
    print(s.__self__ is refunds, s.__func__ is Scorer.score, s("refund refund"))
    print([refunds.score(d) for d in docs] == list(map(refunds.score, docs)))
    """, "bound_methods.py"),
    p("""Methods call each other through `self` (`self.validate(x)` inside `add`), which also means a subclass can replace one of them and
    the others will use the new version (9.4). A method that does not use `self` at all is a hint that it might be a plain function,
    or a `staticmethod` (9.6)."""),
)

section("when", "When a class is the right tool",
    p("""Use a class when you have **state plus rules**: data that must stay consistent and several operations that change it
    (a conversation history with a token limit, a cache with statistics, a rate limiter, a client holding a connection and settings).
    Use a class when you need **many independent objects** of the same kind with the same behaviour. And use one when a library expects
    it: PyTorch models are classes with a `forward` method, scikit-learn estimators are classes with `fit` and `predict`, and Pydantic
    models are classes (11.4)."""),
    p("""Do not use a class just to group functions that share no state: a module does that. Do not write a class with only `__init__` and
    one method: that is a function, or a closure (3.4), in disguise. And for objects that are mainly **data** with little behaviour
    (a record, a config, an API response), a `dataclass` (11.3) writes `__init__`, `__repr__` and `__eq__` for you. The closures of 7.3
    and 7.4 (the circuit breaker, the token bucket) are a good test: they are state plus operations, and as classes they become easier to
    read, inspect and extend (problem 14)."""),
    ex("""
    class RunningMean:
        \"\"\"Mean of a stream of numbers, without storing them.\"\"\"

        def __init__(self):
            self.count = 0
            self.total = 0.0

        def update(self, x):
            self.count += 1
            self.total += x
            return self

        def mean(self):
            return self.total / self.count if self.count else 0.0

    latency = RunningMean()
    for ms in [120, 95, 300]:
        latency.update(ms)
    print(round(latency.mean(), 2), latency.count, vars(latency))
    print(RunningMean().update(1).update(3).mean())     # update returns self, so calls chain
    """, "running_mean.py"),
)

section("warmup", "Warm-up",
    predict("Objects and their state", "easy",
        code="""
        class Budget:
            currency = "USD"

            def __init__(self, limit):
                self.limit = limit
                self.spent = 0

            def spend(self, amount):
                self.spent += amount
                return self.limit - self.spent

        a = Budget(10)
        b = Budget(5)
        print(a.spend(3), a.spend(4), b.spend(1))
        print(a.spent, b.spent, a.currency, Budget.currency)
        print(vars(b), Budget.spend(b, 2))
        """,
        hints=["Each instance has its own `limit` and `spent`; `currency` lives on the class."],
        why="""`a` and `b` keep separate `spent` values in their own `__dict__`, so `a` goes 7 then 3, while `b` goes to 4. `currency` is found on
        the class through either name. `vars(b)` shows only the instance attributes, and `Budget.spend(b, 2)` is the explicit form of
        `b.spend(2)`."""),
    write("A conversation with rules", "easy", tag="GenAI",
        prompt="""Write a class `Conversation` with `__init__(self, system_prompt)` storing the messages as a list of dicts, starting with
        the system message. Methods: `add(role, content)` appends a message, raising `ValueError` for roles other than `"user"` and
        `"assistant"` and for empty or whitespace-only content (stored stripped); `turns()` returns the number of non-system messages;
        `last(n)` returns a **new list** of the last `n` non-system messages.""",
        code="""
        class Conversation:
            pass
        """,
        tests="""
        c = Conversation("Be brief.")
        c.add("user", "  Refund? ")
        c.add("assistant", "Within 5 days.")
        assert c.turns() == 2 and c.messages[0] == {"role": "system", "content": "Be brief."}
        assert c.last(1) == [{"role": "assistant", "content": "Within 5 days."}]
        assert c.last(5) == [{"role": "user", "content": "Refund?"}, {"role": "assistant", "content": "Within 5 days."}]
        c.last(1).clear()
        assert c.turns() == 2
        for role, content in [("system", "x"), ("bot", "x"), ("user", "   ")]:
            try:
                c.add(role, content)
                assert False, role
            except ValueError:
                pass
        assert Conversation("Other").turns() == 0
        """,
        hints=["Keep `self.messages` as the single source of truth; `turns` and `last` compute from it.", "Slicing (`[1:]`, `[-n:]`) always builds a new list."],
        solution="""
        class Conversation:
            ROLES = ("user", "assistant")

            def __init__(self, system_prompt):
                self.messages = [{"role": "system", "content": system_prompt}]

            def add(self, role, content):
                if role not in self.ROLES:
                    raise ValueError(f"role must be one of {self.ROLES}, got {role!r}")
                text = content.strip()
                if not text:
                    raise ValueError("content must not be empty")
                self.messages.append({"role": role, "content": text})

            def turns(self):
                return len(self.messages) - 1

            def last(self, n):
                return self.messages[1:][-n:]
        """,
        why="""All rules live in `add`, so no message can get into the history without passing them; code that uses the class cannot forget a
        check. The valid roles are a class constant, shared and immutable. `last` returns a slice, a new list, so a caller clearing it
        cannot damage the conversation; returning `self.messages` itself would hand out the internal list (2.4), though the dicts inside are
        still shared, which 9.3 addresses. `turns` is computed rather than stored, so it can never get out of sync with the messages."""),
    fix("A method that forgets self", "easy", tag="Data work",
        prompt="""`Inventory` fails as soon as `add` is called. Fix the class so that `add(item, qty)` and `total()` work.""",
        code="""
        class Inventory:
            def __init__(self):
                self.items = {}

            def add(item, qty):
                items[item] = items.get(item, 0) + qty

            def total():
                return sum(self.items.values())
        """,
        tests="""
        inv = Inventory()
        inv.add("pen", 3)
        inv.add("pen", 2)
        inv.add("book", 1)
        assert inv.items == {"pen": 5, "book": 1} and inv.total() == 6
        assert Inventory().total() == 0
        """,
        hints=["Python passes the instance as the first argument of every method call. Name it `self`, and reach the attributes through it."],
        solution="""
        class Inventory:
            def __init__(self):
                self.items = {}

            def add(self, item, qty):
                self.items[item] = self.items.get(item, 0) + qty

            def total(self):
                return sum(self.items.values())
        """,
        why="""`inv.add("pen", 3)` calls `Inventory.add(inv, "pen", 3)`: three arguments for a function that declared two, hence "takes 2
        positional arguments but 3 were given". Even with the parameter added, `items` inside the method is a local or global name, not
        the instance's attribute; attributes are always reached through `self`. Unlike some languages, Python never adds `self`
        implicitly, which makes every attribute access visible in the code."""),
    predict("One list for every instance", "easy",
        code="""
        class Tracker:
            events = []
            count = 0

            def log(self, e):
                self.events.append(e)
                self.count += 1

        a, b = Tracker(), Tracker()
        a.log("start"); b.log("stop"); a.log("retry")
        print(a.events, b.events, Tracker.events is a.events)
        print(a.count, b.count, Tracker.count, vars(a))
        """,
        hints=["`append` mutates the object it finds; `+=` on an int assigns a new value to the instance."],
        why="""`self.events.append(e)` reads `events`, finds the class's single list and mutates it, so all instances see all three events.
        `self.count += 1` is different: it reads the class's `0`, adds one and **assigns** the result to `self.count`, which creates an
        instance attribute; so `a` counts 2, `b` counts 1, and the class value stays 0. Mutation goes to the shared object; assignment
        creates a per-instance one."""),
)

section("medium", "Medium",
    write("Running statistics", "medium", tag="ML",
        prompt="""Write a class `RunningStats` that tracks the count, mean and variance of a stream of numbers without storing them, using
        Welford's method: on each `update(x)`, `count += 1`, `delta = x - mean`, `mean += delta / count`, `m2 += delta * (x - mean)`.
        Provide `update(x)` (returning `self` so calls can chain), `mean()`, `variance()` (sample variance `m2 / (count - 1)`, `0.0` with
        fewer than two values) and `merge(other)` returning a **new** `RunningStats` combining two streams.""",
        code="""
        class RunningStats:
            pass
        """,
        tests="""
        s = RunningStats()
        for x in [2, 4, 4, 4, 5, 5, 7, 9]:
            s.update(x)
        assert s.count == 8 and s.mean() == 5.0 and round(s.variance(), 4) == 4.5714
        a, b = RunningStats(), RunningStats()
        for x in [2, 4, 4, 4]:
            a.update(x)
        for x in [5, 5, 7, 9]:
            b.update(x)
        m = a.merge(b)
        assert m.count == 8 and m.mean() == 5.0 and round(m.variance(), 4) == 4.5714 and a.count == 4
        assert RunningStats().update(3).variance() == 0.0 and RunningStats().mean() == 0.0
        """,
        hints=["For `merge`: `delta = b.mean - a.mean`, `n = a.n + b.n`, `mean = a.mean + delta * b.n / n`, `m2 = a.m2 + b.m2 + delta**2 * a.n * b.n / n`."],
        solution="""
        class RunningStats:
            def __init__(self):
                self.count = 0
                self._mean = 0.0
                self._m2 = 0.0

            def update(self, x):
                self.count += 1
                delta = x - self._mean
                self._mean += delta / self.count
                self._m2 += delta * (x - self._mean)
                return self

            def mean(self):
                return self._mean

            def variance(self):
                return self._m2 / (self.count - 1) if self.count > 1 else 0.0

            def merge(self, other):
                out = RunningStats()
                out.count = self.count + other.count
                if out.count == 0:
                    return out
                delta = other._mean - self._mean
                out._mean = self._mean + delta * other.count / out.count
                out._m2 = self._m2 + other._m2 + delta ** 2 * self.count * other.count / out.count
                return out
        """,
        why="""The state (`count`, `_mean`, `_m2`) and the rules for updating it belong together, and no caller can update one without the others.
        Welford's update avoids the cancellation error of the naive `sum(x**2) - n * mean**2` formula, which loses precision badly for large
        values with small spread. `merge` lets you compute statistics per data shard or per worker and combine them exactly, which is how
        distributed feature statistics are computed. The leading underscore on `_mean` and `_m2` is the convention for "internal, do not
        touch from outside" (9.3). Returning `self` from `update` allows chaining, as pandas and query builders do."""),
    fix("Every client shares one history", "medium", tag="GenAI",
        prompt="""Each `LLMClient` should keep its own request history and its own count. Two clients see each other's requests. Fix it.""",
        code="""
        class LLMClient:
            history = []
            settings = {"temperature": 0.0}

            def __init__(self, model):
                self.model = model

            def ask(self, prompt, **overrides):
                self.settings.update(overrides)
                self.history.append((self.model, prompt))
                return f"{self.model}: {prompt} @ {self.settings['temperature']}"
        """,
        tests="""
        small, large = LLMClient("small"), LLMClient("large")
        assert small.ask("hi") == "small: hi @ 0.0"
        assert large.ask("hello", temperature=0.7) == "large: hello @ 0.7"
        assert small.ask("again") == "small: again @ 0.0"
        assert small.history == [("small", "hi"), ("small", "again")] and large.history == [("large", "hello")]
        assert LLMClient("x").settings == {"temperature": 0.0}
        """,
        hints=["Both `history` and `settings` are mutable class attributes. Create them in `__init__`.",
               "`overrides` should apply to one request, not change the client's settings permanently."],
        solution="""
        class LLMClient:
            DEFAULTS = {"temperature": 0.0}

            def __init__(self, model):
                self.model = model
                self.history = []
                self.settings = dict(self.DEFAULTS)

            def ask(self, prompt, **overrides):
                settings = {**self.settings, **overrides}
                self.history.append((self.model, prompt))
                return f"{self.model}: {prompt} @ {settings['temperature']}"
        """,
        why="""Two shared mutable class attributes caused two bugs. `history` was one list for every client, so `small.history` contained the large
        model's request too. `settings.update(overrides)` changed the shared dict, so after `large` asked with `temperature=0.7`, `small`
        silently used 0.7 as well, a bug that would make an evaluation run non-reproducible. Creating both in `__init__` gives each client
        its own; keeping the defaults as an immutable-by-convention class constant (`DEFAULTS`) and copying them is the usual pattern. The
        per-request overrides now build a new dict and leave the client's settings alone (2.4)."""),
    write("A token budget", "medium", tag="GenAI",
        prompt="""Write a class `TokenBudget(limit)` for capping spend in an agent run. `spend(tokens, label)` records a charge and raises
        `BudgetExceeded` (define it, subclass of `Exception`) **without recording** if it would take the total over the limit;
        `remaining()` returns the tokens left; `breakdown()` returns a dict of total tokens per label, in first-seen order; `reset()`
        clears everything. Reject non-positive or non-integer token counts with `ValueError`.""",
        code="""
        class TokenBudget:
            pass
        """,
        tests="""
        b = TokenBudget(1000)
        b.spend(300, "retrieve"); b.spend(450, "generate"); b.spend(100, "retrieve")
        assert b.remaining() == 150 and b.breakdown() == {"retrieve": 400, "generate": 450}
        try:
            b.spend(200, "generate")
            assert False
        except BudgetExceeded as e:
            assert "200" in str(e) and "150" in str(e)
        assert b.remaining() == 150
        for bad in [0, -5, 2.5, True]:
            try:
                b.spend(bad, "x")
                assert False, bad
            except ValueError:
                pass
        b.reset()
        assert b.remaining() == 1000 and b.breakdown() == {}
        other = TokenBudget(10)
        assert other.remaining() == 10
        """,
        hints=["Store `self.limit` and a list or dict of charges. Check everything before changing anything.", "`isinstance(x, bool)` first: `True` is an `int`."],
        solution="""
        class BudgetExceeded(Exception):
            pass


        class TokenBudget:
            def __init__(self, limit):
                self.limit = limit
                self._by_label = {}

            def spent(self):
                return sum(self._by_label.values())

            def remaining(self):
                return self.limit - self.spent()

            def spend(self, tokens, label):
                if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens <= 0:
                    raise ValueError(f"tokens must be a positive integer, got {tokens!r}")
                if tokens > self.remaining():
                    raise BudgetExceeded(f"cannot spend {tokens} tokens on {label!r}: only {self.remaining()} left")
                self._by_label[label] = self._by_label.get(label, 0) + tokens

            def breakdown(self):
                return dict(self._by_label)

            def reset(self):
                self._by_label = {}
        """,
        why="""The class enforces its invariant, "spent never exceeds the limit", in the only method that changes the state, and it validates
        **before** modifying anything, so a rejected charge leaves the budget exactly as it was (the all-or-nothing rule of 7.3). The
        custom exception tells an agent loop precisely why it must stop, and its message includes both the request and what was left.
        `breakdown` returns a copy so callers cannot alter the records. Storing only the per-label totals is enough for this interface;
        keeping a list of every charge would allow an audit trail, at the cost of memory."""),
    trace("Instance, class and shadowing", "medium",
        prompt="Fill in `a_model`, `b_model` and `cls_model` after each marked line.",
        code="""
        class Agent:
            model = "small"

        a, b = Agent(), Agent()
        a_model, b_model, cls_model = a.model, b.model, Agent.model  # row: "start"
        a.model = "large"
        a_model, b_model, cls_model = a.model, b.model, Agent.model  # row: "set on a"
        Agent.model = "medium"
        a_model, b_model, cls_model = a.model, b.model, Agent.model  # row: "set on class"
        del a.model
        a_model, b_model, cls_model = a.model, b.model, Agent.model  # row: "del a.model"
        """,
        trace_vars=["a_model", "b_model", "cls_model"],
        hints=["Reading checks the instance first, then the class. Assigning through an instance writes to the instance."],
        why="""At first both instances find the class value. `a.model = "large"` creates an instance attribute that shadows the class one for `a`
        only. Changing `Agent.model` affects every instance that does not have its own value, here `b`. Deleting `a`'s attribute makes the
        lookup fall through to the class again, which now says `"medium"`."""),
    fix("Instances that share a default list", "medium", tag="Data work",
        prompt="""`Document(text, tags=[])` should give each document its own tags. Tagging one document tags others. Fix it.""",
        code="""
        class Document:
            def __init__(self, text, tags=[]):
                self.text = text
                self.tags = tags

            def tag(self, label):
                if label not in self.tags:
                    self.tags.append(label)
                return self
        """,
        tests="""
        a = Document("refund policy")
        b = Document("reset password")
        a.tag("billing")
        assert a.tags == ["billing"] and b.tags == []
        shared = ["faq"]
        c = Document("x", tags=shared)
        c.tag("new")
        assert c.tags == ["faq", "new"] and shared == ["faq"]
        """,
        hints=["The default list is created once, when `def __init__` runs (2.4). Use `None` and copy what the caller passes."],
        solution="""
        class Document:
            def __init__(self, text, tags=None):
                self.text = text
                self.tags = list(tags) if tags is not None else []

            def tag(self, label):
                if label not in self.tags:
                    self.tags.append(label)
                return self
        """,
        why="""Methods are functions, so their defaults follow the rule of 2.4: `tags=[]` is evaluated once and every `Document` created without
        tags received **the same** list. The `None` default plus a new list inside `__init__` fixes that. Copying a caller's list with
        `list(tags)` fixes a second, quieter aliasing bug: without it, `c.tag("new")` would also have changed the caller's `shared` list.
        An object should own its mutable state, which usually means copying mutable inputs at construction."""),
    write("A small inverted index", "medium", tag="RAG",
        prompt="""Write a class `KeywordIndex` with `add(doc_id, text)`, `remove(doc_id)` and `search(query)`. Words are lower-cased with
        `.,!?` stripped. `search` returns the sorted ids of documents containing **every** query word (an empty query returns `[]`).
        Adding an existing id replaces its text. Keep an inverted index (word to set of ids) so search does not scan every document,
        and remove ids from it correctly, including words that end up with no documents.""",
        code="""
        class KeywordIndex:
            pass
        """,
        tests="""
        idx = KeywordIndex()
        idx.add("faq", "Refunds take 5 days.")
        idx.add("terms", "No refunds after 30 days!")
        idx.add("auth", "Reset your password.")
        assert idx.search("refunds days") == ["faq", "terms"] and idx.search("Password") == ["auth"]
        idx.add("faq", "Shipping is free.")
        assert idx.search("refunds") == ["terms"] and idx.search("shipping") == ["faq"]
        idx.remove("terms")
        assert idx.search("refunds") == [] and "refunds" not in idx.postings
        assert idx.search("") == [] and idx.search("unknown") == []
        idx.remove("nope")
        """,
        hints=["Keep two dicts: `self.docs` (id to set of words) and `self.postings` (word to set of ids).",
               "Search: intersect the posting sets of the query words; start from the smallest for speed."],
        solution="""
        class KeywordIndex:
            def __init__(self):
                self.docs = {}
                self.postings = {}

            @staticmethod
            def _words(text):
                return {w.strip(".,!?").lower() for w in text.split()} - {""}

            def add(self, doc_id, text):
                self.remove(doc_id)
                words = self._words(text)
                self.docs[doc_id] = words
                for w in words:
                    self.postings.setdefault(w, set()).add(doc_id)

            def remove(self, doc_id):
                for w in self.docs.pop(doc_id, set()):
                    ids = self.postings[w]
                    ids.discard(doc_id)
                    if not ids:
                        del self.postings[w]

            def search(self, query):
                words = self._words(query)
                if not words:
                    return []
                sets = sorted((self.postings.get(w, set()) for w in words), key=len)
                return sorted(set.intersection(*sets))
        """,
        why="""The two dicts must always agree, which is exactly the kind of invariant a class protects: only `add` and `remove` change them, and
        `add` reuses `remove` so a replaced document leaves no stale postings. Deleting empty posting sets keeps the index from growing
        with words that no longer appear anywhere. Search looks up only the query words and intersects their sets, starting from the
        smallest, so its cost depends on how common the words are, not on how many documents exist; that is the core of a search engine's
        inverted index (and of BM25 libraries). `@staticmethod` (9.6) marks `_words` as a helper that does not need the instance."""),
    predict("Bound methods", "medium",
        code="""
        class Greeter:
            def __init__(self, name):
                self.name = name

            def greet(self, who):
                return f"{self.name} greets {who}"

        g = Greeter("ana")
        f = g.greet
        g.name = "bo"
        print(f("cy"), Greeter.greet(g, "dee"))
        print(f.__self__ is g, type(f).__name__, type(Greeter.greet).__name__)
        g.shout = lambda who: who.upper()
        print(g.shout("eve"), "shout" in vars(g), hasattr(Greeter, "shout"))
        """,
        hints=["A bound method remembers the instance, not a copy of its attributes. A function stored on an instance is not bound."],
        why="""`f` is bound to the instance `g`, and it reads `self.name` when called, after it was changed to "bo". Accessing the function
        through the class gives the plain function. A lambda stored as an **instance** attribute is just a function in the instance's
        dict: no `self` is inserted when it is called, which is why it takes only `who`, and the class does not know about it."""),
)

section("hard", "Hard",
    write("A chat session with a token limit", "hard", tag="GenAI",
        prompt="""Write a class `ChatSession(system_prompt, max_tokens)` that keeps a history for an LLM within a token budget. Estimate
        tokens as `len(content.split())` per message. `add(role, content)` appends a message, then, while the total exceeds
        `max_tokens`, drops the **oldest non-system** message (the system message is never dropped). `messages()` returns the history
        as a **new list of new dicts**, so callers cannot change the session. `dropped` counts how many messages were removed. A single
        message larger than the budget on its own raises `ValueError` and is not added.""",
        code="""
        class ChatSession:
            pass
        """,
        tests="""
        s = ChatSession("Be brief and kind.", max_tokens=12)
        s.add("user", "What is the refund window?")
        s.add("assistant", "Thirty days.")
        assert s.dropped == 0 and len(s.messages()) == 3
        s.add("user", "And for sale items please?")
        assert [m["content"] for m in s.messages()] == ["Be brief and kind.", "Thirty days.", "And for sale items please?"]
        assert s.dropped == 1
        out = s.messages()
        out[0]["content"] = "hacked"
        out.append({"role": "user", "content": "x"})
        assert s.messages()[0]["content"] == "Be brief and kind." and len(s.messages()) == 3
        try:
            s.add("user", "one two three four five six seven eight nine")
            assert False
        except ValueError:
            assert len(s.messages()) == 3
        """,
        hints=["Keep `self._system` separately from `self._turns` (a list), and compute the total from both.",
               "`messages()` builds `[dict(m) for m in ...]`, copying each dict."],
        solution="""
        class ChatSession:
            def __init__(self, system_prompt, max_tokens):
                self._system = {"role": "system", "content": system_prompt}
                self._turns = []
                self.max_tokens = max_tokens
                self.dropped = 0

            @staticmethod
            def _tokens(message):
                return len(message["content"].split())

            def total_tokens(self):
                return self._tokens(self._system) + sum(self._tokens(m) for m in self._turns)

            def add(self, role, content):
                message = {"role": role, "content": content}
                if self._tokens(self._system) + self._tokens(message) > self.max_tokens:
                    raise ValueError("message does not fit in the budget even on its own")
                self._turns.append(message)
                while self.total_tokens() > self.max_tokens:
                    self._turns.pop(0)
                    self.dropped += 1

            def messages(self):
                return [dict(self._system)] + [dict(m) for m in self._turns]
        """,
        why="""Keeping the system message apart from the turns makes "never drop the system prompt" structural rather than a condition checked in
        a loop. The window slides by dropping the oldest turns until the total fits, the simplest context-management strategy (others
        summarise old turns instead). The oversize check happens **before** appending, so a rejected message leaves the session unchanged.
        `messages()` returns copies of the list **and** of each dict, because a shallow copy of the list alone would still let callers edit
        the stored messages (2.3); that is encapsulation in Python: not enforced by the language, but by never handing out your internal
        mutable objects. Real code counts tokens with the model's tokenizer, and `pop(0)` on a list is O(n), fine for chat-sized histories
        (a `deque` would make it O(1))."""),
    fix("Read the code: a cache class", "hard", tag="RAG",
        prompt="""Each `ResultCache` should have its own entries and statistics. Instances share entries, hits are never counted, and callers
        can corrupt the cache through `snapshot()`. Read it, find the bugs and fix them.""",
        code="""
        class ResultCache:
            entries = {}

            def __init__(self, name, max_entries=100):
                self.name = name
                self.max_entries = max_entries
                self.hits = 0
                self.misses = 0

            def get(self, key, compute):
                if key in self.entries:
                    hits = self.hits + 1
                    return self.entries[key]
                self.misses += 1
                value = compute(key)
                if len(self.entries) >= self.max_entries:
                    oldest = next(iter(self.entries))
                    del self.entries[oldest]
                self.entries[key] = value
                return value

            def snapshot(self):
                return self.entries
        """,
        tests="""
        search_cache = ResultCache("search", max_entries=2)
        embed_cache = ResultCache("embed")
        calls = []
        def compute(k):
            calls.append(k)
            return [k.upper()]

        assert search_cache.get("refund", compute) == ["REFUND"]
        assert search_cache.get("refund", compute) == ["REFUND"]
        assert embed_cache.get("refund", lambda k: [len(k)]) == [6]
        assert (search_cache.hits, search_cache.misses, embed_cache.misses) == (1, 1, 1)
        search_cache.get("reset", compute); search_cache.get("invoice", compute)
        assert list(search_cache.snapshot()) == ["reset", "invoice"]
        snap = search_cache.snapshot()
        snap["reset"].append("junk"); snap.clear()
        assert search_cache.get("reset", compute) == ["RESET"] and calls == ["refund", "reset", "invoice"]
        """,
        hints=["`entries = {}` at class level is shared by every instance.",
               "`hits = self.hits + 1` creates a local variable.",
               "`snapshot` hands out the internal dict; return copies of the dict and of the cached lists."],
        solution="""
        class ResultCache:
            def __init__(self, name, max_entries=100):
                self.name = name
                self.max_entries = max_entries
                self.hits = 0
                self.misses = 0
                self.entries = {}

            def get(self, key, compute):
                if key in self.entries:
                    self.hits += 1
                    return self.entries[key]
                self.misses += 1
                value = compute(key)
                if len(self.entries) >= self.max_entries:
                    oldest = next(iter(self.entries))
                    del self.entries[oldest]
                self.entries[key] = value
                return value

            def snapshot(self):
                return {k: list(v) for k, v in self.entries.items()}
        """,
        why="""Three bugs, each from this lesson. The class-level `entries` dict was shared, so the embedding cache answered `"refund"` with the
        search cache's result (and every cache evicted the others' entries); creating it in `__init__` gives each instance its own.
        `hits = self.hits + 1` assigned a **local** variable that vanished when the method returned, so the hit count stayed 0, a
        typo-level bug that a metrics dashboard would show as a 0% hit rate; attributes are only changed through `self.`. And
        `snapshot()` returned the internal dict, so a caller's `clear()` emptied the cache and the appended `"junk"` corrupted a cached
        value; returning a copy with copied values protects the cache. Note that `get` still returns the cached list itself, which a
        caller could mutate; caching immutable values (tuples) avoids that entirely."""),
    write("A rate limiter class", "hard", tag="GenAI",
        prompt="""Rewrite the token bucket of 7.4 as a class `TokenBucket(rate, burst, clock)`. It starts full. `acquire(cost=1)` takes
        `cost` tokens and returns `0.0` if they were available, or else returns the seconds to wait **without** taking any; `cost` larger
        than `burst` raises `ValueError`. Add `available()` returning the current number of tokens (after refilling), and `stats()`
        returning `{"granted": g, "denied": d}`.""",
        code="""
        class TokenBucket:
            pass
        """,
        tests="""
        now = [0.0]
        bucket = TokenBucket(rate=2.0, burst=4, clock=lambda: now[0])
        assert [bucket.acquire() for _ in range(4)] == [0.0] * 4 and bucket.acquire() == 0.5
        now[0] = 1.0
        assert bucket.available() == 2.0 and bucket.acquire(2) == 0.0 and bucket.acquire(3) == 1.5
        now[0] = 100.0
        assert bucket.available() == 4.0
        assert bucket.stats() == {"granted": 5, "denied": 2}
        try:
            bucket.acquire(5)
            assert False
        except ValueError:
            pass
        other = TokenBucket(1.0, 1, clock=lambda: now[0])
        assert other.acquire() == 0.0 and other.acquire() == 1.0 and bucket.available() == 4.0
        """,
        hints=["Store `rate`, `burst`, `clock`, `_tokens`, `_last` and the counters in `__init__`.", "A private `_refill()` method updates `_tokens` from the elapsed time; both public methods call it first."],
        solution="""
        class TokenBucket:
            def __init__(self, rate, burst, clock):
                if rate <= 0 or burst < 1:
                    raise ValueError("rate must be positive and burst at least 1")
                self.rate = rate
                self.burst = burst
                self.clock = clock
                self._tokens = float(burst)
                self._last = clock()
                self._granted = 0
                self._denied = 0

            def _refill(self):
                now = self.clock()
                self._tokens = min(self.burst, self._tokens + (now - self._last) * self.rate)
                self._last = now

            def available(self):
                self._refill()
                return self._tokens

            def acquire(self, cost=1):
                if cost > self.burst:
                    raise ValueError(f"cost {cost} exceeds burst size {self.burst}")
                self._refill()
                if self._tokens >= cost:
                    self._tokens -= cost
                    self._granted += 1
                    return 0.0
                self._denied += 1
                return (cost - self._tokens) / self.rate

            def stats(self):
                return {"granted": self._granted, "denied": self._denied}
        """,
        why="""The closure version of 7.4 kept its state in `nonlocal` variables, invisible from outside. As a class, the state is named and
        inspectable, the shared refill step is one private method used by both public ones, and new operations (`available`, `stats`)
        are added without restructuring anything: this is the usual point at which a closure should become a class. Each instance has
        its own tokens and counters, so one bucket per provider or per API key is just one object each. The injected clock keeps it
        testable, and validating `rate` and `burst` in `__init__` means a bucket can never exist in an invalid state."""),
    predict("A class body runs once", "hard",
        code="""
        print("before class")

        class Config:
            print("  running the class body")
            models = ["small", "large"]
            default = models[0]
            limits = {m: 100 * (i + 1) for i, m in enumerate(models)}

            def limit(self):
                return self.limits[self.default]

        print("after class", Config.default, Config.limits)
        c = Config()
        c.default = "large"
        print(c.limit(), Config().limit(), type(c).limit is Config.limit)
        print(Config.__name__, type(Config).__name__, c.__class__ is Config)
        """,
        hints=["The class body is executed once, top to bottom, when the `class` statement runs.", "A class is itself an object, of type `type`."],
        why="""The class body is ordinary code run once at definition time, so its `print` appears immediately, and later lines can use earlier
        names (`default = models[0]`). The dict comprehension in a class body can use `models` because it is the outermost iterable, which
        is evaluated in the class scope. `c.default = "large"` shadows the class attribute for `c` only. Classes are objects too: their type
        is `type`, and every instance knows its class through `__class__`."""),
)

section("interview", "Interview questions",
    explain("What is `self` in Python, and what exactly happens when you call a method?", "medium", tag="Interview",
        why="""`self` is the conventional name for a method's first parameter, which receives the instance the method was called on. It is not a
        keyword, and Python never adds it implicitly inside the body: every attribute access goes through it explicitly. When you write
        `obj.method(a)`, Python looks up `method` on `obj`'s class (via the instance first, then the class and its bases), and because it is
        a function found on the class, the access produces a bound method that remembers `obj`; calling it runs `Class.method(obj, a)`. So
        `obj.method(a)` and `Class.method(obj, a)` are the same call. This is why forgetting `self` in a definition gives "takes 1
        positional argument but 2 were given", and why bound methods can be passed around as callbacks that keep working on their
        instance."""),
    explain("What is the difference between class attributes and instance attributes, and what is the classic bug?", "medium", tag="Interview",
        why="""Instance attributes are stored in each object's `__dict__`, usually set in `__init__` via `self.x = ...`, and are separate per object.
        Class attributes are assigned in the class body and stored once on the class, shared by all instances. Reading `obj.x` checks the
        instance first, then the class; assigning `obj.x = ...` always writes to the instance, shadowing the class attribute for that
        object only. The classic bug is a mutable class attribute, such as `history = []`, used as if it were per instance:
        `self.history.append(...)` reads the shared list and mutates it, so every instance appends to the same list. The same happens with a
        mutable default argument in `__init__`. Use class attributes for constants and genuinely shared data, and create mutable per-object
        state in `__init__`."""),
    explain("In ML and GenAI code, when would you use a class, a dataclass, or plain functions and dicts?", "hard", tag="Interview",
        why="""Plain functions are best for stateless transformations (cleaning text, computing a metric, building a prompt), since they are the
        easiest to test and compose. Dicts suit loosely structured data that crosses boundaries, such as parsed JSON, but their keys are not
        checked, so typos become silent bugs. A dataclass (or a Pydantic model when validation is needed) fits structured data with little
        behaviour: configs, records, API responses, evaluation results; it gives an `__init__`, a readable repr, equality and type hints for
        free. A full class is worth it when there is state plus rules plus operations: a conversation buffer with a token limit, a cache with
        statistics, a rate limiter, a client holding a session and settings, or when a framework requires it (PyTorch `nn.Module`,
        scikit-learn estimators with `fit`/`predict`). Signs that a class is too much: it has only `__init__` and one method, or no state.
        Signs that a dict should become a class: several functions taking the same dict and maintaining rules about its contents."""),
)

recap(
    "A class bundles data (attributes) with the functions that work on it (methods); each instance has its own data and shares the methods.",
    "`C(args)` creates an empty instance, calls `C.__init__(instance, args)`, and returns it. `obj.m(x)` is `C.m(obj, x)`: `self` is that instance.",
    "Instance attributes live in `obj.__dict__`. Reading looks in the instance, then the class; assigning always writes to the instance.",
    "Class attributes are shared: fine for constants, a bug for mutable per-object state. Create lists and dicts in `__init__`, never as class or default values.",
    "Methods accessed through an instance are bound methods; protect your state by validating in methods and returning copies, not internal objects.",
)
