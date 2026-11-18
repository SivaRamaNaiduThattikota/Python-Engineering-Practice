from lesson import *
from diagrams import *

lesson(
    id="m11-4", num="11.4", title="Pydantic models",
    intro="Pydantic validates and converts data according to type hints, which is why it sits at the boundaries of most "
          "Python services: API requests, configuration and LLM output. Models and validation errors, lax versus strict "
          "conversion, `Field` constraints, field and model validators, serialisation and JSON Schema, model configuration, "
          "`TypeAdapter` for types that are not models, and the version 2 traps. Applied to tickets, requests and structured LLM answers.",
    desc="Validation, errors, parsing LLM JSON output, settings.",
    keys="pydantic basemodel model_validate model_validate_json validationerror field constraints field_validator model_validator model_dump model_dump_json model_json_schema configdict extra forbid frozen strict lax typeadapter discriminator validate_call structured output",
)

term("BaseModel", "Pydantic's base class: subclasses declare typed fields, and creating an instance validates and converts the input, or raises `ValidationError`.")
term("ValidationError", "Pydantic's exception, listing every problem found, each with a location (`loc`), a message and an error type.")
term("Lax mode", "Pydantic's default: compatible values are converted (the string `\"5\"` to the int 5). Strict mode accepts only the exact types.")
term("JSON Schema", "A standard JSON description of a data shape; `model_json_schema()` generates it, and LLM structured-output APIs accept it.")

section("basics", "Models: validation and conversion from type hints",
    fig(chain(["raw input|(dict or JSON)", "Pydantic checks and|converts each field", ("a valid model instance", "good")], note="or one ValidationError listing every problem"),
        "A model is a validator built from type hints: input goes in, a trusted object or a complete error report comes out."),
    p("""A **Pydantic model** looks like a dataclass: a class inheriting from `pydantic.BaseModel` with annotated fields. The difference is what happens at
    construction: Pydantic **validates** every field against its type and **converts** compatible input, so `Ticket(id="42", ...)` stores the integer
    42, and incompatible input raises a `ValidationError` that lists **all** problems at once, each with its location. It is the runtime check that
    type hints alone do not provide (11.1), which is why Pydantic is used wherever untrusted data enters a program: web requests (FastAPI is built on
    it), configuration files, message queues and LLM outputs."""),
    ex("""
    from pydantic import BaseModel, ValidationError

    class Ticket(BaseModel):
        id: int
        title: str
        priority: int = 3
        tags: list[str] = []

    t = Ticket(id="42", title="Refund not received", tags=("billing", "eu"))
    print(t, type(t.id).__name__, t.tags)
    print(Ticket(id=1, title="x").tags is Ticket(id=2, title="y").tags)
    try:
        Ticket(id="abc", priority=2.5)
    except ValidationError as e:
        print(e.error_count(), "errors")
        for err in e.errors():
            print(" ", err["loc"], err["type"], "-", err["msg"])
    """, "basics.py"),
    p("""Three things to notice. The string `"42"` and the tuple of tags were **converted** to the declared types: by default Pydantic works in **lax** mode,
    accepting values that convert without losing information. A mutable default such as `[]` is fine in Pydantic, unlike dataclasses (11.3), because
    Pydantic copies defaults for each instance, so the two tag lists are different objects. And the error lists three problems in one exception: an
    `id` that is not an integer, a missing `title`, and a `priority` of 2.5, which Pydantic refuses to truncate to 2. Each error has a location
    (`loc`), a machine-readable `type` and a human message, which is exactly what you need to tell a user, or a model, what to fix."""),
    p("""Data usually arrives as a dict or a JSON string, so models have two class methods: **`Model.model_validate(data)`** for dicts and objects, and
    **`Model.model_validate_json(text)`** for JSON, which parses and validates in one fast step (Pydantic's core is written in Rust). Both return
    an instance or raise `ValidationError`, and both are what you use for LLM output: `Answer.model_validate_json(reply_text)` (problem 5)."""),
)

section("fields", "Field types and constraints",
    p("""Any type from 11.1 and 11.2 works as a field type: `str | None`, `Literal["spam", "ham"]`, `list[Citation]` (nested models), `dict[str, float]`,
    `datetime`, `UUID`, `Enum` classes. Constraints are attached with **`Field(...)`**: numbers take `gt`, `ge`, `lt`, `le`; strings and lists take
    `min_length` and `max_length`; strings take `pattern` (a regex). `Field` also sets a `description` (which ends up in the JSON Schema), a
    `default` or `default_factory`, and an `alias` for input names that are not valid Python identifiers. The same constraints can be written as
    `Annotated[float, Field(ge=0, le=1)]` (11.2), which lets you name a constrained type once and reuse it."""),
    ex("""
    from typing import Annotated, Literal
    from pydantic import BaseModel, Field, ValidationError

    Probability = Annotated[float, Field(ge=0, le=1)]

    class Citation(BaseModel):
        source: str = Field(min_length=1)
        quote: str = Field(max_length=200)

    class Answer(BaseModel):
        label: Literal["answer", "refuse", "clarify"]
        text: str
        confidence: Probability
        citations: list[Citation] = Field(default_factory=list, max_length=5)
        request_id: str | None = Field(default=None, alias="requestId")

    a = Answer.model_validate({"label": "answer", "text": "5 days", "confidence": "0.9",
                               "citations": [{"source": "faq.md", "quote": "Refunds take 5 days."}], "requestId": "r-1"})
    print(a.confidence, a.citations[0].source, a.request_id)
    try:
        Answer.model_validate({"label": "maybe", "text": "x", "confidence": 1.4, "citations": [{"source": "", "quote": "q"}]})
    except ValidationError as e:
        print([(".".join(map(str, err["loc"])), err["type"]) for err in e.errors()])
    """, "fields.py"),
    p("""The error locations are paths into the data, `citations.0.source`, so even deeply nested problems can be reported precisely. Note the version 2 rule
    that surprises people coming from older code: a field annotated `str | None` **without a default is required**. "May be `None`" and "may be
    missing" are different things; give such fields `= None` if they may be absent (problem 10)."""),
)

section("validators", "Validators: custom rules",
    fig(chain(["before validators|(raw input)", "type validation|and conversion", "Field constraints", "after validators", ("model validators|(several fields)", "accent")]),
        "The order Pydantic applies its checks, so you know what each validator receives."),
    p("""Type and constraint checks cover most rules; the rest go into **validators**. `@field_validator("name")` is a class method that receives the value of
    one field and returns the (possibly transformed) value, or raises `ValueError` with a message, which Pydantic turns into a validation error for that
    field. By default it runs **after** Pydantic's own type validation (`mode="after"`), so it receives a value of the declared type; with
    `mode="before"`, it runs first and receives the raw input, which is how you accept extra input formats, such as a comma-separated string for a list
    field (problem 6). `@model_validator(mode="after")` receives the whole validated model and checks rules between fields, such as a start date before
    an end date (problem 7)."""),
    ex("""
    from datetime import date
    from pydantic import BaseModel, ValidationError, field_validator, model_validator

    class Query(BaseModel):
        text: str
        tags: list[str] = []
        start: date | None = None
        end: date | None = None

        @field_validator("text")
        @classmethod
        def not_blank(cls, v: str) -> str:
            v = v.strip()
            if not v:
                raise ValueError("must not be blank")
            return v

        @field_validator("tags", mode="before")
        @classmethod
        def split_tags(cls, v):
            return [t.strip().lower() for t in v.split(",") if t.strip()] if isinstance(v, str) else v

        @model_validator(mode="after")
        def check_range(self):
            if self.start and self.end and self.start > self.end:
                raise ValueError("start must not be after end")
            return self

    print(Query(text="  refund window ", tags="EU, billing,", start="2025-01-01"))
    for bad in [{"text": "  "}, {"text": "x", "start": "2025-03-01", "end": "2025-01-01"}]:
        try:
            Query(**bad)
        except ValidationError as e:
            print(e.errors()[0]["loc"], e.errors()[0]["msg"])
    """, "validators.py"),
    p("""Validators keep rules next to the data they protect, and every way of creating the model runs them, so no invalid object can exist. Keep them pure
    and fast: they run on every validation. A model validator's error has an empty location `()`, because it concerns the model as a whole."""),
)

section("serialise", "Serialising: `model_dump`, JSON and JSON Schema",
    p("""Models convert back to plain data with **`model_dump()`** (a dict, nested models included) and **`model_dump_json()`** (a JSON string, fast).
    Options shape the output: `exclude_none=True` drops fields that are `None`, `exclude={...}` and `include={...}` select fields, and `by_alias=True`
    uses the aliases, so you can read and write external formats such as camel-case JSON while using Python names internally. Dates, enums and nested
    models are serialised correctly without extra code."""),
    p("""**`Model.model_json_schema()`** returns the JSON Schema of the model: types, required fields, constraints, `enum` for literals and the field
    descriptions. That is the schema you send to an LLM API as the structured-output format or as tool parameters (11.2's hand-written generator, done
    for you), so the same class describes the output to the model and validates it when it comes back (problem 12)."""),
    ex("""
    import json
    from typing import Literal
    from pydantic import BaseModel, Field

    class Verdict(BaseModel):
        label: Literal["spam", "ham"] = Field(description="the predicted class")
        confidence: float = Field(ge=0, le=1)
        note: str | None = None

    v = Verdict(label="spam", confidence=0.93)
    print(v.model_dump(), v.model_dump(exclude_none=True), v.model_dump_json())
    schema = Verdict.model_json_schema()
    print(schema["required"], schema["properties"]["label"])
    print(schema["properties"]["confidence"])
    """, "serialise.py"),
)

section("config", "Model configuration and `TypeAdapter`",
    p("""Behaviour that applies to the whole model goes in `model_config = ConfigDict(...)`. **`extra="forbid"`** rejects unknown fields instead of ignoring them,
    which catches typos such as `temprature` in a request (problem 3); `extra="allow"` keeps them. **`frozen=True`** makes instances immutable and
    hashable (like frozen dataclasses). **`str_strip_whitespace=True`** strips every string field. **`strict=True`** turns off lax conversion for the
    whole model, and individual fields can be strict with `Field(strict=True)`. **`validate_assignment=True`** re-validates fields when they are assigned
    after creation; by default, assignment is **not** validated, and neither is `model_copy(update=...)` (problem 16)."""),
    ex("""
    from pydantic import BaseModel, ConfigDict, ValidationError

    class Request(BaseModel):
        model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)
        model: str
        temperature: float = 0.0

    r = Request(model="  small ")
    print(repr(r.model))
    for bad in [{"model": "x", "temprature": 0.5}, {"model": "x", "temperature": "hot"}]:
        try:
            Request(**bad)
        except ValidationError as e:
            print(e.errors()[0]["loc"], e.errors()[0]["type"])
    try:
        r.temperature = "warm"
    except ValidationError as e:
        print("assignment:", e.errors()[0]["type"])
    """, "config.py"),
    p("""Not everything needs a class. **`TypeAdapter(T)`** validates any type: `TypeAdapter(list[int]).validate_python(["1", 2])`, a `TypedDict`, a union of
    models. It is the tool for a top-level list of objects in an LLM reply, and for **discriminated unions**: `Annotated[A | B | C,
    Field(discriminator="type")]` validates the tagged events of 11.2, choosing the model by the value of the `type` field and reporting errors against
    that model only (problem 15). The `@validate_call` decorator applies the same validation to a function's arguments (the production version of
    11.1's `validated`)."""),
)

section("llm", "Pydantic for LLM output",
    fig(flowchart({
        "ask": ("start", 0, 0, "ask the model with|the JSON schema"),
        "parse": ("step", 0, 1, "model_validate_json(reply)"),
        "ok": ("ask", 0, 2, "valid?"),
        "ret": ("end", 1, 2, "return the model"),
        "left": ("ask", 0, 3, "attempts left?"),
        "fix": ("warn", 1, 3, "send the errors back"),
        "fail": ("bad", 0, 4, "raise ValueError"),
    }, [("ask", "parse"), ("parse", "ok"), ("ok", "ret", "yes"), ("ok", "left", "no"), ("left", "fix", "yes"),
        ("fix", "ask", "", {"route": [(1.42, 3), (1.42, 0)]}), ("left", "fail", "no")], cell=(230, 76),
        label="structured output with a repair loop"),
        "Structured output with Pydantic: the model class supplies the schema, validates the reply, and turns failures into precise feedback."),
    p("""Structured output from a model is untrusted input: even with a JSON schema enforced by the provider, values can be out of range, lists empty,
    labels misspelt, or the reply truncated (7.4). The robust loop is: describe the answer as a model, send `model_json_schema()` as the response format
    or tool schema, parse the reply with `model_validate_json`, and on `ValidationError` send the **errors** back to the model in a compact form (location
    and message for each) and ask again, a limited number of times. Libraries such as Instructor and the OpenAI and Anthropic SDKs' parse helpers wrap
    exactly this loop around Pydantic models."""),
    ex("""
    from typing import Literal
    from pydantic import BaseModel, Field, ValidationError

    class Classification(BaseModel):
        label: Literal["spam", "ham", "phish"]
        confidence: float = Field(ge=0, le=1)
        reasons: list[str] = Field(min_length=1)

    def compact(e: ValidationError) -> str:
        return "; ".join(f"{'.'.join(map(str, err['loc'])) or 'reply'}: {err['msg']}" for err in e.errors())

    replies = ['{"label": "Spam", "confidence": 93, "reasons": []}', '{"label": "spam", "confidence": 0.93, "reasons": ["prize offer"]}']
    for reply in replies:
        try:
            result = Classification.model_validate_json(reply)
            print("valid:", result)
        except ValidationError as e:
            print("send back:", compact(e))
    """, "llm_output.py"),
)

section("warmup", "Warm-up",
    predict("Lax conversion and errors", "easy",
        code="""
        from pydantic import BaseModel, ValidationError

        class Item(BaseModel):
            id: int
            price: float
            active: bool = True

        print(Item(id="7", price="9.5", active="yes"))
        print(Item(id=7.0, price=3).model_dump())
        for bad in [{"id": "7a", "price": 1}, {"id": 7.5, "price": 1}, {"price": "x"}]:
            try:
                Item(**bad)
            except ValidationError as e:
                print(e.error_count(), [err["type"] for err in e.errors()])
        """,
        hints=["Lax mode converts strings that look like numbers or booleans, and whole floats to ints, but never loses information."],
        why="""Lax validation converts `"7"` to 7, `"9.5"` to 9.5, `"yes"` to `True`, and `7.0` to 7 because no information is lost. It refuses `"7a"` (not a
        number) and `7.5` (truncating it would lose the fraction), each with a precise error type. The last input has two problems, a missing `id` and an
        unparsable `price`, and both are reported in the same exception."""),
    write("A ticket model with constraints", "easy", tag="Data work",
        prompt="""Write a Pydantic model `Ticket` with: `id` (a positive int), `title` (a string of 3 to 100 characters, whitespace stripped), `priority` (an int
        from 1 to 5, default 3), `status` (one of `"open"`, `"pending"`, `"closed"`, default `"open"`) and `tags` (a list of strings, default empty). Then write
        `ticket_errors(data)` returning `[]` if `data` is a valid ticket, or a sorted list of the field names that failed.""",
        code="""
        from typing import Literal
        from pydantic import BaseModel, Field, ValidationError

        def ticket_errors(data):
            pass
        """,
        tests="""
        t = Ticket(id="12", title="  Refund missing  ")
        assert (t.id, t.title, t.priority, t.status, t.tags) == (12, "Refund missing", 3, "open", [])
        assert ticket_errors({"id": 1, "title": "Login fails", "priority": 5, "status": "pending"}) == []
        assert ticket_errors({"id": 0, "title": "ok", "priority": 9, "status": "done"}) == ["id", "priority", "status", "title"]
        assert ticket_errors({"title": "Valid title"}) == ["id"]
        """,
        hints=["`id: int = Field(gt=0)`; `title: str = Field(min_length=3, max_length=100)` with `model_config = ConfigDict(str_strip_whitespace=True)`.",
               "The field name is the first element of each error's `loc`."],
        solution="""
        from typing import Literal
        from pydantic import BaseModel, ConfigDict, Field, ValidationError


        class Ticket(BaseModel):
            model_config = ConfigDict(str_strip_whitespace=True)
            id: int = Field(gt=0)
            title: str = Field(min_length=3, max_length=100)
            priority: int = Field(default=3, ge=1, le=5)
            status: Literal["open", "pending", "closed"] = "open"
            tags: list[str] = []


        def ticket_errors(data):
            try:
                Ticket.model_validate(data)
            except ValidationError as e:
                return sorted({str(err["loc"][0]) for err in e.errors()})
            return []
        """,
        why="""Each rule is declared on the field it belongs to, and Pydantic checks them all in one pass, so one call reports every bad field. Stripping whitespace
        happens before the length check, which is why `"  Refund missing  "` is stored clean and `"ok"` (2 characters) fails. The `Literal` gives a
        precise "Input should be 'open', 'pending' or 'closed'" error. Sorting a set of first locations turns the detailed errors into a summary for a
        form or an API response; in practice you would return the full `e.errors()` as JSON, which FastAPI does automatically with a 422 response."""),
    fix("A request model that ignores typos", "easy", tag="GenAI",
        prompt="""`ChatRequest` silently ignores unknown fields, so a client sending `temprature` gets the default temperature and no error. Make the model reject
        unknown fields, and add the missing constraint that `temperature` must be between 0 and 2.""",
        code="""
        from pydantic import BaseModel

        class ChatRequest(BaseModel):
            model: str
            prompt: str
            temperature: float = 0.0
        """,
        tests="""
        from pydantic import ValidationError
        assert ChatRequest(model="small", prompt="hi", temperature="0.5").temperature == 0.5
        assert ChatRequest(model="small", prompt="hi").temperature == 0.0
        for bad in [{"model": "small", "prompt": "hi", "temprature": 0.9}, {"model": "small", "prompt": "hi", "temperature": 3}]:
            try:
                ChatRequest.model_validate(bad)
                assert False, bad
            except ValidationError as e:
                assert e.errors()[0]["type"] in ("extra_forbidden", "less_than_equal")
        """,
        hints=["`model_config = ConfigDict(extra=\"forbid\")`, and `temperature: float = Field(default=0.0, ge=0, le=2)`."],
        solution="""
        from pydantic import BaseModel, ConfigDict, Field

        class ChatRequest(BaseModel):
            model_config = ConfigDict(extra="forbid")
            model: str
            prompt: str
            temperature: float = Field(default=0.0, ge=0, le=2)
        """,
        why="""By default Pydantic **ignores** extra fields, which is friendly to evolving clients but dangerous for settings: a misspelt `temprature` is dropped, the
        request runs with temperature 0, and nobody notices that the user's setting was never applied. `extra="forbid"` turns the typo into an
        `extra_forbidden` error naming the field. The range constraint makes 3 fail with `less_than_equal` instead of reaching the provider, which would
        reject it with a less helpful message (or clamp it silently). Public APIs often forbid extras on requests and allow them on responses."""),
    predict("Dumping, excluding and aliases", "easy",
        code="""
        from pydantic import BaseModel, Field

        class User(BaseModel):
            user_id: int = Field(alias="userId")
            name: str
            email: str | None = None

        u = User.model_validate({"userId": "5", "name": "Ana"})
        print(u.user_id, u.model_dump())
        print(u.model_dump(by_alias=True, exclude_none=True), u.model_dump_json(exclude={"email"}))
        try:
            User(user_id=5, name="Bo")
        except Exception as e:
            print(type(e).__name__)
        """,
        hints=["With an alias, the input must use the alias unless the model allows population by field name."],
        why="""The input used the alias `userId`, converted from a string; inside Python the attribute is `user_id`, and `model_dump` uses field names by default. With
        `by_alias=True` the output speaks the external format again, and `exclude_none` drops the empty email. Constructing with the Python name fails with
        a `ValidationError`, because an aliased field is filled from its alias unless the configuration sets `validate_by_name=True` (older code:
        `populate_by_name=True`)."""),
)

section("medium", "Medium",
    write("Validate a model's structured answer", "medium", tag="GenAI",
        prompt="""Write a model `Classification` with `label` (one of `"spam"`, `"ham"`, `"phish"`), `confidence` (a float in `[0, 1]`) and `reasons` (a list of 1 to
        3 non-blank strings, each stripped). Then write `parse_reply(text)` returning `(Classification, [])` when the JSON reply is valid, or `(None,
        errors)` where `errors` is a list of `"<location>: <message>"` strings (location joined with dots, `"reply"` for errors without a location), so they
        can be sent back to the model.""",
        code="""
        from typing import Literal
        from pydantic import BaseModel, Field, ValidationError, field_validator

        def parse_reply(text):
            pass
        """,
        tests="""
        ok, errs = parse_reply('{"label": "phish", "confidence": 0.87, "reasons": [" fake login link ", "urgent tone"]}')
        assert errs == [] and ok.label == "phish" and ok.reasons == ["fake login link", "urgent tone"]
        none, errs = parse_reply('{"label": "Spam", "confidence": 1.5, "reasons": []}')
        assert none is None and len(errs) == 3 and errs[0].startswith("label: ") and errs[1].startswith("confidence: ") and errs[2].startswith("reasons: ")
        none, errs = parse_reply('{"label": "spam", "confidence": 0.9, "reasons": ["  "]}')
        assert errs == ["reasons: Value error, reasons must not be blank"]
        none, errs = parse_reply("Sure! Here is the JSON")
        assert none is None and errs[0].startswith("reply: ")
        """,
        hints=["`reasons: list[str] = Field(min_length=1, max_length=3)` plus a `field_validator(\"reasons\")` that strips and rejects blanks.",
               "`Classification.model_validate_json(text)` reports invalid JSON as a `ValidationError` whose `loc` is empty."],
        solution="""
        from typing import Literal
        from pydantic import BaseModel, Field, ValidationError, field_validator


        class Classification(BaseModel):
            label: Literal["spam", "ham", "phish"]
            confidence: float = Field(ge=0, le=1)
            reasons: list[str] = Field(min_length=1, max_length=3)

            @field_validator("reasons")
            @classmethod
            def strip_reasons(cls, reasons: list[str]) -> list[str]:
                cleaned = [r.strip() for r in reasons]
                if any(not r for r in cleaned):
                    raise ValueError("reasons must not be blank")
                return cleaned


        def parse_reply(text):
            try:
                return Classification.model_validate_json(text), []
            except ValidationError as e:
                errors = []
                for err in e.errors():
                    loc = ".".join(str(part) for part in err["loc"]) or "reply"
                    errors.append(f"{loc}: {err['msg']}")
                return None, errors
        """,
        why="""`model_validate_json` parses and validates in one step, so malformed JSON ("Sure! Here is...") and wrong values end up in the same error format; the JSON
        error simply has no location. Converting each error to `location: message` gives the model precise, short feedback ("label: Input should be 'spam',
        'ham' or 'phish'"), which is far more effective in a repair prompt than a traceback. The validator turns the message of its `ValueError` into a
        "Value error, ..." entry for the field it validates (`reasons`, the whole list, since the validator receives the list). The case-sensitive literal rejects `"Spam"` on purpose; normalising case with a
        `mode="before"` validator would be the lenient alternative."""),
    fix("A validator that runs too late", "medium", tag="Data work",
        prompt="""`Doc.tags` should accept either a list of strings or a comma-separated string (`"billing, EU"`), and always store lower-cased, stripped tags. Passing a
        string fails with "Input should be a valid list", because the validator runs after Pydantic has already rejected the string. Fix it.""",
        code="""
        from pydantic import BaseModel, field_validator

        class Doc(BaseModel):
            id: str
            tags: list[str] = []

            @field_validator("tags")
            @classmethod
            def split(cls, v):
                if isinstance(v, str):
                    v = v.split(",")
                return [t.strip().lower() for t in v if t.strip()]
        """,
        tests="""
        assert Doc(id="d1", tags="Billing, EU,").tags == ["billing", "eu"]
        assert Doc(id="d2", tags=["  FAQ ", ""]).tags == ["faq"]
        assert Doc(id="d3").tags == []
        """,
        hints=["`@field_validator(\"tags\", mode=\"before\")` runs on the raw input, before type validation."],
        solution="""
        from pydantic import BaseModel, field_validator

        class Doc(BaseModel):
            id: str
            tags: list[str] = []

            @field_validator("tags", mode="before")
            @classmethod
            def split(cls, v):
                if isinstance(v, str):
                    v = v.split(",")
                return [t.strip().lower() for t in v if t.strip()]
        """,
        why="""An `after` validator (the default) receives a value that has already passed type validation, so a string never reached it: Pydantic rejected it as "not a
        list" first. A `before` validator runs on the raw input and can reshape it into something the type accepts; Pydantic then validates the
        returned list as `list[str]`. The rule of thumb: `before` to accept extra input formats, `after` to check or normalise values that already have the
        right type. Comma-separated values from query strings, CSV cells and environment variables are the classic case."""),
    write("A date range with a cross-field rule", "medium", tag="Data work",
        prompt="""Write a model `Window` with `start` and `end` (`datetime.date`, accepting ISO strings), and `max_days` (int, default 31). Add a
        `model_validator(mode="after")` that raises `ValueError("end is before start")` when `end < start` and `ValueError(f"window longer than {max_days}
        days")` when the span (end minus start, in days) exceeds `max_days`. Add a property `days` returning the inclusive number of days.""",
        code="""
        from datetime import date
        from pydantic import BaseModel, ValidationError, model_validator

        class Window(BaseModel):
            pass
        """,
        tests="""
        from datetime import date
        from pydantic import ValidationError
        w = Window(start="2025-01-01", end="2025-01-31")
        assert w.start == date(2025, 1, 1) and w.days == 31
        for bad, msg in [({"start": "2025-02-01", "end": "2025-01-01"}, "end is before start"),
                         ({"start": "2025-01-01", "end": "2025-03-01", "max_days": 30}, "window longer than 30 days")]:
            try:
                Window(**bad)
                assert False
            except ValidationError as e:
                assert e.errors()[0]["loc"] == () and msg in e.errors()[0]["msg"]
        assert Window(start="2025-01-01", end="2025-01-01").days == 1
        """,
        hints=["Inside the model validator, `self.start` and `self.end` are already `date` objects; `(self.end - self.start).days` is an int."],
        solution="""
        from datetime import date
        from pydantic import BaseModel, ValidationError, model_validator

        class Window(BaseModel):
            start: date
            end: date
            max_days: int = 31

            @model_validator(mode="after")
            def check(self):
                if self.end < self.start:
                    raise ValueError("end is before start")
                if (self.end - self.start).days > self.max_days:
                    raise ValueError(f"window longer than {self.max_days} days")
                return self

            @property
            def days(self):
                return (self.end - self.start).days + 1
        """,
        why="""Field types turned the ISO strings into `date` objects before the model validator ran, so the cross-field rule compares real dates, not strings. A rule
        involving several fields cannot live in a single field's validator, so `model_validator(mode="after")` is the right place, and it must return
        `self`. Its errors have the location `()`, the model as a whole. Ordinary properties work on Pydantic models as on any class (9.3), and are not
        part of the serialised output. Date windows like this guard reporting and backfill APIs from requests that would scan years of data."""),
    choose("Where to build the TypeAdapter", "medium", tag="Data work",
        prompt="Both validate 2,000 event dicts with a `TypeAdapter`. Which is faster?",
        setup="""from pydantic import BaseModel, TypeAdapter

class Row(BaseModel):
    id: int
    label: str
    score: float

data = [{"id": i, "label": "spam", "score": 0.5} for i in range(2_000)]
def validate_one(d):
    return TypeAdapter(Row).validate_python(d)
ROW = TypeAdapter(Row)""",
        options={
            "a": "rows = [validate_one(d) for d in data]",
            "b": "rows = [ROW.validate_python(d) for d in data]",
        },
        answer="b",
        hints=["What work does creating a `TypeAdapter` involve, and how often does each version do it?"],
        why="""Creating a `TypeAdapter` builds a validator for the type: Pydantic walks the type, generates a core schema and compiles it in its Rust core. Doing that
        inside a function called per item repeats the whole build 2,000 times, while the validation itself is cheap. Build adapters once, at module level
        or in a cached factory, and reuse them; the same applies to models, whose validator is built once when the class is defined. Measured here in
        Pyodide, also note that `model_construct` (which skips validation) is not faster than `model_validate` for simple rows, because validation runs in
        compiled code while `model_construct` runs in Python, so "skip validation for speed" is rarely worth the lost guarantee."""),
    trace("Reading a ValidationError", "medium",
        prompt="Fill in `count`, `locs` and `types` after each marked line.",
        code="""
        from pydantic import BaseModel, Field, ValidationError

        class Item(BaseModel):
            name: str
            qty: int = Field(gt=0)

        class Order(BaseModel):
            id: int
            items: list[Item]

        def info(data):
            try:
                Order.model_validate(data)
                return 0, [], []
            except ValidationError as e:
                return e.error_count(), [err["loc"] for err in e.errors()], [err["type"] for err in e.errors()]

        count, locs, types = info({"id": 1, "items": [{"name": "pen", "qty": 2}]})  # row: "valid"
        count, locs, types = info({"id": "x", "items": [{"name": "pen", "qty": 0}]})  # row: "two problems"
        count, locs, types = info({"items": [{"qty": "3"}, {"name": "ok", "qty": 1}]})  # row: "missing fields"
        """,
        trace_vars=["count", "locs", "types"],
        hints=["Locations are tuples of keys and list indexes. `\"3\"` converts to 3 in lax mode."],
        why="""A valid order produces no errors. In the second, the id is not an integer and the item's quantity fails `gt=0`; the item error's location goes into the
        list by index. In the third, the order id is missing and the first item has no name, while its quantity `"3"` converts fine. Locations are tuples
        such as `('items', 0, 'name')`, which is what lets a UI highlight the exact field."""),
    fix("An Optional field that is required", "medium", tag="GenAI",
        prompt="""`ToolCall.reasoning` is annotated `str | None` and the team assumed that makes it optional, but every call without `reasoning` fails with
        "Field required". Fix the model so `reasoning` may be absent (defaulting to `None`) while `name` and `arguments` stay required.""",
        code="""
        from pydantic import BaseModel

        class ToolCall(BaseModel):
            name: str
            arguments: dict
            reasoning: str | None
        """,
        tests="""
        from pydantic import ValidationError
        t = ToolCall.model_validate({"name": "search", "arguments": {"q": "refund"}})
        assert t.reasoning is None and t.name == "search"
        assert ToolCall(name="x", arguments={}, reasoning="needed docs").reasoning == "needed docs"
        try:
            ToolCall.model_validate({"name": "x"})
            assert False
        except ValidationError as e:
            assert [err["loc"] for err in e.errors()] == [("arguments",)]
        """,
        hints=["In Pydantic v2, a field is optional only if it has a default: `reasoning: str | None = None`."],
        solution="""
        from pydantic import BaseModel

        class ToolCall(BaseModel):
            name: str
            arguments: dict
            reasoning: str | None = None
        """,
        why="""Pydantic v2 separates two questions that v1 mixed up: "may the value be `None`?" (the type, `str | None`) and "may the field be missing?" (whether it has a
        default). Without a default, the field is required even though `None` is an allowed value, so the caller would have to send `"reasoning": null`
        explicitly. Adding `= None` answers both. The same distinction matters for JSON schemas sent to LLMs: a nullable but required field forces the model
        to always emit the key, which is sometimes exactly what you want; choose deliberately."""),
    write("Answers with citations", "medium", tag="RAG",
        prompt="""Write models `Citation(source: str, quote: str)` and `RAGAnswer(answer: str, citations: list[Citation])`. Then write `check_answer(data,
        allowed_sources)` that validates `data` into a `RAGAnswer` (a `ValidationError` propagates), then raises `ValueError` listing (sorted) any cited
        sources not in `allowed_sources`, and returns the answer with duplicate citations removed (same source and quote, first kept, order preserved). An
        answer with no citations is invalid: require at least one with `Field(min_length=1)`.""",
        code="""
        from pydantic import BaseModel, Field

        def check_answer(data, allowed_sources):
            pass
        """,
        tests="""
        from pydantic import ValidationError
        data = {"answer": "Refunds take 5 days.", "citations": [{"source": "faq.md", "quote": "5 days"}, {"source": "faq.md", "quote": "5 days"},
                                                                {"source": "terms.md", "quote": "no refunds after 30 days"}]}
        a = check_answer(data, {"faq.md", "terms.md"})
        assert [c.source for c in a.citations] == ["faq.md", "terms.md"] and isinstance(a, RAGAnswer)
        assert len(data["citations"]) == 3 and a.answer == "Refunds take 5 days."
        try:
            check_answer({"answer": "x", "citations": [{"source": "blog.md", "quote": "q"}, {"source": "aaa.md", "quote": "q"}]}, {"faq.md"})
            assert False
        except ValueError as e:
            assert "aaa.md" in str(e) and str(e).index("aaa.md") < str(e).index("blog.md") and not isinstance(e, ValidationError)
        try:
            check_answer({"answer": "x", "citations": []}, {"faq.md"})
            assert False
        except ValidationError:
            pass
        """,
        hints=["Validate with `RAGAnswer.model_validate(data)`, compute unknown sources with a set difference, and rebuild with `answer.model_copy(update={\"citations\": unique})`."],
        solution="""
        from pydantic import BaseModel, Field


        class Citation(BaseModel):
            source: str
            quote: str


        class RAGAnswer(BaseModel):
            answer: str
            citations: list[Citation] = Field(min_length=1)


        def check_answer(data, allowed_sources):
            answer = RAGAnswer.model_validate(data)
            unknown = sorted({c.source for c in answer.citations} - set(allowed_sources))
            if unknown:
                raise ValueError(f"citations to sources that were not retrieved: {', '.join(unknown)}")
            seen, unique = set(), []
            for c in answer.citations:
                key = (c.source, c.quote)
                if key not in seen:
                    seen.add(key)
                    unique.append(c)
            return answer.model_copy(update={"citations": unique})
        """,
        why="""Two layers of checking with different jobs. The model checks the **shape** (strings where strings belong, at least one citation), something Pydantic does
        generically. The function checks **meaning** that depends on context the model cannot know: whether the cited sources were actually retrieved for
        this question. A citation to a document that was never in the context is a hallucination, and catching it is one of the cheapest RAG quality
        checks (5.P did it with regex; here it works on structured output). `model_copy(update=...)` returns a new model with the deduplicated list; note
        that it does **not** re-validate, which is fine here because the list came from validated citations."""),
    predict("The generated JSON Schema", "medium",
        code="""
        from typing import Literal
        from pydantic import BaseModel, Field

        class Step(BaseModel):
            tool: Literal["search", "calculator"]
            input: str = Field(description="what to send to the tool")

        class Plan(BaseModel):
            steps: list[Step] = Field(min_length=1, max_length=4)
            final: str | None = None

        s = Plan.model_json_schema()
        print(s["required"], sorted(s["properties"]))
        print(s["properties"]["steps"]["minItems"], s["properties"]["steps"]["items"])
        step = s["$defs"]["Step"]
        print(step["properties"]["tool"], step["required"])
        print(s["properties"]["final"])
        """,
        hints=["Nested models are placed in `$defs` and referenced with `$ref`. Literals become `enum` with a type. A field with a default is not required."],
        why="""Only `steps` is required, because `final` has a default. The list constraints become `minItems` and `maxItems`, and the nested `Step` model is defined once
        under `$defs` and referenced, which keeps large schemas compact. The literal becomes an `enum` of strings, the description is carried over, and
        `str | None` becomes an `anyOf` of string and null with its default. This dict is exactly what you pass as a response format or tool schema."""),
)

section("hard", "Hard",
    write("A structured-output repair loop", "hard", tag="GenAI",
        prompt="""Write `ask_structured(ask, prompt, model_cls, attempts=3)`. `ask(messages)` returns the model's reply text. Validate each reply with
        `model_cls.model_validate_json`. On failure, append the reply as an assistant message and a user message `"Your reply was invalid:\\n<errors>\\nReply
        with JSON matching the schema."` where `<errors>` has one `"- <loc>: <msg>"` line per error (`loc` dotted, `reply` if empty). The first user message
        must contain the prompt followed by `"\\nJSON schema: "` and `json.dumps(model_cls.model_json_schema())`. Return `(instance, attempts_used)`; after
        the last failure, raise `ValueError(f"no valid reply after {attempts} attempts")` chained from the last `ValidationError`.""",
        code="""
        import json
        from pydantic import BaseModel, ValidationError

        def ask_structured(ask, prompt, model_cls, attempts=3):
            pass
        """,
        tests="""
        import json
        from typing import Literal
        from pydantic import BaseModel, Field, ValidationError

        class Verdict(BaseModel):
            label: Literal["spam", "ham"]
            confidence: float = Field(ge=0, le=1)

        replies = iter(["not json", '{"label": "eggs", "confidence": 2}', '{"label": "spam", "confidence": 0.9}'])
        seen = []
        def ask(messages):
            seen.append([m["content"] for m in messages])
            return next(replies)

        v, used = ask_structured(ask, "Classify: WIN A PRIZE", Verdict)
        assert v == Verdict(label="spam", confidence=0.9) and used == 3
        assert seen[0][0].startswith("Classify: WIN A PRIZE\\nJSON schema: ") and json.loads(seen[0][0].split("JSON schema: ", 1)[1])["required"] == ["label", "confidence"]
        assert seen[1][1] == "not json" and seen[1][2].startswith("Your reply was invalid:\\n- reply: ")
        lines = seen[2][-1].splitlines()
        assert lines[1].startswith("- label: ") and lines[2].startswith("- confidence: ") and lines[-1] == "Reply with JSON matching the schema."
        try:
            ask_structured(lambda m: "{}", "x", Verdict, attempts=2)
            assert False
        except ValueError as e:
            assert str(e) == "no valid reply after 2 attempts" and isinstance(e.__cause__, ValidationError)
        """,
        hints=["Build the first message once; keep a `messages` list and extend it with `+` after each failure (2.4).",
               "Format errors with a small helper so both the loop and tests agree on the format."],
        solution="""
        import json
        from pydantic import BaseModel, ValidationError


        def _format(e):
            lines = []
            for err in e.errors():
                loc = ".".join(str(p) for p in err["loc"]) or "reply"
                lines.append(f"- {loc}: {err['msg']}")
            return "\\n".join(lines)


        def ask_structured(ask, prompt, model_cls, attempts=3):
            schema = json.dumps(model_cls.model_json_schema())
            messages = [{"role": "user", "content": f"{prompt}\\nJSON schema: {schema}"}]
            last_error = None
            for attempt in range(1, attempts + 1):
                reply = ask(messages)
                try:
                    return model_cls.model_validate_json(reply), attempt
                except ValidationError as e:
                    last_error = e
                    messages = messages + [
                        {"role": "assistant", "content": reply},
                        {"role": "user", "content": f"Your reply was invalid:\\n{_format(e)}\\nReply with JSON matching the schema."},
                    ]
            raise ValueError(f"no valid reply after {attempts} attempts") from last_error
        """,
        why="""The model class is the single source of truth: its JSON Schema tells the model what to produce, `model_validate_json` checks what it produced, and the
        validation errors tell it precisely what to fix, one line per problem with its location. Showing the model its own invalid reply alongside the
        errors usually fixes the output on the next attempt. The loop is bounded, chains the final error from the last `ValidationError` so logs keep the
        details (7.2), and builds new message lists instead of mutating the caller's (2.4). This is the 7.4 repair loop rebuilt on Pydantic, and
        essentially what Instructor does; with providers that enforce schemas server-side, the loop still matters for semantic constraints (ranges,
        lengths, cross-field rules) that schemas cannot fully express."""),
    fix("Read the code: an API request model", "hard", tag="GenAI",
        prompt="""`CompletionRequest` validates requests to an internal LLM gateway. It accepts roles like `"admin"`, accepts a temperature of 7, ignores unknown keys
        such as `max_token`, lets `max_tokens=0` through, and every instance shares one `stop` list. Read it, find the bugs and fix them: roles are
        `system`, `user`, `assistant`, `tool`; temperature in `[0, 2]`; `max_tokens` from 1 to 32,000 (default 512); at least one message; no unknown keys
        at either level; a fresh `stop` list per request with at most 4 entries.""",
        code="""
        from pydantic import BaseModel, Field


        class Message(BaseModel):
            role: str
            content: str


        STOP = []


        class CompletionRequest(BaseModel):
            model: str
            messages: list[Message]
            temperature: float = 1.0
            max_tokens: int = 512
            stop: list[str] = Field(default_factory=lambda: STOP)
        """,
        tests="""
        from pydantic import ValidationError
        ok = CompletionRequest.model_validate({"model": "small", "messages": [{"role": "user", "content": "hi"}], "temperature": "0.2"})
        assert ok.temperature == 0.2 and ok.max_tokens == 512
        ok.stop.append("###")
        assert CompletionRequest(model="m", messages=[{"role": "user", "content": "x"}]).stop == []
        cases = [
            {"model": "m", "messages": [{"role": "admin", "content": "x"}]},
            {"model": "m", "messages": [{"role": "user", "content": "x"}], "temperature": 7},
            {"model": "m", "messages": [{"role": "user", "content": "x"}], "max_token": 100},
            {"model": "m", "messages": [{"role": "user", "content": "x"}], "max_tokens": 0},
            {"model": "m", "messages": []},
            {"model": "m", "messages": [{"role": "user", "content": "x", "name": "bob"}]},
            {"model": "m", "messages": [{"role": "user", "content": "x"}], "stop": ["a", "b", "c", "d", "e"]},
        ]
        for c in cases:
            try:
                CompletionRequest.model_validate(c)
                assert False, c
            except ValidationError:
                pass
        """,
        hints=["Use `Literal` for roles, `Field(ge=..., le=...)` for numbers, `Field(min_length=1)` for messages and `Field(max_length=4)` for stop.",
               "`model_config = ConfigDict(extra=\"forbid\")` on **both** models. `default_factory=list` creates a new list each time."],
        solution="""
        from typing import Literal
        from pydantic import BaseModel, ConfigDict, Field


        class Message(BaseModel):
            model_config = ConfigDict(extra="forbid")
            role: Literal["system", "user", "assistant", "tool"]
            content: str


        class CompletionRequest(BaseModel):
            model_config = ConfigDict(extra="forbid")
            model: str
            messages: list[Message] = Field(min_length=1)
            temperature: float = Field(default=1.0, ge=0, le=2)
            max_tokens: int = Field(default=512, ge=1, le=32_000)
            stop: list[str] = Field(default_factory=list, max_length=4)
        """,
        why="""Every bug was a missing declaration, which is the point: with Pydantic, validation **is** the declarations. A plain `str` role accepted anything; a
        `Literal` accepts only real roles. Unconstrained numbers let 7 and 0 through to the provider (which fails later, with a worse error, or clamps
        silently); `Field(ge, le)` rejects them at the gateway with a precise location. Without `extra="forbid"`, `max_token` was dropped and the
        request ran with the default, and an unknown `name` key inside a message disappeared too, so the setting must be on the nested model as well.
        An empty message list now fails `min_length`. And `default_factory=lambda: STOP` returned the **same** global list each time, so one request's
        stop sequence leaked into every later request (9.1); `default_factory=list` creates a new one."""),
    write("Validate tagged events with a discriminator", "hard", tag="GenAI",
        prompt="""Define three models with a `type` tag: `TextDelta(type: Literal["text"], text: str)`, `ToolUse(type: Literal["tool_use"], name: str, input:
        dict)`, `Stop(type: Literal["stop"], reason: Literal["end", "max_tokens"])`. Build `Event = Annotated[TextDelta | ToolUse | Stop,
        Field(discriminator="type")]` and a `TypeAdapter(list[Event])`. Write `parse_events(json_text)` returning the list of validated event objects, and
        `summarise(events)` returning `{"text": joined text, "tools": [tool names], "stop": reason or None}`.""",
        code="""
        from typing import Annotated, Literal
        from pydantic import BaseModel, Field, TypeAdapter

        def parse_events(json_text):
            pass

        def summarise(events):
            pass
        """,
        tests="""
        from pydantic import ValidationError
        raw = '[{"type": "text", "text": "Refunds "}, {"type": "tool_use", "name": "search", "input": {"q": "refund"}}, {"type": "text", "text": "take 5 days."}, {"type": "stop", "reason": "end"}]'
        events = parse_events(raw)
        assert [type(e).__name__ for e in events] == ["TextDelta", "ToolUse", "TextDelta", "Stop"]
        assert summarise(events) == {"text": "Refunds take 5 days.", "tools": ["search"], "stop": "end"}
        try:
            parse_events('[{"type": "tool_use", "name": "x"}, {"type": "ping"}]')
            assert False
        except ValidationError as e:
            locs = [err["loc"] for err in e.errors()]
            assert locs[0] == (0, "tool_use", "input") and locs[1][0] == 1 and e.errors()[1]["type"] == "union_tag_invalid"
        assert summarise(parse_events("[]")) == {"text": "", "tools": [], "stop": None}
        """,
        hints=["Define the three models first, then `Event` and `EVENTS = TypeAdapter(list[Event])` at module level; `parse_events` is `EVENTS.validate_json(json_text)`.",
               "In `summarise`, dispatch on `isinstance` (or `e.type`)."],
        solution="""
        from typing import Annotated, Literal
        from pydantic import BaseModel, Field, TypeAdapter


        class TextDelta(BaseModel):
            type: Literal["text"]
            text: str


        class ToolUse(BaseModel):
            type: Literal["tool_use"]
            name: str
            input: dict


        class Stop(BaseModel):
            type: Literal["stop"]
            reason: Literal["end", "max_tokens"]


        Event = Annotated[TextDelta | ToolUse | Stop, Field(discriminator="type")]
        EVENTS = TypeAdapter(list[Event])


        def parse_events(json_text):
            return EVENTS.validate_json(json_text)


        def summarise(events):
            text, tools, stop = [], [], None
            for e in events:
                if isinstance(e, TextDelta):
                    text.append(e.text)
                elif isinstance(e, ToolUse):
                    tools.append(e.name)
                elif isinstance(e, Stop):
                    stop = e.reason
            return {"text": "".join(text), "tools": tools, "stop": stop}
        """,
        why="""The discriminator tells Pydantic to read the `type` field first and validate the rest against **only** the matching model, which is faster than trying
        every member of the union and gives far better errors: the missing `input` is reported at `(0, "tool_use", "input")`, inside the tool-use branch,
        and an unknown tag gets a dedicated `union_tag_invalid` error instead of three confusing failures. A `TypeAdapter` validates a type that is not a
        model, here a top-level list, and is built once at module level because constructing it compiles the validator. The result is a list of real
        objects, so `summarise` can dispatch with `isinstance` and a type checker narrows each branch (11.2). Streaming APIs deliver events in exactly
        this tagged form."""),
    predict("What is and is not validated", "hard",
        code="""
        from pydantic import BaseModel, ConfigDict, Field, ValidationError

        class Plain(BaseModel):
            n: int = Field(ge=0)

        class Checked(BaseModel):
            model_config = ConfigDict(validate_assignment=True)
            n: int = Field(ge=0)

        class Frozen(BaseModel):
            model_config = ConfigDict(frozen=True)
            n: int = 0

        p = Plain(n=1)
        p.n = -5
        print(p.n, p.model_copy(update={"n": "oops"}).n)
        c = Checked(n=1)
        try:
            c.n = -5
        except ValidationError as e:
            print("assignment rejected:", e.errors()[0]["type"])
        f = Frozen()
        try:
            f.n = 1
        except ValidationError as e:
            print("frozen:", e.errors()[0]["type"])
        print(hash(f) == hash(Frozen()), Plain.model_construct(n=-1).n)
        """,
        hints=["By default only construction and `model_validate` validate; assignment, `model_copy(update=...)` and `model_construct` do not."],
        why="""Validation happens when a model is **created** from input. Assigning a field afterwards is not checked by default, so `p.n` becomes -5, and
        `model_copy(update=...)` copies values in without validation, so the copy holds a string in an `int` field. `validate_assignment=True` re-validates
        on assignment, rejecting -5 with `greater_than_equal`. Frozen models refuse assignment entirely (a `frozen_instance` error) and become hashable by
        value. `model_construct` skips validation by design. To keep the "every instance is valid" guarantee, freeze models or turn on assignment
        validation, and avoid the unvalidated paths for untrusted data."""),
)

section("interview", "Interview questions",
    explain("Pydantic models or dataclasses: how do you choose?", "medium", tag="Interview",
        why="""Both describe structured data with type hints. Dataclasses generate `__init__`, `__repr__` and `__eq__` but trust their inputs completely: no validation,
        no conversion, minimal overhead, and they are part of the standard library. Pydantic models validate and convert at run time, collect every error
        with precise locations, serialise to and from JSON, and generate JSON Schema, at a cost per instance and with a dependency. So use Pydantic at the
        **boundaries**, wherever data comes from outside the program: HTTP requests and responses (FastAPI), configuration and environment, files and queues,
        and LLM structured output. Use dataclasses (or plain classes) for internal objects that your own code creates from already-valid data. Pydantic can
        also validate dataclasses and `TypedDict`s via `TypeAdapter`, which lets internal types be checked at a boundary without converting the whole codebase."""),
    explain("What is the difference between lax and strict validation, and when would you use strict?", "medium", tag="Interview",
        why="""Lax mode, Pydantic's default, accepts values that can be converted without losing information: the string `"5"` for an `int`, `"0.5"` for a `float`,
        `"yes"` or `1` for a `bool`, a whole float like `3.0` for an `int`, a list where a tuple is declared. It rejects lossy conversions such as `7.5` to
        an `int`. That suits data from text-based sources such as query strings, form fields, environment variables and CSV files. Strict mode accepts only
        the exact types (with a few JSON exceptions), so `"5"` is an error for an `int`. Use strict where a type mismatch signals a bug or an attack rather
        than formatting, for example internal service-to-service JSON, financial amounts, or identifiers where `"1"` versus `1` matters; it can be set per
        model (`ConfigDict(strict=True)`), per field (`Field(strict=True)`) or per call (`model_validate(data, strict=True)`)."""),
    explain("How would you validate LLM outputs reliably at scale?", "hard", tag="Interview",
        why="""Describe each expected output as a Pydantic model with tight types (`Literal` labels, numeric ranges, list lengths, required versus nullable fields),
        and generate the JSON Schema from it for the provider's structured-output or tool-calling mode, so the model is constrained up front. Parse every reply
        with `model_validate_json`, which catches malformed JSON, missing fields and out-of-range values in one step, and add validators for rules schemas
        cannot express (citations must refer to retrieved sources, dates must be ordered). On failure, retry a bounded number of times with the compact
        validation errors fed back, and record each failure with the raw reply, the error types and the model and prompt versions. Track failure and retry
        rates per model and prompt as metrics, since a jump usually means a prompt or model change. Version the output models: changing a schema changes
        what deployed prompts produce, so evolve them compatibly (new optional fields) and evaluate before rolling out. Finally, remember that valid is not
        correct: schema validation guarantees shape, and evaluation datasets are still needed to check the content."""),
)

recap(
    "Pydantic models validate and convert input from type hints; `ValidationError` lists every problem with `loc`, `msg` and `type`.",
    "Lax mode converts compatible values (`\"5\"` to 5) but never loses information; strict mode accepts exact types only.",
    "`Field(...)` adds constraints, defaults, descriptions and aliases; a `str | None` field without a default is still required.",
    "`field_validator` (before or after) and `model_validator` hold custom rules; `extra=\"forbid\"`, `frozen` and `validate_assignment` tighten models.",
    "`model_validate_json`, `model_dump`, `model_json_schema` and `TypeAdapter` (with discriminated unions) are the tools for structured LLM output.",
)
