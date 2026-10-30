def confirmed_bookings(bookings):
    return [
        booking
        for booking in bookings
        if booking.status == "confirmed"
    ]


def unique_customer_ids(bookings):
    return {booking.customer.customer_id for booking in bookings}


def index_bookings(bookings):
    index = {}

    for booking in bookings:
        if booking.booking_id in index:
            raise ValueError("Duplicate booking ID")

        index[booking.booking_id] = booking

    return index


def confirmed_count_by_court(bookings):
    counts = {}

    for booking in bookings:
        if booking.status == "confirmed":
            court_id = booking.court.court_id
            counts[court_id] = counts.get(court_id, 0) + 1

    return counts


def booking_start_time(booking):
    return booking.start_time


def sort_by_start_time(bookings):
    return sorted(bookings, key=booking_start_time)


def sort_by_court_and_start(bookings):
    return sorted(
        bookings,
        key=lambda booking: (
            booking.court.court_id,
            booking.start_time,
        ),
    )
def booking_prices(bookings):
    return {
        booking.booking_id: booking.price
        for booking in bookings
    }


def split_first_booking(bookings):
    if not bookings:
        return None, []

    first, *remaining = bookings
    return first, remaining