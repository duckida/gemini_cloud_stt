"""Config flow for Gemini Cloud STT integration."""

from __future__ import annotations

from typing import Any

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_MODEL, CONF_API_KEY, CONF_LANGUAGE, CONF_VALUE_TEMPLATE
from homeassistant.core import callback, HomeAssistant

import openai
from .const import (
    DEFAULT_MODEL,
    DOMAIN,
    SUPPORTED_MODELS,
    GEMINI_BASE_URL,
    SUPPORTED_LANGUAGES,
    CONF_PROMPT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): vol.In(SUPPORTED_MODELS),
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    def sync_create_and_validate():
        client = openai.OpenAI(api_key=data[CONF_API_KEY], base_url=GEMINI_BASE_URL)
        client.models.list()
    await hass.async_add_executor_job(sync_create_and_validate)


class GeminiCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gemini Cloud STT integration."""

    VERSION = 1

    _name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}

        try:
            await validate_input(self.hass, user_input)
        except Exception as err:
            errors["base"] = "unknown"
            _LOGGER.error("Error validating gemini api key")
        else:
            return self.async_create_entry(
                title="Gemini Cloud STT",
                data=user_input,
            )
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return GeminiCloudOptionsFlowHandler()


class GeminiCloudOptionsFlowHandler(OptionsFlow):
    """Handle a options flow for Google Cloud STT integration."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="Gemini Cloud STT", data=user_input)

        current_model = self.config_entry.options.get(CONF_MODEL, DEFAULT_MODEL)
        current_language = self.config_entry.options.get(CONF_LANGUAGE, "auto")
        current_prompt = CONF_PROMPT

        dynamic_schema = vol.Schema({
            vol.Optional(CONF_MODEL, default=current_model): vol.In(SUPPORTED_MODELS),
            vol.Optional(CONF_LANGUAGE, default=current_language): vol.In(SUPPORTED_LANGUAGES + ['auto']),
            vol.Optional(
                CONF_VALUE_TEMPLATE,
                description={"suggested_value": CONF_PROMPT},
                default=current_prompt
            ): str,
        })

        return self.async_show_form(step_id="init", data_schema=dynamic_schema)