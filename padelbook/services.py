import math
from zoneinfo import ZoneInfo
from padelbook import config

from padelbook.weather_client import WeatherClient
class WeatherPolicy:
    def requires_review(self, rain_mm, wind_kmh):
        raise NotImplementedError("Weather policy must define review rules")


class NormalWeatherPolicy(WeatherPolicy):
    def requires_review(self, rain_mm, wind_kmh):
        return rain_mm >= 1 or wind_kmh >= 35

class StrictWeatherPolicy(WeatherPolicy):
    def requires_review(self, rain_mm, wind_kmh):
        return rain_mm >= 0.5 or wind_kmh >= 25


def requires_weather_review(booking, rain_mm, wind_kmh, policy=None):
    if not booking.court.weather_exposed:
        return False

    for name, value in (
        ("rain_mm", rain_mm),
        ("wind_kmh", wind_kmh),
    ):
        if type(value) not in (int, float):
            raise ValueError(f"{name} must be a number")

        if not math.isfinite(value) or value < 0:
            raise ValueError(
                f"{name} must be finite and non-negative"
            )

    if policy is None:
        policy = NormalWeatherPolicy()

    return policy.requires_review(rain_mm, wind_kmh)
def assess_booking_weather(booking, forecast, policy=None):
    if not booking.court.weather_exposed:
        return "not_required"

    try:
        WeatherClient.validate_forecast(forecast)
    except ValueError:
        return "unknown"

    timezone = ZoneInfo(config.CLUB_TIMEZONE)
    start = booking.start_time.replace(tzinfo=timezone).timestamp()
    end = booking.end_time.replace(tzinfo=timezone).timestamp()

    hourly = forecast["hourly"]
    times = hourly["time"]
    rain = hourly["rain"]
    wind = hourly["wind_speed_10m"]

    covered_until = start
    review_required = False

    for index in range(len(times) - 1):
        interval_start = times[index]
        interval_end = times[index + 1]

        if interval_end <= start or interval_start >= end:
            continue

        if interval_end - interval_start != 3600:
            return "unknown"

        if interval_start > covered_until:
            return "unknown"

        interval_rain = rain[index + 1]
        interval_wind = max(wind[index], wind[index + 1])

        if requires_weather_review(
            booking,
            interval_rain,
            interval_wind,
            policy=policy,
        ):
            review_required = True

        covered_until = min(interval_end, end)

    if covered_until < end:
        return "unknown"

    if review_required:
        return "review_required"

    return "not_required"

def find_indoor_alternatives(club, booking):
    alternatives = []
    bookings = club.get_bookings()

    for court in club.get_courts():
        if court.weather_exposed:
            continue

        if not club.is_court_operational(court.court_id):
            continue

        available = True

        for existing in bookings:
            if existing.status != "confirmed":
                continue

            if existing.court.court_id != court.court_id:
                continue

            if (
                booking.start_time < existing.end_time
                and existing.start_time < booking.end_time
            ):
                available = False
                break

        if available:
            alternatives.append(court)

    return alternatives

def review_booking_weather(club, booking, forecast, policy=None):
    if club.get_booking(booking.booking_id) is not booking:
        raise ValueError("Booking must be registered in this club")

    if booking.status != "confirmed":
        raise ValueError("Only confirmed bookings can be reviewed")

    assessment = assess_booking_weather(
        booking,
        forecast,
        policy=policy,
    )

    alternatives = []

    if assessment in ("review_required", "unknown"):
        booking.mark_for_review()
        alternatives = find_indoor_alternatives(club, booking)

    return {
        "assessment": assessment,
        "requires_review": booking.requires_review,
        "alternative_court_ids": [
            court.court_id for court in alternatives
        ],
    }