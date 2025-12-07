from dataclasses import dataclass

from archguard import enums


@dataclass
class Rule:
    # TODO
    rule_type: enums.RuleType