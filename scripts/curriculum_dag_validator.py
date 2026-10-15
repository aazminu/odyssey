from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class DropletNode:
    slug: str
    title: str
    estimated_minutes: int
    prerequisites: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CurriculumValidationReport:
    is_valid_dag: bool
    topological_order: List[str]
    cycle_nodes: List[str]
    missing_prereqs: Dict[str, List[str]]
    invalid_slugs: List[str]
    critical_path_minutes: int


class CurriculumDAGValidator:
    """Validates Odyssey learning-pathway droplet prerequisite DAGs, detects cycles, and computes critical-path time."""

    def validate(self, droplets: Sequence[DropletNode]) -> CurriculumValidationReport:
        if not droplets:
            return CurriculumValidationReport(
                is_valid_dag=True,
                topological_order=[],
                cycle_nodes=[],
                missing_prereqs={},
                invalid_slugs=[],
                critical_path_minutes=0,
            )

        by_slug: Dict[str, DropletNode] = {}
        invalid_slugs: List[str] = []
        for d in droplets:
            if not SLUG_RE.match(d.slug) or d.estimated_minutes < 0:
                invalid_slugs.append(d.slug)
            by_slug[d.slug] = d

        missing_prereqs: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {d.slug: 0 for d in droplets}
        dependents: Dict[str, List[str]] = {d.slug: [] for d in droplets}

        for d in droplets:
            for p in d.prerequisites:
                if p not in by_slug:
                    missing_prereqs.setdefault(d.slug, []).append(p)
                else:
                    in_degree[d.slug] += 1
                    dependents[p].append(d.slug)

        # Kahn's topological sort + longest-path dynamic programming
        ready = sorted([s for s, deg in in_degree.items() if deg == 0])
        topo_order: List[str] = []
        longest_to: Dict[str, int] = {
            s: max(0, by_slug[s].estimated_minutes) for s in by_slug
        }

        while ready:
            curr = ready.pop(0)
            topo_order.append(curr)
            for nxt in sorted(dependents[curr]):
                cand_time = longest_to[curr] + max(0, by_slug[nxt].estimated_minutes)
                if cand_time > longest_to[nxt]:
                    longest_to[nxt] = cand_time
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    ready.append(nxt)
                    ready.sort()

        cycle_nodes = sorted([s for s, deg in in_degree.items() if deg > 0])
        is_valid = (not cycle_nodes) and (not missing_prereqs) and (not invalid_slugs)
        crit_minutes = max(longest_to.values()) if is_valid and longest_to else 0

        return CurriculumValidationReport(
            is_valid_dag=is_valid,
            topological_order=topo_order if not cycle_nodes else [],
            cycle_nodes=cycle_nodes,
            missing_prereqs=missing_prereqs,
            invalid_slugs=invalid_slugs,
            critical_path_minutes=crit_minutes,
        )
