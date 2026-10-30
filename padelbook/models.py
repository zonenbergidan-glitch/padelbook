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