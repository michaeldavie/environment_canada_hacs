"""Test the Environment Canada options flow."""

from typing import Any
from unittest.mock import patch

from custom_components.environment_canada.const import (
    CONF_RADAR_LAYER,
    CONF_RADAR_LEGEND,
    CONF_RADAR_OPACITY,
    CONF_RADAR_RADIUS,
    CONF_RADAR_TIMESTAMP,
    DEFAULT_RADAR_LAYER,
    DEFAULT_RADAR_LEGEND,
    DEFAULT_RADAR_OPACITY,
    DEFAULT_RADAR_RADIUS,
    DEFAULT_RADAR_TIMESTAMP,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import init_integration


async def test_options_flow_shows_defaults(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test options flow renders with library defaults when no options are set."""
    config_entry = await init_integration(hass, ec_data)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    schema_keys = {str(k) for k in result["data_schema"].schema}
    assert CONF_RADAR_LAYER in schema_keys
    assert CONF_RADAR_LEGEND in schema_keys
    assert CONF_RADAR_TIMESTAMP in schema_keys
    assert CONF_RADAR_OPACITY in schema_keys
    assert CONF_RADAR_RADIUS in schema_keys


async def test_options_flow_saves_options(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test that submitting options saves them to config_entry.options."""
    config_entry = await init_integration(hass, ec_data)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    new_options = {
        CONF_RADAR_LAYER: "rain",
        CONF_RADAR_LEGEND: False,
        CONF_RADAR_TIMESTAMP: False,
        CONF_RADAR_OPACITY: 30,
        CONF_RADAR_RADIUS: 100,
    }
    with patch(
        "custom_components.environment_canada.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], new_options
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == new_options


async def test_options_flow_uses_existing_options_as_defaults(
    hass: HomeAssistant, ec_data: dict[str, Any]
) -> None:
    """Test options flow pre-fills with previously saved option values."""
    saved_options = {
        CONF_RADAR_LAYER: "snow",
        CONF_RADAR_LEGEND: False,
        CONF_RADAR_TIMESTAMP: True,
        CONF_RADAR_OPACITY: 50,
        CONF_RADAR_RADIUS: 300,
    }
    config_entry = await init_integration(hass, ec_data, options=saved_options)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    schema = result["data_schema"].schema
    defaults = {str(k): k.default() for k in schema if hasattr(k, "default")}

    assert defaults[CONF_RADAR_LAYER] == "snow"
    assert defaults[CONF_RADAR_LEGEND] is False
    assert defaults[CONF_RADAR_OPACITY] == 50
    assert defaults[CONF_RADAR_RADIUS] == 300


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
    }

    mock_ecmap = await _setup_entry_with_options(hass, ec_data, options)

    mock_ecmap.assert_called_once()
    call_kwargs = mock_ecmap.call_args.kwargs
    assert call_kwargs["layer"] == "snow"
    assert call_kwargs["legend"] is False
    assert call_kwargs["timestamp"] is False
    assert call_kwargs["layer_opacity"] == 40
    assert call_kwargs["radius"] == 150


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
