from time import perf_counter


class OperationTimer:
    def __init__(self, operation_name):
        if not isinstance(operation_name, str) or not operation_name.strip():
            raise ValueError("Operation name must be a non-empty string")

        self.operation_name = operation_name.strip()
        self._started_at = None
        self.elapsed_seconds = None

    def __enter__(self):
        self._started_at = perf_counter()
        self.elapsed_seconds = None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed_seconds = perf_counter() - self._started_at

        # החריגה ממשיכה החוצה לאחר סיום המדידה.
        return False