from collections import defaultdict, deque

EDGE_KEYS = [
    ("on_pass", "✓"), ("on_fail", "✗"),
    ("on_true", "T"), ("on_false", "F"),
    ("on_approve", "✓"), ("on_decline", "✗"),
    ("on_timeout", "⏱"),
    ("on_complete", "→"), ("on_error", "✗"),
    ("on_skip", "⊘"),
    ("next", "→"),
]

# Canonical set of all edge key names (for validation / traversal)
EDGE_KEY_NAMES = [key for key, _ in EDGE_KEYS]

TYPE_ICONS = {
    "shell": "⚙",
    "agent": "🤖",
    "human": "👤",
    "condition": "◆",
    "subflow": "📦",
    "log": "📝",
    "parallel": "⫰",
}


def build_edges(config: dict) -> list[tuple[str, str, str]]:
    """Extract all edges as (from, to, label) tuples."""
    edges = []
    for name, step in config.get("steps", {}).items():
        for key, label in EDGE_KEYS:
            target = step.get(key)
            if target:
                edges.append((name, target, label))
        # Parallel branches
        for branch in step.get("branches", []):
            branch_next = branch.get("next") or branch.get("on_pass")
            if branch_next:
                edges.append((name, branch_next, f"branch:{branch.get('name', '?')}"))
    return edges


def render_graph(config: dict) -> str:
    """Render pipeline as ASCII DAG."""
    entry = config.get("entry", "?")
    steps = config.get("steps", {})
    edges = build_edges(config)

    # Build adjacency: node → [(target, label)]
    adj = defaultdict(list)
    for src, dst, label in edges:
        adj[src].append((dst, label))

    # Topological sort (BFS) — handles cycles via visited set
    visited = []
    seen = set()
    queue = deque([entry])
    while queue:
        node = queue.popleft()
        if node in seen or node not in steps:
            continue
        seen.add(node)
        visited.append(node)
        for target, _ in adj.get(node, []):
            if target not in seen:
                queue.append(target)
    # Add any unvisited nodes
    for node in steps:
        if node not in seen:
            visited.append(node)

    # Render
    lines = []
    lines.append(f"Pipeline: {entry}")
    lines.append("─" * 50)

    for node in visited:
        step = steps[node]
        node_type = step.get("type", "?")
        icon = TYPE_ICONS.get(node_type, "?")
        marker = " ▶" if node == entry else "  "
        max_v = step.get("max_visits")
        visit_tag = f" [max:{max_v}]" if max_v else ""

        lines.append(f"{marker} {icon} {node} ({node_type}){visit_tag}")

        targets = adj.get(node, [])
        for i, (target, label) in enumerate(targets):
            is_last = i == len(targets) - 1
            prefix = "  └─" if is_last else "  ├─"
            lines.append(f"{prefix} [{label}] → {target}")

    lines.append("─" * 50)
    lines.append(f"Nodes: {len(steps)} | Edges: {len(edges)}")

    return "\n".join(lines)
