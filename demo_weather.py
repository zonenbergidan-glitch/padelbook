import argparse
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from padelbook.models import Customer, OutdoorCourt, Booking
from padelbook.services import assess_booking_weather
from padelbook.weather_client import WeatherClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch a real forecast from Open-Meteo",
    )
    args = parser.parse_args()

    timezone = ZoneInfo("Asia/Jerusalem")
    tomorrow = datetime.now(timezone).date() + timedelta(days=1)
    start = datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, 18, 30
    )

    booking = Booking(
        1001,
        Customer(1, "Demo Player"),
        OutdoorCourt(1, "Outdoor A", 160),
        start,
        90,
    )

    if args.live:
        source = "Live API"
        try:
            forecast = WeatherClient().get_hourly_forecast(
                32.0853, 34.7818
            )
        except (requests.RequestException, ValueError):
            logging.exception("Could not obtain a valid forecast")
            forecast = None
            source = "Live API unavailable"
    else:
        source = "Synthetic offline data"
        times = [
            int(
                start.replace(
                    hour=hour,
                    minute=0,
                    tzinfo=timezone,
                ).timestamp()
            )
            for hour in (18, 19, 20)
        ]
        forecast = {
            "hourly": {
                "time": times,
                "rain": [0, 0, 2],
                "wind_speed_10m": [10, 10, 10],
            }
        }

    result = assess_booking_weather(booking, forecast)

    print(f"Source: {source}")
    print(f"Booking starts: {booking.start_time}")
    print(f"Booking ends: {booking.end_time}")
    print(f"Weather assessment: {result}")
    print(f"Booking status: {booking.status}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()