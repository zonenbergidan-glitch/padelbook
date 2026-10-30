from padelbook.models import Customer, OutdoorCourt, IndoorCourt

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

if __name__ == "__main__":
    main()
        