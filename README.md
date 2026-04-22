# Environment Canada for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/michaeldavie/environment_canada_hacs/actions/workflows/validate.yaml/badge.svg)](https://github.com/michaeldavie/environment_canada_hacs/actions/workflows/validate.yaml)
[![Tests](https://github.com/michaeldavie/environment_canada_hacs/actions/workflows/tests.yaml/badge.svg)](https://github.com/michaeldavie/environment_canada_hacs/actions/workflows/tests.yaml)

Meteorological data for Canadian locations from [Environment and Climate Change Canada](https://weather.gc.ca/index_e.html).

This custom component provides the same functionality as the built-in `environment_canada` integration, plus features from pending pull requests that have not yet been merged into Home Assistant core.

**Features beyond the built-in integration:**

- **Precip Type radar layer** — shows precipitation type classification in addition to rain and snow layers (from [core PR #161602](https://github.com/home-assistant/core/pull/161602))
- **Richer alert data** — a single `alerts` sensor replaces the five separate category sensors; each alert exposes title, colour, area, text, status, confidence, impact, and more (from [core PR #164481](https://github.com/home-assistant/core/pull/164481))
- **Configurable radar camera** — radar type, legend, timestamp, opacity, and map radius are all adjustable from the integration's Configure dialog

---

## Installation

### Via HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaeldavie&repository=environment_canada_hacs&category=integration)

1. Click the button above, or open HACS in your Home Assistant instance, go to **Integrations**, click **⋮ → Custom repositories**, and add `michaeldavie/environment_canada_hacs` as an Integration.
2. Search for **Environment Canada** and install it.
3. Restart Home Assistant.

### Manual

1. Copy the `custom_components/environment_canada` directory into your `<config>/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

After installation, add the integration via **Settings → Devices & Services → Add Integration → Environment Canada**.

### Location selection

Choose your weather location using either:

- **Station selector** — select a station from a dropdown of all Environment Canada weather stations.
- **Coordinates** — provide latitude and longitude to automatically use the nearest station (defaults to your Home Assistant location).

---

## Migrating from the built-in integration

This custom component uses the same domain (`environment_canada`) and will replace the built-in integration. Before installing:

1. Go to **Settings → Devices & Services** and remove the existing Environment Canada integration.
2. Install this custom component and restart Home Assistant.
3. Re-add the integration via **Add Integration**.

> **Note:** Your entity IDs will be the same after re-adding, so most automations and dashboards will continue working. The one exception is the alert sensors — see below.

### Alert sensor migration

The five separate alert category sensors have been replaced by a single combined `sensor.<name>_alerts` entity. If you have automations or dashboard cards that reference the old entity IDs, update them as follows:

| Old entity | Replacement |
|---|---|
| `sensor.<name>_advisories` | `sensor.<name>_alerts` filtered by `type == 'advisory'` |
| `sensor.<name>_warnings` | `sensor.<name>_alerts` filtered by `type == 'warning'` |
| `sensor.<name>_watches` | `sensor.<name>_alerts` filtered by `type == 'watch'` |
| `sensor.<name>_statements` | `sensor.<name>_alerts` filtered by `type == 'statement'` |
| `sensor.<name>_endings` | `sensor.<name>_alerts` filtered by `type == 'ending'` |

To replicate an old per-category count (e.g. warnings), use a template:

```yaml
{{ state_attr('sensor.NAME_alerts', 'alerts')
   | selectattr('type', 'eq', 'warning')
   | list | count }}
```

---

## Entities

### Weather

Current conditions, daily forecast, and hourly forecast.

### Radar map (camera)

A loop of radar imagery from the last 3 hours. This entity is **disabled by default** — enable it from the entity's settings dialog.

The camera is configurable via **Settings → Devices & Services → Environment Canada → Configure**:

| Option | Default | Description |
|---|---|---|
| Radar type | Precipitation type | `Rain`, `Snow`, or `Precipitation type` |
| Show legend | On | Toggle the colour legend overlay |
| Show timestamp | On | Toggle the timestamp overlay |
| Radar opacity | 65 | Opacity of the radar layer (0–100) |
| Map radius | 200 km | Radius of the radar map |

Changes take effect immediately after saving (the integration reloads automatically).

The radar type can also be changed at runtime without a reload using the `environment_canada.set_radar_type` action (see [Actions](#actions) below).

### Sensors

#### Conditions and forecasts

- Current condition
- Forecast summary
- [Icon code](https://dd.weather.gc.ca/today/citypage_weather/docs/Current_Conditions_Icons-Icones_conditions_actuelles.pdf)
- Barometric pressure
- Pressure tendency
- Humidity
- Visibility
- UV index
- Air quality health index (AQHI)

#### Temperature

- Temperature
- Forecast high temperature
- Forecast low temperature
- Dewpoint
- Wind chill (only below 0 °C)
- Humidex (only above 19 °C)

#### Wind

- Wind speed
- Wind gust
- Wind direction
- Wind bearing

#### Precipitation

- Probability of precipitation

#### Alerts

- **Alerts** — total count of active alerts across all categories. The `alerts` attribute contains a list of all active alerts. Each alert may include:

  | Field | Description |
  |---|---|
  | `title` | Alert name |
  | `issued` | Publication datetime |
  | `color` | Risk colour level (e.g. `yellow`, `red`) |
  | `expiry` | Expiration datetime |
  | `url` | Link to the full alert text |
  | `text` | Full alert text (WFS source only) |
  | `area` | Geographic area name (WFS source only) |
  | `status` | Alert status, e.g. `active` (WFS source only) |
  | `confidence` | Confidence level (WFS source only) |
  | `impact` | Impact description (WFS source only) |
  | `alert_code` | Alert code (WFS source only) |
  | `type` | Alert type: `advisory`, `warning`, `watch`, `statement`, or `ending` |

  WFS-only fields are omitted when the integration falls back to XML parsing.

---

## Solving problems

### Service interruptions

Although infrequent, there have been some outages of the Environment Canada service. If you see errors similar to the one below, check the [Environment Canada mailing list](https://comm.collab.science.gc.ca/mailman3/hyperkitty/list/dd_info@comm.collab.science.gc.ca/) for known issues before opening a report.

```
2022-10-05 12:25:08 ERROR Timeout fetching environment_canada weather data
```

### Sensor `unavailable` or `unknown`

Not all stations provide a complete set of data. Browse the [raw XML for your station](https://dd.weather.gc.ca/today/citypage_weather/) to see what data is available.

---

## Template sensors

Replace `NAME` with the name of your weather or sensor entity.

### Feels like

```yaml
template:
  - sensor:
      - name: "Feels Like"
        device_class: temperature
        unit_of_measurement: "°C"
        state: >
          {% if not is_state('sensor.NAME_humidex', 'unknown') %}
            {{ states('sensor.NAME_humidex') }}
          {% elif not is_state('sensor.NAME_wind_chill', 'unknown') %}
            {{ states('sensor.NAME_wind_chill') }}
          {% else %}
            {{ states('sensor.NAME_temperature') | round(0) }}
          {% endif %}
```

### Additional forecast data

```yaml
template:
  - trigger:
      - platform: time_pattern
        hours: "/4"
      - platform: homeassistant
        event: start
      - platform: event
        event_type: event_template_reloaded
    actions:
      - action: environment_canada.get_forecasts
        target:
          entity_id: weather.NAME
        response_variable: forecasts
    sensor:
      - name: Weather Forecast Daily
        unique_id: weather_forecast_daily
        state: "{{ states('weather.NAME') }}"
        attributes:
          daily: "{{ forecasts['weather.NAME']['daily_forecast'] }}"
          hourly: "{{ forecasts['weather.NAME']['hourly_forecast'] }}"
          summary: "{{ forecasts['weather.NAME']['daily_forecast'][0]['text_summary'] }}"
          temperature_unit: "{{ state_attr('weather.NAME', 'temperature_unit') }}"
```

### Alert count by category

```yaml
{{ state_attr('sensor.NAME_alerts', 'alerts')
   | selectattr('type', 'eq', 'warning')
   | list | count }}
```

### Active alert titles

```yaml
{{ state_attr('sensor.NAME_alerts', 'alerts')
   | map(attribute='title')
   | list | join(', ') }}
```

---

## Actions

### `environment_canada.get_forecasts`

Returns the raw Environment Canada forecast data (both `daily_forecast` and `hourly_forecast`).

| Parameter | Description |
|---|---|
| `entity_id` | The weather entity to get the forecast for |

### `environment_canada.set_radar_type`

Sets the radar layer for the camera entity.

| Parameter | Description |
|---|---|
| `entity_id` | The camera entity to update |
| `radar_type` | One of `Auto`, `Rain`, `Snow`, or `Precip Type` |

`Auto` selects **Rain** from April through October and **Snow** from November through March.
