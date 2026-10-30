from padelbook.models import Customer


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


if __name__ == "__main__":
    main()