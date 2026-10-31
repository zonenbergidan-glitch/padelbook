import logging
import time

import requests


logger = logging.getLogger(__name__)


class WeatherClient:
    URL = "https://api.open-meteo.com/v1/forecast"
    MAX_ATTEMPTS = 3
    RETRY_DELAY = 1

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

                return response.json()

            except (requests.Timeout, requests.ConnectionError):
                logger.warning(
                    "Weather request failed on attempt %s of %s",
                    attempt,
                    self.MAX_ATTEMPTS,
                )

                if attempt == self.MAX_ATTEMPTS:
                    raise

                time.sleep(self.RETRY_DELAY)