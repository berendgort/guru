# Wire notes — Windguru `iapi.php`

Captured 2026-09-22 via Cursor browser on `https://www.windguru.cz/201` + direct HTTP.

## Principle (same as fli)

SPA loads forecast through **`/int/iapi.php`**. Drive that JSON. Optional text surface: [micro.windguru.cz](https://micro.windguru.cz/help.php).

## Hosts

| Host | Role |
|------|------|
| `https://www.windguru.cz/int/iapi.php` | Search, `forecast_spot`, simple `forecast` |
| `https://www.windguru.net/int/iapi.php` | SPA multi-model `forecast` with `rundef` + `cache_index` |

Always send **`Referer: https://www.windguru.cz/{id_spot}`** (or `/` for search).

## Working queries (v0.1)

### `q=search_spots&search=…`
`{ count, spots: [{ id_spot, spotname, country, nickname? }] }`

### `q=forecast_spot&id_spot=…`
`spots["201"]` → `spotname`, `lat`, `lon`, `alt`, `models`  
`tabs[0].id_model_arr` → per-model `rundef`, `cache_index` (for SPA form)

### `q=forecast&id_spot=…&id_model=3`
Top-level: `lat`, `lon`, `alt`, `sunrise`, `sunset`, **`fcst`**

`fcst` parallel arrays (wind in **knots**):
`hours`, `WINDSPD`, `GUST`, `WINDDIR`, `TMP`/`TMPE`, `APCP`/`APCP1`, `TCDC`, `RH`, `initstamp`, `initdate`

### SPA form (next if simple breaks — fli `_tfs` lesson)
```
https://www.windguru.net/int/iapi.php?q=forecast
  &id_model=3&rundef=…&id_spot=201&WGCACHEABLE=21600&cache_index=…
```

## Models (partial)

| Name | id_model |
|------|----------|
| GFS 13 km | 3 |
| ICON (seen on 201) | 117 |
| others | 52, 109, 107, 21, 45, 84, … |

## Rate limits

Unknown. Act human; backoff on errors.
