from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum_dag_validator import CurriculumDAGValidator, DropletNode


def run_benchmark(seed: int = 42) -> List[Dict[str, Any]]:
    """Run reproducible Odyssey curriculum droplet DAG validation and critical-path benchmarks."""
    _ = seed
    validator = CurriculumDAGValidator()

    # 1. Acyclic full-stack learning pathway
    valid_pathway = [
        DropletNode("git-fundamentals", "Git Fundamentals", 30, ()),
        DropletNode("typescript-basics", "TypeScript Basics", 45, ("git-fundamentals",)),
        DropletNode("nextjs-routing", "Next.js App Router", 60, ("typescript-basics",)),
        DropletNode("strapi-cms", "Strapi Headless CMS", 40, ("git-fundamentals",)),
        DropletNode("odyssey-fullstack", "Full-Stack Odyssey Capstone", 90, ("nextjs-routing", "strapi-cms")),
    ]
    rep_valid = validator.validate(valid_pathway)

    # 2. Cyclic dependency isolation (true cycle vs downstream acyclic node)
    cyclic_pathway = [
        DropletNode("mod-a", "Module A", 20, ("mod-b",)),
        DropletNode("mod-b", "Module B", 25, ("mod-a",)),
        DropletNode("mod-c", "Downstream Acyclic Module C", 30, ("mod-b",)),
    ]
    rep_cycle = validator.validate(cyclic_pathway)

    # 3. Missing prerequisite detection
    missing_pathway = [
        DropletNode("advanced-docker", "Advanced Docker", 35, ("linux-shell", "linux-shell")),
    ]
    rep_missing = validator.validate(missing_pathway)

    return [
        {
            "benchmark": "fullstack_pathway_critical_path",
            "droplet_count": len(valid_pathway),
            "is_valid_dag": rep_valid.is_valid_dag,
            "critical_path_minutes": rep_valid.critical_path_minutes,
            "cycle_nodes": len(rep_valid.cycle_nodes),
            "missing_prereqs": len(rep_valid.missing_prereqs),
            "status": "VALID_DAG",
        },
        {
            "benchmark": "cycle_isolation_with_downstream_node",
            "droplet_count": len(cyclic_pathway),
            "is_valid_dag": rep_cycle.is_valid_dag,
            "critical_path_minutes": rep_cycle.critical_path_minutes,
            "cycle_nodes": len(rep_cycle.cycle_nodes),
            "missing_prereqs": len(rep_cycle.missing_prereqs),
            "status": "CYCLE_ISOLATED" if rep_cycle.cycle_nodes == ["mod-a", "mod-b"] else "ERROR",
        },
        {
            "benchmark": "missing_prerequisite_guard",
            "droplet_count": len(missing_pathway),
            "is_valid_dag": rep_missing.is_valid_dag,
            "critical_path_minutes": rep_missing.critical_path_minutes,
            "cycle_nodes": len(rep_missing.cycle_nodes),
            "missing_prereqs": len(rep_missing.missing_prereqs),
            "status": "MISSING_DETECTED" if "advanced-docker" in rep_missing.missing_prereqs else "ERROR",
        },
    ]


def format_markdown_table(rows: Sequence[Dict[str, Any]]) -> str:
    headers = [
        "benchmark",
        "droplet_count",
        "is_valid_dag",
        "critical_path_minutes",
        "cycle_nodes",
        "missing_prereqs",
        "status",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run reproducible Odyssey curriculum DAG validation and critical-path benchmarks."
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for benchmark results.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible benchmark execution.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file path to write benchmark output.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    rows = run_benchmark(seed=args.seed)
    rendered = (
        json.dumps({"seed": args.seed, "benchmarks": rows}, indent=2)
        if args.format == "json"
        else format_markdown_table(rows)
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
