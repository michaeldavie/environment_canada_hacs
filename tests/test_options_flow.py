"""Test the Environment Canada options flow."""

from typing import Any
from unittest.mock import patch

from custom_components.environment_canada.const import (
    CONF_RADAR_COLORS,
    CONF_RADAR_DURATION,
    CONF_RADAR_FPS,
    CONF_RADAR_FUTURE_MINUTES,
    CONF_RADAR_INTERPOLATION,
    CONF_RADAR_LAYER,
    CONF_RADAR_LEGEND,
    CONF_RADAR_OPACITY,
    CONF_RADAR_RADIUS,
    CONF_RADAR_TIMESTAMP,
    CONF_RADAR_WEBP,
    DEFAULT_RADAR_COLORS,
    DEFAULT_RADAR_DURATION,
    DEFAULT_RADAR_FPS,
    DEFAULT_RADAR_FUTURE_MINUTES,
    DEFAULT_RADAR_INTERPOLATION,
    DEFAULT_RADAR_LAYER,
    DEFAULT_RADAR_LEGEND,
    DEFAULT_RADAR_OPACITY,
    DEFAULT_RADAR_RADIUS,
    DEFAULT_RADAR_TIMESTAMP,
    DEFAULT_RADAR_WEBP,
    DOMAIN,
    SECTION_IMAGE,
    SECTION_MAP,
    SECTION_RADAR,
    SECTION_TIME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import init_integration


def _section_field_names(data_schema, section_key: str) -> set[str]:
    """Return the field names nested inside a given section of a data schema."""
    for key, value in data_schema.schema.items():
        if str(key) == section_key:
            return {str(inner_key) for inner_key in value.schema.schema}
    raise KeyError(section_key)


def _section_defaults(data_schema, section_key: str) -> dict[str, Any]:
    """Return the default values nested inside a given section of a data schema."""
    for key, value in data_schema.schema.items():
        if str(key) == section_key:
            return {
                str(inner_key): inner_key.default()
                for inner_key in value.schema.schema
                if hasattr(inner_key, "default")
            }
    raise KeyError(section_key)


async def test_options_flow_shows_defaults(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test options flow renders with library defaults when no options are set."""
    config_entry = await init_integration(hass, ec_data)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    data_schema = result["data_schema"]
    assert {str(k) for k in data_schema.schema} == {
        SECTION_MAP,
        SECTION_RADAR,
        SECTION_TIME,
        SECTION_IMAGE,
    }
    assert _section_field_names(data_schema, SECTION_MAP) == {CONF_RADAR_RADIUS}
    assert _section_field_names(data_schema, SECTION_RADAR) == {
        CONF_RADAR_LAYER,
        CONF_RADAR_COLORS,
        CONF_RADAR_OPACITY,
        CONF_RADAR_LEGEND,
    }
    assert _section_field_names(data_schema, SECTION_TIME) == {
        CONF_RADAR_DURATION,
        CONF_RADAR_FUTURE_MINUTES,
        CONF_RADAR_TIMESTAMP,
    }
    assert _section_field_names(data_schema, SECTION_IMAGE) == {
        CONF_RADAR_INTERPOLATION,
        CONF_RADAR_FPS,
        CONF_RADAR_WEBP,
    }


async def test_options_flow_saves_options(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test that submitting options saves them, flattened, to config_entry.options."""
    config_entry = await init_integration(hass, ec_data)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    submitted = {
        SECTION_MAP: {CONF_RADAR_RADIUS: 100},
        SECTION_RADAR: {
            CONF_RADAR_LAYER: "rain",
            CONF_RADAR_COLORS: "8",
            CONF_RADAR_OPACITY: 30,
            CONF_RADAR_LEGEND: False,
        },
        SECTION_TIME: {
            CONF_RADAR_DURATION: 30,
            CONF_RADAR_FUTURE_MINUTES: 15,
            CONF_RADAR_TIMESTAMP: False,
        },
        SECTION_IMAGE: {
            CONF_RADAR_INTERPOLATION: True,
            CONF_RADAR_FPS: 10,
            CONF_RADAR_WEBP: True,
        },
    }
    with patch(
        "custom_components.environment_canada.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], submitted
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_RADAR_RADIUS: 100,
        CONF_RADAR_LAYER: "rain",
        CONF_RADAR_COLORS: "8",
        CONF_RADAR_OPACITY: 30,
        CONF_RADAR_LEGEND: False,
        CONF_RADAR_DURATION: 30,
        CONF_RADAR_FUTURE_MINUTES: 15,
        CONF_RADAR_TIMESTAMP: False,
        CONF_RADAR_INTERPOLATION: True,
        CONF_RADAR_FPS: 10,
        CONF_RADAR_WEBP: True,
    }


async def test_options_flow_uses_existing_options_as_defaults(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test options flow pre-fills with previously saved (flat) option values."""
    saved_options = {
        CONF_RADAR_LAYER: "snow",
        CONF_RADAR_LEGEND: False,
        CONF_RADAR_TIMESTAMP: True,
        CONF_RADAR_OPACITY: 50,
        CONF_RADAR_RADIUS: 300,
        CONF_RADAR_DURATION: 60,
        CONF_RADAR_FPS: 15,
        CONF_RADAR_COLORS: "8",
        CONF_RADAR_INTERPOLATION: True,
        CONF_RADAR_WEBP: True,
        CONF_RADAR_FUTURE_MINUTES: 30,
    }
    config_entry = await init_integration(hass, ec_data, options=saved_options)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    data_schema = result["data_schema"]
    map_defaults = _section_defaults(data_schema, SECTION_MAP)
    radar_defaults = _section_defaults(data_schema, SECTION_RADAR)
    time_defaults = _section_defaults(data_schema, SECTION_TIME)
    image_defaults = _section_defaults(data_schema, SECTION_IMAGE)

    assert map_defaults[CONF_RADAR_RADIUS] == 300
    assert radar_defaults[CONF_RADAR_LAYER] == "snow"
    assert radar_defaults[CONF_RADAR_LEGEND] is False
    assert radar_defaults[CONF_RADAR_OPACITY] == 50
    assert radar_defaults[CONF_RADAR_COLORS] == "8"
    assert time_defaults[CONF_RADAR_DURATION] == 60
    assert time_defaults[CONF_RADAR_FUTURE_MINUTES] == 30
    assert time_defaults[CONF_RADAR_TIMESTAMP] is True
    assert image_defaults[CONF_RADAR_INTERPOLATION] is True
    assert image_defaults[CONF_RADAR_FPS] == 15
    assert image_defaults[CONF_RADAR_WEBP] is True


async def _setup_entry_with_options(
    hass: HomeAssistant, ec_data: dict[str, Any], options: dict
) -> Any:
    """Set up the integration with specific options, capturing ECMap call args."""
    from unittest.mock import AsyncMock, MagicMock

    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.environment_canada.const import CONF_STATION, DOMAIN
    from homeassistant.const import CONF_LANGUAGE, CONF_LATITUDE, CONF_LONGITUDE

    fixture = {
        CONF_LATITUDE: 55.55,
        CONF_LONGITUDE: 42.42,
        CONF_STATION: "XX/1234567",
        CONF_LANGUAGE: "Gibberish",
    }

    def mock_ec():
        m = MagicMock()
        m.station_id = fixture[CONF_STATION]
        m.lat = fixture[CONF_LATITUDE]
        m.lon = fixture[CONF_LONGITUDE]
        m.language = fixture[CONF_LANGUAGE]
        m.update = AsyncMock()
        return m

    radar_mock = mock_ec()
    radar_mock.image = b"GIF..."
    radar_mock.timestamp = ec_data["metadata"].timestamp
    radar_mock.layer = "precip_type"
    radar_mock.metadata = {"attribution": "Data provided by Environment Canada"}
    radar_mock.clear_cache = MagicMock()

    weather_mock = mock_ec()
    weather_mock.conditions = ec_data["conditions"]
    weather_mock.alerts = ec_data["alerts"]
    weather_mock.daily_forecasts = ec_data["daily_forecasts"]
    weather_mock.hourly_forecasts = ec_data["hourly_forecasts"]
    weather_mock.metadata = ec_data["metadata"]

    ecmap_mock = MagicMock(return_value=radar_mock)

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=fixture, title="Home", options=options
    )
    config_entry.add_to_hass(hass)

    with (
        patch("custom_components.environment_canada.ECWeather", return_value=weather_mock),
        patch("custom_components.environment_canada.ECAirQuality", return_value=mock_ec()),
        patch("custom_components.environment_canada.ECMap", ecmap_mock),
        patch("custom_components.environment_canada.config_flow.ECWeather", return_value=weather_mock),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return ecmap_mock


async def test_ecmap_created_with_options(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test ECMap is instantiated with option values on setup."""
    options = {
        CONF_RADAR_LAYER: "snow",
        CONF_RADAR_LEGEND: False,
        CONF_RADAR_TIMESTAMP: False,
        CONF_RADAR_OPACITY: 40,
        CONF_RADAR_RADIUS: 150,
        CONF_RADAR_DURATION: 30,
        CONF_RADAR_FPS: 10,
        CONF_RADAR_COLORS: "8",
        CONF_RADAR_INTERPOLATION: True,
        CONF_RADAR_WEBP: True,
        CONF_RADAR_FUTURE_MINUTES: 20,
    }

    mock_ecmap = await _setup_entry_with_options(hass, ec_data, options)

    mock_ecmap.assert_called_once()
    call_kwargs = mock_ecmap.call_args.kwargs
    assert call_kwargs["layer"] == "snow"
    assert call_kwargs["legend"] is False
    assert call_kwargs["timestamp"] is False
    assert call_kwargs["layer_opacity"] == 40
    assert call_kwargs["radius"] == 150
    assert call_kwargs["loop_minutes"] == 30
    assert call_kwargs["fps"] == 10
    assert call_kwargs["colors"] == 8
    assert call_kwargs["interpolation"] is True
    assert call_kwargs["webp"] is True
    assert call_kwargs["future_minutes"] == 20


async def test_ecmap_created_with_defaults_when_no_options(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test ECMap is instantiated with default values when no options are set."""
    mock_ecmap = await _setup_entry_with_options(hass, ec_data, {})

    mock_ecmap.assert_called_once()
    call_kwargs = mock_ecmap.call_args.kwargs
    assert call_kwargs["layer"] == DEFAULT_RADAR_LAYER
    assert call_kwargs["legend"] == DEFAULT_RADAR_LEGEND
    assert call_kwargs["timestamp"] == DEFAULT_RADAR_TIMESTAMP
    assert call_kwargs["layer_opacity"] == DEFAULT_RADAR_OPACITY
    assert call_kwargs["radius"] == DEFAULT_RADAR_RADIUS
    assert call_kwargs["loop_minutes"] == DEFAULT_RADAR_DURATION
    assert call_kwargs["fps"] == DEFAULT_RADAR_FPS
    assert call_kwargs["colors"] == int(DEFAULT_RADAR_COLORS)
    assert call_kwargs["interpolation"] == DEFAULT_RADAR_INTERPOLATION
    assert call_kwargs["webp"] == DEFAULT_RADAR_WEBP
    assert call_kwargs["future_minutes"] == DEFAULT_RADAR_FUTURE_MINUTES
