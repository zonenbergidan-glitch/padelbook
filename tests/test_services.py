from datetime import datetime

import pytest

from padelbook.models import Customer, OutdoorCourt, IndoorCourt, Booking
from padelbook.services import (
    requires_weather_review,
    NormalWeatherPolicy,
    StrictWeatherPolicy,
)


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

@pytest.fixture
def outdoor_booking():
    customer = Customer(1, "Demo Player")
    court = OutdoorCourt(1, "Outdoor A", 160)

    return Booking(
        1,
        customer,
        court,
        datetime(2026, 11, 20, 18),
        90,
    )


@pytest.mark.parametrize(
    "rain_mm, wind_kmh, expected",
    [
        (0, 10, False),
        (0.9, 34.9, False),
        (1, 10, True),
        (0, 35, True),
        (0, 50, True),
        (2, 40, True),
    ],
)
def test_outdoor_weather_thresholds(
    outdoor_booking, rain_mm, wind_kmh, expected
):
    result = requires_weather_review(
        outdoor_booking,
        rain_mm=rain_mm,
        wind_kmh=wind_kmh,
    )

    assert result is expected


def test_indoor_court_ignores_rain_and_wind():
    customer = Customer(1, "Demo Player")
    court = IndoorCourt(1, "Indoor A", 160)
    booking = Booking(
        1,
        customer,
        court,
        datetime(2026, 11, 20, 18),
        90,
    )

    assert requires_weather_review(
        booking, rain_mm=10, wind_kmh=60
    ) is False

@pytest.mark.parametrize(
    "rain_mm, wind_kmh, normal_expected, strict_expected",
    [
        (0, 10, False, False),
        (0.5, 10, False, True),
        (0, 25, False, True),
        (0.4, 24.9, False, False),
        (1, 35, True, True),
    ],
)
def test_weather_policy_selection(
    outdoor_booking,
    rain_mm,
    wind_kmh,
    normal_expected,
    strict_expected,
):
    normal_result = requires_weather_review(
        outdoor_booking,
        rain_mm,
        wind_kmh,
        policy=NormalWeatherPolicy(),
    )
    strict_result = requires_weather_review(
        outdoor_booking,
        rain_mm,
        wind_kmh,
        policy=StrictWeatherPolicy(),
    )

    assert normal_result is normal_expected
    assert strict_result is strict_expected