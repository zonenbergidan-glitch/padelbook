import math
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