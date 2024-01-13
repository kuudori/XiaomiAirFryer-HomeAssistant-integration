"""The Xiaomi AirFryer component."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .fryer_miot import FryerMiot, FryerMiotYBAF, FryerMiotSCK, FryerMiotMi
from .const import (
    DOMAIN,
    DOMAINS,
    DEFAULT_SCAN_INTERVAL,
    MODELS_CARELI,
    MODELS_SILEN,
    MODELS_MIOT,
    MODELS_ALL_DEVICES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, hass_config: dict):
    """Set up the Xiaomi AirFryer Component."""
    hass.data[DOMAIN] = {}
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Update options if available"""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return all(
        [
            await hass.config_entries.async_forward_entry_unload(entry, domain)
            for domain in DOMAINS
        ]
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a Xiaomi AirFryer from a config entry."""
    config = entry.data or entry.options

    host = config.get("host")
    token = config.get("token")
    model = config.get("model", "")
    scan_interval = config.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    fryer_class = determine_fryer_class(model)
    fryer = fryer_class(host, token, model=model)
    hass.data[DOMAIN][host] = fryer

    for platform in DOMAINS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


def determine_fryer_class(model):
    """Determine the fryer class based on the model."""
    if model in MODELS_CARELI:
        return FryerMiot
    elif model in MODELS_SILEN:
        return FryerMiotSCK
    elif model in MODELS_MIOT:
        return FryerMiotMi
    elif model in MODELS_ALL_DEVICES:
        return FryerMiot
    else:
        _LOGGER.error("Unknown model: %s", model)
        return FryerMiot  # Default class
