import hashlib
import json
from dataclasses import dataclass, field
from typing import Sequence

from archguard.reporting.types import Violation

# Keys

def _stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha1(text: str) -> str:
    # short stable key, good enough for dedupe/baseline matching
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ViolationKeyStrategy:
    """
    Builds stable keys for violations so baselines can match the same violation
    across runs/commits.

    Default strategy:
    - Include rule_id (so rule refactors don't collide)
    - Include "subject identity":
      - dependency: (dep_type, src_id, dst_id)
      - node: (node_id)
    """

    def key_for(self, v: Violation) -> str:
        details = v.details or {}
        target = details.get("target")

        if target == "dependency":
            payload = {
                "rule": v.rule_id,
                "target": "dependency",
                "dep_type": details.get("dep_type"),
                "src_id": details.get("src_id"),
                "dst_id": details.get("dst_id"),
            }
            return _sha1(_stable_json(payload))

        if target == "node":
            payload = {
                "rule": v.rule_id,
                "target": "node",
                "node_id": details.get("node_id"),
            }
            return _sha1(_stable_json(payload))

        # Fallback (shouldn't happen)
        payload = {"rule": v.rule_id, "target": target, "message": v.message}
        return _sha1(_stable_json(payload))

# Baseline compare

@dataclass(frozen=True, slots=True)
class BaselineResult:
    """
    Compare output between current and baseline.

    - new: present now, not in baseline
    - existing: present now and in baseline
    - fixed: present in baseline, not present now
    """
    new: tuple[Violation, ...]
    existing: tuple[Violation, ...]
    fixed: tuple[Violation, ...]


@dataclass(frozen=True, slots=True)
class BaselineComparer:
    """
    Compare current violations against baseline violations.
    """
    key_strategy: ViolationKeyStrategy = field(default_factory=ViolationKeyStrategy)

    def compare(self, current: Sequence[Violation], baseline: Sequence[Violation]) -> BaselineResult:
        cur_by_key: dict[str, Violation] = {self.key_strategy.key_for(v): v for v in current}
        base_by_key: dict[str, Violation] = {self.key_strategy.key_for(v): v for v in baseline}

        new_keys = cur_by_key.keys() - base_by_key.keys()
        existing_keys = cur_by_key.keys() & base_by_key.keys()
        fixed_keys = base_by_key.keys() - cur_by_key.keys()

        new = tuple(cur_by_key[k] for k in sorted(new_keys))
        existing = tuple(cur_by_key[k] for k in sorted(existing_keys))
        fixed = tuple(base_by_key[k] for k in sorted(fixed_keys))

        return BaselineResult(new=new, existing=existing, fixed=fixed)
