import asyncio
import time

from padelbook.async_services import (
    fetch_forecasts_serial,
    fetch_forecasts_parallel,
)


class SimulatedWeatherClient:
    def get_hourly_forecast(self, latitude, longitude):
        time.sleep(0.4)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": {
                "time": [1793440800],
                "rain": [0.0],
                "wind_speed_10m": [10.0],
            },
        }


async def main():
    locations = [
        (32.0853, 34.7818),
        (31.7683, 35.2137),
        (32.7940, 34.9896),
    ]
    client = SimulatedWeatherClient()

    started = time.perf_counter()
    serial = await fetch_forecasts_serial(locations, client)
    serial_seconds = time.perf_counter() - started

    started = time.perf_counter()
    parallel = await fetch_forecasts_parallel(locations, client)
    parallel_seconds = time.perf_counter() - started

    assert serial == parallel
    assert len(parallel) == 3

    print("Source: simulated requests, 0.4 seconds each")
    print(f"Independent requests: {len(locations)}")
    print(f"Serial time: {serial_seconds:.3f} seconds")
    print(f"Parallel time: {parallel_seconds:.3f} seconds")
    print(f"Same ordered results: {serial == parallel}")


if __name__ == "__main__":
    asyncio.run(main())