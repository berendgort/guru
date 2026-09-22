from importlib.metadata import PackageNotFoundError, version

from guru.models.blend import BestForecast, BlendWeight
from guru.models.forecast import Forecast, ForecastHour, Spot
from guru.search.blend import get_best_forecast
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import get_spot, resolve_spot, search_spots

try:
    __version__ = version("windguru")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.3.5"

__all__ = [
    "BestForecast",
    "BlendWeight",
    "Forecast",
    "ForecastHour",
    "Spot",
    "get_best_forecast",
    "get_forecast",
    "get_spot",
    "resolve_spot",
    "search_spots",
    "spots_near",
    "__version__",
]
