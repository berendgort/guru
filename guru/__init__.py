from guru.models.forecast import Forecast, ForecastHour, Spot
from guru.search.forecast import get_forecast
from guru.search.spots import search_spots

__version__ = "0.1.0"

__all__ = [
    "Forecast",
    "ForecastHour",
    "Spot",
    "get_forecast",
    "search_spots",
    "__version__",
]
