"""Define tests for the SimpliSafe config flow."""
import json
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

from simplipy.errors import SimplipyError

from homeassistant import data_entry_flow
from homeassistant.components.simplisafe import DOMAIN, config_flow
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME

from tests.common import MockConfigEntry, mock_coro


def mock_api():
    """Mock SimpliSafe API class."""
    api = MagicMock()
    type(api).refresh_token = PropertyMock(return_value="12345abc")
    return api


async def test_duplicate_error(hass):
    """Test that errors are shown when duplicates are added."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    MockConfigEntry(domain=DOMAIN, unique_id="user@email.com", data=conf).add_to_hass(
        hass
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_credentials(hass):
    """Test that invalid credentials throws an error."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    flow = config_flow.SimpliSafeFlowHandler()
    flow.hass = hass
    flow.context = {"source": SOURCE_USER}

    with patch(
        "simplipy.API.login_via_credentials",
        return_value=mock_coro(exception=SimplipyError),
    ):
        result = await flow.async_step_user(user_input=conf)
        assert result["errors"] == {"base": "invalid_credentials"}


async def test_show_form(hass):
    """Test that the form is served with no input."""
    flow = config_flow.SimpliSafeFlowHandler()
    flow.hass = hass
    flow.context = {"source": SOURCE_USER}

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_import(hass):
    """Test that the import step works."""
    conf = {CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"}

    flow = config_flow.SimpliSafeFlowHandler()
    flow.hass = hass
    flow.context = {"source": SOURCE_USER}

    mop = mock_open(read_data=json.dumps({"refresh_token": "12345"}))

    with patch(
        "simplipy.API.login_via_credentials",
        return_value=mock_coro(return_value=mock_api()),
    ):
        with patch("homeassistant.util.json.open", mop, create=True):
            with patch("homeassistant.util.json.os.open", return_value=0):
                with patch("homeassistant.util.json.os.replace"):
                    result = await flow.async_step_import(import_config=conf)

                    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
                    assert result["title"] == "user@email.com"
                    assert result["data"] == {
                        CONF_USERNAME: "user@email.com",
                        CONF_TOKEN: "12345abc",
                    }


async def test_step_user(hass):
    """Test that the user step works."""
    conf = {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
    }

    flow = config_flow.SimpliSafeFlowHandler()
    flow.hass = hass
    flow.context = {"source": SOURCE_USER}

    mop = mock_open(read_data=json.dumps({"refresh_token": "12345"}))

    with patch(
        "simplipy.API.login_via_credentials",
        return_value=mock_coro(return_value=mock_api()),
    ):
        with patch("homeassistant.util.json.open", mop, create=True):
            with patch("homeassistant.util.json.os.open", return_value=0):
                with patch("homeassistant.util.json.os.replace"):
                    result = await flow.async_step_user(user_input=conf)

                    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
                    assert result["title"] == "user@email.com"
                    assert result["data"] == {
                        CONF_USERNAME: "user@email.com",
                        CONF_TOKEN: "12345abc",
                    }
