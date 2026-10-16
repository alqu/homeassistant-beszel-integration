"""Tests for Beszel integration setup and migration."""

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beszel import async_migrate_entry
from custom_components.beszel.const import DOMAIN


class TestBeszelMigration:
    """Exercise Beszel config-entry migrations."""

    async def test_future_config_version_is_rejected(self, hass):
        """A downgrade must not accept an unknown config-entry schema."""
        entry = MockConfigEntry(
            data={"future": "value"}, domain=DOMAIN, unique_id="future", version=3
        )
        assert not await async_migrate_entry(hass, entry)
        assert entry.data == {"future": "value"}
        assert entry.version == 3

    async def test_current_config_version_is_unchanged(self, hass):
        """Current config entries need no migration."""
        entry = MockConfigEntry(
            data={"host": "http://beszel.local"},
            domain=DOMAIN,
            unique_id="current",
            version=2,
        )
        assert await async_migrate_entry(hass, entry)
        assert entry.data == {"host": "http://beszel.local"}

    async def test_migrate_legacy_config_and_identifiers(self, hass):
        """Version one entries retain entities with scoped identifiers."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"Host": "beszel.local/", "Password": "password", "Username": "user"},
            unique_id="beszel.local/_user",
            version=1,
        )
        entry.add_to_hass(hass)
        entity_registry = er.async_get(hass)
        entity = entity_registry.async_get_or_create(
            "sensor", DOMAIN, "beszel_system_stats_cpu", config_entry=entry
        )
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id, identifiers={(DOMAIN, "system")}
        )
        assert await async_migrate_entry(hass, entry)
        migrated_entity = entity_registry.async_get(entity.entity_id)
        migrated_device = device_registry.async_get(device.id)
        assert entry.data == {
            "host": "http://beszel.local",
            "password": "password",
            "username": "user",
        }
        assert entry.unique_id == "http://beszel.local_user"
        assert entry.version == 2
        assert migrated_entity.unique_id == f"beszel_{entry.entry_id}_system_stats_cpu"
        assert migrated_device.identifiers == {(DOMAIN, f"{entry.entry_id}_system")}
