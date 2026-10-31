import asyncio
import logging

import requests

from padelbook.weather_client import WeatherClient


logger = logging.getLogger(__name__)


async def fetch_one_forecast(client, location):
    latitude, longitude = location

    try:
        return await asyncio.to_thread(
            client.get_hourly_forecast,
            latitude,
            longitude,
        )
    except (requests.RequestException, ValueError):
        logger.warning(
            "Forecast unavailable for location %s",
            location,
        )
        return None


async def fetch_forecasts_serial(locations, client=None):
    if client is None:
        client = WeatherClient()

    results = []

    for location in locations:
        forecast = await fetch_one_forecast(client, location)
        results.append(forecast)

    return results


async def fetch_forecasts_parallel(locations, client=None):
    if client is None:
        client = WeatherClient()

    tasks = [
        fetch_one_forecast(client, location)
        for location in locations
    ]

    return await asyncio.gather(*tasks)