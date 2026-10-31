import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
import requests

from padelbook.async_services import (
    AsyncWeatherClient,
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
    client.get_hourly_forecast = AsyncMock(
        side_effect=lambda latitude, longitude: forecasts[
            (latitude, longitude)
        ]
    )

    serial = asyncio.run(fetch_forecasts_serial(locations, client))
    parallel = asyncio.run(fetch_forecasts_parallel(locations, client))

    expected = [forecasts[location] for location in locations]
    assert serial == expected
    assert parallel == expected
    assert client.get_hourly_forecast.await_count == 6


@pytest.mark.parametrize(
    "fetch_function",
    [fetch_forecasts_serial, fetch_forecasts_parallel],
)
def test_failed_request_preserves_other_results(fetch_function):
    locations = [(1, 1), (2, 2), (3, 3)]

    async def fake_forecast(latitude, longitude):
        if latitude == 2:
            raise requests.Timeout("Unavailable")
        return {"location": (latitude, longitude)}

    client = Mock()
    client.get_hourly_forecast = AsyncMock(side_effect=fake_forecast)

    results = asyncio.run(fetch_function(locations, client))

    assert results == [
        {"location": (1, 1)},
        None,
        {"location": (3, 3)},
    ]
    assert client.get_hourly_forecast.await_count == 3


@pytest.mark.parametrize(
    "fetch_function",
    [fetch_forecasts_serial, fetch_forecasts_parallel],
)
def test_empty_locations_make_no_requests(fetch_function):
    client = Mock()
    client.get_hourly_forecast = AsyncMock()

    results = asyncio.run(fetch_function([], client))

    assert results == []
    client.get_hourly_forecast.assert_not_called()


def test_parallel_results_preserve_input_order():
    async def scenario():
        locations = [(1, 1), (2, 2), (3, 3)]
        finished = {number: asyncio.Event() for number in (1, 2, 3)}
        completion_order = []

        async def fake_forecast(latitude, longitude):
            if latitude < 3:
                await finished[latitude + 1].wait()

            completion_order.append(latitude)
            finished[latitude].set()
            return {"location": (latitude, longitude)}

        client = Mock()
        client.get_hourly_forecast = AsyncMock(side_effect=fake_forecast)
        results = await asyncio.wait_for(
            fetch_forecasts_parallel(locations, client),
            timeout=5,
        )

        assert completion_order == [3, 2, 1]
        assert results == [
            {"location": (1, 1)},
            {"location": (2, 2)},
            {"location": (3, 3)},
        ]

    asyncio.run(scenario())


def test_async_client_wraps_synchronous_weather_client():
    synchronous_client = Mock()
    synchronous_client.get_hourly_forecast.return_value = {
        "hourly": {
            "time": [1793440800],
            "rain": [0.0],
            "wind_speed_10m": [10.0],
        }
    }
    client = AsyncWeatherClient(synchronous_client)

    result = asyncio.run(
        client.get_hourly_forecast(32.0853, 34.7818)
    )

    assert result["hourly"]["rain"] == [0.0]
    synchronous_client.get_hourly_forecast.assert_called_once_with(
        32.0853, 34.7818
    )