"""Tests for the Beszel config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beszel.api import BeszelApiAuthError
from custom_components.beszel.const import DOMAIN


async def test_user_flow_normalises_host(hass):
    """The user flow stores lower-case keys and a normalised host."""
    with (
        patch("custom_components.beszel.config_flow.BeszelApiClient") as api_class,
        patch("custom_components.beszel.async_setup_entry", return_value=True),
    ):
        api_class.return_value.async_authenticate = AsyncMock()
        api_class.return_value.host = "http://beszel.local"
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "beszel.local/",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "http://beszel.local",
        CONF_PASSWORD: "password",
        CONF_USERNAME: "user",
    }
    assert result["result"].unique_id == "http://beszel.local_user"


async def test_user_flow_reports_invalid_authentication(hass):
    """Invalid credentials return the translated authentication error."""
    with patch("custom_components.beszel.config_flow.BeszelApiClient") as api_class:
        api_class.return_value.async_authenticate = AsyncMock(
            side_effect=BeszelApiAuthError("invalid credentials")
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: "beszel.local",
                CONF_PASSWORD: "wrong",
                CONF_USERNAME: "user",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauthentication_updates_only_the_password(hass):
    """Reauthentication retains the configured Hub and username."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "http://beszel.local",
            CONF_PASSWORD: "old",
            CONF_USERNAME: "user",
        },
        unique_id="http://beszel.local_user",
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"entry_id": entry.entry_id, "source": SOURCE_REAUTH},
        data=entry.data,
    )
    assert result["step_id"] == "reauth_confirm"
    with (
        patch("custom_components.beszel.config_flow.BeszelApiClient") as api_class,
        patch.object(hass.config_entries, "async_reload", return_value=True) as reload,
    ):
        api_class.return_value.async_authenticate = AsyncMock()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-password"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {
        CONF_HOST: "http://beszel.local",
        CONF_PASSWORD: "new-password",
        CONF_USERNAME: "user",
    }
    reload.assert_awaited_once_with(entry.entry_id)
