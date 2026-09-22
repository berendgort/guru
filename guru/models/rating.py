"""Windguru star rating -- mirrors site defaults from Preferences.

Windguru does not publish a closed-form formula in Help, but the free
Preferences UI exposes the defaults used for the forecast-table stars:

- 1 star if average wind ≥ ``limit1`` (default **10.6** kt)
- 2 stars if average wind ≥ ``limit2`` (default **15.6** kt)
- 3 stars if average wind ≥ ``limit3`` (default **19.4** kt)
- Stars render **blue** when air temp < ``tlimit`` (default **10** °C)

Sources: https://www.windguru.cz/forms/preferences.php (guest defaults),
community guides (stars ≈ wind strength for wind/kite; not a surf score).
"""

from __future__ import annotations

__all__ = (
    "DEFAULT_LIMIT_1_KN",
    "DEFAULT_LIMIT_2_KN",
    "DEFAULT_LIMIT_3_KN",
    "DEFAULT_TEMP_BLUE_C",
    "WindguruRating",
    "windguru_rating",
)

from dataclasses import dataclass

# Guest defaults from Windguru Preferences → "Windguru star rating"
DEFAULT_LIMIT_1_KN = 10.6
DEFAULT_LIMIT_2_KN = 15.6
DEFAULT_LIMIT_3_KN = 19.4
DEFAULT_TEMP_BLUE_C = 10.0


@dataclass(frozen=True)
class WindguruRating:
    stars: int  # 0-3
    cold: bool  # blue stars on the site
    wind_kn: float | None
    temp_c: float | None

    @property
    def label(self) -> str:
        if self.stars <= 0:
            return "-"
        marks = "★" * self.stars
        return f"{marks} cold" if self.cold else marks

    @property
    def ascii(self) -> str:
        """Pipe-safe form for narrow terminals / logs."""
        if self.stars <= 0:
            return "0"
        return f"{self.stars}{'c' if self.cold else ''}"


def windguru_rating(
    wind_kn: float | None,
    temp_c: float | None = None,
    *,
    limit1: float = DEFAULT_LIMIT_1_KN,
    limit2: float = DEFAULT_LIMIT_2_KN,
    limit3: float = DEFAULT_LIMIT_3_KN,
    tlimit: float = DEFAULT_TEMP_BLUE_C,
) -> WindguruRating:
    """Compute Windguru-style stars from average wind (knots) + air temp."""
    stars = 0
    if wind_kn is not None:
        if wind_kn >= limit3:
            stars = 3
        elif wind_kn >= limit2:
            stars = 2
        elif wind_kn >= limit1:
            stars = 1
    cold = temp_c is not None and temp_c < tlimit and stars > 0
    return WindguruRating(
        stars=stars, cold=cold, wind_kn=wind_kn, temp_c=temp_c
    )
