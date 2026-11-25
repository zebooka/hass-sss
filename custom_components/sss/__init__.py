"""Save camera snapshots with optional dimensions and timeout."""

import os

import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_CONTROL
from homeassistant.components.camera import async_get_image
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, CONF_FILENAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, Unauthorized, UnknownUser
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, SERVICE_SNAPSHOT

def _positive_integer(value: object) -> int:
    """Accept positive integers, including strings produced by templates."""
    if isinstance(value, bool) or not (
        isinstance(value, int) or isinstance(value, str) and value.isdecimal()
    ):
        raise vol.Invalid("expected a positive integer")
    value = int(value)
    if value < 1:
        raise vol.Invalid("expected a positive integer")
    return value


SNAPSHOT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_domain("camera"),
        vol.Required(CONF_FILENAME): cv.template,
        vol.Optional("width"): _positive_integer,
        vol.Optional("height"): _positive_integer,
        vol.Optional("timeout", default=10): _positive_integer,
    }
)


def _write_image(filename: str, image: bytes) -> None:
    """Create the destination directory and write the image off the event loop."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as image_file:
        image_file.write(image)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register the snapshot action."""

    async def async_snapshot(call: ServiceCall) -> None:
        entity_id = call.data[ATTR_ENTITY_ID]
        if call.context.user_id:
            user = await hass.auth.async_get_user(call.context.user_id)
            if user is None:
                raise UnknownUser(context=call.context)
            if not user.is_admin and not user.permissions.check_entity(
                entity_id, POLICY_CONTROL
            ):
                raise Unauthorized(
                    context=call.context, entity_id=entity_id, permission=POLICY_CONTROL
                )

        filename = call.data[CONF_FILENAME].async_render()
        if not await hass.async_add_executor_job(hass.config.is_allowed_path, filename):
            raise HomeAssistantError(
                f"Cannot write `{filename}`; configure allowlist_external_dirs "
                "in configuration.yaml if necessary"
            )

        image = await async_get_image(
            hass,
            entity_id,
            timeout=call.data["timeout"],
            width=call.data.get("width"),
            height=call.data.get("height"),
        )
        try:
            await hass.async_add_executor_job(_write_image, filename, image.content)
        except OSError as err:
            raise HomeAssistantError(f"Cannot write snapshot to `{filename}`: {err}") from err

    hass.services.async_register(DOMAIN, SERVICE_SNAPSHOT, async_snapshot, SNAPSHOT_SCHEMA)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove the snapshot action."""
    hass.services.async_remove(DOMAIN, SERVICE_SNAPSHOT)
    return True
