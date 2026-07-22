from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_RADIUS,
    CONF_THRESHOLD,
    DEFAULT_RADIUS,
    DEFAULT_THRESHOLD,
    DOMAIN,
)


class SwissRainRadarConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            user_input["latitude"] = self.hass.config.latitude
            user_input["longitude"] = self.hass.config.longitude

            return self.async_create_entry(
                title="MeteoSwiss Rain Radar",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_RADIUS,
                    default=DEFAULT_RADIUS,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_THRESHOLD,
                    default=DEFAULT_THRESHOLD,
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_RADIUS,
                    default=self.config_entry.options.get(
                        CONF_RADIUS,
                        self.config_entry.data[CONF_RADIUS],
                    ),
                ): vol.Coerce(float),

                vol.Optional(
                    CONF_THRESHOLD,
                    default=self.config_entry.options.get(
                        CONF_THRESHOLD,
                        self.config_entry.data[CONF_THRESHOLD],
                    ),
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )