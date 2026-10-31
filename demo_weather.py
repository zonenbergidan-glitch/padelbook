import argparse
import logging
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from padelbook.models import Customer, OutdoorCourt, Booking
from padelbook.services import (
    NormalWeatherPolicy,
    StrictWeatherPolicy,
    review_booking_weather,
)
from padelbook.weather_client import WeatherClient
from padelbook.models import PadelClub
from padelbook.factories import create_court


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch a real forecast from Open-Meteo",
    )
    parser.add_argument(
        "--policy",
        choices=("normal", "strict"),
        default="normal",
        help="Weather policy chosen by the club manager",
    )
    parser.add_argument(
        "--demo-rain-mm",
        type=float,
        default=2.0,
        help="Rain in the final offline forecast hour; ignored with --live",
    )
    args = parser.parse_args(argv)

    if not math.isfinite(args.demo_rain_mm) or args.demo_rain_mm < 0:
        parser.error("--demo-rain-mm must be finite and non-negative")

    if args.policy == "strict":
        policy = StrictWeatherPolicy()
    else:
        policy = NormalWeatherPolicy()

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
    club = PadelClub("Weather Demo Club")
    club.add_court(booking.court)

    indoor = create_court(
        "indoor",
        court_id=2,
        name="Indoor A",
        hourly_rate=160,
    )
    club.add_court(indoor)
    club.add_booking(booking)
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
                "rain": [0, 0, args.demo_rain_mm],
                "wind_speed_10m": [10, 10, 10],
            }
        }

    result = review_booking_weather(
        club, booking, forecast, policy=policy
    )

    print(f"Source: {source}")
    print(f"Weather policy: {args.policy}")
    print(f"Booking starts: {booking.start_time}")
    print(f"Booking ends: {booking.end_time}")
    print(f"Weather assessment: {result['assessment']}")
    print(f"Requires review: {result['requires_review']}")
    print(
        f"Indoor alternatives: "
        f"{result['alternative_court_ids']}"
    )
    print(f"Original court: {booking.court.court_id}")
    print(f"Booking status: {booking.status}")
    print(f"Stored bookings: {len(club.get_bookings())}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
