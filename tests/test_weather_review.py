from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from padelbook.models import Customer, OutdoorCourt, Booking
from padelbook.services import assess_booking_weather


@pytest.fixture
def booking():
    return Booking(
        1,
        Customer(1, "Demo Player"),
        OutdoorCourt(1, "Outdoor A", 160),
        datetime(2026, 11, 20, 18, 30),
        90,
    )


@pytest.mark.parametrize(
    "hours, rain, wind, expected",
    [
        (
            [18, 19, 20],
            [0, 0, 0],
            [10, 10, 10],
            "not_required",
        ),
        (
            [18, 19, 20],
            [0, 0, 2],
            [10, 10, 10],
            "review_required",
        ),
        (
            [18, 19, 20],
            [0, 0, 0],
            [10, 10, 40],
            "review_required",
        ),
        (
            [18, 19],
            [0, 0],
            [10, 10],
            "unknown",
        ),
        (
            [18, 20],
            [0, 0],
            [10, 10],
            "unknown",
        ),
    ],
)
def test_assess_booking_weather(
    booking, hours, rain, wind, expected
):
    timezone = ZoneInfo("Asia/Jerusalem")
    timestamps = [
        int(
            datetime(
                2026, 11, 20, hour, tzinfo=timezone
            ).timestamp()
        )
        for hour in hours
    ]

    forecast = {
        "hourly": {
            "time": timestamps,
            "rain": rain,
            "wind_speed_10m": wind,
        }
    }

    result = assess_booking_weather(booking, forecast)

    assert result == expected
    assert booking.status == "confirmed"
    assert booking.requires_review is False