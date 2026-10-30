class Customer:
    def __init__(self, customer_id, name):
        if type(customer_id) is not int or customer_id <= 0:
            raise ValueError("Customer ID must be a positive integer")

        if not isinstance(name, str):
            raise ValueError("Customer name must be a string")

        name = name.strip()

        if not name:
            raise ValueError("Customer name cannot be empty")

        self.customer_id = customer_id
        self.name = name

    def __str__(self):
        return f"Customer #{self.customer_id}: {self.name}"

    def __repr__(self):
        return (
            f"Customer(customer_id={self.customer_id!r}, "
            f"name={self.name!r})"
        )

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Customer data must be a dictionary")

        if "customer_id" not in data or "name" not in data:
            raise ValueError("Customer data must include customer_id and name")

        return cls(data["customer_id"], data["name"])

    def __eq__(self, other):
        if not isinstance(other, Customer):
            return NotImplemented

        return self.customer_id == other.customer_id

class Court:
    def __init__(self, court_id, name, hourly_rate):
        if type(court_id) is not int or court_id <= 0:
            raise ValueError("Court ID must be a positive integer")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Court name must be a non-empty string")

        if (
            type(hourly_rate) not in (int, float)
            or not 0 < hourly_rate < float("inf")
        ):
            raise ValueError("Hourly rate must be a positive finite number")

        self.court_id = court_id
        self.name = name.strip()
        self.hourly_rate = hourly_rate

    def calculate_price(self, duration_minutes):
        if type(duration_minutes) is not int or duration_minutes <= 0:
            raise ValueError("Duration must be a positive number")

        return self.hourly_rate * (duration_minutes / 60)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Court data must be a dictionary")

        required = ("court_id", "name", "hourly_rate")
        if any(field not in data for field in required):
            raise ValueError("Court data must include court_id, name and hourly_rate")

        return cls(data["court_id"], data["name"], data["hourly_rate"])

    @staticmethod
    def validate_cancellation(booking_price, hours_before):
        if (
            type(booking_price) not in (int, float)
            or not 0 < booking_price < float("inf")
        ):
            raise ValueError("Booking price must be a positive finite number")

        if (
            type(hours_before) not in (int, float)
            or not 0 <= hours_before < float("inf")
        ):
            raise ValueError("Hours before the booking must be a non-negative finite number")

    def cancellation_fee(self, booking_price, hours_before):
        raise NotImplementedError("Each court type must define its cancellation policy")

    def __str__(self):
        return f"{self.name}: {self.hourly_rate} NIS per hour"

    def __repr__(self):
        return (
            f"{type(self).__name__}(court_id={self.court_id!r}, "
            f"name={self.name!r}, hourly_rate={self.hourly_rate!r})"
        )


class OutdoorCourt(Court):
    def cancellation_fee(self, booking_price, hours_before):
        self.validate_cancellation(booking_price, hours_before)

        if hours_before >= 12:
            return 0

        return booking_price * 0.5


class IndoorCourt(Court):
    def cancellation_fee(self, booking_price, hours_before):
        self.validate_cancellation(booking_price, hours_before)

        if hours_before >= 24:
            return 0

        if hours_before >= 12:
            return booking_price * 0.5

        return booking_price
    