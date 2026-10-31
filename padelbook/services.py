class WeatherPolicy:
    def requires_review(self, rain_mm, wind_kmh):
        raise NotImplementedError("Weather policy must define review rules")


class NormalWeatherPolicy(WeatherPolicy):
    def requires_review(self, rain_mm, wind_kmh):
        return rain_mm >= 1 or wind_kmh >= 35


def requires_weather_review(booking, rain_mm, wind_kmh, policy=None):
    if not booking.court.weather_exposed:
        return False

    if policy is None:
        policy = NormalWeatherPolicy()

    return policy.requires_review(rain_mm, wind_kmh)