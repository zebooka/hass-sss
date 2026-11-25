"""Tests for the snapshot action using the Home Assistant service registry."""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
import voluptuous as vol
from homeassistant.components import camera
from homeassistant.core import Context, HomeAssistant
from homeassistant.data_entry_flow import AbortFlow, FlowResultType
from homeassistant.exceptions import HomeAssistantError, Unauthorized, UnknownUser

sys.path.insert(0, "/config")
from custom_components.sss import async_setup_entry, async_unload_entry
from custom_components.sss.config_flow import SavedSnapshotSizeConfigFlow


def run(coro):
    """Run each test without a pytest async plugin."""
    return asyncio.run(coro)


async def setup_hass(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.config.allowlist_external_dirs.add(str(tmp_path))
    await async_setup_entry(hass, None)
    return hass


def test_config_flow_creates_single_entry(tmp_path):
    async def test():
        hass = HomeAssistant(str(tmp_path))
        entry_lookup = Mock(return_value=None)
        hass.config_entries = SimpleNamespace(
            flow=SimpleNamespace(async_progress_by_handler=Mock(return_value=[])),
            async_entry_for_domain_unique_id=entry_lookup,
        )
        flow = SavedSnapshotSizeConfigFlow()
        flow.hass = hass
        flow.context = {"source": "user"}
        flow.flow_id = "test"
        result = await flow.async_step_user()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Saved Snapshot Size"
        assert result["data"] == {}

        entry_lookup.return_value = SimpleNamespace(source="user")
        second_flow = SavedSnapshotSizeConfigFlow()
        second_flow.hass = hass
        second_flow.context = {"source": "user"}
        second_flow.flow_id = "second"
        with pytest.raises(AbortFlow) as err:
            await second_flow.async_step_user()
        assert err.value.reason == "already_configured"

    run(test())


def test_snapshot_saves_camera_image_with_options(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)
        cam = SimpleNamespace(
            use_stream_for_stills=False,
            async_camera_image=AsyncMock(return_value=b"image bytes"),
            content_type="image/png",
        )
        filename = tmp_path / "nested" / "snapshot.jpg"
        with patch.object(camera, "get_camera_from_entity_id", return_value=cam):
            await hass.services.async_call(
                "sss", "snapshot",
                {"entity_id": "camera.door", "filename": str(filename),
                 "width": 640, "height": 480, "timeout": 3},
                blocking=True,
            )
        assert filename.read_bytes() == b"image bytes"
        cam.async_camera_image.assert_awaited_once_with(width=640, height=480)
        await async_unload_entry(hass, None)
        assert not hass.services.has_service("sss", "snapshot")

    run(test())


def test_snapshot_defaults_and_filename_template(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)
        filename = tmp_path / "snapshot.jpg"
        filename.write_bytes(b"old")
        image = SimpleNamespace(content=b"new")
        with patch("custom_components.sss.async_get_image", new=AsyncMock(return_value=image)) as get_image:
            await hass.services.async_call(
                "sss", "snapshot",
                {"entity_id": "camera.door", "filename": str(tmp_path / "{{ 'snapshot' }}.jpg")},
                blocking=True,
            )
        get_image.assert_awaited_once_with(hass, "camera.door", timeout=10, width=None, height=None)
        assert filename.read_bytes() == b"new"

    run(test())


@pytest.mark.parametrize("field,value", [
    ("width", 0), ("width", -1), ("height", 0), ("timeout", 0),
    ("timeout", "invalid"), ("width", 1.5), ("height", True),
    ("entity_id", "light.lamp"), ("entity_id", ["camera.one", "camera.two"]),
])
def test_invalid_input_is_rejected(tmp_path, field, value):
    async def test():
        hass = await setup_hass(tmp_path)
        data = {"entity_id": "camera.door", "filename": str(tmp_path / "snapshot.jpg"), field: value}
        with pytest.raises(vol.Invalid):
            await hass.services.async_call("sss", "snapshot", data, blocking=True)

    run(test())


def test_path_is_checked_before_camera_access(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)
        with patch("custom_components.sss.async_get_image", new=AsyncMock()) as get_image:
            with pytest.raises(HomeAssistantError, match="allowlist_external_dirs"):
                await hass.services.async_call(
                    "sss", "snapshot", {"entity_id": "camera.door", "filename": "/not-allowed/image.jpg"}, blocking=True
                )
        get_image.assert_not_awaited()

    run(test())


def test_camera_errors_do_not_overwrite_file(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)
        filename = tmp_path / "snapshot.jpg"
        filename.write_bytes(b"old")
        with patch("custom_components.sss.async_get_image", new=AsyncMock(side_effect=HomeAssistantError("camera failed"))):
            with pytest.raises(HomeAssistantError, match="camera failed"):
                await hass.services.async_call(
                    "sss", "snapshot", {"entity_id": "camera.door", "filename": str(filename)}, blocking=True
                )
        assert filename.read_bytes() == b"old"

    run(test())


def test_timeout_is_applied_to_camera(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)

        async def slow_image(**kwargs):
            await asyncio.sleep(5)
            return b"too late"

        cam = SimpleNamespace(
            use_stream_for_stills=False,
            async_camera_image=slow_image,
            content_type="image/png",
        )
        filename = tmp_path / "image.jpg"
        with patch.object(camera, "get_camera_from_entity_id", return_value=cam):
            with pytest.raises(HomeAssistantError):
                await hass.services.async_call(
                    "sss", "snapshot",
                    {"entity_id": "camera.door", "filename": str(filename), "timeout": 1},
                    blocking=True,
                )
        assert not filename.exists()

    run(test())


def test_authorized_user_can_take_snapshot(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)
        check_entity = Mock(return_value=True)
        user = SimpleNamespace(is_admin=False, permissions=SimpleNamespace(check_entity=check_entity))
        hass.auth = SimpleNamespace(async_get_user=AsyncMock(return_value=user))
        with patch("custom_components.sss.async_get_image", new=AsyncMock(return_value=SimpleNamespace(content=b"image"))):
            await hass.services.async_call(
                "sss", "snapshot", {"entity_id": "camera.door", "filename": str(tmp_path / "image.jpg")},
                blocking=True, context=Context(user_id="user"),
            )
        check_entity.assert_called_once_with("camera.door", "control")
        assert (tmp_path / "image.jpg").read_bytes() == b"image"

    run(test())


def test_write_error_is_reported(tmp_path):
    async def test():
        hass = await setup_hass(tmp_path)
        with patch("custom_components.sss.async_get_image", new=AsyncMock(return_value=SimpleNamespace(content=b"image"))):
            with patch("custom_components.sss._write_image", side_effect=OSError("disk full")):
                with pytest.raises(HomeAssistantError, match="disk full"):
                    await hass.services.async_call(
                        "sss", "snapshot", {"entity_id": "camera.door", "filename": str(tmp_path / "image.jpg")}, blocking=True
                    )

    run(test())


@pytest.mark.parametrize("user,exception", [
    (None, UnknownUser),
    (SimpleNamespace(is_admin=False, permissions=SimpleNamespace(check_entity=Mock(return_value=False))), Unauthorized),
])
def test_user_without_access_is_rejected(tmp_path, user, exception):
    async def test():
        hass = await setup_hass(tmp_path)
        hass.auth = SimpleNamespace(async_get_user=AsyncMock(return_value=user))
        with patch("custom_components.sss.async_get_image", new=AsyncMock()) as get_image:
            with pytest.raises(exception):
                await hass.services.async_call(
                    "sss", "snapshot", {"entity_id": "camera.door", "filename": str(tmp_path / "image.jpg")},
                    blocking=True, context=Context(user_id="user"),
                )
        get_image.assert_not_awaited()

    run(test())
