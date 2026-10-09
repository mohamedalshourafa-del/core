"""Switch platform for TIS Control relay channels."""

from typing import Any, override

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TISConfigEntry
from .entity import TISEntity, specs_for

# Commands are single UDP datagrams and state is pushed, so nothing needs throttling.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TISConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TIS Control switches."""
    hub = entry.runtime_data
    async_add_entities(TISSwitch(hub, spec) for spec in specs_for(hub, Platform.SWITCH))


class TISSwitch(TISEntity, SwitchEntity):
    """A relay channel."""

    @property
    @override
    def is_on(self) -> bool:
        """Return true if the relay is closed."""
        return bool(self.level)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Close the relay."""
        self._set(100)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Open the relay."""
        self._set(0)

    def _set(self, level: int) -> None:
        self.hub.gateway.set_channel(*self.address, self.channel, level)
        # The module confirms on the bus within ~0.1 s; show the new state right away.
        self.hub.set_level((*self.address, self.channel), level)
        self.async_write_ha_state()
