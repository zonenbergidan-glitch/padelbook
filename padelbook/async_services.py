import asyncio
import logging

import requests

from padelbook.weather_client import WeatherClient


logger = logging.getLogger(__name__)


class AsyncWeatherClient:
    def __init__(self, client=None):
        self.client = client if client is not None else WeatherClient()

    async def get_hourly_forecast(self, latitude, longitude):
        return await asyncio.to_thread(
            self.client.get_hourly_forecast,
            latitude,
            longitude,
        )


async def fetch_one_forecast(client, location):
    latitude, longitude = location

    try:
        return await client.get_hourly_forecast(latitude, longitude)
    except (requests.RequestException, ValueError):
        logger.warning(
            "Forecast unavailable for location %s",
            location,
        )
        return None


async def fetch_forecasts_serial(locations, client=None):
    if client is None:
        client = AsyncWeatherClient()

    results = []

    for location in locations:
        forecast = await fetch_one_forecast(client, location)
        results.append(forecast)

    return results


async def fetch_forecasts_parallel(locations, client=None):
    if client is None:
        client = AsyncWeatherClient()

    tasks = [
        fetch_one_forecast(client, location)
        for location in locations
    ]

    return await asyncio.gather(*tasks)
