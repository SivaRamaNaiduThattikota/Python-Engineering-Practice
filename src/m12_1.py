from lesson import *
from diagrams import *

lesson(
    id="m12-1", num="12.1", title="pathlib and files",
    intro="Almost every ML and GenAI job starts and ends with files: corpora to index, datasets to load, checkpoints and "
          "reports to write. Paths as objects with `pathlib`, finding files with `glob`, text files and encodings, binary "
          "files and chunked reading, seeking, and atomic writes that survive crashes. Applied to corpora, checkpoints, "
          "duplicate detection and log tails.",
    desc="Paths, glob, text and binary files, atomic writes.",
    keys="pathlib path purepath glob rglob iterdir mkdir parents exist_ok unlink open mode encoding utf-8 newline binary bytes chunk seek tell hashlib sha256 atomic write os.replace fsync tempfile mkstemp temporarydirectory",
)

term("Path", "A `pathlib` object representing a file-system path, with methods to join, inspect, read and write instead of string manipulation.")
term("Encoding", "The rule that turns text (characters) into bytes and back, such as UTF-8. Opening a text file always uses one, so name it explicitly.")
term("Atomic write", "Writing a file so that readers see either the complete old content or the complete new content, never a half-written file: write a temporary file, then rename it over the target.")

section("paths", "Paths as objects",
    fig(stage_map(12, "a document ingestion job"), "Module 12 at a glance: files, data formats, logging and configuration, the plumbing every real job needs."),
    fig(table(["expression", "result"], [
        ["Path('data') / 'raw' / 'a.md'", "data/raw/a.md"],
        ["p.name", "'a.md'"],
        ["p.stem", "'a'"],
        ["p.suffix", "'.md'"],
        ["p.parent", "data/raw"],
        ["p.with_suffix('.txt')", "data/raw/a.txt"],
    ], label="the parts of a path"),
        "A `Path` is an object with named parts, so you never split strings on slashes by hand."),
    p("""File paths are strings in old code, glued together with `+` or `os.path.join` and taken apart with `split`. **`pathlib.Path`** replaces that with an object
    that knows how paths are built: the `/` operator joins parts (`root / "runs" / name`), and attributes take a path apart: `name` (the last part),
    `stem` (the name without its last suffix), `suffix` and `suffixes`, `parent` and `parents`, `parts`. Methods derive new paths: `with_suffix(".json")`,
    `with_name("config.json")`, `relative_to(root)`. The same code works on Windows and Linux, because `Path` is `WindowsPath` or `PosixPath`
    depending on the system; `PurePosixPath` and `PureWindowsPath` do the path arithmetic for one system without touching the disk, which is
    handy in tests."""),
    ex("""
    from pathlib import PurePosixPath as P

    ckpt = P("/data/runs/exp-1/model.best.pt")
    print(ckpt.name, ckpt.stem, ckpt.suffix, ckpt.suffixes)
    print(ckpt.parent, ckpt.parent.name, ckpt.with_suffix(".onnx"))
    root = P("/data")
    print(ckpt.relative_to(root), ckpt.is_relative_to(root / "runs"), (root / "cache" / "emb.npy").as_posix())
    print(P("a/b/../c"), P("logs") / "/tmp/app.log")
    """, "paths.py"),
    p("""Two details catch people. Pure path arithmetic does not resolve `..`, because `a/b/..` only equals `a` if `b` is not a symbolic link, which
    only the disk can say; `Path.resolve()` asks the disk and returns the absolute, normalised path. And joining an **absolute** path discards
    everything before it: `P("logs") / "/tmp/app.log"` is `/tmp/app.log`. That second rule matters for security: joining a user-supplied name to an
    upload folder can escape it, so check `(base / name).resolve().is_relative_to(base.resolve())` before using such a path."""),
    p("""Paths can be passed to everything that accepts a file name (`open`, `json.load` callers, pandas, NumPy), because they implement
    `os.fspath`. Convert to a string with `str(path)` only when a library insists, and use `as_posix()` when you need forward slashes on every
    system, for example as a stable key in a manifest."""),
)

section("explore", "Exploring and changing the file system",
    p("""Concrete paths talk to the disk: `exists()`, `is_file()`, `is_dir()`, `stat().st_size` and `st_mtime` (size and modification time).
    `iterdir()` lists a folder's direct children, **in no guaranteed order**, so sort when order matters. **`glob(pattern)`** finds matches inside a
    folder: `*` matches within one name, `?` one character, `[ab]` a set, and `**` any number of folders, so `root.glob("**/*.md")` and
    `root.rglob("*.md")` both search the whole tree. Results are lazy generators, again unordered."""),
    p("""Changes: `mkdir(parents=True, exist_ok=True)` creates a folder and any missing parents, and does not fail if it exists (without those flags
    it raises `FileNotFoundError` or `FileExistsError`). `unlink(missing_ok=True)` deletes a file, `rmdir()` an empty folder, and
    `shutil.rmtree(path)` a whole tree. `rename(target)` and `replace(target)` move a file; `replace` overwrites an existing target on every system,
    which makes it the tool for atomic writes below. `shutil.copy2` copies a file with its metadata. `tempfile.TemporaryDirectory()` is a context
    manager (10.2) that creates a fresh folder and deletes it afterwards, which is what tests and scratch work should use."""),
    ex("""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in ["docs/faq.md", "docs/refunds.md", "docs/old/2019.md", "notes.txt", ".cache/x.md"]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"content of {rel}", encoding="utf-8")
        print(sorted(p.name for p in root.iterdir()))
        print(sorted(p.relative_to(root).as_posix() for p in root.glob("docs/*.md")))
        print(sorted(p.relative_to(root).as_posix() for p in root.rglob("*.md")))
        print((root / "notes.txt").stat().st_size, (root / "missing.txt").exists())
    print(root.exists())
    """, "explore.py"),
    p("""`rglob` also walked into `.cache`: hidden folders are not skipped automatically, so a corpus loader must filter them itself (problem 5),
    as it must skip `.git`, `node_modules` and virtual environments."""),
)

section("text", "Text files and encodings",
    fig(chain(["bytes on disk", ("decode with an|explicit encoding", "accent"), "str in memory", ("encode on write,|same encoding", "accent")], note="leave out encoding= and the platform default is used"),
        "Text files are bytes plus an encoding; always pass `encoding=\"utf-8\"` so the result does not depend on the machine."),
    p("""`open(path, mode, encoding=...)` returns a file object. The mode says what you will do: `"r"` read (the default), `"w"` write, truncating any existing
    file to empty **immediately**, `"a"` append to the end, `"x"` create, failing with `FileExistsError` if the file exists, and `"+"` adds the other
    direction (`"r+"`). Always use it in a `with` block so it is closed, which also flushes buffered writes to the operating system. `Path.read_text()`
    and `write_text()` do open, read or write, and close in one call, for small files."""),
    p("""A text file is bytes on disk, and an **encoding** turns them into characters. UTF-8 is the standard for data and code, but `open` without `encoding=`
    uses the platform's default, which is still a legacy code page such as cp1252 on many Windows machines, so the same code reads `café` correctly on a
    Mac and as `cafÃ©` (or crashes) on a colleague's laptop. **Always pass `encoding="utf-8"`.** Read with `errors="replace"` when the input may contain
    invalid bytes and losing a character is acceptable (scraped web text), and with `encoding="utf-8-sig"` when files from Excel start with a byte-order
    mark. Text mode also translates line endings: on reading, `\\r\\n` and `\\r` become `\\n`; on writing, `\\n` becomes the platform's line ending,
    unless you pass `newline=""` (12.2 needs that for CSV)."""),
    ex("""
    import os, tempfile

    path = os.path.join(tempfile.mkdtemp(), "notes.txt")
    with open(path, "w", encoding="utf-8") as f:
        print(f.write("café\\nrefund window\\n"))
    print(os.path.getsize(path), "bytes on disk")
    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, start=1):
            print(number, repr(line))
    with open(path, encoding="latin-1") as f:
        print(f.readline().rstrip())
    with open(path, encoding="ascii", errors="replace") as f:
        print(f.readline().rstrip())
    """, "text.py"),
    p("""`write` returns the number of **characters** written, 19, while the file holds 20 bytes, because `é` takes two bytes in UTF-8. Iterating over a
    file yields one line at a time, newline included, and reads lazily, so a 50 GB log can be processed with constant memory; `f.read()` and
    `f.readlines()` load everything, which is fine for small files only. Decoding UTF-8 bytes as Latin-1 never fails but produces the classic
    mojibake `cafÃ©`, and decoding as ASCII with `errors="replace"` turns each invalid byte into the replacement character `�`."""),
)

section("binary", "Binary files, chunks and seeking",
    p("""Mode `"rb"` or `"wb"` opens a file in **binary** mode: no encoding, no newline translation, reads return `bytes`. Use it for images, model weights,
    NumPy and Parquet files, compressed data, and whenever you hash or copy a file exactly. Large binary files are read in **chunks**: `f.read(n)` returns
    up to `n` bytes and `b""` at the end, so `for chunk in iter(lambda: f.read(1 << 16), b""):` walks any file with 64 KiB of memory. Hashing a file this
    way, `hashlib.sha256()` updated chunk by chunk, gives a content fingerprint used to detect duplicate documents and changed datasets (problem 7)."""),
    p("""A file object has a **position**. `f.tell()` returns it, `f.seek(offset, whence)` moves it: `whence` 0 counts from the start, 1 from the current
    position, 2 from the end (with a negative offset). In binary mode positions are byte offsets, which is how tools such as `tail` read the end of a huge
    log without reading the whole file (problem 12). In text mode `seek` only accepts values previously returned by `tell`, because a character may
    span several bytes."""),
    ex("""
    import hashlib, os, tempfile

    path = os.path.join(tempfile.mkdtemp(), "weights.bin")
    with open(path, "wb") as f:
        f.write(b"HDR1" + bytes(range(256)) * 1000)
    digest = hashlib.sha256()
    chunks = 0
    with open(path, "rb") as f:
        print(f.read(4), f.tell())
        f.seek(0)
        for chunk in iter(lambda: f.read(65_536), b""):
            digest.update(chunk)
            chunks += 1
        f.seek(-3, 2)
        print(list(f.read()), f.tell())
    with open(path, "rb") as f:
        print(chunks, digest.hexdigest() == hashlib.sha256(f.read()).hexdigest())
    """, "binary.py"),
)

section("atomic", "Atomic writes",
    fig(chain(["write to a temp file|in the same folder", "flush and fsync", ("os.replace(tmp, target)", "accent"), ("readers see the old file|or the new one, never half", "good")]),
        "An atomic write: the target is only replaced once the new content is complete and on disk."),
    p("""Opening a file with `"w"` empties it at once, and the new content is written over time. If the program crashes, is killed, or raises an exception
    halfway through (an unserialisable value at the end of a `json.dump`), the file is left truncated or half-written, and the old content is gone.
    For a model registry, a checkpoint index or a config file, that turns one failed run into a broken system."""),
    p("""The fix is an **atomic write**: write the new content to a temporary file **in the same folder**, flush it and ask the operating system to put it on
    disk (`f.flush()` then `os.fsync(f.fileno())`), then call **`os.replace(tmp, target)`**. On the same file system, a rename is atomic: other readers see
    either the old file or the new one, never a mix. If anything fails before the rename, delete the temporary file and the target is untouched. The
    temporary file must be in the same folder because a rename across file systems is a copy, which is not atomic; `tempfile.mkstemp(dir=folder)`
    creates a uniquely named file there, so two writers never collide on the temporary name."""),
    ex("""
    import json, os, tempfile
    from pathlib import Path

    def save_json_atomic(path, data):
        path = Path(path)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except BaseException:
            os.unlink(tmp)
            raise

    target = Path(tempfile.mkdtemp()) / "registry.json"
    save_json_atomic(target, {"best": "v3"})
    try:
        save_json_atomic(target, {"best": "v4", "model": object()})
    except TypeError as e:
        print("failed:", e)
    print(target.read_text(encoding="utf-8"), sorted(p.name for p in target.parent.iterdir()))
    """, "atomic.py"),
    p("""The failed save raised, its temporary file was removed, and the registry still holds the complete previous version. `except BaseException` (not
    `Exception`) also cleans up on `KeyboardInterrupt`, and the error is re-raised (7.2). Problem 10 fixes a non-atomic save, and problem 13 turns the
    pattern into a reusable context manager."""),
)

section("warmup", "Warm-up",
    predict("Taking a path apart", "easy",
        code="""
        from pathlib import PurePosixPath as P

        p = P("/srv/corpus/en/faq.v2.md")
        print(p.name, p.stem, p.suffix, p.suffixes)
        print(p.parent.name, p.parents[2], p.with_suffix(".json"), p.with_stem("faq"))
        print(p.relative_to("/srv/corpus"), p.parts[:3])
        print(P("/srv") / "corpus" / "x.md", P("data") / "/etc/passwd", P("a/./b//c"))
        """,
        hints=["`stem` drops only the last suffix. `parents[0]` is the parent. Joining an absolute path restarts from it."],
        why="""`name` is the last part and `suffix` its last extension, so the stem keeps `.v2`; `suffixes` lists both. `parents[2]` goes up three levels. `with_suffix`
        replaces only the last extension, and `with_stem` replaces the part before it, so `.v2` disappears and `.md` stays. Joining `"/etc/passwd"`
        discards `data` because the right-hand side is absolute, the reason user-supplied names must be checked before joining. Redundant `.` parts and
        double slashes are cleaned up, while `..` would be kept."""),
    write("Checkpoint paths and the latest checkpoint", "easy", tag="ML",
        prompt="""Write `checkpoint_path(root, run, step)` returning `Path(root) / "runs" / run / "step-000123.pt"` (step padded to 6 digits), and
        `latest_checkpoint(run_dir)` returning the path of the checkpoint with the highest step number among files named `step-<digits>.pt` (ignoring
        names like `step-best.pt` and `step-000010.pt.tmp`), or `None` if there are none. Old runs used unpadded names such as `step-50.pt`, so compare
        numbers, not strings.""",
        code="""
        from pathlib import Path

        def checkpoint_path(root, run, step):
            pass

        def latest_checkpoint(run_dir):
            pass
        """,
        tests="""
        import tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp())
        assert checkpoint_path(root, "exp-1", 123) == root / "runs" / "exp-1" / "step-000123.pt"
        run = checkpoint_path(root, "exp-1", 0).parent
        run.mkdir(parents=True)
        assert latest_checkpoint(run) is None
        for name in ["step-000010.pt", "step-50.pt", "step-000100.pt", "step-best.pt", "step-000999.pt.tmp", "notes.txt"]:
            (run / name).write_bytes(b"w")
        assert latest_checkpoint(run) == run / "step-000100.pt"
        (run / "step-7000.pt").write_bytes(b"w")
        assert latest_checkpoint(run).name == "step-7000.pt"
        """,
        hints=["`run_dir.glob(\"step-*.pt\")` finds candidates; `path.stem.removeprefix(\"step-\")` must be all digits.",
               "`max(candidates, key=...)` with the parsed int, or `None` for an empty list."],
        solution="""
        from pathlib import Path


        def checkpoint_path(root, run, step):
            return Path(root) / "runs" / run / f"step-{step:06d}.pt"


        def latest_checkpoint(run_dir):
            found = []
            for path in Path(run_dir).glob("step-*.pt"):
                number = path.stem.removeprefix("step-")
                if number.isdigit():
                    found.append((int(number), path))
            if not found:
                return None
            return max(found)[1]
        """,
        why="""Building paths with `/` keeps them correct on every system, and padding the step makes new names sort correctly even as strings. The glob pattern
        `step-*.pt` requires the name to **end** in `.pt`, which excludes the temporary file, and the digit check excludes `step-best.pt`. Comparing parsed
        integers is what makes the legacy `step-50.pt` and `step-7000.pt` order correctly: as strings, `"step-50.pt"` sorts after `"step-000100.pt"`. The
        `(number, path)` tuples sort by number first. Training scripts use exactly this to resume from the last checkpoint after a crash."""),
    fix("A transcript that keeps only the last turn", "easy", tag="GenAI",
        prompt="""`log_turn` should add one JSON line per chat turn to a transcript file, creating the file on first use. After a conversation, the file contains only the
        final turn. Fix it.""",
        code="""
        import json

        def log_turn(path, role, content):
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"role": role, "content": content}) + "\\n")
        """,
        tests="""
        import json, os, tempfile
        path = os.path.join(tempfile.mkdtemp(), "chat.jsonl")
        for role, text in [("user", "Refund?"), ("assistant", "5 days."), ("user", "Thanks, café")]:
            log_turn(path, role, text)
        with open(path, encoding="utf-8") as f:
            turns = [json.loads(line) for line in f]
        assert [t["role"] for t in turns] == ["user", "assistant", "user"]
        assert turns[2]["content"] == "Thanks, café"
        """,
        hints=["Mode `\"w\"` truncates the file every time it is opened."],
        solution="""
        import json

        def log_turn(path, role, content):
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"role": role, "content": content}) + "\\n")
        """,
        why="""`"w"` empties the file the moment it is opened, so each call replaced the whole transcript with one line. `"a"` opens for appending, creating the file if
        needed and writing every new line at the end, which is how logs and JSON Lines transcripts grow. Appending one complete line per call also keeps the
        file readable after a crash: at worst the last line is incomplete, and a reader can skip it (12.2)."""),
    predict("Modes, lines and positions", "easy",
        code="""
        import os, tempfile

        path = os.path.join(tempfile.mkdtemp(), "notes.txt")
        with open(path, "w", encoding="utf-8") as f:
            print(f.write("first\\nsecond"))
        with open(path, "a", encoding="utf-8") as f:
            f.write("\\nthird\\n")
        with open(path, encoding="utf-8") as f:
            print(repr(f.readline()), f.readlines(), repr(f.read()))
        try:
            open(path, "x")
        except FileExistsError as e:
            print(type(e).__name__)
        with open(path, "w", encoding="utf-8") as f:
            pass
        print(os.path.getsize(path))
        """,
        hints=["`write` returns the number of characters. `readline` keeps the newline. Opening with `\"w\"` truncates even if nothing is written."],
        why="""The first write returns 12, the characters in `first`, the newline and `second`. Appending adds the rest, so the file has three lines. `readline` returns
        the first line with its newline, `readlines` the remaining lines, and `read` at the end of the file returns an empty string, not an error. Mode
        `"x"` refuses to open an existing file. Finally, opening with `"w"` and writing nothing still empties the file to 0 bytes, the danger behind
        problem 10."""),
)

section("medium", "Medium",
    write("Load a document corpus", "medium", tag="RAG",
        prompt="""Write `load_corpus(root)` returning a dict from each document's path relative to `root` (as a POSIX string) to its text, for every `.md` and `.txt`
        file in the whole tree (suffix compared case-insensitively). Skip anything inside a folder whose name starts with `.`, skip files whose text is
        empty or only whitespace, read as UTF-8, and return the dict with keys in sorted order.""",
        code="""
        from pathlib import Path

        def load_corpus(root):
            pass
        """,
        tests="""
        import tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp())
        files = {"docs/faq.md": "Refunds take 5 days.", "docs/empty.txt": "  \\n", ".git/info.txt": "x", "notes/a/b.txt": "Déjà vu",
                 "README.MD": "Readme", "docs/.drafts/wip.md": "draft", "image.png": "not text", "docs/.hidden.md": "kept"}
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text, encoding="utf-8")
        corpus = load_corpus(root)
        assert list(corpus) == ["README.MD", "docs/.hidden.md", "docs/faq.md", "notes/a/b.txt"]
        assert corpus["notes/a/b.txt"] == "Déjà vu" and load_corpus(root / "notes") == {"a/b.txt": "Déjà vu"}
        """,
        hints=["`Path(root).rglob(\"*\")` and filter: `path.is_file()`, `path.suffix.lower()`, and the folder parts of `path.relative_to(root)`.",
               "Only the folders matter for the hidden check: `rel.parts[:-1]`."],
        solution="""
        from pathlib import Path

        SUFFIXES = {".md", ".txt"}


        def load_corpus(root):
            root = Path(root)
            docs = {}
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in SUFFIXES:
                    continue
                rel = path.relative_to(root)
                if any(part.startswith(".") for part in rel.parts[:-1]):
                    continue
                text = path.read_text(encoding="utf-8")
                if text.strip():
                    docs[rel.as_posix()] = text
            return dict(sorted(docs.items()))
        """,
        why="""`rglob` walks the entire tree, hidden folders included, so the loader makes three decisions explicitly: which file types are documents (case-insensitive,
        since `README.MD` exists in real repositories), which folders are not content (`.git`, drafts, caches; a hidden **file** is kept, as the spec says),
        and which files are empty. Keys relative to the root, with forward slashes, are stable document ids: the same on Windows and Linux and independent of
        where the corpus is checked out, which matters when the ids are stored in a vector index (5.P). Sorting makes runs reproducible, since `rglob`
        order is not guaranteed."""),
    fix("Saving artefacts into a new folder", "medium", tag="ML",
        prompt="""`save_artifact` writes a file into `root/run/` for a training run. The first call for a new `root` fails with `FileNotFoundError` when `root` itself
        does not exist yet, and the second artefact of a run fails with `FileExistsError`. Fix it, keeping the return value.""",
        code="""
        from pathlib import Path

        def save_artifact(root, run, name, text):
            folder = Path(root) / run
            folder.mkdir()
            path = folder / name
            path.write_text(text, encoding="utf-8")
            return path
        """,
        tests="""
        import tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp()) / "artifacts"
        a = save_artifact(root, "exp-1", "metrics.json", '{"f1": 0.91}')
        b = save_artifact(root, "exp-1", "notes.md", "lr 3e-4")
        assert a.read_text(encoding="utf-8") == '{"f1": 0.91}' and b.parent == a.parent == root / "exp-1"
        assert sorted(p.name for p in (root / "exp-1").iterdir()) == ["metrics.json", "notes.md"]
        """,
        hints=["`mkdir(parents=True, exist_ok=True)`."],
        solution="""
        from pathlib import Path

        def save_artifact(root, run, name, text):
            folder = Path(root) / run
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / name
            path.write_text(text, encoding="utf-8")
            return path
        """,
        why="""Plain `mkdir()` creates exactly one folder, failing if its parent is missing (`parents=True` creates the whole chain) and failing if it already exists
        (`exist_ok=True` makes that fine, while still raising if a **file** of that name is in the way). Checking `exists()` first and then creating would
        be a race when two processes start at once; the flags make the call safe to repeat, which is what every "make sure the output folder exists" line
        should be."""),
    write("Find duplicate documents", "medium", tag="Data work",
        prompt="""Write `sha256_file(path, chunk_size=65536)` returning the hex SHA-256 of a file, reading it in binary chunks of `chunk_size` bytes. Then write
        `find_duplicates(root)` returning a sorted list of groups, each a sorted list of POSIX paths relative to `root`, of files in the tree with identical
        content (groups of two or more only). Only hash files whose size is shared with another file.""",
        code="""
        import hashlib
        from pathlib import Path

        def sha256_file(path, chunk_size=65536):
            pass

        def find_duplicates(root):
            pass
        """,
        tests="""
        import hashlib, tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp())
        data = {"a/faq.md": b"Refunds take 5 days.", "b/faq-copy.md": b"Refunds take 5 days.", "c/faq.md": b"Refunds take 5 dayz.",
                "x.txt": b"hello", "y/z.txt": b"hello", "w.txt": b"hello", "unique.bin": b"\\x00" * 50}
        for rel, content in data.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(content)
        assert sha256_file(root / "x.txt", chunk_size=2) == hashlib.sha256(b"hello").hexdigest()
        assert find_duplicates(root) == [["a/faq.md", "b/faq-copy.md"], ["w.txt", "x.txt", "y/z.txt"]]
        hashed = []
        original = sha256_file
        def counting(path, chunk_size=65536):
            hashed.append(Path(path).name)
            return original(path, chunk_size)
        globals()["sha256_file"] = counting
        find_duplicates(root)
        globals()["sha256_file"] = original
        assert "unique.bin" not in hashed and len(hashed) == 6
        """,
        hints=["`for chunk in iter(lambda: f.read(chunk_size), b\"\"): h.update(chunk)`.",
               "First group paths by `stat().st_size`; hash only groups with more than one file; then group by digest."],
        solution="""
        import hashlib
        from pathlib import Path


        def sha256_file(path, chunk_size=65536):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    h.update(chunk)
            return h.hexdigest()


        def find_duplicates(root):
            root = Path(root)
            by_size = {}
            for path in root.rglob("*"):
                if path.is_file():
                    by_size.setdefault(path.stat().st_size, []).append(path)
            by_hash = {}
            for paths in by_size.values():
                if len(paths) < 2:
                    continue
                for path in paths:
                    by_hash.setdefault(sha256_file(path), []).append(path.relative_to(root).as_posix())
            return sorted(sorted(group) for group in by_hash.values() if len(group) > 1)
        """,
        why="""Reading in fixed-size chunks keeps memory constant whatever the file size, and the digest is identical to hashing the whole content at once. Grouping by
        size first is the classic optimisation: files of different sizes cannot be identical, and `stat` is far cheaper than reading, so in a real corpus
        most files are never hashed (here the unique 50-byte file is skipped, while the two 20-byte files are hashed and found to differ). Content hashes
        are how ingestion pipelines skip documents they have already embedded, and how dataset versioning tools detect changed files."""),
    choose("Open once or once per line", "medium", tag="Data work",
        prompt="Both write 3,000 lines to a file. Which is faster?",
        setup="""import os, tempfile
path = os.path.join(tempfile.mkdtemp(), "out.txt")
lines = [f"record {i}\\n" for i in range(3_000)]""",
        options={
            "a": "for line in lines:\n    with open(path, \"a\", encoding=\"utf-8\") as f:\n        f.write(line)",
            "b": "with open(path, \"w\", encoding=\"utf-8\") as f:\n    for line in lines:\n        f.write(line)",
        },
        answer="b",
        hints=["What does every `open` and `close` cost, compared with a buffered `write`?"],
        why="""Opening a file is a system call that looks up the path, checks permissions and allocates a file object, and closing flushes the buffer with another system
        call, so option A pays that 3,000 times. Option B opens once, and its writes go into an in-memory buffer that is flushed to the operating system
        in large blocks. Keep files open for the duration of a batch; append-per-call (problem 3) is right only for events that arrive one at a time, such as
        log lines from separate requests."""),
    trace("Seeking in a binary file", "medium",
        prompt="Fill in `data` and `pos` after each marked line.",
        code="""
        import os, tempfile

        path = os.path.join(tempfile.mkdtemp(), "b.bin")
        with open(path, "wb") as f:
            f.write(bytes(range(10, 20)))

        f = open(path, "rb")
        data, pos = list(f.read(3)), f.tell()  # row: "first read"
        f.seek(-2, 2)
        data, pos = list(f.read()), f.tell()  # row: "from the end"
        f.seek(1)
        f.seek(4, 1)
        data, pos = list(f.read(2)), f.tell()  # row: "relative seek"
        data, pos = list(f.read(100)), f.tell()  # row: "past the end"
        f.close()
        """,
        trace_vars=["data", "pos"],
        hints=["The file holds the bytes 10 to 19 at positions 0 to 9. `seek(offset, 1)` moves relative to the current position."],
        why="""Reading three bytes from the start returns 10, 11, 12 and leaves the position at 3. Seeking to two bytes before the end and reading the rest returns the last
        two bytes, leaving the position at the end, 10. Seeking to 1 and then 4 further lands on position 5, so the next two bytes are 15 and 16. Asking for
        more bytes than remain is not an error: `read` returns what is left, here 17, 18, 19, and the position stops at the end."""),
    fix("A config save that corrupts the file", "medium", tag="GenAI",
        prompt="""`save_config` writes the prompt configuration as JSON. When a value is not serialisable, the call raises, as it should, but it also leaves the file
        half-written, so the service cannot start. Make the save atomic: on failure, the previous file must be intact and no temporary file left
        behind.""",
        code="""
        import json, os
        from pathlib import Path

        def save_config(path, config):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        """,
        tests="""
        import json, tempfile
        from pathlib import Path
        target = Path(tempfile.mkdtemp()) / "prompt.json"
        save_config(target, {"model": "small", "temperature": 0.2})
        try:
            save_config(target, {"model": "large", "temperature": 0.7, "callback": print})
            assert False
        except TypeError:
            pass
        assert json.loads(target.read_text(encoding="utf-8")) == {"model": "small", "temperature": 0.2}
        assert [p.name for p in target.parent.iterdir()] == ["prompt.json"]
        save_config(target, {"model": "large"})
        assert json.loads(target.read_text(encoding="utf-8")) == {"model": "large"}
        """,
        hints=["Write to a temporary file in the same folder, then `os.replace(tmp, path)`; delete the temporary file if anything fails."],
        solution="""
        import json, os
        from pathlib import Path

        def save_config(path, config):
            path = Path(path)
            tmp = path.with_name(path.name + ".tmp")
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
        """,
        why="""`json.dump` writes to the file piece by piece as it encodes, so by the time it reached the function it could not serialise, the opening `"w"` had already
        emptied the file and the first keys had been written: the service then failed to parse its own config. Writing to a temporary file means the
        target is only touched by `os.replace`, which swaps the complete new file in at once. The fixed temporary name is fine for a single writer; with
        concurrent writers, use `tempfile.mkstemp` for a unique name, as in the lesson's example."""),
    predict("Encodings and bytes", "medium",
        code="""
        import os, tempfile

        path = os.path.join(tempfile.mkdtemp(), "t.txt")
        with open(path, "w", encoding="utf-8") as f:
            n = f.write("naïve café")
        print(n, os.path.getsize(path), len("✓".encode("utf-8")))
        with open(path, encoding="latin-1") as f:
            print(f.read())
        with open(path, "rb") as f:
            print(f.read(5))
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("id")
        with open(path, "rb") as f:
            raw = f.read()
        with open(path, encoding="utf-8") as f:
            plain = f.read()
        print(raw, len(plain), plain == "id")
        """,
        hints=["`ï` and `é` take two bytes each in UTF-8; `✓` takes three. `utf-8-sig` writes a three-byte byte-order mark."],
        why="""The text has 10 characters and 12 bytes, because two of them need two bytes in UTF-8. Reading UTF-8 bytes as Latin-1 decodes each byte as one character,
        producing mojibake. The first five bytes are `n`, `a`, the two bytes of `ï` (shown as escapes) and `v`: five bytes but only four characters. Writing with
        `utf-8-sig` prefixes the byte-order mark `\\xef\\xbb\\xbf`; reading it back as plain `utf-8` keeps the mark as an invisible character `\\ufeff`,
        so the string has three characters and does not equal `"id"`, the bug behind CSV headers that "do not match" (read such files with
        `utf-8-sig`)."""),
)

section("hard", "Hard",
    write("Tail a large log", "hard", tag="Data work",
        prompt="""Write `tail(path, n, block=1024)` returning the last `n` lines of a UTF-8 text file (without newlines), like the `tail` command, **without reading the
        whole file**: open it in binary mode, read blocks of `block` bytes backwards from the end until you have more than `n` newlines or reach the start,
        then decode. Lines may contain multi-byte characters that a block boundary can cut. Return `[]` for `n <= 0` or an empty file.""",
        code="""
        def tail(path, n, block=1024):
            pass
        """,
        tests="""
        import os, tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "app.log")
        lines = [f"{i:05d} réponse ✓ ok" for i in range(5_000)]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\\n".join(lines) + "\\n")
        assert tail(path, 3) == lines[-3:]
        assert tail(path, 2, block=7) == lines[-2:] and tail(path, 1, block=1) == lines[-1:]
        assert tail(path, 0) == [] and len(tail(path, 10_000, block=4096)) == 5_000
        short = os.path.join(d, "short.log")
        with open(short, "w", encoding="utf-8") as f:
            f.write("a\\nb\\nc")
        assert tail(short, 2) == ["b", "c"] and tail(short, 5) == ["a", "b", "c"]
        open(os.path.join(d, "empty.log"), "w").close()
        assert tail(os.path.join(d, "empty.log"), 3) == []
        reads = []
        real_open = open
        class Spy:
            def __init__(self, f): self.f = f
            def __enter__(self): return self
            def __exit__(self, *a): self.f.close()
            def seek(self, *a): return self.f.seek(*a)
            def tell(self): return self.f.tell()
            def read(self, size=-1):
                reads.append(size)
                return self.f.read(size)
        import builtins
        builtins.open = lambda *a, **k: Spy(real_open(*a, **k))
        try:
            tail(path, 2, block=256)
        finally:
            builtins.open = real_open
        assert sum(reads) <= 512 and -1 not in reads
        """,
        hints=["`f.seek(0, 2)` and `f.tell()` give the size. Move `pos` back by `min(block, pos)`, `seek(pos)`, and prepend `f.read(step)`.",
               "If you stopped before the start of the file, the first line is probably cut: drop everything up to the first `b\"\\n\"` before decoding.",
               "`splitlines()` on the decoded text, then the last `n`."],
        solution="""
        def tail(path, n, block=1024):
            if n <= 0:
                return []
            with open(path, "rb") as f:
                f.seek(0, 2)
                pos = f.tell()
                data = b""
                while pos > 0 and data.count(b"\\n") <= n:
                    step = min(block, pos)
                    pos -= step
                    f.seek(pos)
                    data = f.read(step) + data
            if pos > 0:
                data = data[data.index(b"\\n") + 1:]
            return data.decode("utf-8").splitlines()[-n:]
        """,
        why="""The file is read from the end in blocks, so the cost depends on the size of the last few lines, not of the file: two lines of a 150 KB log need at most two
        256-byte reads. Binary mode is required because only byte offsets can be seeked freely (text-mode `seek` accepts only `tell` values). The loop
        stops once it has **more** than `n` newlines, since with a trailing newline, `n` complete lines need `n + 1`. When it stopped mid-file, the
        first bytes belong to a line that was cut, possibly in the middle of a multi-byte character, so everything before the first newline is dropped
        before decoding, which also prevents a `UnicodeDecodeError` at the boundary. Log viewers, monitoring agents and "show the last error" debugging
        tools all work this way."""),
    write("An atomic-write context manager", "hard", tag="GenAI",
        prompt="""Write a context manager `atomic_write(path, mode="w", encoding="utf-8")` that yields a file object for a temporary file in the same folder (created
        with `tempfile.mkstemp`, name starting with `"."`) and, on a clean exit, flushes, `fsync`s and replaces `path` with it. On an exception, delete the
        temporary file and re-raise; `path` is untouched. Support `"w"` (text, with the encoding) and `"wb"` (binary, no encoding); any other mode raises
        `ValueError` before creating anything.""",
        code="""
        import os, tempfile
        from contextlib import contextmanager
        from pathlib import Path

        @contextmanager
        def atomic_write(path, mode="w", encoding="utf-8"):
            yield
        """,
        tests="""
        import json, tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        target = d / "index.json"
        with atomic_write(target) as f:
            json.dump({"docs": 3, "name": "café"}, f)
        assert json.loads(target.read_text(encoding="utf-8")) == {"docs": 3, "name": "café"}
        try:
            with atomic_write(target) as f:
                f.write('{"docs": ')
                raise RuntimeError("embedding service down")
        except RuntimeError:
            pass
        assert json.loads(target.read_text(encoding="utf-8"))["docs"] == 3 and [p.name for p in d.iterdir()] == ["index.json"]
        with atomic_write(d / "emb.bin", "wb") as f:
            f.write(bytes([1, 2, 3]))
        assert (d / "emb.bin").read_bytes() == bytes([1, 2, 3])
        try:
            with atomic_write(d / "x.txt", "a") as f:
                pass
            assert False
        except ValueError:
            pass
        assert sorted(p.name for p in d.iterdir()) == ["emb.bin", "index.json"]
        """,
        hints=["Validate the mode first. `fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=\".\" + path.name + \".\")`, then `os.fdopen(fd, mode, encoding=...)`.",
               "Put the `yield` inside `try`; on `BaseException`, unlink the temporary file and `raise`."],
        solution="""
        import os, tempfile
        from contextlib import contextmanager
        from pathlib import Path


        @contextmanager
        def atomic_write(path, mode="w", encoding="utf-8"):
            if mode not in ("w", "wb"):
                raise ValueError(f"atomic_write supports 'w' and 'wb', not {mode!r}")
            path = Path(path)
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
            try:
                with os.fdopen(fd, mode, encoding=None if "b" in mode else encoding) as f:
                    yield f
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
            except BaseException:
                try:
                    os.unlink(tmp)
                except FileNotFoundError:
                    pass
                raise
        """,
        why="""The context manager packages the atomic-write recipe so callers write normally inside a `with` block (10.2). `mkstemp` creates a uniquely named file in the
        **target's folder**, so the final `os.replace` is a rename on the same file system, and concurrent writers never share a temporary file. The
        `yield` sits inside `try`, so an exception in the caller's block, here a failing embedding service, lands in the `except`, which removes the
        partial file and re-raises (a generator-based manager must re-raise, or the error would be swallowed). Only a clean exit reaches the flush, the
        `fsync` that forces the data to disk before the rename, and the replace. Validating the mode before `mkstemp` means a bad call leaves nothing behind.
        Vector-index writers, model registries and caching layers use exactly this helper."""),
    fix("Read the code: summarising prediction files", "hard", tag="ML",
        prompt="""`summarise_runs` counts predicted labels across the JSON prediction files of many runs and writes a summary. It misses every run in a subfolder,
        counts draft files (names starting with `_`) that should be ignored, crashes when the output folder does not exist, leaves file handles open, and the
        summary ends up with only one line, in no particular order. Fix it so the summary has one `label count` line per label, sorted by count descending and
        then label, written as UTF-8, and the function returns the summary path.""",
        code="""
        import json
        from pathlib import Path


        def summarise_runs(src_dir, out_dir):
            counts = {}
            for path in Path(src_dir).glob("*.json"):
                data = json.loads(open(path).read())
                for p in data["predictions"]:
                    counts[p["label"]] = counts.get(p["label"], 0) + 1
            out = Path(out_dir) / "summary.txt"
            for label in counts:
                with open(out, "w") as f:
                    f.write(f"{label} {counts[label]}\\n")
            return out
        """,
        tests="""
        import json, tempfile
        from pathlib import Path
        src = Path(tempfile.mkdtemp())
        runs = {"run-1.json": ["spam", "ham", "spam"], "2025/run-2.json": ["phish", "ham", "spam"], "2025/q1/run-3.json": ["ham"],
                "_draft.json": ["spam"] * 10, "2025/_old.json": ["phish"] * 5}
        for rel, labels in runs.items():
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            (src / rel).write_text(json.dumps({"predictions": [{"id": i, "label": l} for i, l in enumerate(labels)]}), encoding="utf-8")
        out = summarise_runs(src, src.parent / (src.name + "-out") / "reports")
        assert out.name == "summary.txt"
        assert out.read_text(encoding="utf-8").splitlines() == ["ham 3", "spam 3", "phish 1"]
        """,
        hints=["`rglob(\"*.json\")` plus a name check; `path.read_text(encoding=\"utf-8\")` opens and closes the file.",
               "Create the output folder with `mkdir(parents=True, exist_ok=True)` and write all lines once, sorted with the key `(-count, label)`."],
        solution="""
        import json
        from pathlib import Path


        def summarise_runs(src_dir, out_dir):
            counts = {}
            for path in sorted(Path(src_dir).rglob("*.json")):
                if path.name.startswith("_"):
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                for p in data["predictions"]:
                    counts[p["label"]] = counts.get(p["label"], 0) + 1
            out_dir = Path(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / "summary.txt"
            ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            out.write_text("".join(f"{label} {n}\\n" for label, n in ordered), encoding="utf-8")
            return out
        """,
        why="""Each bug is a file-handling habit from this lesson. `glob("*.json")` searches one folder; `rglob` searches the tree. Draft files need an explicit rule,
        since nothing skips them by default. `open(path).read()` without `with` leaves closing to the garbage collector, and without `encoding` reads with
        the platform default; `read_text(encoding="utf-8")` fixes both. Writing needs the folder to exist (`mkdir` with both flags). The loop reopened the
        summary with `"w"` for every label, truncating it each time, so only the last label survived; building the whole text and writing it once fixes
        that, and the sort key `(-count, label)` gives a deterministic order, so summaries from two runs can be compared with a plain diff."""),
    predict("Path rules across systems", "hard",
        code="""
        from pathlib import PurePosixPath as P, PureWindowsPath as W

        print(W("C:/Data/Model.PT") == W("c:\\\\data\\\\model.pt"), P("Data/m.pt") == P("data/m.pt"))
        print(W("C:/data/runs") / "exp", W("C:/data").drive, W("C:/data") / "D:/other")
        print(sorted([P("b/2.txt"), P("a/10.txt"), P("a/9.txt")]))
        print(P("archive.tar.gz").stem, repr(P(".bashrc").suffix), P(".bashrc").stem)
        print(P("/srv/uploads/../etc").parts, P("x").with_suffix(".txt").with_suffix(""))
        """,
        hints=["Windows paths compare case-insensitively and accept both separators. Pure paths sort by their parts as strings. A leading dot is not a suffix."],
        why="""Windows paths ignore case and treat `/` and `\\` alike, so the two Windows paths are equal, while POSIX paths are case-sensitive. Windows paths print with
        backslashes, keep the drive separately, and joining a path on another drive starts over from it, like an absolute POSIX path. Paths sort by their
        parts as strings, so `10.txt` comes before `9.txt` (sort by a parsed number when that matters, as in problem 2). A name such as `.bashrc` is all
        stem and no suffix. Pure paths keep `..` as a part, which is why upload paths must be resolved before checking where they point, and
        `with_suffix("")` removes a suffix."""),
)

section("interview", "Interview questions",
    explain("What is an atomic write, and how do you implement one in Python?", "medium", tag="Interview",
        why="""An atomic write makes a file change all-or-nothing: readers and later runs see either the complete old file or the complete new one, never a truncated or
        half-written file, even if the process crashes or raises halfway. Opening the target with `"w"` cannot give that, because it truncates the file
        immediately and writes over time. The recipe: create a temporary file **in the same folder** (`tempfile.mkstemp(dir=target.parent)` gives a unique
        name), write everything to it, `flush()` and `os.fsync()` so the data reaches the disk, then `os.replace(tmp, target)`, which renames it over the
        target atomically on the same file system, on POSIX and Windows. On any exception, delete the temporary file and re-raise. Same folder matters
        because a rename across file systems becomes a copy, which is not atomic. Use it for config files, model registries, indexes, caches and any file
        another process reads while you write; for appending events, a log line per write is usually enough."""),
    explain("Why should you always pass an encoding when opening text files?", "medium", tag="Interview",
        why="""Text files are bytes, and `open` needs an encoding to turn them into characters. Without `encoding=`, Python uses the platform's default: UTF-8 on Linux and
        macOS, but often a legacy code page such as cp1252 on Windows. So code that reads `café` correctly on the developer's laptop produces `cafÃ©` or raises
        `UnicodeDecodeError` on another machine or in a container, and files it writes are unreadable elsewhere. Passing `encoding="utf-8"` makes behaviour
        identical everywhere. Related choices: `errors="replace"` (or `"ignore"`) for messy input where losing a character beats crashing, `utf-8-sig`
        for files with a byte-order mark from Excel, and binary mode for anything that is not text. Python 3.15 makes UTF-8 the default (PEP 686), and linters
        such as Ruff and Pylint flag `open` calls without an encoding, but explicit is still the habit to show."""),
    explain("How would you process a 50 GB log or JSONL file in Python?", "hard", tag="Interview",
        why="""Never load it: stream it. Iterating over a text file object reads one line at a time through a buffer, so memory stays constant, and generators (6.3) can
        filter, parse and aggregate as lines pass, keeping only running totals or a bounded structure such as a heap of top-k or a reservoir sample. For
        binary data, read fixed-size chunks with `f.read(n)`. Write results incrementally too, appending one line per record or flushing batches, and write
        final outputs atomically. Make the job **resumable**: record the byte offset (`tell()` in binary mode) or the line count of the last committed batch,
        and `seek` there on restart. For speed, measure first: parsing usually dominates I/O, so faster parsers (`orjson`), splitting the file by byte
        ranges at line boundaries across processes (14.3), or columnar tools (pandas `chunksize`, Polars, DuckDB scanning the file directly) are the next
        steps. Compressed input can be streamed with `gzip.open` in text mode. Finally, handle bad records (invalid JSON, broken encodings) by counting and
        logging them instead of crashing at hour three."""),
)

recap(
    "Use `pathlib.Path`: `/` joins, `name`, `stem`, `suffix`, `parent`, `relative_to` and `with_suffix` replace string surgery; absolute parts reset a join.",
    "`glob`, `rglob` and `iterdir` are unordered and do not skip hidden folders; sort and filter explicitly. `mkdir(parents=True, exist_ok=True)` is repeat-safe.",
    "Always pass `encoding=\"utf-8\"`; `\"w\"` truncates at once, `\"a\"` appends, `\"x\"` refuses existing files; iterate lines to stream big files.",
    "Binary mode for bytes: read in chunks, hash with `hashlib`, and `seek`/`tell` by byte offset to read from the end.",
    "Atomic writes: temporary file in the same folder, flush and `fsync`, then `os.replace`; delete the temporary file on failure.",
)
