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
    ]
    rep_cycle = validator.validate(cyclic)
    assert rep_cycle.is_valid_dag is False
    assert rep_cycle.cycle_nodes == ["mod-a", "mod-b"]

    missing = [
        DropletNode("advanced-docker", "Advanced Docker", 35, ("linux-shell",)),
    ]
    rep_missing = validator.validate(missing)
    assert rep_missing.is_valid_dag is False
    assert rep_missing.missing_prereqs == {"advanced-docker": ["linux-shell"]}
