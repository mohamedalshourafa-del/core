"""Test the TIS Control switches."""

from unittest.mock import MagicMock, patch

import pytest
from syrupy.assertion import SnapshotAssertion
from tis_smartbus import OpCode

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry, snapshot_platform

RELAY_5 = "switch.plant_room_rcu_channel_5"


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, mock_gateway: MagicMock, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the integration with only the switch platform."""
    mock_config_entry.add_to_hass(hass)
    with patch("homeassistant.components.tis_control.PLATFORMS", [Platform.SWITCH]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    return mock_config_entry


async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    setup_entry: MockConfigEntry,
) -> None:
    """Test the switch entities."""
    await snapshot_platform(hass, entity_registry, snapshot, setup_entry.entry_id)


@pytest.mark.usefixtures("setup_entry")
async def test_turn_on_off(hass: HomeAssistant, mock_gateway: MagicMock) -> None:
    """Test opening and closing a relay."""
    assert hass.states.get(RELAY_5).state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: RELAY_5}, blocking=True
    )
    mock_gateway.set_channel.assert_called_with(4, 200, 5, 0)
    assert hass.states.get(RELAY_5).state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: RELAY_5}, blocking=True
    )
    mock_gateway.set_channel.assert_called_with(4, 200, 5, 100)
    assert hass.states.get(RELAY_5).state == STATE_ON


@pytest.mark.usefixtures("setup_entry")
async def test_state_pushed_from_the_bus(
    hass: HomeAssistant, mock_gateway: MagicMock
) -> None:
    """A wall switch opens relay 5: the module announces [channel, 0xF8, level]."""
    mock_gateway.push((4, 200), OpCode.SINGLE_CHANNEL_REPLY, bytes.fromhex("05f800"))
    await hass.async_block_till_done()
    assert hass.states.get(RELAY_5).state == STATE_OFF
