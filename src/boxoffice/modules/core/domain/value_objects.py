import re
from dataclasses import dataclass

from boxoffice.modules.core.domain.errors import DomainValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_REGION_RE = re.compile(r"^[A-Z]{2}$")


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise DomainValidationError("Invalid email address")
        normalized = self.value.strip().lower()
        if len(normalized) > 254 or not _EMAIL_RE.match(normalized):
            raise DomainValidationError("Invalid email address")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:

    amount_usd: int

    def __post_init__(self):
        if isinstance(self.amount_usd, bool) or not isinstance(self.amount_usd, int):
            raise DomainValidationError("Money amount must be an integer")
        if self.amount_usd < 0:
            raise DomainValidationError("Money amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount_usd + other.amount_usd)

    @classmethod
    def zero(cls) -> "Money":
        return cls(0)


@dataclass(frozen=True)
class RegionCode:

    value: str

    def __post_init__(self):
        normalized = self.value.strip().upper() if isinstance(self.value, str) else ""
        if not _REGION_RE.match(normalized):
            raise DomainValidationError("Region must be a 2-letter code, e.g. US")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
