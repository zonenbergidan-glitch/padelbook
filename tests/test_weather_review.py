from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from padelbook.models import Customer, OutdoorCourt, Booking
from padelbook.services import assess_booking_weather
from datetime import timedelta

from padelbook.models import IndoorCourt, PadelClub
from padelbook.services import find_indoor_alternatives
from padelbook.models import MaintenanceIssue
from padelbook.services import review_booking_weather


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

def test_missing_forecast_returns_unknown(booking):
    result = assess_booking_weather(booking, None)

    assert result == "unknown"
    assert booking.status == "confirmed"
    assert booking.requires_review is False


def test_indoor_booking_does_not_need_forecast():
    from padelbook.models import IndoorCourt

    booking = Booking(
        2,
        Customer(1, "Demo Player"),
        IndoorCourt(2, "Indoor A", 160),
        datetime(2026, 11, 20, 18, 30),
        90,
    )

    result = assess_booking_weather(booking, None)

    assert result == "not_required"
    assert booking.status == "confirmed"
    assert booking.requires_review is False

@pytest.fixture
def club_with_indoor(booking):
    club = PadelClub("Demo Club")
    indoor = IndoorCourt(2, "Indoor A", 160)

    club.add_court(booking.court)
    club.add_court(indoor)
    club.add_booking(booking)

    return club, indoor


def test_suggests_free_indoor_court(booking, club_with_indoor):
    club, indoor = club_with_indoor

    alternatives = find_indoor_alternatives(club, booking)

    assert alternatives == [indoor]
    assert booking.court.weather_exposed is True
    assert booking.status == "confirmed"


@pytest.mark.parametrize(
    "offset_minutes, expected_available",
    [
        (-60, True),
        (0, False),
        (90, True),
    ],
)
def test_indoor_alternative_availability(
    booking,
    club_with_indoor,
    offset_minutes,
    expected_available,
):
    club, indoor = club_with_indoor

    existing = Booking(
        2,
        booking.customer,
        indoor,
        booking.start_time + timedelta(minutes=offset_minutes),
        60,
    )
    club.add_booking(existing)

    alternatives = find_indoor_alternatives(club, booking)

    if expected_available:
        assert alternatives == [indoor]
    else:
        assert alternatives == []
def test_blocked_indoor_court_is_not_suggested(
    booking, club_with_indoor
):
    club, indoor = club_with_indoor

    issue = MaintenanceIssue(
        1,
        indoor,
        "Broken glass",
        1,
        blocks_court=True,
    )
    club.add_issue(issue)

    assert find_indoor_alternatives(club, booking) == []

    club.close_issue(issue.issue_id)

    assert find_indoor_alternatives(club, booking) == [indoor]
@pytest.mark.parametrize(
    "rain_mm, expected_assessment, expected_review",
    [
        (0, "not_required", False),
        (2, "review_required", True),
        (None, "unknown", True),
    ],
)
def test_complete_weather_review(
    booking,
    club_with_indoor,
    rain_mm,
    expected_assessment,
    expected_review,
):
    club, indoor = club_with_indoor
    forecast = None

    if rain_mm is not None:
        timezone = ZoneInfo("Asia/Jerusalem")
        times = [
            int(
                booking.start_time.replace(
                    hour=hour,
                    minute=0,
                    tzinfo=timezone,
                ).timestamp()
            )
            for hour in (18, 19, 20)
        ]

        forecast = {
            "hourly": {
                "time": times,
                "rain": [0, 0, rain_mm],
                "wind_speed_10m": [10, 10, 10],
            }
        }

    result = review_booking_weather(club, booking, forecast)

    assert result["assessment"] == expected_assessment
    assert result["requires_review"] is expected_review
    assert booking.requires_review is expected_review

    expected_alternatives = (
        [indoor.court_id] if expected_review else []
    )
    assert result["alternative_court_ids"] == expected_alternatives

    assert booking.status == "confirmed"
    assert booking.court.weather_exposed is True
    assert len(club.get_bookings()) == 1