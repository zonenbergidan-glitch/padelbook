class BookingCollection:
    def __init__(self, bookings):
        self._bookings = list(bookings)

    def __iter__(self):
        return BookingIterator(self._bookings)

    def __len__(self):
        return len(self._bookings)


class BookingIterator:
    def __init__(self, bookings):
        self._bookings = bookings
        self._position = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._position >= len(self._bookings):
            raise StopIteration

        booking = self._bookings[self._position]
        self._position += 1

        return booking
def generate_confirmed_bookings(bookings):
    for booking in bookings:
        if booking.status == "confirmed":
            yield booking
def booking_ids_pipeline(bookings, minimum_price):
    confirmed = (
        booking
        for booking in bookings
        if booking.status == "confirmed"
    )

    expensive = (
        booking
        for booking in confirmed
        if booking.price >= minimum_price
    )

    booking_ids = (
        booking.booking_id
        for booking in expensive
    )

    return booking_ids