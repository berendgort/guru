from guru.models.forecast import wind_dir_cardinal
from guru.models.models import resolve_model


def test_wind_dir_cardinal() -> None:
    assert wind_dir_cardinal(0) == "N"
    assert wind_dir_cardinal(90) == "E"
    assert wind_dir_cardinal(None) == "-"


def test_resolve_model() -> None:
    assert resolve_model("gfs") == (3, "gfs")
    assert resolve_model(3)[0] == 3
