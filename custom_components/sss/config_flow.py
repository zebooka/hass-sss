"""Config flow for Saved Snapshot Size."""

from homeassistant import config_entries

from .const import DOMAIN


class SavedSnapshotSizeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Allow one instance of the service."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the configuration entry without additional settings."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Saved Snapshot Size", data={})
