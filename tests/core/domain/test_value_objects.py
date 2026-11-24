import pytest

from boxoffice.modules.core.domain.errors import DomainValidationError
from boxoffice.modules.core.domain.value_objects import Email, Money, RegionCode


def test_email_normalized():
    assert Email("  A@B.com ").value == "a@b.com"


@pytest.mark.parametrize("bad", ["", "x", "a@b", "a b@c.com"])
def test_email_invalid(bad):
    with pytest.raises(DomainValidationError):
        Email(bad)


def test_money_add_and_zero():
    assert Money(2) + Money(3) == Money(5)
    assert Money.zero() == Money(0)


@pytest.mark.parametrize("bad", [-1, 1.5, "10", True])
def test_money_invalid(bad):
    with pytest.raises(DomainValidationError):
        Money(bad)


def test_region_normalized_and_validated():
    assert RegionCode("ua").value == "UA"
    for bad in ["", "USA", "1A", None]:
        with pytest.raises(DomainValidationError):
            RegionCode(bad)
