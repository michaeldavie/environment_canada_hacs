"""Common fixtures for Environment Canada tests."""

import contextlib
from datetime import datetime
import json
import os
from unittest.mock import PropertyMock, patch

from env_canada.ec_weather import MetaData
import pytest


def load_fixture(filename: str) -> str:
    """Load a fixture file from the fixtures directory."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(fixture_path) as f:
        return f.read()


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


@pytest.fixture
def entity_registry_enabled_by_default():
    """Enable all entities by default (removed from PHCC 0.13.316)."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        new_callable=PropertyMock,
        return_value=True,
    ):
        yield


@pytest.fixture
def ec_data():
    """Load Environment Canada data."""

    def data_hook(weather):
        """Convert timestamp string to datetime."""

        if t := weather.get("timestamp"):
            with contextlib.suppress(ValueError):
                weather["timestamp"] = datetime.fromisoformat(t)
        elif t := weather.get("period"):
            with contextlib.suppress(ValueError):
                weather["period"] = datetime.fromisoformat(t)
        if t := weather.get("metadata"):
            weather["metadata"] = MetaData(**t)
        return weather

    return json.loads(
        load_fixture("current_conditions_data.json"),
        object_hook=data_hook,
    )
