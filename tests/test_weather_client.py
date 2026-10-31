from unittest.mock import Mock

import pytest
import requests

from padelbook.weather_client import WeatherClient


def test_get_hourly_forecast(monkeypatch):
    expected = {
        "hourly": {
            "time": [1793440800],
            "rain": [2.0],
            "wind_speed_10m": [10.0],
        }
    }
    response = Mock()
    response.json.return_value = expected
    mock_get = Mock(return_value=response)

    monkeypatch.setattr(
        "padelbook.weather_client.requests.get",
        mock_get,
    )

    client = WeatherClient()
    result = client.get_hourly_forecast(32.0853, 34.7818)

    assert result == expected
    response.raise_for_status.assert_called_once()
    mock_get.assert_called_once_with(
        WeatherClient.URL,
        params={
            "latitude": 32.0853,
            "longitude": 34.7818,
            "hourly": "rain,wind_speed_10m",
            "wind_speed_unit": "kmh",
            "timezone": "Asia/Jerusalem",
            "timeformat": "unixtime",
            "forecast_days": 16,
        },
        timeout=10,
    )


def test_get_hourly_forecast_http_error(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError(
        "Server error"
    )
    mock_get = Mock(return_value=response)

    monkeypatch.setattr(
        "padelbook.weather_client.requests.get",
        mock_get,
    )

    client = WeatherClient()

    with pytest.raises(requests.HTTPError):
        client.get_hourly_forecast(32.0853, 34.7818)

    response.json.assert_not_called()
@pytest.mark.parametrize(
    "error_class",
    [requests.Timeout, requests.ConnectionError],
)
def test_weather_request_recovers_after_failure(
    monkeypatch, error_class
):
    response = Mock()
    payload = {
        "hourly": {
            "time": [1793440800],
            "rain": [0.0],
            "wind_speed_10m": [10.0],
        }
    }
    response.json.return_value = payload

    mock_get = Mock(
        side_effect=[
            error_class("Temporary failure"),
            response,
        ]
    )
    mock_sleep = Mock()

    monkeypatch.setattr(
        "padelbook.weather_client.requests.get", mock_get
    )
    monkeypatch.setattr(
        "padelbook.weather_client.time.sleep", mock_sleep
    )

    result = WeatherClient().get_hourly_forecast(
        32.0853, 34.7818
    )

    assert result == payload
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(1)


@pytest.mark.parametrize(
    "error_class",
    [requests.Timeout, requests.ConnectionError],
)
def test_weather_request_stops_after_three_failures(
    monkeypatch, error_class
):
    mock_get = Mock(side_effect=error_class("Unavailable"))
    mock_sleep = Mock()

    monkeypatch.setattr(
        "padelbook.weather_client.requests.get", mock_get
    )
    monkeypatch.setattr(
        "padelbook.weather_client.time.sleep", mock_sleep
    )

    with pytest.raises(error_class):
        WeatherClient().get_hourly_forecast(
            32.0853, 34.7818
        )

    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2
@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"hourly": {}},
        {
            "hourly": {
                "time": [1793440800],
                "rain": [],
                "wind_speed_10m": [10],
            }
        },
        {
            "hourly": {
                "time": [1793440800],
                "rain": [-1],
                "wind_speed_10m": [10],
            }
        },
        {
            "hourly": {
                "time": [1793440800],
                "rain": [0],
                "wind_speed_10m": [None],
            }
        },
    ],
)
def test_weather_client_rejects_invalid_payload(
    monkeypatch, payload
):
    response = Mock()
    response.json.return_value = payload
    mock_get = Mock(return_value=response)

    monkeypatch.setattr(
        "padelbook.weather_client.requests.get",
        mock_get,
    )

    with pytest.raises(ValueError):
        WeatherClient().get_hourly_forecast(
            32.0853, 34.7818
        )

    mock_get.assert_called_once()