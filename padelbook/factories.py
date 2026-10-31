from padelbook.models import OutdoorCourt, IndoorCourt


def create_court(court_type, court_id, name, hourly_rate):
    court_classes = {
        "outdoor": OutdoorCourt,
        "indoor": IndoorCourt,
    }

    if not isinstance(court_type, str):
        raise ValueError("Court type must be a string")

    court_class = court_classes.get(court_type)

    if court_class is None:
        raise ValueError("Unknown court type")

    return court_class(court_id, name, hourly_rate)