def requires_weather_review(booking, rain_mm, wind_kmh):
    if not booking.court.weather_exposed:
        return False

    return rain_mm >= 1 or wind_kmh >= 35