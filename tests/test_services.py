from datetime import datetime

import pytest

from padelbook.models import Customer, OutdoorCourt, IndoorCourt, Booking
from padelbook.services import requires_weather_review


@pytest.mark.parametrize(
    "court_class, expected",
    [
        (OutdoorCourt, True),
        (IndoorCourt, False),
    ],
)
def test_weather_review_for_rain(court_class, expected):
    customer = Customer(1, "Demo Player")
    court = court_class(1, "Demo Court", 160)
    booking = Booking(
        1,
        customer,
        court,
        datetime(2026, 11, 20, 18),
        90,
    )

    result = requires_weather_review(
        booking,
        rain_mm=2,
        wind_kmh=10,
    )

    assert result is expected