from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier

from padelbook.models import (
    Booking,
    Customer,
    OutdoorCourt,
    PadelClub,
)


def main():
    club = PadelClub("Thread Demo")
    court = OutdoorCourt(1, "Outdoor A", 160)
    club.add_court(court)

    bookings = [
        Booking(
            booking_id,
            Customer(booking_id, f"Player {booking_id}"),
            court,
            datetime(2026, 11, 20, 18),
            60,
        )
        for booking_id in (1, 2)
    ]

    barrier = Barrier(2)

    def submit_booking(booking):
        barrier.wait(timeout=5)

        try:
            club.add_booking(booking)
        except ValueError as error:
            return booking.booking_id, False, str(error)

        return booking.booking_id, True, "Accepted"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit_booking, bookings))

    for booking_id, accepted, message in results:
        status = "accepted" if accepted else "rejected"
        print(f"Booking {booking_id}: {status} — {message}")

    accepted_count = sum(
        1 for _, accepted, _ in results if accepted
    )
    stored_count = len(club.get_bookings())

    assert accepted_count == 1
    assert stored_count == 1

    print(f"Accepted requests: {accepted_count}")
    print(f"Stored bookings: {stored_count}")


if __name__ == "__main__":
    main()