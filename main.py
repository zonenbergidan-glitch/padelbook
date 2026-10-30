from datetime import datetime

from padelbook.models import Customer, OutdoorCourt, IndoorCourt, Booking

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

if __name__ == "__main__":
    main()
        