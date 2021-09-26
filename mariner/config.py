from functools import lru_cache
from pathlib import Path
from typing import MutableMapping, Optional, Sequence

import toml


def __get_config_filename() -> Optional[str]:
    potential_paths: Sequence[Path] = [
        Path("config.toml"),
        Path("~/.mariner/config.toml"),
        Path("/etc/mariner/config.toml"),
    ]
    try:
        path = next(
            path for path in potential_paths if path.exists() and not path.is_dir()
        )
    except StopIteration:
        return None
    return str(path.absolute())


@lru_cache(maxsize=None)
def _get_config() -> MutableMapping[str, object]:
    filename = __get_config_filename()
    if filename is None:
        return {}
    with open(filename, "r") as file:
        toml_string = file.read()
        return toml.loads(toml_string)


def get_files_directory() -> Path:
    config = _get_config()
    return Path(str(config.get("files_directory", "/mnt/usb_share")))


def get_printer_display_name() -> Optional[str]:
    printer_config = _get_config().get("printer")
    if not isinstance(printer_config, dict):
        return None
    display_name = printer_config.get("display_name")
    if display_name is None:
        return None
    return str(display_name)


def get_printer_serial_port() -> str:
    default_port = "/dev/serial0"
    printer_config = _get_config().get("printer")
    if not isinstance(printer_config, dict):
        return default_port
    return str(printer_config.get("serial_port", default_port))


def get_printer_baudrate() -> int:
    default_baudrate = 115200
    printer_config = _get_config().get("printer")
    if not isinstance(printer_config, dict):
        return default_baudrate
    return int(printer_config.get("baudrate", default_baudrate))


def get_relay_pin() -> Optional[int]:
    printer_config = _get_config().get("relay_board")
    if not isinstance(printer_config, dict):
        return None
    return int(printer_config.get("relay_pin", None))


def get_relay_initial_value() -> Optional[int]:
    printer_config = _get_config().get("relay_board")
    if not isinstance(printer_config, dict):
        return None
    return int(printer_config.get("initial_value", None))


def get_relay_active_high() -> Optional[bool]:
    printer_config = _get_config().get("relay_board")
    if not isinstance(printer_config, dict):
        return None
    return bool(printer_config.get("active_high", None))


def get_http_host() -> str:
    default_host = "0.0.0.0"
    http_config = _get_config().get("http")
    if not isinstance(http_config, dict):
        return default_host
    return str(http_config.get("host", default_host))


def get_http_port() -> int:
    default_port = 5050
    http_config = _get_config().get("http")
    if not isinstance(http_config, dict):
        return default_port
    return int(http_config.get("port", default_port))


def get_cache_directory() -> str:
    default_directory = "/tmp/mariner/"
    cache_config = _get_config().get("cache")
    if not isinstance(cache_config, dict):
        return default_directory
    return str(cache_config.get("directory", default_directory))


def get_ha_srv() -> Optional[str]:
    ha_config = _get_config().get("homeassistant")
    if not isinstance(ha_config, dict):
        return None
    ha_srv = printer_config.get("address")
    if ha_srv is None:
        return None
    return str(ha_srv)


def get_ha_usr() -> Optional[str]:
    ha_config = _get_config().get("homeassistant")
    if not isinstance(ha_config, dict):
        return None
    ha_usr = printer_config.get("user")
    if ha_usr is None:
        return None
    return str(ha_usr)


def get_ha_pass() -> Optional[str]:
    ha_config = _get_config().get("homeassistant")
    if not isinstance(ha_config, dict):
        return None
    ha_pass = printer_config.get("password")
    if ha_pass is None:
        return None
    return str(ha_pass)


def get_ha_topic() -> Optional[str]:
    ha_config = _get_config().get("homeassistant")
    if not isinstance(ha_config, dict):
        return None
    ha_topic = printer_config.get("topic")
    if ha_topic is None:
        return None
    return str(ha_topic)

