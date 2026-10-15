import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum_dag_validator import CurriculumDAGValidator, DropletNode


def test_valid_curriculum_dag_and_critical_path() -> None:
    validator = CurriculumDAGValidator()
    droplets = [
        DropletNode("git-fundamentals", "Git Fundamentals", 30, ()),
        DropletNode("typescript-basics", "TypeScript Basics", 45, ("git-fundamentals",)),
        DropletNode("nextjs-routing", "Next.js App Router", 60, ("typescript-basics",)),
        DropletNode("strapi-cms", "Strapi Headless CMS", 40, ("git-fundamentals",)),
        DropletNode("odyssey-fullstack", "Full-Stack Odyssey Capstone", 90, ("nextjs-routing", "strapi-cms")),
    ]
    report = validator.validate(droplets)
    assert report.is_valid_dag is True
    assert report.topological_order[0] == "git-fundamentals"
    assert report.topological_order[-1] == "odyssey-fullstack"
    # Critical path: 30 (git) + 45 (ts) + 60 (nextjs) + 90 (capstone) = 225 min
    assert report.critical_path_minutes == 225


def test_cycle_and_missing_prerequisite_detection() -> None:
    validator = CurriculumDAGValidator()
    cyclic = [
        DropletNode("mod-a", "Module A", 20, ("mod-b",)),
        DropletNode("mod-b", "Module B", 25, ("mod-a",)),
        DropletNode("mod-c", "Downstream Acyclic Module C", 30, ("mod-b",)),
    ]
    rep_cycle = validator.validate(cyclic)
    assert rep_cycle.is_valid_dag is False
    # Downstream acyclic node mod-c must not be falsely reported as a cycle member
    assert rep_cycle.cycle_nodes == ["mod-a", "mod-b"]

    missing = [
        DropletNode("advanced-docker", "Advanced Docker", 35, ("linux-shell", "linux-shell")),
    ]
    rep_missing = validator.validate(missing)
    assert rep_missing.is_valid_dag is False
    assert rep_missing.missing_prereqs == {"advanced-docker": ["linux-shell"]}


def test_cli_benchmark_markdown_json_and_reproducibility(
    capsys: object, tmp_path: Path
) -> None:
    import json
    import subprocess
    import pytest
    import benchmark as odyssey_bench

    rows_1 = odyssey_bench.run_benchmark(seed=42)
    rows_2 = odyssey_bench.run_benchmark(seed=42)
    assert rows_1 == rows_2
    assert len(rows_1) == 3

    md = odyssey_bench.format_markdown_table(rows_1)
    assert "| benchmark | droplet_count | is_valid_dag | critical_path_minutes |" in md
    assert "fullstack_pathway_critical_path" in md
    assert "cycle_isolation_with_downstream_node" in md

    out_path = tmp_path / "odyssey_bench.json"
    rc = odyssey_bench.main(["--format", "json", "--seed", "42", "--output", str(out_path)])
    assert rc == 0
    captured = capsys.readouterr().out  # type: ignore[attr-defined]
    data = json.loads(captured)
    assert data["seed"] == 42
    assert data["benchmarks"] == rows_1
    assert json.loads(out_path.read_text(encoding="utf-8")) == data

    script_path = Path(__file__).resolve().parent / "benchmark.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--format", "markdown"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "missing_prerequisite_guard" in proc.stdout

    with pytest.raises(SystemExit):
        odyssey_bench.main(["--format", "invalid_fmt"])


