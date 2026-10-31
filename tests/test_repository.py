import json

import pytest

from padelbook.models import Customer, OutdoorCourt
from padelbook.repository import load_bookings


@pytest.fixture
def booking_data():
    customers = {1: Customer(1, "Demo Player")}
    courts = {1: OutdoorCourt(1, "Outdoor A", 160)}
    record = {
        "booking_id": 101,
        "customer_id": 1,
        "court_id": 1,
        "start_time": "2026-11-20T18:00:00",
        "duration_minutes": 90,
    }

    return customers, courts, record


def test_load_valid_booking(tmp_path, booking_data):
    customers, courts, record = booking_data
    path = tmp_path / "bookings.jsonl"
    path.write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )

    bookings = load_bookings(path, customers, courts)

    assert list(bookings) == [101]
    assert bookings[101].customer is customers[1]
    assert bookings[101].court is courts[1]
    assert bookings[101].price == 240
    assert bookings[101].status == "confirmed"


def test_duplicate_booking_id_is_rejected(tmp_path, booking_data):
    customers, courts, record = booking_data
    path = tmp_path / "bookings.jsonl"
    line = json.dumps(record) + "\n"
    path.write_text(line + line, encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="line 2: Duplicate booking ID",
    ):
        load_bookings(path, customers, courts)


def test_unknown_customer_is_rejected(tmp_path, booking_data):
    customers, courts, record = booking_data
    record["customer_id"] = 99
    path = tmp_path / "bookings.jsonl"
    path.write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Customer does not exist"):
        load_bookings(path, customers, courts)


def test_missing_field_is_rejected(tmp_path, booking_data):
    customers, courts, record = booking_data
    del record["duration_minutes"]
    path = tmp_path / "bookings.jsonl"
    path.write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required fields"):
        load_bookings(path, customers, courts)