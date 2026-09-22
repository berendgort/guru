# Wire — Windguru `iapi.php`

Public JSON the SPA uses. Drive these endpoints with `curl_cffi` + **Referer**. Never scrape HTML, Tune jBox, or MapLibre.

Captured 2026-09-22 (Castelldefels `201`, De Slufter `48309`). Fixtures under `fixtures/`.

## Hosts

| Base | Use |
|------|-----|
| `https://www.windguru.cz/int/iapi.php` | Search, simplemap, `forecast_spot`, `forecast`, `model_info_full` |
| `https://www.windguru.net/int/iapi.php` | SPA `forecast` with `rundef` + `cache_index` (fallback) |

| Call | Referer |
|------|---------|
| search / model_info | `https://www.windguru.cz/` |
| spot / forecast | `https://www.windguru.cz/{id_spot}` |
| simplemap | `https://www.windguru.cz/map/spot/` |

## Queries (free)

### `q=search_spots&search=…`

```json
{ "count": N, "spots": [{ "id_spot", "spotname", "country", "nickname?" }] }
```

Name search only — no lat/lon. CLI: `guru spots`.

### `q=spots&opt=simplemap&WGCACHEABLE=1800`

Same markers as the [spot map](https://www.windguru.cz/map/spot/):

```json
{ "count": N, "spots": [[id_spot, spotname, lat, lon], ...] }
```

~10k rows worldwide. CLI: `guru near --lat --lon`. No PRO.

### `q=forecast_spot&id_spot=…`

| Path | Content |
|------|---------|
| `spots["{id}"]` | name, lat/lon/alt, **`models`** (id_model list for that spot) |
| `tabs[0].blend` | **WINDGURU DEFAULT** (`id_blend_settings: 1`): `res_sensitivity`, `init_sensitivity`, `model_koef` |
| `tabs[0].id_model_arr` | per-model `rundef`, `cache_index`, `initstr` |

### `q=model_info_full`

Keyed by id string. Fields used by blend: `model_name`, `resolution`, `initstamp`, `priority`, `wave`, `virtual`.

### `q=forecast&id_spot=…&id_model=…`

Top-level + `fcst` parallel arrays (**knots**): `hours`, `WINDSPD`, `GUST`, `WINDDIR`, `TMP`/`TMPE`, `APCP`/`APCP1`, `TCDC`, `RH`, `initstamp`.

### Windguru rating (stars)

The free forecast JSON lists `RATING` in `default_vars` but does **not** return a `RATING` array — the SPA paints stars client-side. Same for `WCHILL` (listed in `default_vars`, not present as a free `fcst` array in captured fixtures). Suit chill uses Open-Meteo SST when available, else air + wind-speed proxy. Guest Preferences defaults (`/forms/preferences.php`):

| Stars | Min average wind (kt) |
|-------|------------------------|
| 1 | 10.6 |
| 2 | 15.6 |
| 3 | 19.4 |

Blue stars when air temp **< 10 °C** (`tlimit`). `guru` mirrors this in `guru.models.rating.windguru_rating` and attaches `rating` / `rating_stars` / `rating_cold` on each forecast hour and advice window.

Also returns `wgmodel` (resolution_real, initstamp) when needed for debugging.

### SPA fallback (if simple `forecast` dies)

```
GET …/windguru.net/int/iapi.php?q=forecast
  &id_model=3&rundef=…&id_spot=201&WGCACHEABLE=21600&cache_index=…
```

When simple `forecast` dies: prefer params from `forecast_spot` tab rows (`rundef`, etc.).

## WINDGURU DEFAULT weights

Port of SPA `di.calcSortByWeights` → `guru/search/blend.py`.

```
res_w[id]  = normalize( resolution ** (-2 * res_sensitivity) )
init_w[id] = normalize( ai(init_sensitivity, age_h) )
wgt_raw    = res_w * init_w * model_koef[id]
weight     = wgt_raw / Σ wgt_raw

ai(s, age) = max(0, 100*(age+4)^(-0.5*s) - 3*s*age)
age_h      = (max_initstamp - initstamp) / 3600
normalize  = scale so mean≈1, cap individual ≤1.5
```

Skip `wave`, `virtual`, and id `100` (WG Mix table). Sort weight desc, then `priority` asc. Product: **top 3**.

## Agent path

`spots` | `near` → `best` (preset locked) → ignore lower models.

## Fixtures

| File | Source |
|------|--------|
| `search_castelldefels.json` | `search_spots` |
| `forecast_spot_201.json` | Castelldefels |
| `forecast_spot_48309.json` | De Slufter |
| `model_info_full.json` | live catalog |
| `forecast_201_gfs.json` | GFS sample |
| `spots_simplemap_nl.json` | NL bbox subset of simplemap |

Refresh: `python scripts/capture_fixtures.py`

## Rate limits

Unknown. Retries via tenacity; prefer `WGCACHEABLE` on simplemap. Be polite.
