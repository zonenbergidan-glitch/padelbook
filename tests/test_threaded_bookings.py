from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier

import pytest

from padelbook.models import (
    Booking,
    Customer,
    OutdoorCourt,
    PadelClub,
)


@pytest.mark.parametrize(
    "different_court, offset_minutes, expected_accepted",
    [
        (False, 0, 1),
        (False, 60, 2),
        (True, 0, 2),
    ],
)
def test_concurrent_booking_requests(
    different_court,
    offset_minutes,
    expected_accepted,
):
    club = PadelClub("Thread Demo")
    first_court = OutdoorCourt(1, "Outdoor A", 160)
    second_court = OutdoorCourt(2, "Outdoor B", 160)

    club.add_court(first_court)
    club.add_court(second_court)

    start = datetime(2026, 11, 20, 18)
    target_court = (
        second_court if different_court else first_court
    )

    bookings = [
        Booking(
            1,
            Customer(1, "First Player"),
            first_court,
            start,
            60,
        ),
        Booking(
            2,
            Customer(2, "Second Player"),
            target_court,
            start + timedelta(minutes=offset_minutes),
            60,
        ),
    ]

    barrier = Barrier(2)

    def submit_booking(booking):
        barrier.wait(timeout=5)

        try:
            club.add_booking(booking)
        except ValueError:
            return False

        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit_booking, bookings))

    assert results.count(True) == expected_accepted
    assert results.count(False) == 2 - expected_accepted
    assert len(club.get_bookings()) == expected_accepted