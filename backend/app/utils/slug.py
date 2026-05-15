import re


def slugify(value: str, *, max_length: int = 96) -> str:
    base = value.strip().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if not base:
        base = "organization"
    return base[:max_length]
