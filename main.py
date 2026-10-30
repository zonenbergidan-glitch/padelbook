from datetime import datetime

from padelbook.models import Customer, MaintenanceIssue, OutdoorCourt, IndoorCourt, Booking , WaitRequest
from padelbook.models import (
    Customer,
    OutdoorCourt,
    IndoorCourt,
    Booking,
    PadelClub,
)
from padelbook.processing import (
    confirmed_bookings,
    unique_customer_ids,
    index_bookings,
    confirmed_count_by_court,
    sort_by_start_time,
    sort_by_court_and_start,
    booking_prices,
    split_first_booking,
)
from pathlib import Path

from padelbook.repository import load_bookings
from padelbook.iterators import (
    BookingCollection,
    generate_confirmed_bookings,
    booking_ids_pipeline,
)

def main():
    customer = Customer(1, "  Demo Player  ")
    same_customer = Customer.from_dict(
        {"customer_id": 1, "name": "Demo Player"}
    )
    another_customer = Customer(2, "Another Player")

    print(customer)
    print(repr(customer))
    print(customer == same_customer)
    print(customer == another_customer)

    try:
        Customer.from_dict({"customer_id": 3})
    except ValueError as error:
        print(error)


    courts = [
        OutdoorCourt(1, "Outdoor A", 160),
        IndoorCourt(2, "Indoor A", 160),
    ]

    expected_fees = [0, 120]

    for court, expected in zip(courts, expected_fees):
        fee = court.cancellation_fee(240, 18)
        assert fee == expected, f"Expected {expected}, got {fee}"
        print(f"{court.name}: cancellation fee = {fee:.2f} NIS")

    print(f"90-minute price: {courts[0].calculate_price(90):.2f} NIS")

    try:
        courts[0].calculate_price(0)
    except ValueError as error:
        print(error)

    booking_data = {
        "booking_id": 2,
        "customer_id": customer.customer_id,
        "court_id": courts[1].court_id,
        "start_time": "2026-11-10T18:00:00",
        "duration_minutes": 90,
    }

    indoor_booking = Booking.from_dict(
        booking_data,
        customer,
        courts[1],
    )

    fee = indoor_booking.cancel(datetime(2026, 11, 10, 0, 0))

    assert fee == 120
    assert indoor_booking.status == "cancelled"

    print(f"Cancellation fee: {fee:.2f} NIS")
    print(f"Booking status: {indoor_booking.status}")

    try:
        indoor_booking.cancel(datetime(2026, 11, 10, 0, 0))
    except ValueError as error:
        print(error)
    club = PadelClub("Demo Padel Club")

    for court in courts:
        club.add_court(court)

    assert len(club) == 2
    assert club.get_court(1) is courts[0]
    assert club.get_court(999) is None

    print(club)

    try:
        club.add_court(courts[0])
    except ValueError as error:
        print(error)
    first_booking = Booking(
        10, customer, courts[0],
        datetime(2026, 11, 10, 18, 0), 90,
    )
    club.add_booking(first_booking)

    overlapping_booking = Booking(
        11, customer, courts[0],
        datetime(2026, 11, 10, 19, 0), 60,
    )

    try:
        club.add_booking(overlapping_booking)
    except ValueError as error:
        print(error)

    assert club.get_booking(11) is None

    next_booking = Booking(
        12, customer, courts[0],
        datetime(2026, 11, 10, 19, 30), 60,
    )
    club.add_booking(next_booking)

    assert club.get_booking(10) is first_booking
    assert club.get_booking(12) is next_booking

    print("Back-to-back booking accepted")

    for request_id in (1, 2, 3):
        request = WaitRequest(
            request_id,
            customer,
            courts[0],
            datetime(2026, 11, 10, 18, 0),
            90,
        )
        club.add_wait_request(request)

    assert club.waiting_count == 3

    for expected_id in (1, 2, 3):
        request = club.pop_wait_request()
        assert request.request_id == expected_id
        print(f"Next wait request: {request.request_id}")

    assert club.waiting_count == 0
    assert club.pop_wait_request() is None

    print("Empty waiting list handled")

    requests = [
        WaitRequest(
            10, customer, courts[1],
            datetime(2026, 11, 10, 18, 0), 90,
        ),
        WaitRequest(
            11, customer, courts[0],
            datetime(2026, 11, 10, 18, 0), 90,
        ),
        WaitRequest(
            12, customer, courts[0],
            datetime(2026, 11, 10, 18, 0), 90,
        ),
    ]

    for request in requests:
        club.add_wait_request(request)

    # הזמנה 10 נוצרה קודם ונוספה למועדון.
    first_booking.cancel(datetime(2026, 11, 10, 0, 0))

    selected = club.pop_matching_wait_request(first_booking.booking_id)

    assert selected.request_id == 11
    assert club.waiting_count == 2

    print(f"Matching request: {selected.request_id}")

    # בקשה 10 למגרש אחר; בקשה 12 מתאימה אך הגיעה אחרי 11.
    remaining_first = club.pop_wait_request()
    remaining_second = club.pop_wait_request()

    assert remaining_first.request_id == 10
    assert remaining_second.request_id == 12

    print(
        f"Remaining order: "
        f"{remaining_first.request_id}, {remaining_second.request_id}"
    )

    assert club.pop_matching_wait_request(first_booking.booking_id) is None
    issues = [
        MaintenanceIssue(1, courts[0], "Paint needs repair", 3),
        MaintenanceIssue(2, courts[0], "Broken glass on court", 1),
        MaintenanceIssue(3, courts[1], "Lighting failure", 2),
        MaintenanceIssue(4, courts[1], "Loose fence panel", 1),
    ]

    for issue in issues:
        club.add_issue(issue)

    for expected_id in (2, 4, 3, 1):
        issue = club.pop_next_issue()
        assert issue.issue_id == expected_id
        print(f"Next issue: {issue.issue_id}, priority: {issue.priority}")

    assert club.pop_next_issue() is None
    print("Empty issue queue handled")
    club.add_issue(
        MaintenanceIssue(
            20, courts[0], "Damaged playing surface", 1,
            blocks_court=True,
        )
    )
    club.add_issue(
        MaintenanceIssue(
            21, courts[0], "Unsafe entrance gate", 1,
            blocks_court=True,
        )
    )

    assert not club.is_court_operational(1)

    maintenance_booking = Booking(
        30, customer, courts[0],
        datetime(2026, 11, 11, 18, 0), 90,
    )

    try:
        club.add_booking(maintenance_booking)
    except ValueError as error:
        print(error)

    assert club.get_booking(30) is None

    club.close_issue(20)
    assert not club.is_court_operational(1)
    print("Court remains blocked after closing one issue")

    club.close_issue(21)
    assert club.is_court_operational(1)

    club.add_booking(maintenance_booking)
    assert club.get_booking(30) is maintenance_booking
    print("Court reopened and booking accepted")

    assert club.pop_next_issue() is None
    assert not maintenance_booking.requires_review

    club.add_issue(
        MaintenanceIssue(
            22, courts[0], "New surface damage", 1,
            blocks_court=True,
        )
    )

    assert maintenance_booking.requires_review
    assert maintenance_booking.status == "confirmed"

    print("Existing booking marked for review")

    club.close_issue(22)

    assert club.is_court_operational(1)
    assert maintenance_booking.requires_review

    print("Review flag preserved after repair")
    all_bookings = club.get_bookings()
    active_bookings = confirmed_bookings(all_bookings)

    customer_ids = unique_customer_ids(active_bookings)
    booking_index = index_bookings(all_bookings)
    counts = confirmed_count_by_court(all_bookings)

    assert all(
        booking.status == "confirmed"
        for booking in active_bookings
    )
    assert booking_index[30] is maintenance_booking

    print(f"Customers with confirmed bookings: {len(customer_ids)}")

    for court_id, count in counts.items():
        print(f"Court {court_id}: {count} confirmed bookings")

    ordered_bookings = sort_by_start_time(active_bookings)
    print(
        "Bookings by start time:",
        [booking.booking_id for booking in ordered_bookings],
    )

    ordered_by_court = sort_by_court_and_start(active_bookings)
    print(
        "Bookings by court and start:",
        [booking.booking_id for booking in ordered_by_court],
    ) 
    
    prices = booking_prices(active_bookings)

    assert prices == {12: 160, 30: 240}
    print(f"Booking prices: {prices}")

    first, remaining = split_first_booking(ordered_bookings)

    assert first.booking_id == 12
    assert [booking.booking_id for booking in remaining] == [30]
    assert split_first_booking([]) == (None, [])

    print(f"First booking: {first.booking_id}")
    print(f"Remaining bookings: {len(remaining)}")

    # מעקב אחר לקוחות שהקבלה צריכה ליצור איתם קשר.
    pending_contact = set(customer_ids)

    pending_contact.add(another_customer.customer_id)
    assert another_customer.customer_id in pending_contact

    # הלקוח הנוסף טופל ולכן מוסר מהקבוצה.
    pending_contact.discard(another_customer.customer_id)

    # discard אינו נכשל גם כשהמזהה כבר אינו בקבוצה.
    pending_contact.discard(another_customer.customer_id)

    assert pending_contact == customer_ids
    print(f"Customers still awaiting contact: {len(pending_contact)}") 
    data_path = (
        Path(__file__).resolve().parent
        / "data"
        / "sample_data.jsonl"
    )

    customers_by_id = {
        customer.customer_id: customer,
        another_customer.customer_id: another_customer,
    }

    courts_by_id = {
        court.court_id: court
        for court in courts
    }

    loaded_bookings = load_bookings(
        data_path,
        customers_by_id,
        courts_by_id,
    )

    assert len(loaded_bookings) == 15
    assert loaded_bookings[101].price == 240
    assert loaded_bookings[102].price == 160

    print(f"Loaded bookings: {len(loaded_bookings)}")
    print(f"Booking 101 price: {loaded_bookings[101].price:.2f} NIS")

    loaded_club = PadelClub("Loaded Demo Club")

    for court in courts:
        loaded_club.add_court(court)

    for booking in loaded_bookings.values():
        loaded_club.add_booking(booking)

    print("All loaded bookings accepted by the club")
    collection = BookingCollection(loaded_bookings.values())

    first_iterator = iter(collection)
    second_iterator = iter(collection)

    assert first_iterator is not second_iterator

    first_booking_a = next(first_iterator)
    second_booking_a = next(first_iterator)
    first_booking_b = next(second_iterator)

    assert first_booking_a.booking_id == 101
    assert second_booking_a.booking_id == 102
    assert first_booking_b.booking_id == 101

    print(
        "First iterator:",
        first_booking_a.booking_id,
        second_booking_a.booking_id,
    )
    print("Second iterator:", first_booking_b.booking_id)

    visited_ids = [
        booking.booking_id
        for booking in collection
    ]

    assert visited_ids == list(range(101, 116))
    print(f"Collection traversal: {len(visited_ids)} bookings")

    empty_iterator = iter(BookingCollection([]))

    try:
        next(empty_iterator)
    except StopIteration:
        print("Empty iterator raises StopIteration")
    confirmed_generator = generate_confirmed_bookings(all_bookings)

    print("Generator created")

    first_generated = next(confirmed_generator)
    assert first_generated.booking_id == 12
    print(f"First generated booking: {first_generated.booking_id}")

    remaining_ids = []

    for booking in confirmed_generator:
        remaining_ids.append(booking.booking_id)

    assert remaining_ids == [30]
    print(f"Remaining generated bookings: {remaining_ids}")

    assert list(confirmed_generator) == []
    print("Exhausted generator returns no more bookings")

    restarted_ids = [
        booking.booking_id
        for booking in generate_confirmed_bookings(all_bookings)
    ]

    assert restarted_ids == [12, 30]
    print(f"New generator starts again: {restarted_ids}")
    pipeline = booking_ids_pipeline(collection, minimum_price=200)

    first_id = next(pipeline)
    second_id = next(pipeline)

    assert first_id == 101
    assert second_id == 104

    print(f"First two pipeline results: {first_id}, {second_id}")

    # עוצרים כאן: לא צורכים את יתר התוצאות.


if __name__ == "__main__":
    main()
        