import pytest

from padelbook.models import OutdoorCourt, IndoorCourt
from padelbook.factories import create_court


@pytest.mark.parametrize(
    "court_type, expected_class",
    [
        ("outdoor", OutdoorCourt),
        ("indoor", IndoorCourt),
    ],
)
def test_create_court(court_type, expected_class):
    court = create_court(
        court_type,
        court_id=1,
        name="Demo Court",
        hourly_rate=160,
    )

    assert isinstance(court, expected_class)
    assert court.court_id == 1
    assert court.name == "Demo Court"
    assert court.hourly_rate == 160


def test_create_court_rejects_unknown_type():
    with pytest.raises(ValueError):
        create_court(
            "unknown",
            court_id=1,
            name="Demo Court",
            hourly_rate=160,
        )