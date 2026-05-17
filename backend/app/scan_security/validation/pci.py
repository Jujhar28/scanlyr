"""Payment card validation (Luhn)."""

from __future__ import annotations

import re


def normalize_card_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def luhn_check(card_number: str) -> bool:
    digits = normalize_card_digits(card_number)
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0
