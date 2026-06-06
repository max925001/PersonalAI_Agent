from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Email:
    """Email value object validating syntax."""
    value: str

    def __post_init__(self):
        cleaned = self.value.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", cleaned):
            raise ValueError("Invalid email format")
        object.__setattr__(self, "value", cleaned)


@dataclass(frozen=True)
class PasswordHash:
    """Password hash representation."""
    value: str