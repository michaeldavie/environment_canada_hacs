"""Test Environment Canada diagnostics."""

from http import HTTPStatus
from typing import Any

from syrupy.assertion import SnapshotAssertion

from custom_components.environment_canada.const import CONF_STATION
from homeassistant.const import CONF_LANGUAGE, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from . import init_integration

FIXTURE_USER_INPUT = {
    CONF_LATITUDE: 55.55,
    CONF_LONGITUDE: 42.42,
    CONF_STATION: "XX/1234567",
    CONF_LANGUAGE: "Gibberish",
}


async def get_diagnostics_for_config_entry(hass, hass_client, config_entry):
    """Return the diagnostics for a config entry."""
    client = await hass_client()
    response = await client.get(
        f"/api/diagnostics/config_entry/{config_entry.entry_id}"
    )
    assert response.status == HTTPStatus.OK
    return await response.json()


async def test_entry_diagnostics(
    hass: HomeAssistant,
    hass_client,
    snapshot: SnapshotAssertion,
    ec_data: dict[str, Any],
) -> None:
    """Test config entry diagnostics."""

    config_entry = await init_integration(hass, ec_data)
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, config_entry
    )

    assert diagnostics == snapshot
