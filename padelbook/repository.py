import json

from padelbook.models import Booking


def load_bookings(path, customers, courts):
    bookings = {}

    required_fields = (
        "booking_id",
        "customer_id",
        "court_id",
        "start_time",
        "duration_minutes",
    )

    with open(path, encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                data = json.loads(line)

                if not isinstance(data, dict):
                    raise ValueError("Each record must be a JSON object")

                if any(field not in data for field in required_fields):
                    raise ValueError("Booking record is missing required fields")

                for field in ("booking_id", "customer_id", "court_id"):
                    if type(data[field]) is not int or data[field] <= 0:
                        raise ValueError(f"{field} must be a positive integer")

                if not isinstance(data["start_time"], str):
                    raise ValueError("Start time must be a string")

                if data["booking_id"] in bookings:
                    raise ValueError("Duplicate booking ID")

                customer = customers.get(data["customer_id"])
                court = courts.get(data["court_id"])

                if customer is None:
                    raise ValueError("Customer does not exist")

                if court is None:
                    raise ValueError("Court does not exist")

                booking = Booking.from_dict(data, customer, court)
                bookings[booking.booking_id] = booking

            except ValueError as error:
                raise ValueError(
                    f"Invalid booking on line {line_number}: {error}"
                ) from error

    return bookings