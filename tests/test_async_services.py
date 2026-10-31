import asyncio
from unittest.mock import Mock

import pytest
import requests
from threading import Event

from padelbook.async_services import (
    fetch_forecasts_serial,
    fetch_forecasts_parallel,
)


def test_serial_and_parallel_return_same_ordered_results():
    locations = [
        (32.0853, 34.7818),
        (31.7683, 35.2137),
        (32.7940, 34.9896),
    ]
    forecasts = {
        location: {"location": location}
        for location in locations
    }

    client = Mock()
    client.get_hourly_forecast.side_effect = (
        lambda latitude, longitude: forecasts[
            (latitude, longitude)
        ]
    )

    serial = asyncio.run(
        fetch_forecasts_serial(locations, client)
    )
    parallel = asyncio.run(
        fetch_forecasts_parallel(locations, client)
    )

    expected = [forecasts[location] for location in locations]

    assert serial == expected
    assert parallel == expected
    assert client.get_hourly_forecast.call_count == 6


@pytest.mark.parametrize(
    "fetch_function",
    [fetch_forecasts_serial, fetch_forecasts_parallel],
)
def test_failed_request_preserves_other_results(fetch_function):
    locations = [(1, 1), (2, 2), (3, 3)]

    def fake_forecast(latitude, longitude):
        if latitude == 2:
            raise requests.Timeout("Unavailable")

        return {"location": (latitude, longitude)}

    client = Mock()
    client.get_hourly_forecast.side_effect = fake_forecast

    results = asyncio.run(
        fetch_function(locations, client)
    )

    assert results == [
        {"location": (1, 1)},
        None,
        {"location": (3, 3)},
    ]
    assert client.get_hourly_forecast.call_count == 3


@pytest.mark.parametrize(
    "fetch_function",
    [fetch_forecasts_serial, fetch_forecasts_parallel],
)
def test_empty_locations_make_no_requests(fetch_function):
    client = Mock()

    results = asyncio.run(fetch_function([], client))

    assert results == []
    client.get_hourly_forecast.assert_not_called()
def test_parallel_results_preserve_input_order():
    locations = [(1, 1), (2, 2), (3, 3)]
    finished = {number: Event() for number in (1, 2, 3)}
    completion_order = []

    def fake_forecast(latitude, longitude):
        if latitude < 3:
            next_finished = finished[latitude + 1]

            if not next_finished.wait(timeout=5):
                raise RuntimeError("Tasks did not run concurrently")

        completion_order.append(latitude)
        finished[latitude].set()

        return {"location": (latitude, longitude)}

    client = Mock()
    client.get_hourly_forecast.side_effect = fake_forecast

    results = asyncio.run(
        fetch_forecasts_parallel(locations, client)
    )

    assert completion_order == [3, 2, 1]
    assert results == [
        {"location": (1, 1)},
        {"location": (2, 2)},
        {"location": (3, 3)},
    ]