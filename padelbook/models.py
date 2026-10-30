from datetime import datetime, timedelta
from collections import deque 
import heapq
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
    
class Booking:
    def __init__(
        self,
        booking_id,
        customer,
        court,
        start_time,
        duration_minutes,
    ):
        if type(booking_id) is not int or booking_id <= 0:
            raise ValueError("Booking ID must be a positive integer")

        if not isinstance(customer, Customer):
            raise ValueError("Customer must be a Customer object")

        if not isinstance(court, Court):
            raise ValueError("Court must be a Court object")

        if not isinstance(start_time, datetime):
            raise ValueError("Start time must be a datetime object")

        # בשלב זה כל המועדים הם זמנים מקומיים ללא אזור זמן.
        if start_time.tzinfo is not None:
            raise ValueError("Start time must be a local datetime without timezone")

        # המתודה הקיימת גם בודקת שמשך המשחק תקין.
        price = court.calculate_price(duration_minutes)

        self.booking_id = booking_id
        self.customer = customer
        self.court = court
        self._start_time = start_time
        self._duration_minutes = duration_minutes
        self._price = price
        self._status = "confirmed"
        self._requires_review = False

    @property
    def start_time(self):
        return self._start_time

    @property
    def duration_minutes(self):
        return self._duration_minutes

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration_minutes)

    @property
    def price(self):
        return self._price

    @property
    def status(self):
        return self._status
    @classmethod
    def from_dict(cls, data, customer, court):
        if not isinstance(data, dict):
            raise ValueError("Booking data must be a dictionary")

        required = (
            "booking_id",
            "customer_id",
            "court_id",
            "start_time",
            "duration_minutes",
        )

        if any(field not in data for field in required):
            raise ValueError("Booking data is missing required fields")

        if not isinstance(customer, Customer):
            raise ValueError("Customer must be a Customer object")

        if not isinstance(court, Court):
            raise ValueError("Court must be a Court object")

        if data["customer_id"] != customer.customer_id:
            raise ValueError("Customer ID does not match the supplied customer")

        if data["court_id"] != court.court_id:
            raise ValueError("Court ID does not match the supplied court")

        try:
            start_time = datetime.fromisoformat(data["start_time"])
        except (TypeError, ValueError):
            raise ValueError("Start time must be a valid ISO datetime string") from None

        return cls(
            data["booking_id"],
            customer,
            court,
            start_time,
            data["duration_minutes"],
        )

    def cancel(self, cancelled_at):
        if self.status == "cancelled":
            raise ValueError("Booking is already cancelled")

        if not isinstance(cancelled_at, datetime):
            raise ValueError("Cancellation time must be a datetime object")

        if cancelled_at.tzinfo is not None:
            raise ValueError("Cancellation time must be a local datetime without timezone")

        if cancelled_at >= self.start_time:
            raise ValueError("Booking must be cancelled before it starts")

        hours_before = (
            self.start_time - cancelled_at
        ).total_seconds() / 3600

        fee = self.court.cancellation_fee(self.price, hours_before)

        self._status = "cancelled"

        return fee
    @property
    def requires_review(self):
        return self._requires_review

    def mark_for_review(self):
        if self.status == "confirmed":
            self._requires_review = True

    def __str__(self):
        return (
            f"Booking #{self.booking_id}: {self.customer.name}, "
            f"{self.court.name}, "
            f"{self.start_time:%d/%m/%Y %H:%M}"
            f"–{self.end_time:%H:%M}, "
            f"{self.price:.2f} NIS, {self.status}"
        )

    def __repr__(self):
        return (
            f"Booking(booking_id={self.booking_id!r}, "
            f"customer_id={self.customer.customer_id!r}, "
            f"court_id={self.court.court_id!r}, "
            f"start_time={self.start_time!r}, "
            f"duration_minutes={self.duration_minutes!r}, "
            f"price={self.price!r}, status={self.status!r})"
        )

class PadelClub:
    def __init__(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Club name must be a non-empty string")

        self.name = name.strip()
        self._courts = {}
        self._bookings = {}
        self._waiting_list = deque()
        self._issues = {}
        self._issue_queue = []
        self._issue_sequence = 0

    def add_court(self, court):
        if not isinstance(court, Court):
            raise ValueError("Court must be a Court object")

        if court.court_id in self._courts:
            raise ValueError("Court ID already exists")

        self._courts[court.court_id] = court

    def get_court(self, court_id):
        return self._courts.get(court_id)

    def add_booking(self, booking):
        if not self.is_court_operational(booking.court.court_id):
            raise ValueError("Court is unavailable due to maintenance")

        if booking.booking_id in self._bookings:
            raise ValueError("Booking ID already exists")

        registered_court = self.get_court(booking.court.court_id)

        if registered_court is not booking.court:
            raise ValueError("Booking court must be registered in this club")

        if booking.status != "confirmed":
            raise ValueError("Only confirmed bookings can be added")

        for existing in self._bookings.values():
            if existing.status != "confirmed":
                continue

            if existing.court.court_id != booking.court.court_id:
                continue

            if (
                booking.start_time < existing.end_time
                and existing.start_time < booking.end_time
            ):
                raise ValueError("Court is already booked for this time")

        self._bookings[booking.booking_id] = booking

    def get_booking(self, booking_id):
        return self._bookings.get(booking_id)
    def add_wait_request(self, request):
        if not isinstance(request, WaitRequest):
            raise ValueError("Request must be a WaitRequest object")

        if self.get_court(request.court.court_id) is not request.court:
            raise ValueError("Requested court must be registered in this club")

        for existing in self._waiting_list:
            if existing.request_id == request.request_id:
                raise ValueError("Wait request ID already exists")

        self._waiting_list.append(request)

    def pop_wait_request(self):
        if not self._waiting_list:
            return None

        return self._waiting_list.popleft()

    @property
    def waiting_count(self):
        return len(self._waiting_list)
    def pop_matching_wait_request(self, booking_id):
        booking = self.get_booking(booking_id)

        if booking is None:
            raise ValueError("Booking does not exist")

        if booking.status != "cancelled":
            raise ValueError("Booking must be cancelled first")

        selected = None
        request_count = len(self._waiting_list)

        for _ in range(request_count):
            request = self._waiting_list.popleft()

            matches = (
                request.court is booking.court
                and request.start_time == booking.start_time
                and request.duration_minutes == booking.duration_minutes
            )

            if selected is None and matches:
                selected = request
            else:
                self._waiting_list.append(request)

        return selected
    def add_issue(self, issue):
        if not isinstance(issue, MaintenanceIssue):
            raise ValueError("Issue must be a MaintenanceIssue object")

        if self.get_court(issue.court.court_id) is not issue.court:
            raise ValueError("Issue court must be registered in this club")

        if issue.issue_id in self._issues:
            raise ValueError("Issue ID already exists")

        self._issues[issue.issue_id] = issue
        self._issue_sequence += 1

        entry = (
            issue.priority,
            self._issue_sequence,
            issue.issue_id,
        )
        heapq.heappush(self._issue_queue, entry)
        if issue.blocks_court:
            for booking in self._bookings.values():
                if booking.court is issue.court:
                    booking.mark_for_review()

    def pop_next_issue(self):
        while self._issue_queue:
            priority, sequence, issue_id = heapq.heappop(self._issue_queue)
            issue = self._issues[issue_id]

            if issue.status != "closed":
                return issue

        return None
    
    def is_court_operational(self, court_id):
        if self.get_court(court_id) is None:
            raise ValueError("Court does not exist")

        for issue in self._issues.values():
            if (
                issue.court.court_id == court_id
                and issue.blocks_court
                and issue.status != "closed"
            ):
                return False

        return True

    def close_issue(self, issue_id):
        issue = self._issues.get(issue_id)

        if issue is None:
            raise ValueError("Issue does not exist")

        issue.close()

    def get_bookings(self):
        return list(self._bookings.values())

    def __len__(self):
        return len(self._courts)

    def __str__(self):
        return f"{self.name}: {len(self)} courts"

    def __repr__(self):
        return (
            f"PadelClub(name={self.name!r}, "
            f"court_count={len(self)}, "
            f"booking_count={len(self._bookings)})"
        ) 
     
class WaitRequest:
    def __init__(
        self,
        request_id,
        customer,
        court,
        start_time,
        duration_minutes,
    ):
        if type(request_id) is not int or request_id <= 0:
            raise ValueError("Request ID must be a positive integer")

        if not isinstance(customer, Customer):
            raise ValueError("Customer must be a Customer object")

        if not isinstance(court, Court):
            raise ValueError("Court must be a Court object")

        if not isinstance(start_time, datetime):
            raise ValueError("Start time must be a datetime object")

        if start_time.tzinfo is not None:
            raise ValueError("Start time must be a local datetime without timezone")

        # שימוש בבדיקת משך המשחק שכבר קיימת במגרש.
        court.calculate_price(duration_minutes)

        self.request_id = request_id
        self.customer = customer
        self.court = court
        self.start_time = start_time
        self.duration_minutes = duration_minutes

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration_minutes)

    def __str__(self):
        return (
            f"Wait request #{self.request_id}: "
            f"{self.customer.name}, {self.court.name}, "
            f"{self.start_time:%d/%m/%Y %H:%M}"
        )

    def __repr__(self):
        return (
            f"WaitRequest(request_id={self.request_id!r}, "
            f"customer_id={self.customer.customer_id!r}, "
            f"court_id={self.court.court_id!r}, "
            f"start_time={self.start_time!r}, "
            f"duration_minutes={self.duration_minutes!r})"
        ) 
class MaintenanceIssue:
    def __init__(
        self, issue_id, court, description, priority, blocks_court=False
    ):
        if type(issue_id) is not int or issue_id <= 0:
            raise ValueError("Issue ID must be a positive integer")

        if not isinstance(court, Court):
            raise ValueError("Court must be a Court object")

        if not isinstance(description, str) or not description.strip():
            raise ValueError("Description must be a non-empty string")

        if type(priority) is not int or priority not in (1, 2, 3):
            raise ValueError("Priority must be 1, 2 or 3")
        if type(blocks_court) is not bool:
            raise ValueError("Blocks court must be True or False")

        self.issue_id = issue_id
        self.court = court
        self.description = description.strip()
        self._priority = priority
        self._blocks_court = blocks_court
        self._status = "open"

    @property
    def blocks_court(self):
        return self._blocks_court

    @property
    def status(self):
        return self._status

    def close(self):
        if self.status == "closed":
            raise ValueError("Issue is already closed")

        self._status = "closed"

    @property
    def priority(self):
        return self._priority

    def __str__(self):
        return (
            f"Issue #{self.issue_id}: {self.description}, "
            f"court={self.court.name}, priority={self.priority}"
        )

    def __repr__(self):
        return (
            f"MaintenanceIssue(issue_id={self.issue_id!r}, "
            f"court_id={self.court.court_id!r}, "
            f"description={self.description!r}, "
            f"priority={self.priority!r})"
        ) 

