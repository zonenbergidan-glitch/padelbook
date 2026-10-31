import logging
import time

import requests
import math


logger = logging.getLogger(__name__)


class WeatherClient:
    URL = "https://api.open-meteo.com/v1/forecast"
    MAX_ATTEMPTS = 3
    RETRY_DELAY = 1

    @staticmethod
    def validate_forecast(data):
        if not isinstance(data, dict):
            raise ValueError("Weather response must be a dictionary")

        hourly = data.get("hourly")

        if not isinstance(hourly, dict):
            raise ValueError("Missing hourly weather data")

        times = hourly.get("time")
        rain = hourly.get("rain")
        wind = hourly.get("wind_speed_10m")

        for values in (times, rain, wind):
            if not isinstance(values, list) or not values:
                raise ValueError("Weather arrays must be non-empty lists")

        if not (len(times) == len(rain) == len(wind)):
            raise ValueError("Weather arrays must have equal lengths")

        previous_time = None

        for timestamp in times:
            if type(timestamp) is not int:
                raise ValueError("Weather timestamps must be integers")

            if previous_time is not None and timestamp <= previous_time:
                raise ValueError("Weather timestamps must be increasing")

            previous_time = timestamp

        for measurements in (rain, wind):
            for value in measurements:
                if type(value) not in (int, float):
                    raise ValueError("Weather measurements must be numbers")

                if not math.isfinite(value) or value < 0:
                    raise ValueError(
                        "Weather measurements must be finite and non-negative"
                    )

        return data

    def get_hourly_forecast(self, latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "rain,wind_speed_10m",
            "wind_speed_unit": "kmh",
            "timezone": "Asia/Jerusalem",
            "timeformat": "unixtime",
            "forecast_days": 16,
        }

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                response = requests.get(
                    self.URL,
                    params=params,
                    timeout=10,
                )
                response.raise_for_status()

                data = response.json()
                return self.validate_forecast(data)

            except (requests.Timeout, requests.ConnectionError):
                logger.warning(
                    "Weather request failed on attempt %s of %s",
                    attempt,
                    self.MAX_ATTEMPTS,
                )

                if attempt == self.MAX_ATTEMPTS:
                    raise

                time.sleep(self.RETRY_DELAY)