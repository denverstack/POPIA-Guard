"""Shared Rule definition used by both the POPIA and secret pattern
registries.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

Validator = Callable[[str, str], bool]


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    severity: str
    pattern: re.Pattern[str]
    validator: Validator | None = None
