from lesson import *
from diagrams import *

lesson(
    id="m16-4", num="16.4", title="Graphs",
    intro="Dependencies between tasks, imports between modules, links between documents, calls between services, steps in an agent's "
          "plan: all graphs. Representing a graph with dicts, breadth-first and depth-first search, shortest paths with and without "
          "weights, connected components and union-find, cycle detection, and topological sort for running dependency DAGs in the "
          "right order, with the complexity of each.",
    desc="BFS, DFS and topological sort, for dependencies and agent DAGs.",
    keys="graph adjacency list directed undirected bfs breadth-first dfs depth-first shortest path parent pointers connected components union-find disjoint set path compression cycle detection topological sort kahn dag dijkstra heapq weighted",
)

term("Graph", "A set of nodes connected by edges. Edges can be directed (A depends on B) or undirected (A and B are linked), and can carry weights.")
term("DAG", "A directed acyclic graph: directed edges and no cycles, the shape of every valid dependency structure (build steps, pipelines, agent plans).")
term("Topological order", "An ordering of a DAG's nodes in which every node comes after all the nodes it depends on.")

section("represent", "Representing graphs",
    fig(table(["node", "neighbours (adjacency list)"], [
        ["a", "b, c"], ["b", "d"], ["c", "d"], ["d", ""],
    ], label="graph = {'a': ['b', 'c'], 'b': ['d'], 'c': ['d'], 'd': []}"),
        "An adjacency list stores each node's neighbours, so visiting them costs only as much as there are."),
    p("""In Python, a graph is usually a **dict from each node to its neighbours**, an adjacency list: `{"ingest": ["chunk"], "chunk": ["embed"], ...}`, with sets instead of lists
    when you need fast "is there an edge?" checks, and dicts of dicts (`{"a": {"b": 3}}`) for weighted edges. Undirected edges are stored in both directions. This uses O(V + E)
    memory for V nodes and E edges, and iterating a node's neighbours costs O(its degree). An adjacency matrix (a V-by-V table) costs O(V^2) memory and suits only small,
    dense graphs. Remember to include nodes that have no outgoing edges, which a dict built only from edge sources silently drops (problem 7). Libraries such as `networkx`
    offer all the algorithms below, and `graphlib.TopologicalSorter` in the standard library does topological sorting."""),
)

section("bfs", "Breadth-first search",
    fig(flowchart({
        "s": ("start", 0, 0, "queue = [start],|visited = {start}"),
        "ask": ("ask", 0, 1, "queue empty?"),
        "end": ("end", 1, 1, "done"),
        "pop": ("step", 0, 2, "node = popleft()"),
        "nb": ("accent", 0, 3, "each unvisited neighbour:|mark visited, append"),
    }, [("s", "ask"), ("ask", "end", "yes"), ("ask", "pop", "no"), ("pop", "nb"), ("nb", "ask", "", {"route": [(-0.45, 3), (-0.45, 1)]})],
        cell=(260, 80), label="breadth-first search"),
        "Marking nodes when they are queued means each node is queued once, and the first visit is along a path with the fewest edges."),
    p("""**BFS** explores a graph in layers: first the start node, then all its neighbours, then their unvisited neighbours, and so on, using a **queue** (`collections.deque`,
    16.1) and a `visited` set marked when a node is **enqueued**. Because it reaches nodes in order of distance, the first time BFS reaches a node it has found a path with the
    **fewest edges**, so it computes shortest paths in unweighted graphs; recording each node's **parent** lets you rebuild the path backwards (problem 5). It runs in
    O(V + E). Typical uses: degrees of separation, the fewest hops between two documents in a link graph, crawling a site to a maximum depth, and the shortest sequence of
    transformations (word ladders, state machines)."""),
    ex("""
    from collections import deque

    links = {
        "home": ["pricing", "docs"],
        "docs": ["api", "faq"],
        "pricing": ["faq"],
        "faq": ["refunds"],
        "api": [],
        "refunds": ["home"],
    }

    def bfs(graph, start):
        dist = {start: 0}
        order = []
        queue = deque([start])
        while queue:
            node = queue.popleft()
            order.append(node)
            for nxt in graph.get(node, []):
                if nxt not in dist:
                    dist[nxt] = dist[node] + 1
                    queue.append(nxt)
        return order, dist

    order, dist = bfs(links, "home")
    print(order)
    print(dist)
    """, "bfs.py"),
)

section("dfs", "Depth-first search",
    p("""**DFS** follows one path as deep as possible before backtracking, using recursion or an explicit **stack**. It does not find shortest paths, but it is the natural tool for
    exploring everything reachable, finding **connected components**, detecting **cycles**, and producing a topological order. In Python, prefer an explicit stack for large graphs:
    recursion depth is limited (about 1,000 frames by default, and deep recursion can crash a browser-based Python like this site's). For cycle detection in a **directed** graph,
    DFS marks nodes with three states: unvisited, **in progress** (on the current path) and done; meeting an in-progress node means a back edge, which is a cycle (problem
    14)."""),
)

section("topo", "Topological sort",
    fig(chain([("round 1:|load, fetch", "accent"), "round 2:|clean", "round 3:|embed, index", ("round 4:|evaluate", "good")], note="every task in one round can run in parallel"),
        "Kahn's algorithm in rounds: each round holds the tasks whose dependencies are all done."),
    p("""A **topological order** lists the nodes of a DAG so that each node comes after its dependencies; it exists exactly when there is no cycle. **Kahn's algorithm** counts each
    node's unmet dependencies (its in-degree), starts with the nodes that have none, and repeatedly removes a ready node, decrementing its dependants' counts and adding any
    that reach zero; if some nodes never become ready, they are on or behind a cycle. Processing the ready set in **rounds** also gives **levels**: every node in one round can
    run in parallel, which is how build systems, Airflow DAGs and multi-step agent plans schedule work (problem 6). It runs in O(V + E)."""),
    ex("""
    from graphlib import TopologicalSorter, CycleError

    plan = {"answer": {"retrieve", "rerank"}, "rerank": {"retrieve"}, "retrieve": {"embed_query"}, "embed_query": set(), "log": {"answer"}}
    ts = TopologicalSorter(plan)
    print(list(ts.static_order()))
    try:
        list(TopologicalSorter({"a": {"b"}, "b": {"a"}}).static_order())
    except CycleError as e:
        print("cycle:", e.args[1])
    """, "graphlib_demo.py"),
)

section("weighted", "Weighted shortest paths and union-find",
    p("""When edges have costs (latency between services, price of a model call, distance), BFS no longer finds the cheapest path. **Dijkstra's algorithm** does, for non-negative
    weights: keep a priority queue (`heapq`) of `(distance, node)`, repeatedly pop the closest unfinished node, and **relax** its edges, pushing any neighbour whose tentative
    distance improves; with a heap it runs in O((V + E) log V). Negative weights break it (Bellman-Ford handles them). For undirected connectivity questions that arrive as a
    stream of edges ("are these two records the same customer?"), **union-find** (disjoint sets) keeps a parent pointer per node; `find` follows parents to a root, with **path
    compression** flattening the chain, and `union` links two roots, so each operation is nearly O(1) amortised (problem 12)."""),
)

section("warmup", "Warm-up",
    predict("BFS layers and DFS order", "easy",
        code="""
        from collections import deque

        g = {"a": ["b", "c"], "b": ["d"], "c": ["d", "e"], "d": ["f"], "e": ["f"], "f": []}

        def bfs_order(start):
            seen, order, q = {start}, [], deque([start])
            while q:
                n = q.popleft()
                order.append(n)
                for m in g[n]:
                    if m not in seen:
                        seen.add(m)
                        q.append(m)
            return order

        def dfs_order(start):
            seen, order, stack = set(), [], [start]
            while stack:
                n = stack.pop()
                if n in seen:
                    continue
                seen.add(n)
                order.append(n)
                for m in reversed(g[n]):
                    stack.append(m)
            return order

        print(bfs_order("a"), dfs_order("a"))
        print(bfs_order("d"), dfs_order("e"))
        """,
        hints=["BFS visits by distance from the start; this DFS pushes neighbours in reverse so the first neighbour is explored first."],
        why="""BFS visits `a`, then both its neighbours, then the nodes two steps away, so `d` and `e` come before `f`. The iterative DFS goes as deep as possible along the first
        neighbour (`a`, `b`, `d`, `f`) before backtracking to `c` and `e`; pushing neighbours in reverse order makes it visit them in their listed order, like the recursive version.
        Starting elsewhere only reaches what is reachable from there, since edges are directed."""),
    write("Build an adjacency list", "easy", tag="Data work",
        prompt="""Write `build_graph(edges, directed=True)` returning a dict from every node (including nodes that only appear as targets) to a **sorted list** of its neighbours, and
        `degrees(graph)` returning `{node: (out_degree, in_degree)}`. For undirected graphs, store each edge in both directions and ignore duplicate edges.""",
        code="""
        def build_graph(edges, directed=True):
            pass

        def degrees(graph):
            pass
        """,
        tests="""
        edges = [("ingest", "chunk"), ("chunk", "embed"), ("chunk", "index"), ("embed", "index"), ("ingest", "chunk")]
        g = build_graph(edges)
        assert g == {"chunk": ["embed", "index"], "embed": ["index"], "index": [], "ingest": ["chunk"]}
        assert degrees(g) == {"chunk": (2, 1), "embed": (1, 1), "index": (0, 2), "ingest": (1, 0)}
        u = build_graph([("a", "b"), ("b", "c"), ("b", "a")], directed=False)
        assert u == {"a": ["b"], "b": ["a", "c"], "c": ["b"]}
        assert build_graph([]) == {}
        """,
        hints=["Collect neighbours in sets (`defaultdict(set)`), make sure targets get an entry too, then convert to sorted lists with sorted keys.",
               "In-degree: count how many lists each node appears in."],
        solution="""
        from collections import defaultdict


        def build_graph(edges, directed=True):
            adj = defaultdict(set)
            for a, b in edges:
                adj[a].add(b)
                adj[b]
                if not directed:
                    adj[b].add(a)
            return {node: sorted(adj[node]) for node in sorted(adj)}


        def degrees(graph):
            indeg = {node: 0 for node in graph}
            for node, nbrs in graph.items():
                for m in nbrs:
                    indeg[m] = indeg.get(m, 0) + 1
            return {node: (len(graph[node]), indeg[node]) for node in graph}
        """,
        why="""The adjacency list is the workhorse representation: O(V + E) memory and fast iteration over a node's neighbours. Sets remove duplicate edges (the repeated
        `ingest -> chunk`), and touching `adj[b]` ensures that sinks such as `index`, which have no outgoing edges, still appear as nodes, otherwise algorithms that iterate over
        the dict's keys would miss them. Sorting makes the output deterministic, which matters for tests and for reproducible scheduling. Out-degree is the length of a node's
        list; in-degree counts how often it appears as a target, which is exactly what Kahn's algorithm needs."""),
    fix("A search that uses a stack instead of a queue", "easy", tag="RAG",
        prompt="""`hops(graph, start)` should return the minimum number of links from `start` to every reachable page, but it pops from the **end** of its list, so it explores depth-first
        and records longer distances for some pages. Make it a real breadth-first search with a `deque`.""",
        code="""
        def hops(graph, start):
            dist = {start: 0}
            todo = [start]
            while todo:
                node = todo.pop()
                for nxt in graph.get(node, []):
                    if nxt not in dist:
                        dist[nxt] = dist[node] + 1
                        todo.append(nxt)
            return dist
        """,
        tests="""
        g = {"home": ["docs", "blog"], "blog": ["post1"], "post1": ["post2"], "post2": ["faq"], "docs": ["faq"], "faq": []}
        assert hops(g, "home") == {"home": 0, "blog": 1, "docs": 1, "post1": 2, "faq": 2, "post2": 3}
        assert hops(g, "faq") == {"faq": 0} and hops({}, "x") == {"x": 0}
        """,
        hints=["`from collections import deque`; `todo = deque([start])` and `node = todo.popleft()`."],
        solution="""
        from collections import deque

        def hops(graph, start):
            dist = {start: 0}
            todo = deque([start])
            while todo:
                node = todo.popleft()
                for nxt in graph.get(node, []):
                    if nxt not in dist:
                        dist[nxt] = dist[node] + 1
                        todo.append(nxt)
            return dist
        """,
        why="""Assigning a distance the first time a node is reached is only correct if nodes are reached in order of distance, which is what a FIFO queue guarantees: all nodes at distance
        1 are processed before any at distance 2. With `pop()` (a stack), the search took the last discovered page first, went down the blog chain, and reached `faq` through the long
        `blog -> post1 -> post2` path, recording 4 instead of 2; with the links listed in the other order it would have been right by luck, which is why such bugs survive tests. `deque.popleft()` is O(1), whereas `list.pop(0)` would make the search quadratic."""),
    predict("Kahn's algorithm in rounds", "easy",
        code="""
        def levels(deps):
            nodes = set(deps) | {d for ds in deps.values() for d in ds}
            remaining = {n: set(deps.get(n, ())) for n in nodes}
            rounds = []
            while remaining:
                ready = sorted(n for n, ds in remaining.items() if not ds)
                if not ready:
                    raise ValueError(f"cycle among {sorted(remaining)}")
                rounds.append(ready)
                for n in ready:
                    del remaining[n]
                for ds in remaining.values():
                    ds.difference_update(ready)
            return rounds

        pipeline = {"report": ["metrics", "plots"], "metrics": ["predict"], "plots": ["predict"], "predict": ["train", "features"], "train": ["features"]}
        print(levels(pipeline))
        try:
            levels({"a": ["b"], "b": ["c"], "c": ["a"], "d": []})
        except ValueError as e:
            print(e)
        """,
        hints=["A task is ready when all its dependencies are done; each round runs every ready task, sorted for a stable order."],
        why="""`features` depends on nothing, so it runs first; `train` needs only `features`; `predict` needs both; `metrics` and `plots` both need only `predict`, so they form one round
        and could run in parallel; `report` comes last. Dependencies that only appear as values (`features`) still count as nodes. When a round finds nothing ready while tasks
        remain, those tasks wait on each other: a cycle. Here `d` runs in the first round and `a`, `b`, `c` are reported."""),
)

section("medium", "Medium",
    write("Shortest path with parents", "medium", tag="RAG",
        prompt="""Write `shortest_path(graph, start, goal)` returning the list of nodes on a path with the fewest edges from `start` to `goal` (inclusive), or `None` if unreachable, using BFS
        with a parent dict. When several shortest paths exist, prefer the one found by exploring neighbours in their listed order.""",
        code="""
        from collections import deque

        def shortest_path(graph, start, goal):
            pass
        """,
        tests="""
        kg = {
            "refund": ["policy", "payment"],
            "policy": ["terms"],
            "payment": ["card", "terms"],
            "terms": ["legal"],
            "card": ["legal"],
            "legal": [],
        }
        assert shortest_path(kg, "refund", "legal") == ["refund", "policy", "terms", "legal"]
        assert shortest_path(kg, "payment", "legal") == ["payment", "card", "legal"]
        assert shortest_path(kg, "refund", "refund") == ["refund"] and shortest_path(kg, "legal", "refund") is None
        assert shortest_path(kg, "refund", "missing") is None
        """,
        hints=["`parent = {start: None}`; when you first see a neighbour, set its parent. When `goal` is dequeued (or first seen), walk parents back to `start` and reverse."],
        solution="""
        from collections import deque


        def shortest_path(graph, start, goal):
            parent = {start: None}
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node == goal:
                    path = []
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    return path[::-1]
                for nxt in graph.get(node, []):
                    if nxt not in parent:
                        parent[nxt] = node
                        queue.append(nxt)
            return None
        """,
        why="""BFS reaches every node first along a path with the fewest edges, so remembering **who discovered** each node is enough to reconstruct that path backwards from the goal,
        in O(V + E) time and O(V) memory. The `parent` dict doubles as the visited set. Exploring neighbours in listed order makes ties deterministic (`policy` before `payment`).
        In a knowledge graph, the shortest chain of relations between two entities is a compact explanation to show the user or to feed a model; graph-based retrieval uses
        such multi-hop paths to answer questions no single document answers."""),
    write("Run an agent plan as a DAG", "medium", tag="GenAI",
        prompt="""An agent's plan is a dict from step name to the list of steps it needs first. Write `execution_levels(plan)` returning a list of levels (each a sorted list of steps that can
        run in parallel once the previous levels are done), and `run_plan(plan, run_step)` that executes the steps level by level, calling `run_step(name, inputs)` where `inputs`
        maps each dependency to its result, and returns all results. A cycle raises `ValueError` listing the steps involved; a dependency that is not itself a step raises
        `KeyError`.""",
        code="""
        def execution_levels(plan):
            pass

        def run_plan(plan, run_step):
            pass
        """,
        tests="""
        plan = {
            "search_docs": [],
            "search_tickets": [],
            "rerank": ["search_docs", "search_tickets"],
            "draft": ["rerank"],
            "check_policy": ["rerank"],
            "answer": ["draft", "check_policy"],
        }
        assert execution_levels(plan) == [["search_docs", "search_tickets"], ["rerank"], ["check_policy", "draft"], ["answer"]]
        calls = []
        def run_step(name, inputs):
            calls.append((name, sorted(inputs)))
            return f"{name}({','.join(sorted(inputs))})"
        results = run_plan(plan, run_step)
        assert results["answer"] == "answer(check_policy,draft)" and [c[0] for c in calls][:2] == ["search_docs", "search_tickets"]
        assert calls[2] == ("rerank", ["search_docs", "search_tickets"])
        try:
            execution_levels({"a": ["b"], "b": ["a"], "c": []})
            assert False
        except ValueError as e:
            assert "a" in str(e) and "b" in str(e) and "c" not in str(e).split(":")[-1]
        try:
            execution_levels({"a": ["ghost"]})
            assert False
        except KeyError:
            pass
        """,
        hints=["Validate dependencies first. Then Kahn's algorithm in rounds: the ready steps are those whose dependencies are all done.",
               "`run_plan` walks the levels in order; a step's `inputs` are `{d: results[d] for d in plan[step]}`."],
        solution="""
        def execution_levels(plan):
            for step, deps in plan.items():
                for d in deps:
                    if d not in plan:
                        raise KeyError(f"step {step!r} depends on unknown step {d!r}")
            remaining = {step: set(deps) for step, deps in plan.items()}
            levels = []
            while remaining:
                ready = sorted(s for s, deps in remaining.items() if not deps)
                if not ready:
                    raise ValueError(f"cycle among steps: {', '.join(sorted(remaining))}")
                levels.append(ready)
                for s in ready:
                    del remaining[s]
                for deps in remaining.values():
                    deps.difference_update(ready)
            return levels


        def run_plan(plan, run_step):
            results = {}
            for level in execution_levels(plan):
                for step in level:
                    results[step] = run_step(step, {d: results[d] for d in plan[step]})
            return results
        """,
        why="""Agent frameworks and workflow engines represent multi-step work as a DAG, so independent steps (two searches) can run concurrently and every step sees its dependencies'
        outputs. Kahn's algorithm in rounds gives both a valid order and the parallel levels; in an async runner, each level becomes one `asyncio.gather` (14.4). Validating that
        every dependency names a real step catches typos in a model-generated plan before anything runs, and the cycle check turns a plan that could never finish into a clear
        error, which can be sent back to the model to repair (7.4). The cost is O(V + E) per level scan here (O(V + E) overall with in-degree counters)."""),
    fix("Topological sort that drops dependency-only nodes", "medium", tag="Data work",
        prompt="""`build_order(deps)` returns an order in which packages can be built (dependencies first). Packages that appear only as dependencies, and have no entry of their own, are
        missing from the result, and the function crashes with `KeyError` when it decrements their counts. Fix it so every node mentioned anywhere is included, using in-degree
        counts and a queue, with ready nodes processed in sorted order.""",
        code="""
        from collections import deque

        def build_order(deps):
            indegree = {pkg: len(d) for pkg, d in deps.items()}
            dependants = {pkg: [] for pkg in deps}
            for pkg, d in deps.items():
                for dep in d:
                    dependants[dep].append(pkg)
            queue = deque(sorted(p for p, n in indegree.items() if n == 0))
            order = []
            while queue:
                p = queue.popleft()
                order.append(p)
                for q in sorted(dependants[p]):
                    indegree[q] -= 1
                    if indegree[q] == 0:
                        queue.append(q)
            if len(order) != len(indegree):
                raise ValueError("cycle")
            return order
        """,
        tests="""
        deps = {"app": ["httpx", "pydantic"], "httpx": ["anyio", "certifi"], "pydantic": ["typing-extensions"]}
        assert build_order(deps) == ["anyio", "certifi", "typing-extensions", "httpx", "pydantic", "app"]
        assert build_order({}) == [] and build_order({"solo": []}) == ["solo"]
        try:
            build_order({"a": ["b"], "b": ["a"]})
            assert False
        except ValueError:
            pass
        """,
        hints=["Collect `nodes = set(deps) | {d for ds in deps.values() for d in ds}` and give every node an in-degree and a dependants list."],
        solution="""
        from collections import deque

        def build_order(deps):
            nodes = set(deps) | {d for ds in deps.values() for d in ds}
            indegree = {n: len(deps.get(n, ())) for n in nodes}
            dependants = {n: [] for n in nodes}
            for pkg, d in deps.items():
                for dep in d:
                    dependants[dep].append(pkg)
            queue = deque(sorted(p for p, n in indegree.items() if n == 0))
            order = []
            while queue:
                p = queue.popleft()
                order.append(p)
                for q in sorted(dependants[p]):
                    indegree[q] -= 1
                    if indegree[q] == 0:
                        queue.append(q)
            if len(order) != len(nodes):
                raise ValueError("cycle")
            return order
        """,
        why="""Leaf dependencies (`anyio`, `certifi`) are written only as values, never as keys, so a graph built from the keys alone has no entry for them: they never enter the queue,
        and the first `dependants[dep]` lookup fails. Taking the union of keys and values gives every node an in-degree (0 for leaves, which makes them the first ready nodes)
        and a dependants list. Comparing the output length with the number of nodes detects cycles: nodes on a cycle never reach in-degree 0. This node-collection step is the
        most common bug in hand-written dependency resolution, the same mistake as the sink nodes in problem 2."""),
    trace("Union-find with path compression", "medium",
        prompt="Fill in `state` after each marked line: the parent list and a `find` result.",
        code="""
        parent = list(range(6))

        def find(x):
            root = x
            while parent[root] != root:
                root = parent[root]
            while parent[x] != root:
                parent[x], x = root, parent[x]
            return root

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)

        union(1, 2)
        union(3, 4)
        state = (list(parent), find(2))  # row: "two pairs"
        union(2, 4)
        state = (list(parent), find(4))  # row: "merge the pairs"
        parent[5] = 4
        state = (list(parent), find(5), list(parent))  # row: "compression"
        """,
        trace_vars=["state"],
        hints=["`union` makes the smaller root the parent of the larger. `find` walks to the root, then points every node on the way directly at it."],
        why="""Each union links two roots, here always attaching the larger root under the smaller, so sets are identified by their smallest member. Merging `{1, 2}` with `{3, 4}` links
        root 3 under root 1, so `find(4)` walks 4, 3, 1 and, by path compression, points 4 directly at 1 (the list in that row was copied before `find(4)` ran, so it still
        shows 4 pointing at 3; the next row shows the compressed pointer). In the last row, 5 is attached under 4 by hand; finding it walks 5, 4, 1
        and compresses the path so 5 now points at 1 too: the tuple shows the list before and after the call, since `find` mutates it. Compression (with union by size or rank)
        keeps trees almost flat, giving nearly constant time per operation."""),
    write("Resolve duplicate customers", "medium", tag="Data work",
        prompt="""Records that share an email **or** a phone number belong to the same customer, transitively. Write `customer_groups(records)` where each record is `{"id", "email", "phone"}`
        (either may be `None`), returning a sorted list of groups, each a sorted list of record ids. Build a graph linking records through shared values and find connected
        components with an iterative DFS.""",
        code="""
        from collections import defaultdict

        def customer_groups(records):
            pass
        """,
        tests="""
        records = [
            {"id": "r1", "email": "ana@shop.io", "phone": None},
            {"id": "r2", "email": "ana@shop.io", "phone": "555-1"},
            {"id": "r3", "email": "a.lee@mail.com", "phone": "555-1"},
            {"id": "r4", "email": "bo@shop.io", "phone": "555-9"},
            {"id": "r5", "email": None, "phone": None},
            {"id": "r6", "email": "BO@shop.io", "phone": None},
        ]
        assert customer_groups(records) == [["r1", "r2", "r3"], ["r4", "r6"], ["r5"]]
        assert customer_groups([]) == []
        """,
        hints=["Normalise emails (lower-case). Map each `(\"email\", value)` and `(\"phone\", value)` to the record ids that have it; link those records to each other.",
               "Then a standard components loop: for each unvisited id, DFS with a stack, collecting the component."],
        solution="""
        from collections import defaultdict


        def customer_groups(records):
            by_value = defaultdict(list)
            for r in records:
                if r.get("email"):
                    by_value[("email", r["email"].strip().lower())].append(r["id"])
                if r.get("phone"):
                    by_value[("phone", r["phone"].strip())].append(r["id"])
            graph = {r["id"]: set() for r in records}
            for ids in by_value.values():
                for a in ids:
                    graph[a].update(i for i in ids if i != a)
            seen, groups = set(), []
            for start in graph:
                if start in seen:
                    continue
                stack, comp = [start], []
                seen.add(start)
                while stack:
                    node = stack.pop()
                    comp.append(node)
                    for nxt in graph[node]:
                        if nxt not in seen:
                            seen.add(nxt)
                            stack.append(nxt)
                groups.append(sorted(comp))
            return sorted(groups)
        """,
        why="""Entity resolution is a connected-components problem: `r1` and `r3` share nothing directly, but `r1` shares an email with `r2`, and `r2` a phone with `r3`, so all three are
        one customer. Indexing records by each normalised identifying value links them in O(total records) for typical data, and an iterative DFS (no recursion limit) groups
        them in O(V + E). Linking every pair within a large value group is quadratic in that group's size, so production code links each record only to the **first** record
        with the same value, or uses union-find (problem 12), which needs no explicit graph at all."""),
    predict("Dijkstra on service latencies", "medium",
        code="""
        import heapq

        def dijkstra(graph, start):
            dist = {start: 0}
            heap = [(0, start)]
            while heap:
                d, node = heapq.heappop(heap)
                if d > dist[node]:
                    continue
                for nxt, w in graph.get(node, {}).items():
                    nd = d + w
                    if nd < dist.get(nxt, float("inf")):
                        dist[nxt] = nd
                        heapq.heappush(heap, (nd, nxt))
            return dist

        latency = {
            "gateway": {"auth": 5, "cache": 2},
            "cache": {"retriever": 30, "auth": 1},
            "auth": {"retriever": 10},
            "retriever": {"llm": 200},
            "llm": {},
        }
        print(dijkstra(latency, "gateway"))
        fewest_hops = ["gateway", "auth", "retriever", "llm"]
        print(sum(latency[a][b] for a, b in zip(fewest_hops, fewest_hops[1:])))
        """,
        hints=["Pop the closest unfinished node, then lower its neighbours' tentative distances. A stale heap entry (larger than the recorded distance) is skipped."],
        why="""Dijkstra settles nodes in order of distance: `cache` at 2, then `auth` at 3 through the cache (cheaper than the direct 5), `retriever` at 13 through auth (instead of 32 directly
        from the cache), and `llm` at 213. The path with the fewest hops costs 215, so "fewest edges" and "cheapest" differ once edges have weights, which is why BFS is not enough.
        Skipping heap entries whose distance is larger than the best known one replaces the decrease-key operation that `heapq` does not provide."""),
)

section("hard", "Hard",
    write("Cheapest route with Dijkstra", "hard", tag="GenAI",
        prompt="""A router can answer a request through a chain of steps, each edge `(a, b, cost)` with a non-negative cost (dollars or milliseconds). Write `cheapest(edges, start, goal)`
        returning `(cost, path)` for the cheapest path, or `(None, [])` if unreachable, using Dijkstra with `heapq` and parent pointers; ties keep the first path found. Raise
        `ValueError` on a negative cost.""",
        code="""
        import heapq
        from collections import defaultdict

        def cheapest(edges, start, goal):
            pass
        """,
        tests="""
        edges = [
            ("request", "small_model", 0.2), ("request", "cache", 0.01), ("cache", "small_model", 0.15),
            ("small_model", "check", 0.05), ("request", "large_model", 2.0), ("large_model", "check", 0.05),
            ("check", "answer", 0.0), ("cache", "answer", 1.5),
        ]
        cost, path = cheapest(edges, "request", "answer")
        assert round(cost, 2) == 0.21 and path == ["request", "cache", "small_model", "check", "answer"]
        assert cheapest(edges, "answer", "request") == (None, []) and cheapest(edges, "request", "request") == (0, ["request"])
        try:
            cheapest([("a", "b", -1)], "a", "b")
            assert False
        except ValueError:
            pass
        """,
        hints=["`graph = defaultdict(list)`; heap of `(cost, node)`; `dist = {start: 0}`, `parent = {start: None}`.",
               "When popping `goal`, rebuild the path from `parent`. Skip stale entries with `if d > dist[node]: continue`."],
        solution="""
        import heapq
        from collections import defaultdict


        def cheapest(edges, start, goal):
            graph = defaultdict(list)
            for a, b, w in edges:
                if w < 0:
                    raise ValueError(f"negative cost on {a} -> {b}")
                graph[a].append((b, w))
            dist, parent = {start: 0}, {start: None}
            heap = [(0, start)]
            while heap:
                d, node = heapq.heappop(heap)
                if d > dist[node]:
                    continue
                if node == goal:
                    path = []
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    return d, path[::-1]
                for nxt, w in graph[node]:
                    nd = d + w
                    if nd < dist.get(nxt, float("inf")):
                        dist[nxt], parent[nxt] = nd, node
                        heapq.heappush(heap, (nd, nxt))
            return None, []
        """,
        why="""Dijkstra pops nodes in order of their final cost, so when the goal is popped its cost and parent chain are final, and the search can stop early. Relaxation keeps, for each node,
        the cheapest known way in and who provided it, so the cheapest route (cache, then the small model, then the check, 0.21) beats both the direct small-model route (0.25)
        and the large model. Non-negative costs are essential: a negative edge could make an already settled node cheaper later, which Dijkstra never revisits, so the function
        rejects them. With a heap the cost is O((V + E) log V); model routers, network routing and map apps all rely on this algorithm or its variants (A*)."""),
    write("Union-find for clustering duplicates", "hard", tag="RAG",
        prompt="""Write a class `DisjointSet` with `find(x)` (path compression; unseen items start as their own set), `union(a, b)` (union by size; returns `True` if two sets were merged),
        and `groups()` (a sorted list of sorted member lists). Then write `cluster(pairs, items)` that unions every near-duplicate pair (for example from 16.2's shingle search) and
        returns the groups including singletons from `items`.""",
        code="""
        class DisjointSet:
            pass

        def cluster(pairs, items):
            pass
        """,
        tests="""
        ds = DisjointSet()
        assert ds.union("a", "b") and ds.union("c", "d") and not ds.union("b", "a")
        assert ds.find("a") == ds.find("b") and ds.find("a") != ds.find("c")
        assert ds.union("b", "d") and ds.groups() == [["a", "b", "c", "d"]]
        pairs = [("faq-1", "faq-2"), ("faq-2", "faq-7"), ("faq-3", "faq-4"), ("faq-7", "faq-1")]
        assert cluster(pairs, ["faq-1", "faq-2", "faq-3", "faq-4", "faq-5", "faq-7"]) == [["faq-1", "faq-2", "faq-7"], ["faq-3", "faq-4"], ["faq-5"]]
        big = DisjointSet()
        for i in range(1, 20_000):
            big.union(i - 1, i)
        assert big.find(0) == big.find(19_999) and len(big.groups()) == 1
        """,
        hints=["Store `parent` and `size` dicts; `find` adds unseen items, walks to the root, then compresses the path iteratively.",
               "`union` attaches the smaller tree's root under the larger one's root and adds the sizes."],
        solution="""
        class DisjointSet:
            def __init__(self):
                self.parent, self.size = {}, {}

            def find(self, x):
                if x not in self.parent:
                    self.parent[x], self.size[x] = x, 1
                    return x
                root = x
                while self.parent[root] != root:
                    root = self.parent[root]
                while self.parent[x] != root:
                    self.parent[x], x = root, self.parent[x]
                return root

            def union(self, a, b):
                ra, rb = self.find(a), self.find(b)
                if ra == rb:
                    return False
                if self.size[ra] < self.size[rb]:
                    ra, rb = rb, ra
                self.parent[rb] = ra
                self.size[ra] += self.size[rb]
                return True

            def groups(self):
                members = {}
                for x in self.parent:
                    members.setdefault(self.find(x), []).append(x)
                return sorted(sorted(m) for m in members.values())


        def cluster(pairs, items):
            ds = DisjointSet()
            for x in items:
                ds.find(x)
            for a, b in pairs:
                ds.union(a, b)
            return ds.groups()
        """,
        why="""Union-find answers "are these in the same group?" while groups are being formed, without building or searching a graph: near-duplicate pairs from a similarity search are
        merged as they arrive, and transitivity (`faq-1` ~ `faq-2` ~ `faq-7`) comes for free. Union by size keeps trees shallow and path compression flattens them on every `find`,
        so a chain of 20,000 unions stays fast and, because both loops are iterative, never hits a recursion limit. Clusters then drive deduplication (keep one representative per
        cluster), and the same structure appears in Kruskal's minimum spanning tree and in entity resolution at scale."""),
    fix("Read the code: a site crawler", "hard", tag="RAG",
        prompt="""`crawl(start, get_links, max_depth)` should return every page reachable within `max_depth` links of `start`, each with its depth, visiting each page **once**. It has no
        visited set (pages are fetched again and again, and a link loop never ends without the depth limit), treats `/docs` and `/docs/` as different pages, allows one level too many,
        and uses `list.pop(0)`. Fix it: a `deque`, a visited set on normalised URLs (strip a trailing slash except for the root, drop `#fragments`), depth `<= max_depth`, and a dict
        page -> depth returned in BFS order. The grader counts calls to `get_links`.""",
        code="""
        def crawl(start, get_links, max_depth):
            depth_of = {}
            queue = [(start, 0)]
            while queue:
                page, depth = queue.pop(0)
                if depth > max_depth + 1:
                    continue
                depth_of[page] = depth
                for link in get_links(page):
                    queue.append((link, depth + 1))
            return depth_of
        """,
        tests="""
        site = {
            "/": ["/docs/", "/pricing", "/blog#top"],
            "/docs": ["/docs/api", "/", "/docs/faq/"],
            "/pricing": ["/docs", "/pricing/"],
            "/blog": ["/blog/post-1"],
            "/docs/api": ["/docs/api/v2"],
            "/docs/faq": ["/docs"],
            "/blog/post-1": [],
            "/docs/api/v2": [],
        }
        calls = []
        def get_links(page):
            calls.append(page)
            return site.get(page, [])
        out = crawl("/", get_links, max_depth=2)
        assert out == {"/": 0, "/docs": 1, "/pricing": 1, "/blog": 1, "/docs/api": 2, "/docs/faq": 2, "/blog/post-1": 2}
        assert list(out) == ["/", "/docs", "/pricing", "/blog", "/docs/api", "/docs/faq", "/blog/post-1"]
        assert sorted(calls) == sorted(["/", "/docs", "/pricing", "/blog"]) and crawl("/", get_links, 0) == {"/": 0}
        """,
        hints=["`normalise(u)`: drop `#...`, then strip a trailing `/` unless the URL is `/`.",
               "Mark pages visited when you enqueue them; only call `get_links` for pages whose depth is below `max_depth` (their links would be too deep otherwise)."],
        solution="""
        from collections import deque


        def _normalise(url):
            url = url.split("#", 1)[0]
            if len(url) > 1 and url.endswith("/"):
                url = url[:-1]
            return url


        def crawl(start, get_links, max_depth):
            start = _normalise(start)
            depth_of = {start: 0}
            queue = deque([start])
            while queue:
                page = queue.popleft()
                depth = depth_of[page]
                if depth == max_depth:
                    continue
                for link in get_links(page):
                    link = _normalise(link)
                    if link not in depth_of:
                        depth_of[link] = depth + 1
                        queue.append(link)
            return depth_of
        """,
        why="""A crawler is a BFS over a graph you discover as you go, and each bug breaks one BFS rule. Without a visited set, pages linking back to each other were fetched repeatedly
        (exponentially many paths), and without the depth limit it would never stop. URL normalisation decides what counts as the same node: `/docs` and `/docs/`, or a link
        with a `#fragment`, are one page, and treating them as different doubles the work and the duplicates in a RAG index. Recording depth when a page is first enqueued gives
        its true minimum depth, the off-by-one `max_depth + 1` let a third level in, and pages at the maximum depth are not expanded at all, which saves the fetches the grader
        counted. `deque.popleft` keeps it linear."""),
    predict("Detecting cycles with three colours", "hard",
        code="""
        def find_cycle(graph):
            WHITE, GREY, BLACK = 0, 1, 2
            colour = {n: WHITE for n in graph}
            for start in sorted(graph):
                if colour[start] != WHITE:
                    continue
                stack = [(start, iter(sorted(graph[start])))]
                path = [start]
                colour[start] = GREY
                while stack:
                    node, it = stack[-1]
                    nxt = next(it, None)
                    if nxt is None:
                        colour[node] = BLACK
                        stack.pop()
                        path.pop()
                    elif colour.get(nxt, WHITE) == GREY:
                        return path[path.index(nxt):] + [nxt]
                    elif colour.get(nxt, WHITE) == WHITE:
                        colour[nxt] = GREY
                        path.append(nxt)
                        stack.append((nxt, iter(sorted(graph.get(nxt, [])))))
            return None

        imports = {"api": ["models", "utils"], "models": ["db"], "db": ["utils"], "utils": []}
        print(find_cycle(imports))
        imports["utils"] = ["models"]
        print(find_cycle(imports))
        print(find_cycle({"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"]}), find_cycle({"x": ["x"]}))
        """,
        hints=["Grey means \"on the current path\". Reaching a grey node closes a cycle; reaching a black node is fine (it was fully explored already)."],
        why="""The first graph is a DAG: `utils` is reached twice, but the second time it is already black, which is not a cycle. After `utils` imports `models`, the search goes `api`,
        `models`, `db`, `utils`, and the edge back to the grey `models` closes the cycle `models -> db -> utils -> models`. Starting from the alphabetically first node finds
        `a -> b -> c -> a`, and a self-loop is the shortest cycle. The explicit stack of iterators replaces recursion, so deep dependency chains cannot overflow the call stack;
        this is the check that import-cycle linters (15.1) and workflow engines run before accepting a graph."""),
)

section("interview", "Interview questions",
    explain("BFS or DFS: how do you choose?", "medium", tag="Interview",
        why="""Both visit everything reachable in O(V + E). Use **BFS** (a queue) when you need **shortest paths in unweighted graphs** or anything layered by distance: fewest hops, nearest
        matching node, level-by-level processing, crawling to a depth; it may hold a whole frontier in memory, which can be wide. Use **DFS** (a stack or recursion) when you need
        to explore paths fully: connected components, cycle detection with colours, topological order by finishing times, backtracking searches, or when the graph is deep and
        narrow; it uses memory proportional to the depth, but recursion in Python is limited, so use an explicit stack for big graphs. For weighted shortest paths neither is
        enough: Dijkstra (non-negative weights) or Bellman-Ford. Mention visited sets (marked on enqueue for BFS) to avoid revisiting nodes and infinite loops on cycles."""),
    explain("What is a topological sort, and where have you used one?", "medium", tag="Interview",
        why="""A topological sort orders the nodes of a directed acyclic graph so that every edge points forward: each node appears after everything it depends on. It exists if and only
        if the graph has no cycle, so computing one doubles as cycle detection. Kahn's algorithm repeatedly takes nodes with no remaining dependencies (in-degree zero), and
        processing them in rounds yields groups that can run in parallel; a DFS that outputs nodes in reverse finishing order is the alternative. Both are O(V + E). Uses:
        build systems and package installers (dependencies before dependants), data pipelines and Airflow DAGs, running an agent's multi-step plan where steps consume earlier
        results, spreadsheet recalculation, migration ordering, and course prerequisites. In Python, `graphlib.TopologicalSorter` provides it, including an incremental API
        (`get_ready`, `done`) that fits concurrent execution."""),
    explain("How would you find the shortest route between two services when calls have different latencies, and when does your method fail?", "hard", tag="Interview",
        why="""Model the services as a directed graph with edge weights equal to latency (or cost) and run **Dijkstra's algorithm** from the source: a min-heap keyed by tentative distance,
        repeatedly settling the closest node and relaxing its outgoing edges, with parent pointers to rebuild the route, O((V + E) log V); stop early when the destination is
        settled. It fails with **negative weights** (use Bellman-Ford, O(V E), which also detects negative cycles), and it optimises a single additive metric, so trade-offs
        (latency versus cost, reliability) need a combined weight or a multi-objective method. Weights that change over time or with load call for recomputation, and for huge
        graphs with geometry (maps) **A*** with an admissible heuristic explores far fewer nodes. If all weights are equal, plain BFS suffices; with only 0 and 1 weights, a deque-
        based 0-1 BFS is linear."""),
)

recap(
    "Represent graphs as dicts of neighbour lists or sets (O(V + E) memory), and include nodes that only appear as edge targets.",
    "BFS with a deque and visited-on-enqueue finds fewest-edge paths; record parents to rebuild them.",
    "DFS (prefer an explicit stack) finds components and cycles; three colours detect cycles in directed graphs.",
    "Topological sort (Kahn's algorithm, in rounds for parallel levels) orders dependency DAGs and reports cycles.",
    "Dijkstra with `heapq` finds cheapest paths for non-negative weights; union-find groups connected items with near O(1) operations.",
)
